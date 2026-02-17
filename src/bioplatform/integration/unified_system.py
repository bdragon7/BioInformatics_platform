from __future__ import annotations

from ..console.dual_console import DualConsoleSession
from ..logging.advanced_logger import BioInformaticsLogger
from ..plotting.visual_plot_builder import PlotConfiguration, generate_matplotlib_code
from ..plugins.embedded_plugins import EmbeddedPluginManager


class UnifiedBioInformaticsSystem:
    """Wires plotting, console, plugin health, and logging into one orchestrator."""

    def __init__(self) -> None:
        self.logger = BioInformaticsLogger()
        self.plugin_manager = EmbeddedPluginManager()
        self.console = DualConsoleSession()

    def verify_system(self) -> dict[str, dict[str, str | bool]]:
        status = self.plugin_manager.get_plugin_status()
        for name, payload in status.items():
            state = "loaded" if payload["loaded"] else "missing"
            self.logger.log("INFO", f"plugin:{name}:{state}", context="verify_system")
        return status

    def on_plot_requested(self, config: PlotConfiguration) -> str:
        code = generate_matplotlib_code(config)
        self.console.run_python("# generated plotting code")
        self.logger.log("INFO", f"plot:{config.plot_type.value}", context="plot_builder")
        return code
