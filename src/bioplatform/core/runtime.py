from __future__ import annotations

import functools
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar


@dataclass(slots=True)
class RuntimeConfig:
    python_exe: str = "python"
    rscript_exe: str = "Rscript"
    cwd: Path | None = None


@dataclass(frozen=True, slots=True)
class ComputeContext:
    backend: str
    device_label: str
    gpu_available: bool
    details: dict[str, str]


class HardwareAbstractionLayer:
    """Detect and expose best-available compute backend.

    Priority: torch-cuda -> cupy -> numba-cpu -> numpy-cpu.
    """

    def detect(self) -> ComputeContext:
        details: dict[str, str] = {}
        try:
            import torch  # type: ignore

            if bool(torch.cuda.is_available()):
                details["cuda_device"] = str(torch.cuda.get_device_name(0))
                return ComputeContext("torch-cuda", details["cuda_device"], True, details)
            details["torch"] = "installed-cpu-only"
        except Exception as exc:
            details["torch"] = f"unavailable:{exc}"

        try:
            import cupy as cp  # type: ignore

            count = int(cp.cuda.runtime.getDeviceCount())
            if count > 0:
                props = cp.cuda.runtime.getDeviceProperties(0)
                name = props.get("name", b"cuda").decode() if isinstance(props.get("name", b""), (bytes, bytearray)) else "cuda"
                details["cupy_device"] = str(name)
                return ComputeContext("cupy", str(name), True, details)
        except Exception as exc:
            details["cupy"] = f"unavailable:{exc}"

        try:
            import numba  # type: ignore

            details["numba"] = getattr(numba, "__version__", "installed")
            return ComputeContext("numba-cpu", "CPU-optimized", False, details)
        except Exception as exc:
            details["numba"] = f"unavailable:{exc}"

        return ComputeContext("numpy-cpu", "CPU-standard", False, details)


F = TypeVar("F", bound=Callable[..., object])


def _estimate_size(args: tuple[object, ...], kwargs: dict[str, object]) -> int:
    candidates = list(args) + list(kwargs.values())
    for obj in candidates:
        if hasattr(obj, "size"):
            try:
                return int(getattr(obj, "size"))
            except Exception:
                pass
        if isinstance(obj, (list, tuple)):
            return len(obj)
    return 0


def accelerate(threshold: int = 100_000) -> Callable[[F], F]:
    """Attach backend selection metadata to a function call.

    When large inputs are detected and GPU backend is available, this wrapper
    marks the call as GPU-targeted while preserving API compatibility.
    """

    def decorator(func: F) -> F:
        hal = HardwareAbstractionLayer()

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            size = _estimate_size(args, kwargs)
            ctx = hal.detect()
            backend = ctx.backend if size >= threshold else "cpu-fast-path"
            setattr(wrapper, "last_backend", backend)
            return func(*args, **kwargs)

        setattr(wrapper, "last_backend", "unknown")
        return wrapper  # type: ignore[return-value]

    return decorator


class DualRuntimeBridge:
    """Executes Python and R tasks using subprocess for portability and isolation."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()

    def run_python(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.config.python_exe, str(script_path), *args],
            cwd=str(self.config.cwd) if self.config.cwd else None,
            check=False,
            capture_output=True,
            text=True,
        )

    def run_r(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.config.rscript_exe, str(script_path), *args],
            cwd=str(self.config.cwd) if self.config.cwd else None,
            check=False,
            capture_output=True,
            text=True,
        )
