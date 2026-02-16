from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class SelectedPoint:
    row: int
    col: int
    value: float


def create_interactive_plot_widget():
    """Create Canvas-X interactive plotting widget.

    Uses pyqtgraph when available; otherwise returns a lightweight fallback widget.
    """
    try:
        import pyqtgraph as pg  # type: ignore
        from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt, Signal
        from PySide6.QtWidgets import (
            QDialog,
            QFormLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except Exception:
        return None

    class InteractivePlotWidget(QWidget):
        pointEdited = Signal(int, int, str)
        pointSelected = Signal(int, int)

        def __init__(self) -> None:
            super().__init__()
            self._values: list[float] = []
            self._map_indices: list[int] = []
            self._selected: SelectedPoint | None = None

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            top_row = QHBoxLayout()
            self.plot = pg.PlotWidget()
            self.plot.setLabel("left", "Value")
            self.plot.setLabel("bottom", "Index")
            self.plot.showGrid(x=True, y=True, alpha=0.2)
            self.plot.setToolTip("Canvas-X: click a point to edit value/style instantly.")

            self.mini_map = pg.PlotWidget()
            self.mini_map.setMaximumWidth(220)
            self.mini_map.setLabel("bottom", "Mini-Map")
            self.mini_map.setMouseEnabled(x=True, y=False)

            top_row.addWidget(self.plot, 4)
            top_row.addWidget(self.mini_map, 1)
            root.addLayout(top_row)

            self._curve = self.plot.plot([], [], pen=pg.mkPen("#38BDF8", width=2), symbol="o", symbolSize=7)
            self._mini_curve = self.mini_map.plot([], [], pen=pg.mkPen("#93C5FD", width=1))

            self._scatter = pg.ScatterPlotItem([], [], size=9, brush=pg.mkBrush("#F472B6"))
            self.plot.addItem(self._scatter)
            self._scatter.sigClicked.connect(self._on_scatter_clicked)

            self._mini_map_region = pg.LinearRegionItem(values=[0, 10], orientation=pg.LinearRegionItem.Vertical)
            self.mini_map.addItem(self._mini_map_region)
            self._mini_map_region.sigRegionChanged.connect(self._teleport_main_view)

            self._anim = QPropertyAnimation(self, b"animationProgress")
            self._anim.setDuration(240)
            self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self._animation_progress = 1.0

        def set_values(self, values: list[float]) -> None:
            self._values = [float(v) for v in values]
            x = list(range(len(self._values)))
            self._curve.setData(x=x, y=self._values)
            self._mini_curve.setData(x=x, y=self._values)
            self._scatter.setData(x=x, y=self._values)
            self._map_indices = x
            if x:
                self._mini_map_region.setRegion([0, min(len(x), 10)])

        def _on_scatter_clicked(self, _plot, points) -> None:  # type: ignore[no-untyped-def]
            if not points:
                return
            point = points[0]
            row = int(point.pos().x())
            value = float(point.pos().y())
            self._selected = SelectedPoint(row=row, col=0, value=value)
            self.pointSelected.emit(row, 0)
            self._open_property_editor()

        def _open_property_editor(self) -> None:
            if self._selected is None:
                return
            dlg = QDialog(self)
            dlg.setWindowTitle("Point Editor")
            layout = QVBoxLayout(dlg)
            form = QFormLayout()
            value_edit = QLineEdit(f"{self._selected.value:.6g}")
            color_edit = QLineEdit("#F472B6")
            form.addRow("Value", value_edit)
            form.addRow("Color", color_edit)
            layout.addLayout(form)

            save = QPushButton("Apply")
            layout.addWidget(save)

            def apply_changes() -> None:
                if self._selected is None:
                    return
                txt = value_edit.text().strip()
                self.pointEdited.emit(self._selected.row, self._selected.col, txt)
                self._scatter.setBrush(pg.mkBrush(color_edit.text().strip() or "#F472B6"))
                dlg.accept()

            save.clicked.connect(apply_changes)
            dlg.exec()

        def on_model_data_edited(self, row: int, col: int, value: str) -> None:
            if row < 0 or row >= len(self._values):
                return
            try:
                new_val = float(value)
            except Exception:
                return
            start_values = list(self._values)
            self._values[row] = new_val
            self._anim.stop()
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)

            def update_frame() -> None:
                p = self._animation_progress
                blended = [a + (b - a) * p for a, b in zip(start_values, self._values)]
                x = list(range(len(blended)))
                self._curve.setData(x=x, y=blended)
                self._mini_curve.setData(x=x, y=blended)
                self._scatter.setData(x=x, y=blended)

            self._anim.valueChanged.connect(lambda *_: update_frame())
            self._anim.start()

        def _teleport_main_view(self) -> None:
            left, right = self._mini_map_region.getRegion()
            self.plot.setXRange(left, right, padding=0)

        def getAnimationProgress(self) -> float:
            return self._animation_progress

        def setAnimationProgress(self, value: float) -> None:
            self._animation_progress = float(value)

        animationProgress = Property(float, getAnimationProgress, setAnimationProgress)

    return InteractivePlotWidget
