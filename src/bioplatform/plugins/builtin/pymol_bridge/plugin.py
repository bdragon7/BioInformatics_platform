from __future__ import annotations

import subprocess
import sys
from typing import Any

from bioplatform.core.structure_integration import detect_pymol
from bioplatform.plugins.base import BioPlugin, PluginContext


class Plugin(BioPlugin):
    plugin_id = "structure.pymol_bridge"
    plugin_name = "PyMOL Structural Bridge"

    def register_ui(self, context: PluginContext) -> dict[str, str]:
        status = detect_pymol()
        return {
            "title": "PyMOL Bridge",
            "subtitle": status.message,
            "workspace": context.workspace,
        }

    def execute_logic(self, payload: dict[str, object]) -> dict[str, object]:
        mode = str(payload.get("mode", "status"))
        if mode == "status":
            status = detect_pymol()
            return {"available": status.available, "message": status.message}

        if mode == "install":
            cmd = [sys.executable, "-m", "pip", "install", "git+https://github.com/schrodinger/pymol-open-source.git"]
            proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
            status = detect_pymol()
            return {
                "ok": proc.returncode == 0 and status.available,
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "")[-4000:],
                "stderr": (proc.stderr or "")[-4000:],
                "available": status.available,
            }

        if mode == "health":
            status = detect_pymol()
            return {
                "plugin": self.plugin_id,
                "available": status.available,
                "message": status.message,
                "source": "github.com/schrodinger/pymol-open-source",
            }

        raise ValueError("Unsupported PyMOL bridge mode")
