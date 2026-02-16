from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..core.runtime import HardwareAbstractionLayer


@dataclass(frozen=True, slots=True)
class LocalModelInfo:
    name: str
    path: Path
    size_bytes: int
    variant: str


class GemmaLoader:
    """Load local Gemma GGUF models from portable storage.

    Scans `models/llm/*.gguf` and supports dual defaults:
    - gemma-2b-it (faster)
    - gemma-7b-it (higher quality)
    """

    def __init__(self, models_dir: Path | None = None, context_window: int = 4096) -> None:
        self.models_dir = models_dir or Path("models/llm")
        self.context_window = context_window
        self.hal = HardwareAbstractionLayer()
        self._llm = None
        self._active_model: LocalModelInfo | None = None

    def list_models(self) -> list[LocalModelInfo]:
        if not self.models_dir.exists():
            return []
        models: list[LocalModelInfo] = []
        for p in sorted(self.models_dir.glob("*.gguf")):
            lower = p.name.lower()
            variant = "other"
            if "2b" in lower:
                variant = "gemma-2b"
            elif "7b" in lower:
                variant = "gemma-7b"
            models.append(LocalModelInfo(name=p.stem, path=p, size_bytes=p.stat().st_size, variant=variant))
        return models

    def resolve_default_model_paths(self) -> dict[str, Path | None]:
        models = self.list_models()
        two_b = next((m.path for m in models if m.variant == "gemma-2b"), None)
        seven_b = next((m.path for m in models if m.variant == "gemma-7b"), None)
        return {"gemma_2b": two_b, "gemma_7b": seven_b}

    def has_any_model(self) -> bool:
        return bool(self.list_models())

    def _n_gpu_layers(self) -> int:
        ctx = self.hal.detect()
        return -1 if ctx.gpu_available else 0

    def load(self, prefer: str = "both") -> LocalModelInfo | None:
        models = self.list_models()
        if not models:
            self._active_model = None
            self._llm = None
            return None

        selected: LocalModelInfo
        if prefer == "2b":
            selected = next((m for m in models if m.variant == "gemma-2b"), models[0])
        elif prefer == "7b":
            selected = next((m for m in models if m.variant == "gemma-7b"), models[0])
        else:  # both: pick 2b for responsiveness, keep 7b discoverable for heavier tasks
            selected = next((m for m in models if m.variant == "gemma-2b"), models[0])

        self._active_model = selected
        try:
            from llama_cpp import Llama  # type: ignore

            self._llm = Llama(
                model_path=str(selected.path),
                n_ctx=self.context_window,
                n_gpu_layers=self._n_gpu_layers(),
                verbose=False,
            )
        except Exception:
            self._llm = None
        return selected

    @property
    def active_model(self) -> LocalModelInfo | None:
        return self._active_model

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2) -> str:
        if self._llm is None:
            self.load(prefer="both")
        if self._llm is None:
            # Portable fallback when llama-cpp not available.
            return (
                "[Local Gemma fallback] Suggested next step: review outliers and run an additional replicate "
                "set before final model selection."
            )
        out = self._llm(prompt, max_tokens=max_tokens, temperature=temperature)
        return str(out["choices"][0]["text"]).strip()

    def stream_generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2) -> Iterator[str]:
        if self._llm is None:
            self.load(prefer="both")
        if self._llm is None:
            for token in "[Local Gemma fallback] No model binary detected.".split(" "):
                yield token + " "
            return

        stream = self._llm(prompt, max_tokens=max_tokens, temperature=temperature, stream=True)
        for chunk in stream:
            token = str(chunk["choices"][0].get("text", ""))
            if token:
                yield token
