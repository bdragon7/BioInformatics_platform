from __future__ import annotations

import json
import os
from dataclasses import dataclass
from itertools import product
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .local_engine import GemmaLoader

Provider = Literal["chatgpt", "gemini", "local"]


@dataclass(slots=True)
class DoEMessage:
    role: Literal["user", "assistant"]
    content: str


class DoEAssistant:
    """Design-of-experiments assistant with cloud + local Gemma backends."""

    def __init__(self, provider: Provider = "chatgpt", api_key: str | None = None) -> None:
        self.provider = provider
        self.api_key = api_key or self._read_key(provider)
        self.history: list[DoEMessage] = []
        self.gemma_loader = GemmaLoader()

    @staticmethod
    def _read_key(provider: Provider) -> str | None:
        if provider == "chatgpt":
            return os.environ.get("OPENAI_API_KEY")
        if provider == "gemini":
            return os.environ.get("GEMINI_API_KEY")
        return None

    @staticmethod
    def system_prompt() -> str:
        return (
            "You are an experimental design assistant for biology labs. "
            "Recommend statistically sound, practical designs with sample-size and randomization guidance."
        )

    def _with_scientific_context(self, user_message: str, pipeline_stats: dict[str, float] | None = None) -> str:
        if not pipeline_stats:
            return user_message
        stats_text = ", ".join(f"{k}={v:.4g}" for k, v in pipeline_stats.items())
        return (
            "You are a biophysics and microbiology expert. "
            f"Current pipeline stats: {stats_text}. "
            "Use this context in your recommendation.\n\n"
            + user_message
        )

    def chat(self, user_message: str, pipeline_stats: dict[str, float] | None = None) -> str:
        contextual_message = self._with_scientific_context(user_message, pipeline_stats)
        self.history.append(DoEMessage("user", contextual_message))

        if self.provider == "local":
            return self._local_chat(contextual_message)

        if self.gemma_loader.has_any_model() and not self.api_key:
            return self._local_chat(contextual_message)

        if not self.api_key:
            return (
                "API key missing. Configure OPENAI_API_KEY for ChatGPT or GEMINI_API_KEY for Gemini. "
                "Alternatively place Gemma GGUF model files in models/llm/ for local mode."
            )

        if self.provider == "chatgpt":
            return self._chatgpt_chat(contextual_message)
        return self._gemini_chat(contextual_message)

    def _local_chat(self, contextual_message: str) -> str:
        message = self.gemma_loader.generate(self.system_prompt() + "\n\n" + contextual_message)
        self.history.append(DoEMessage("assistant", message))
        return message

    def stream_chat(self, user_message: str, pipeline_stats: dict[str, float] | None = None):  # type: ignore[no-untyped-def]
        contextual_message = self._with_scientific_context(user_message, pipeline_stats)
        self.history.append(DoEMessage("user", contextual_message))
        for token in self.gemma_loader.stream_generate(self.system_prompt() + "\n\n" + contextual_message):
            yield token

    def local_models_status(self) -> dict[str, object]:
        defaults = self.gemma_loader.resolve_default_model_paths()
        return {
            "available": self.gemma_loader.has_any_model(),
            "active": self.gemma_loader.active_model.path.name if self.gemma_loader.active_model else None,
            "gemma_2b": str(defaults["gemma_2b"]) if defaults["gemma_2b"] else None,
            "gemma_7b": str(defaults["gemma_7b"]) if defaults["gemma_7b"] else None,
        }

    def _chatgpt_chat(self, user_message: str) -> str:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": self.system_prompt()},
                *[{"role": m.role, "content": m.content} for m in self.history],
            ],
            "temperature": 0.2,
        }
        req = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=40) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            message = body["choices"][0]["message"]["content"]
            self.history.append(DoEMessage("assistant", message))
            return message
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"ChatGPT request failed: {exc}"

    def _gemini_chat(self, user_message: str) -> str:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={self.api_key}"
        )
        prompt = self.system_prompt() + "\n\n" + "\n".join(f"{m.role}: {m.content}" for m in self.history)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        req = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=40) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            message = body["candidates"][0]["content"]["parts"][0]["text"]
            self.history.append(DoEMessage("assistant", message))
            return message
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"Gemini request failed: {exc}"

    def generate_factorial_design(self, factors: list[str], levels: list[int]) -> list[dict[str, int]]:
        if len(factors) != len(levels):
            raise ValueError("factors and levels must have same length")
        runs = product(*[range(level) for level in levels])
        return [dict(zip(factors, run)) for run in runs]

    def reset_conversation(self) -> None:
        self.history.clear()
