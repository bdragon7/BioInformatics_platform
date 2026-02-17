from __future__ import annotations

from dataclasses import dataclass
import importlib


@dataclass(slots=True)
class PluginHealth:
    name: str
    loaded: bool
    version: str = "N/A"
    error: str = ""
    install_command: str = ""


class EmbeddedPluginManager:
    """Checks presence of optional scientific plugins without hard dependency."""

    TARGETS = {
        "pymol": "pip install pymol-open-source",
        "rdkit": "conda install -c conda-forge rdkit",
        "biopandas": "pip install biopandas",
        "prody": "pip install prody",
    }

    def __init__(self) -> None:
        self.plugins: dict[str, PluginHealth] = {}
        self.refresh()

    def refresh(self) -> None:
        self.plugins = {name: self._probe(name, cmd) for name, cmd in self.TARGETS.items()}

    def _probe(self, module_name: str, install_cmd: str) -> PluginHealth:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "unknown")
            return PluginHealth(name=module_name, loaded=True, version=str(version), install_command=install_cmd)
        except Exception as exc:
            return PluginHealth(name=module_name, loaded=False, error=str(exc), install_command=install_cmd)

    def get_plugin_status(self) -> dict[str, dict[str, str | bool]]:
        return {
            name: {
                "loaded": info.loaded,
                "version": info.version,
                "error": info.error,
                "install_command": info.install_command,
            }
            for name, info in self.plugins.items()
        }
