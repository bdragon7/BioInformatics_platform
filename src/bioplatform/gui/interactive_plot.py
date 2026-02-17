from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SelectedPoint:
    row: int
    col: int
    value: float


@dataclass(slots=True)
class PlotViewState:
    kind: str = "line"
    marker: str = "o"
    line_width: float = 2.0
    color: str = "#38BDF8"
    bar_width: float = 0.65


def parse_custom_entry(command: str) -> dict[str, str]:
    """Parse user custom-entry commands like `kind=scatter;color=#aabbcc`.

    Supports separators `;` and `,` and normalizes keys to lowercase.
    """
    result: dict[str, str] = {}
    text = str(command or "").strip()
    if not text:
        return result
    for chunk in text.replace(",", ";").split(";"):
        token = chunk.strip()
        if not token:
            continue
        if "=" not in token:
            result[token.lower()] = "true"
            continue
        key, value = token.split("=", 1)
        result[key.strip().lower()] = value.strip()
    return result


def create_interactive_plot_widget():
    """Create Canvas-X interactive plotting widget.

    Uses pyqtgraph when available; otherwise returns a lightweight fallback widget.
    """
    try:
        import pyqtgraph as pg  # type: ignore
        from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, Qt, Signal
        from PySide6.QtWidgets import (
            QComboBox,
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
            self._state = PlotViewState()
            self._state_map = {
                "line": "line",
                "bar": "bar",
                "scatter": "scatter",
                "heatmap": "heatmap",
            }

            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            controls = QHBoxLayout()
            controls.addWidget(QLabel("Quick-Select"))
            self.quick_select = QComboBox()
            self.quick_select.addItems(["Line", "Bar", "Scatter", "Heatmap"])
            self.quick_select.setToolTip("Pre-configured presets with butter-smooth transitions.")
            self.quick_select.currentTextChanged.connect(self._on_quick_select_changed)
            controls.addWidget(self.quick_select)

            controls.addWidget(QLabel("Custom Entry"))
            self.custom_entry = QLineEdit()
            self.custom_entry.setPlaceholderText("kind=scatter;color=#A93226;line_width=2.4;marker=t")
            self.custom_entry.returnPressed.connect(self._on_custom_entry_submit)
            controls.addWidget(self.custom_entry, 1)

            self.custom_apply = QPushButton("Apply")
            self.custom_apply.clicked.connect(self._on_custom_entry_submit)
            controls.addWidget(self.custom_apply)
            root.addLayout(controls)

            top_row = QHBoxLayout()
            self.plot = pg.PlotWidget()
            self.plot.setLabel("left", "Value")
            self.plot.setLabel("bottom", "Index")
            self.plot.showGrid(x=True, y=True, alpha=0.12)
            self.plot.setBackground("#0F172A")
            self.plot.setToolTip("Canvas-X: click a point to edit value/style instantly.")

            self.mini_map = pg.PlotWidget()
            self.mini_map.setMaximumWidth(220)
            self.mini_map.setLabel("bottom", "Mini-Map")
            self.mini_map.setMouseEnabled(x=True, y=False)
            self.mini_map.setBackground("#0F172A")

            top_row.addWidget(self.plot, 4)
            top_row.addWidget(self.mini_map, 1)
            root.addLayout(top_row)

            self._curve = self.plot.plot([], [], pen=pg.mkPen(self._state.color, width=self._state.line_width), symbol=self._state.marker, symbolSize=7)
            self._mini_curve = self.mini_map.plot([], [], pen=pg.mkPen("#93C5FD", width=1))

            self._scatter = pg.ScatterPlotItem([], [], size=9, brush=pg.mkBrush("#F472B6"))
            self.plot.addItem(self._scatter)
            self._scatter.sigClicked.connect(self._on_scatter_clicked)

            self._bar_graph = pg.BarGraphItem(x=[], height=[], width=self._state.bar_width, brush=self._state.color)
            self.plot.addItem(self._bar_graph)
            self._bar_graph.setVisible(False)

            self._heatmap = pg.ImageItem()
            self.plot.addItem(self._heatmap)
            self._heatmap.setVisible(False)

            self._mini_map_region = pg.LinearRegionItem(values=[0, 10], orientation=pg.LinearRegionItem.Vertical)
            self.mini_map.addItem(self._mini_map_region)
            self._mini_map_region.sigRegionChanged.connect(self._teleport_main_view)

            self._anim = QPropertyAnimation(self, b"animationProgress")
            self._anim.setDuration(220)
            self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self._animation_progress = 1.0
            self._anim.valueChanged.connect(self._refresh_plot)

        def set_values(self, values: list[float]) -> None:
            filtered: list[float] = []
            for value in values:
                try:
                    filtered.append(float(value))
                except Exception:
                    filtered.append(0.0)
            self._values = filtered
            self._map_indices = list(range(len(self._values)))
            self._refresh_plot()
            if self._map_indices:
                self._mini_map_region.setRegion([0, min(len(self._map_indices), 10)])

        def load_tabular_records(self, records: list[dict[str, Any]]) -> None:
            """Auto-map first numeric column from CSV/JSON-like rows."""
            if not records:
                self.set_values([])
                return
            sample_keys = list(records[0].keys())
            chosen: str | None = None
            for key in sample_keys:
                ok = True
                for row in records[:30]:
                    try:
                        float(row.get(key, 0.0))
                    except Exception:
                        ok = False
                        break
                if ok:
                    chosen = key
                    break
            if chosen is None:
                self.set_values([0.0 for _ in records])
                return
            self.set_values([float(row.get(chosen, 0.0) or 0.0) for row in records])

        def _on_quick_select_changed(self, label: str) -> None:
            self._state.kind = self._state_map.get(label.lower(), "line")
            self._animate_refresh()

        def _on_custom_entry_submit(self) -> None:
            args = parse_custom_entry(self.custom_entry.text())
            if "kind" in args:
                kind = args["kind"].lower()
                if kind in self._state_map.values():
                    self._state.kind = kind
                    idx = ["line", "bar", "scatter", "heatmap"].index(kind)
                    self.quick_select.setCurrentIndex(idx)
            if "color" in args:
                self._state.color = args["color"]
            if "line_width" in args:
                try:
                    self._state.line_width = max(0.5, float(args["line_width"]))
                except Exception:
                    pass
            if "marker" in args:
                self._state.marker = args["marker"] or self._state.marker
            if "bar_width" in args:
                try:
                    self._state.bar_width = max(0.1, float(args["bar_width"]))
                except Exception:
                    pass
            self._animate_refresh()

        def _animate_refresh(self) -> None:
            self._anim.stop()
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()

        def _refresh_plot(self, *_args) -> None:
            x = list(range(len(self._values)))
            self._mini_curve.setData(x=x, y=self._values)
            self._scatter.setData(x=x, y=self._values)
            self._curve.setPen(pg.mkPen(self._state.color, width=self._state.line_width))
            self._curve.setSymbol(self._state.marker)

            kind = self._state.kind
            self._curve.setVisible(kind in {"line", "scatter"})
            self._scatter.setVisible(kind in {"line", "scatter"})
            self._bar_graph.setVisible(kind == "bar")
            self._heatmap.setVisible(kind == "heatmap")

            if kind in {"line", "scatter"}:
                self._curve.setData(x=x, y=self._values)
            if kind == "bar":
                self._bar_graph.setOpts(x=x, height=self._values, width=self._state.bar_width, brush=self._state.color)
            if kind == "heatmap":
                if self._values:
                    self._heatmap.setImage([self._values], levels=(min(self._values), max(self._values) or 1.0))
                else:
                    self._heatmap.clear()

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
            color_edit = QLineEdit(self._state.color)
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
                self._state.color = color_edit.text().strip() or self._state.color
                self._animate_refresh()
                dlg.accept()

            save.clicked.connect(apply_changes)
            dlg.exec()

        def on_model_data_edited(self, row: int, col: int, value: str) -> None:
            if row < 0 or row >= len(self._values):
                return
            try:
                self._values[row] = float(value)
            except Exception:
                return
            self._animate_refresh()

        def _teleport_main_view(self) -> None:
            left, right = self._mini_map_region.getRegion()
            self.plot.setXRange(left, right, padding=0)

        def getAnimationProgress(self) -> float:
            return self._animation_progress

        def setAnimationProgress(self, value: float) -> None:
            self._animation_progress = float(value)

        animationProgress = Property(float, getAnimationProgress, setAnimationProgress)

    return InteractivePlotWidget
