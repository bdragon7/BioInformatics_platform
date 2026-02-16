from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..core.structure_integration import detect_pymol
from ..llm.doe_assistant import DoEAssistant
from ..visualization.editor_state import GraphEditorState, GraphElement


@dataclass(slots=True)
class StructureSessionState:
    selected_residue: str
    ligand_distance_a: float
    scene_name: str


def create_structure_viewport_widget():
    """Create PyMOL-backed structural viewport with safe fallback.

    Returns a QWidget subclass or `None` when PySide6 is unavailable.
    """
    try:
        from PySide6.QtCore import QThread, Qt, Signal
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import (
            QDialog,
            QFrame,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QSlider,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except Exception:
        return None

    class PyMOLCommandWorker(QThread):
        finished_ok = Signal(str)
        failed = Signal(str)

        def __init__(self, command: str) -> None:
            super().__init__()
            self.command = command

        def run(self) -> None:  # type: ignore[override]
            try:
                import pymol.cmd as cmd  # type: ignore

                cmd.do(self.command)
                self.finished_ok.emit(self.command)
            except Exception as exc:
                self.failed.emit(str(exc))

    class GemmaInsightWorker(QThread):
        token = Signal(str)
        complete = Signal(str)

        def __init__(self, assistant: DoEAssistant, prompt: str) -> None:
            super().__init__()
            self.assistant = assistant
            self.prompt = prompt

        def run(self) -> None:  # type: ignore[override]
            chunks: list[str] = []
            for tok in self.assistant.stream_chat(self.prompt):
                chunks.append(tok)
                self.token.emit(tok)
            self.complete.emit("".join(chunks))

    class StructureViewport(QWidget):
        residueSelected = Signal(int)

        def __init__(self) -> None:
            super().__init__()
            self.state = GraphEditorState()
            self.state.upsert(GraphElement(id="scene", kind="pymol-scene", properties={"camera": "default"}))
            self._pymol_worker: PyMOLCommandWorker | None = None
            self._gemma_worker: GemmaInsightWorker | None = None
            self._assistant = DoEAssistant(provider="local")

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            header = QFrame()
            header.setObjectName("GlassPanel")
            h = QHBoxLayout(header)
            h.addWidget(QLabel("Apex Structural Intelligence"))
            self.status_label = QLabel("Initializing")
            h.addWidget(self.status_label)
            root.addWidget(header)

            body = QHBoxLayout()
            self.viewport = QTextEdit()
            self.viewport.setReadOnly(True)
            self.viewport.setPlaceholderText("PyMOL viewport stream / fallback render log")
            body.addWidget(self.viewport, 3)

            side = QVBoxLayout()
            self.history_slider = QSlider(Qt.Orientation.Horizontal)
            self.history_slider.setRange(0, 0)
            self.history_slider.valueChanged.connect(self._scrub_history)
            side.addWidget(QLabel("HistorySlider"))
            side.addWidget(self.history_slider)

            self.sync_btn = QPushButton("Sync Selected Residue -> Table")
            self.sync_btn.clicked.connect(lambda: self.select_residue("TYR-154", 154))
            side.addWidget(self.sync_btn)

            self.outlier_btn = QPushButton("Focus Outlier")
            self.outlier_btn.clicked.connect(lambda: self.focus_outlier(index=42, x=12.4, y=18.2, z=6.9))
            side.addWidget(self.outlier_btn)

            self.docking_btn = QPushButton("Apply Docking CGO Overlay")
            self.docking_btn.clicked.connect(lambda: self.push_docking_overlay(score=-7.4))
            side.addWidget(self.docking_btn)

            self.gemma_btn = QPushButton("Gemma Structural Mentor")
            self.gemma_btn.clicked.connect(self.generate_gemma_insight)
            side.addWidget(self.gemma_btn)

            body.addLayout(side, 2)
            root.addLayout(body)

            self._init_pymol_status()

        def _init_pymol_status(self) -> None:
            status = detect_pymol()
            if status.available:
                self.status_label.setText("PyMOL: embedded")
                self.viewport.append("PyMOL backend detected. Commands will run in dedicated QThread.")
            else:
                self.status_label.setText("PyMOL: fallback")
                self.viewport.append(status.message)

        def _run_pymol_command(self, command: str) -> None:
            self._pymol_worker = PyMOLCommandWorker(command)
            self._pymol_worker.finished_ok.connect(lambda c: self.viewport.append(f"cmd.do -> {c}"))
            self._pymol_worker.failed.connect(lambda e: self.viewport.append(f"PyMOL fallback log: {e}"))
            self._pymol_worker.start()

        def select_residue(self, residue_label: str, table_row: int) -> None:
            self.viewport.append(f"Selected residue: {residue_label}")
            self.residueSelected.emit(table_row)
            self.state.set_property("scene", "selected_residue", residue_label)
            self.history_slider.setRange(0, len(self.state._undo))
            self._run_pymol_command(f"select hotspot, resi {table_row}; color cyan, hotspot")

        def focus_outlier(self, index: int, x: float, y: float, z: float) -> None:
            self.viewport.append(f"Outlier #{index} => zoom center @ ({x:.2f}, {y:.2f}, {z:.2f})")
            self.state.set_property("scene", f"outlier_{index}", {"x": x, "y": y, "z": z})
            self.history_slider.setRange(0, len(self.state._undo))
            self._run_pymol_command(f"pseudoatom outlier, pos=[{x},{y},{z}]; show spheres, outlier; color red, outlier")

        def push_docking_overlay(self, score: float) -> None:
            self.viewport.append(f"CGO docking overlay updated. score={score:.2f}")
            self.state.set_property("scene", "docking_score", score)
            self.history_slider.setRange(0, len(self.state._undo))
            # Placeholder CGO command hook.
            self._run_pymol_command("set cgo_line_width, 4")

        def _scrub_history(self, value: int) -> None:
            while len(self.state._undo) > value:
                if not self.state.undo():
                    break
            while len(self.state._undo) < value and self.state._redo:
                if not self.state.redo():
                    break
            self.viewport.append(f"History scrubbed -> {value}")

        def generate_gemma_insight(self) -> None:
            props = self.state.elements["scene"].properties
            residue = str(props.get("selected_residue", "TYR-154"))
            prompt = (
                "You are a structural mentor. "
                f"Ligand is 3.2Å from {residue}. "
                "Relate this to ionic strength and growth kinetics in one paragraph."
            )
            self.viewport.append("[Gemma] generating structural insight…")
            self._gemma_worker = GemmaInsightWorker(self._assistant, prompt)
            self._gemma_worker.token.connect(lambda t: self.viewport.insertPlainText(t))
            self._gemma_worker.complete.connect(lambda _: self.viewport.append("\n[Gemma] complete."))
            self._gemma_worker.start()

    return StructureViewport


def open_structure_viewport(parent: object | None = None, on_residue_row: Callable[[int], None] | None = None) -> None:
    widget_cls = create_structure_viewport_widget()
    if widget_cls is None:
        return

    from PySide6.QtWidgets import QDialog, QVBoxLayout

    dlg = QDialog(parent)
    dlg.setWindowTitle("Apex Structural Intelligence")
    layout = QVBoxLayout(dlg)
    widget = widget_cls()
    if on_residue_row is not None:
        widget.residueSelected.connect(on_residue_row)
    layout.addWidget(widget)
    dlg.resize(1100, 760)
    dlg.exec()
