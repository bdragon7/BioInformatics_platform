from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
# Convenience for running from a source checkout only.
# Canonical entrypoint is: python -m bioplatform
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def ensure_r_installed() -> bool:
    from bioplatform.setup import ensure_r_installed as _ensure_r_installed

    return _ensure_r_installed()


def ensure_pymol_installed() -> None:
    from bioplatform.setup import ensure_pymol_installed as _ensure_pymol_installed

    _ensure_pymol_installed()


def run_app(*, project, data, workflow, debug):
    from bioplatform.gui.app import run

    return run(project=project, data=data, workflow=workflow, debug=debug)


def run_helix() -> int:
    from bioplatform.gui.helix_main_window import run_helix_ui

    return run_helix_ui()


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

    # Optional runtime prerequisites
    r_ok = ensure_r_installed()
    if not r_ok:
        print("R runtime not available. Launching with R-dependent workflows disabled.")
    ensure_pymol_installed()
    if args.helix_ui:
        return run_helix()
    return run_app(project=args.project, data=args.data, workflow=args.workflow, debug=args.debug)


if __name__ == "__main__":
    raise SystemExit(main())
