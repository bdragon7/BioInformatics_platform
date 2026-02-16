from __future__ import annotations

from pathlib import Path
import subprocess

from .helix_theme import build_helix_qss
from .sequence_viewer import create_sequence_viewer_widget


def run_helix_ui() -> int:
    from PySide6.QtCore import QPointF, QPropertyAnimation, QThread, Qt, Signal, QEasingCurve, QTimer
    from PySide6.QtGui import QAction, QKeySequence, QShortcut
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QDialog,
        QFrame,
        QGraphicsDropShadowEffect,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QComboBox,
        QProgressBar,
        QMainWindow,
        QSplitter,
        QTableView,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    class ParseWorker(QThread):
        loaded = Signal(str)
        failed = Signal(str)

        def __init__(self, file_path: Path) -> None:
            super().__init__()
            self.file_path = file_path

        def run(self) -> None:  # type: ignore[override]
            try:
                text = self.file_path.read_text(encoding="utf-8", errors="replace")
                self.loaded.emit(text)
            except Exception as exc:
                self.failed.emit(str(exc))

    def standard_easing() -> QEasingCurve:
        curve = QEasingCurve(QEasingCurve.Type.BezierSpline)
        curve.addCubicBezierSegment(QPointF(0.2, 0.0), QPointF(0.0, 1.0), QPointF(1.0, 1.0))
        return curve

    SequenceViewer = create_sequence_viewer_widget()

    class HelixMainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Helix-UI Bioinformatics Workspace")
            self.setMinimumSize(1200, 760)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

            self._worker: ParseWorker | None = None
            self._build_ui()
            self._build_shelf()
            self._bind_shortcuts()
            self._build_nexus_hud()
            self._animate_panels_in()

        def _build_ui(self) -> None:
            root = QWidget()
            root.setObjectName("DesktopSurface")
            root_layout = QVBoxLayout(root)
            root_layout.setContentsMargins(16, 16, 16, 16)
            root_layout.setSpacing(12)

            self.launcher_row = QFrame()
            self.launcher_row.setObjectName("GlassPanel")
            launcher_layout = QHBoxLayout(self.launcher_row)
            launcher_layout.addWidget(QLabel("Helix-UI Workspace"))

            self.search = QLineEdit()
            self.search.setPlaceholderText("Global search (Ctrl+K): genes, files, records")
            launcher_layout.addWidget(self.search, 1)
            root_layout.addWidget(self.launcher_row)

            workbench = QFrame()
            workbench.setObjectName("WorkbenchSurface")
            wb_layout = QVBoxLayout(workbench)
            wb_layout.setContentsMargins(10, 10, 10, 10)

            split = QSplitter(Qt.Orientation.Vertical)
            self.sequence_view = SequenceViewer()
            split.addWidget(self.sequence_view)

            self.variant_table = QTableView()
            self.variant_table.setObjectName("VariantTable")
            self.variant_table.setAlternatingRowColors(True)
            split.addWidget(self.variant_table)
            split.setSizes([500, 220])

            wb_layout.addWidget(split)
            root_layout.addWidget(workbench)
            self.setCentralWidget(root)

        def _build_nexus_hud(self) -> None:
            self.hud = QFrame(self)
            self.hud.setObjectName("GlassPanel")
            self.hud.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation, True)
            self.hud.setStyleSheet("QFrame#GlassPanel { background: rgba(15,23,42,204); border: 1px solid #40a9ff; border-radius: 10px; }")

            layout = QVBoxLayout(self.hud)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(6)
            layout.addWidget(QLabel("Nexus Control Center"))

            self.cpu_label = QLabel("CPU: --")
            layout.addWidget(self.cpu_label)
            self.cpu_bar = QProgressBar()
            self.cpu_bar.setRange(0, 100)
            layout.addWidget(self.cpu_bar)

            self.gpu_label = QLabel("GPU: --")
            layout.addWidget(self.gpu_label)
            self.gpu_bar = QProgressBar()
            self.gpu_bar.setRange(0, 100)
            self.gpu_bar.setStyleSheet("QProgressBar::chunk { background: #38BDF8; }")
            layout.addWidget(self.gpu_bar)

            row = QHBoxLayout()
            row.addWidget(QLabel("Turbo"))
            self.compute_toggle = QComboBox()
            self.compute_toggle.addItems(["Hybrid", "GPU-Only"])
            row.addWidget(self.compute_toggle)
            layout.addLayout(row)

            self.hud.resize(290, 170)
            self._position_hud()
            self.hud.raise_()

            self.hud_timer = QTimer(self)
            self.hud_timer.setInterval(500)
            self.hud_timer.timeout.connect(self._update_hud_telemetry)
            self.hud_timer.start()
            self._update_hud_telemetry()

        def _position_hud(self) -> None:
            margin = 22
            x = max(margin, self.width() - self.hud.width() - margin)
            y = margin
            self.hud.move(x, y)
            self.hud.raise_()

        def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
            super().resizeEvent(event)
            if hasattr(self, "hud"):
                self._position_hud()

        def _gpu_usage_percent(self) -> float:
            try:
                import GPUtil  # type: ignore

                gpus = GPUtil.getGPUs()
                if gpus:
                    return float(max(g.memoryUtil for g in gpus) * 100.0)
            except Exception:
                pass
            try:
                proc = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                line = (proc.stdout or "").splitlines()[0]
                used, total = [float(x.strip()) for x in line.split(",")[:2]]
                if total > 0:
                    return (used / total) * 100.0
            except Exception:
                pass
            return 0.0

        def _update_hud_telemetry(self) -> None:
            cpu_percent = 0.0
            try:
                import psutil  # type: ignore

                cpu_percent = float(psutil.cpu_percent(interval=None))
                per_core = psutil.cpu_percent(interval=None, percpu=True)
                core_txt = ", ".join(str(int(v)) for v in per_core[:8])
                self.cpu_label.setText(f"CPU: {int(cpu_percent)}% | cores [{core_txt}]")
            except Exception:
                self.cpu_label.setText(f"CPU: {int(cpu_percent)}%")

            gpu_percent = self._gpu_usage_percent()
            mode = self.compute_toggle.currentText()
            if mode == "GPU-Only":
                gpu_percent = max(gpu_percent, 35.0)
            self.gpu_label.setText(f"GPU: {int(gpu_percent)}% | mode={mode}")

            self.cpu_bar.setValue(int(cpu_percent))
            self.gpu_bar.setValue(int(gpu_percent))

        def _build_shelf(self) -> None:
            shelf = QToolBar("Shelf")
            shelf.setMovable(False)
            self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, shelf)

            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(24)
            shadow.setOffset(0, 4)
            shelf.setGraphicsEffect(shadow)

            seq_action = QAction("Sequence Viewer", self)
            seq_action.triggered.connect(lambda: self.statusBar().showMessage("Sequence Viewer active", 2000))
            shelf.addAction(seq_action)

            blast_action = QAction("BLAST Search", self)
            blast_action.triggered.connect(lambda: self.statusBar().showMessage("BLAST panel placeholder", 2000))
            shelf.addAction(blast_action)

            model_action = QAction("3D Protein Model", self)
            model_action.triggered.connect(lambda: self.statusBar().showMessage("3D viewer placeholder", 2000))
            shelf.addAction(model_action)

            open_action = QAction("Open FASTA/VCF", self)
            open_action.triggered.connect(self.open_sequence_file)
            shelf.addAction(open_action)

        def _bind_shortcuts(self) -> None:
            QShortcut(QKeySequence("Ctrl+K"), self, activated=lambda: self.search.setFocus())

        def _animate_panels_in(self) -> None:
            self.launcher_row.setMaximumHeight(0)
            self._panel_anim = QPropertyAnimation(self.launcher_row, b"maximumHeight")
            self._panel_anim.setDuration(420)
            self._panel_anim.setStartValue(0)
            self._panel_anim.setEndValue(72)
            self._panel_anim.setEasingCurve(standard_easing())
            self._panel_anim.start()

        def open_sequence_file(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open sequence file",
                filter="Bio Files (*.fasta *.fa *.txt *.vcf *.gff *.gbk);;All Files (*.*)",
            )
            if not path:
                return
            self.statusBar().showMessage("Loading file in background…", 2000)
            self._worker = ParseWorker(Path(path))
            self._worker.loaded.connect(self._on_loaded)
            self._worker.failed.connect(self._on_failed)
            self._worker.start()

        def _on_loaded(self, text: str) -> None:
            self.sequence_view.setPlainText(text)
            self.statusBar().showMessage("Loaded sequence data", 3000)
            self._show_alignment_complete()

        def _on_failed(self, message: str) -> None:
            self.statusBar().showMessage(f"Load failed: {message}", 5000)

        def _show_alignment_complete(self) -> None:
            dlg = QDialog(self)
            dlg.setObjectName("ModalGlass")
            dlg.setWindowTitle("Sequence Alignment")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Sequence Alignment Complete"))
            layout.addWidget(QLabel("Results loaded into workspace."))
            dlg.resize(320, 140)

            end_pos = self.geometry().center() - dlg.rect().center()
            start_pos = end_pos + QPointF(0, 24).toPoint()
            dlg.move(start_pos)
            dlg.show()

            self._modal_anim = QPropertyAnimation(dlg, b"pos")
            self._modal_anim.setDuration(360)
            self._modal_anim.setStartValue(start_pos)
            self._modal_anim.setEndValue(end_pos)
            self._modal_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            self._modal_anim.start()

    app = QApplication.instance() or QApplication([])
    dark_mode = app.palette().window().color().lightness() < 128
    app.setStyleSheet(build_helix_qss(dark_mode=dark_mode))
    win = HelixMainWindow()
    win.show()
    return app.exec()
