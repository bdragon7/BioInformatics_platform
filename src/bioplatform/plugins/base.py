from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class PluginContext:
    app_name: str
    workspace: str


class BioPlugin(ABC):
    """Base class for hot-swappable bioinformatics plugins."""

    plugin_id: str = "unknown"
    plugin_name: str = "Unnamed Plugin"

    @abstractmethod
    def register_ui(self, context: PluginContext) -> dict[str, str]:
        """Return lightweight UI metadata used by dashboard/marketplace."""

    @abstractmethod
    def execute_logic(self, payload: dict[str, object]) -> dict[str, object]:
        """Run plugin logic against core engine payload."""
