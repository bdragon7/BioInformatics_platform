from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bioplatform.gui.app import run
from bioplatform.gui.helix_main_window import run_helix_ui
from bioplatform.setup import ensure_pymol_installed, ensure_r_installed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch Bioinformatics Studio")
    parser.add_argument("--project", type=Path, help="Open a specific project path")
    parser.add_argument("--data", type=Path, help="Import a data file on launch")
    parser.add_argument("--workflow", type=str, help="Run a saved workflow by name")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging")
    parser.add_argument("--helix-ui", action="store_true", help="Launch Helix-UI glassmorphic workspace")
    return parser


def main() -> int:
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication

        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    args = build_parser().parse_args()

    # Critical runtime prerequisites
    if not ensure_r_installed():
        print("R runtime installation/verification failed. Exiting.")
        return 1
    ensure_pymol_installed()
    if args.helix_ui:
        return run_helix_ui()
    return run(project=args.project, data=args.data, workflow=args.workflow, debug=args.debug)


if __name__ == "__main__":
    raise SystemExit(main())
