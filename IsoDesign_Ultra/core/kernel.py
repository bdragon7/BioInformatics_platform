from __future__ import annotations

import importlib.util
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class PluginMetadata:
    name: str
    version: str
    inputs: list[str]
    outputs: list[str]
    language: str = "python"
    dependencies: list[str] | None = None


@runtime_checkable
class PluginProtocol(Protocol):
    metadata: PluginMetadata

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class BasePlugin(ABC):
    metadata: PluginMetadata

    @abstractmethod
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(slots=True)
class PluginHandle:
    plugin_id: str
    path: Path
    metadata: PluginMetadata
    executable: Any


class PluginLoader:
    """Discovery + loading for Python and R plugins with metadata validation."""

    def __init__(self, plugins_dir: Path | str = "plugins") -> None:
        self.plugins_dir = Path(plugins_dir)
        self.registry: dict[str, PluginHandle] = {}

    def discover(self) -> list[Path]:
        if not self.plugins_dir.exists():
            return []
        files: list[Path] = []
        files.extend(self.plugins_dir.rglob("*.py"))
        files.extend(self.plugins_dir.rglob("*.R"))
        return [p for p in files if p.name != "__init__.py"]

    def load_all(self) -> dict[str, PluginHandle]:
        self.registry.clear()
        for file in self.discover():
            handle = self._load_single(file)
            if handle is not None:
                self.registry[handle.plugin_id] = handle
        return self.registry

    def _load_single(self, path: Path) -> PluginHandle | None:
        metadata = self._extract_metadata(path)
        if metadata is None:
            return None
        plugin_id = f"{metadata.language}:{metadata.name}@{metadata.version}"
        if path.suffix.lower() == ".py":
            executable = self._load_python_plugin(path)
        else:
            executable = self._load_r_plugin(path)
        return PluginHandle(plugin_id=plugin_id, path=path, metadata=metadata, executable=executable)

    def _extract_metadata(self, path: Path) -> PluginMetadata | None:
        metadata_path = path.with_name("metadata.json")
        if metadata_path.exists():
            raw = json.loads(metadata_path.read_text(encoding="utf-8"))
            return PluginMetadata(
                name=str(raw.get("name", path.stem)),
                version=str(raw.get("version", "0.1.0")),
                inputs=[str(x) for x in raw.get("inputs", [])],
                outputs=[str(x) for x in raw.get("outputs", [])],
                language=str(raw.get("language", "python" if path.suffix == ".py" else "r")),
                dependencies=[str(x) for x in raw.get("dependencies", [])],
            )

        if path.suffix.lower() == ".py":
            mod = self._import_module(path)
            info = getattr(mod, "__plugin_info__", None)
            if isinstance(info, dict):
                return PluginMetadata(
                    name=str(info.get("name", path.stem)),
                    version=str(info.get("version", "0.1.0")),
                    inputs=[str(x) for x in info.get("inputs", [])],
                    outputs=[str(x) for x in info.get("outputs", [])],
                    language=str(info.get("language", "python")),
                    dependencies=[str(x) for x in info.get("dependencies", [])],
                )
        return None

    def _import_module(self, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to import plugin: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _load_python_plugin(self, path: Path) -> Any:
        module = self._import_module(path)
        if hasattr(module, "Plugin"):
            return module.Plugin()  # type: ignore[misc]
        if hasattr(module, "run"):
            return getattr(module, "run")
        return module

    def _load_r_plugin(self, path: Path) -> Any:
        try:
            from rpy2 import robjects  # type: ignore
        except Exception as exc:
            return {"error": f"rpy2 unavailable: {exc}", "path": str(path)}

        def wrapped(payload: dict[str, Any]) -> dict[str, Any]:
            script = path.read_text(encoding="utf-8")
            robjects.r(script)
            if "run_plugin" not in robjects.globalenv:
                return {"error": "R plugin missing run_plugin(payload)"}
            fn = robjects.globalenv["run_plugin"]
            res = fn(json.dumps(payload))
            return {"result": str(res[0]) if len(res) else ""}

        return wrapped

    def start_hot_reload(self) -> Any:
        """Start watchdog observer if installed; returns observer or None."""
        try:
            from watchdog.events import FileSystemEventHandler  # type: ignore
            from watchdog.observers import Observer  # type: ignore
        except Exception:
            return None

        loader = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):  # type: ignore[no-untyped-def]
                if event.is_directory:
                    return
                if str(event.src_path).endswith((".py", ".R", "metadata.json")):
                    loader.load_all()

            on_created = on_modified  # type: ignore[assignment]
            on_deleted = on_modified  # type: ignore[assignment]

        observer = Observer()
        observer.schedule(Handler(), str(self.plugins_dir), recursive=True)
        observer.start()
        return observer


def detect_hardware_backend() -> dict[str, Any]:
    """Best-effort hardware backend detection for hybrid compute routing."""
    details: dict[str, Any] = {"backend": "cpu", "gpu_available": False}
    try:
        import torch  # type: ignore

        if bool(torch.cuda.is_available()):
            details["backend"] = "torch-cuda"
            details["gpu_available"] = True
            details["device"] = str(torch.cuda.get_device_name(0))
            return details
    except Exception as exc:
        details["torch_error"] = str(exc)

    try:
        import cupy as cp  # type: ignore

        count = int(cp.cuda.runtime.getDeviceCount())
        if count > 0:
            details["backend"] = "cupy"
            details["gpu_available"] = True
            details["device_count"] = count
            return details
    except Exception as exc:
        details["cupy_error"] = str(exc)

    try:
        import numba  # type: ignore

        details["backend"] = "numba-cpu"
        details["numba_version"] = getattr(numba, "__version__", "installed")
    except Exception as exc:
        details["numba_error"] = str(exc)
    return details


def health_check() -> dict[str, Any]:
    status: dict[str, Any] = {"python": True, "r_home": bool(os.environ.get("R_HOME"))}
    status.update({f"compute_{k}": v for k, v in detect_hardware_backend().items()})
    try:
        from rdkit import Chem  # type: ignore

        mol = Chem.MolFromSmiles("CCO")
        status["rdkit"] = mol is not None
    except Exception as exc:
        status["rdkit"] = False
        status["rdkit_error"] = str(exc)

    try:
        from rpy2 import robjects  # type: ignore

        status["rpy2"] = True
        status["r_version"] = str(robjects.r("R.version.string")[0])
    except Exception as exc:
        status["rpy2"] = False
        status["rpy2_error"] = str(exc)

    return status
