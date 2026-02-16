from __future__ import annotations

import csv
from math import sqrt
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median


def _col_to_index(label: str) -> int:
    label = label.strip().upper()
    if not label or not label.isalpha():
        raise ValueError("Invalid column label")
    value = 0
    for ch in label:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value - 1


def _cell_ref_to_pos(ref: str) -> tuple[int, int]:
    ref = ref.strip().upper()
    letters = ""
    numbers = ""
    for ch in ref:
        if ch.isalpha() and not numbers:
            letters += ch
        elif ch.isdigit():
            numbers += ch
        else:
            raise ValueError("Invalid cell reference")
    if not letters or not numbers:
        raise ValueError("Invalid cell reference")
    row = int(numbers) - 1
    if row < 0:
        raise ValueError("Row must be >= 1")
    return row, _col_to_index(letters)


def _safe_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def evaluate_formula(rows: list[list[str]], formula: str, current_cell: tuple[int, int], depth: int = 0) -> str:
    if depth > 12:
        return "#CYCLE"
    expr = formula.strip()
    if not expr.startswith("="):
        return formula
    body = expr[1:].strip()

    def cell_value(r: int, c: int) -> float:
        if r < 0 or c < 0 or r >= len(rows) or c >= len(rows[r]):
            return 0.0
        if (r, c) == current_cell:
            return 0.0
        raw = rows[r][c]
        if isinstance(raw, str) and raw.startswith("="):
            nested = evaluate_formula(rows, raw, (r, c), depth + 1)
            return _safe_float(nested)
        return _safe_float(str(raw))

    def range_values(range_expr: str) -> list[float]:
        if ":" not in range_expr:
            r, c = _cell_ref_to_pos(range_expr)
            return [cell_value(r, c)]
        left, right = [x.strip() for x in range_expr.split(":", 1)]
        r1, c1 = _cell_ref_to_pos(left)
        r2, c2 = _cell_ref_to_pos(right)
        rs = range(min(r1, r2), max(r1, r2) + 1)
        cs = range(min(c1, c2), max(c1, c2) + 1)
        vals = []
        for rr in rs:
            for cc in cs:
                vals.append(cell_value(rr, cc))
        return vals

    upper = body.upper()
    for fn in ["SUM", "AVERAGE", "MIN", "MAX", "STDDEV", "STDEV"]:
        if upper.startswith(f"{fn}(") and body.endswith(")"):
            inner = body[len(fn) + 1 : -1].strip()
            vals = range_values(inner)
            if not vals:
                return "0"
            if fn == "SUM":
                return str(sum(vals))
            if fn == "AVERAGE":
                return str(sum(vals) / len(vals))
            if fn == "MIN":
                return str(min(vals))
            if fn == "MAX":
                return str(max(vals))
            if len(vals) <= 1:
                return "0"
            avg = sum(vals) / len(vals)
            sample_var = sum((v - avg) ** 2 for v in vals) / (len(vals) - 1)
            return str(sqrt(sample_var))

    if upper.startswith("SQRT(") and body.endswith(")"):
        inner = body[5:-1].strip()
        vals = range_values(inner) if ":" in inner or (inner and inner[0].isalpha()) else []
        if vals:
            return str(sqrt(max(vals[0], 0.0)))
        try:
            return str(sqrt(max(float(inner), 0.0)))
        except Exception:
            return "#ERR"

    tokens = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch.isalpha():
            start = i
            while i < len(body) and body[i].isalpha():
                i += 1
            while i < len(body) and body[i].isdigit():
                i += 1
            ref = body[start:i]
            try:
                rr, cc = _cell_ref_to_pos(ref)
                tokens.append(str(cell_value(rr, cc)))
            except Exception:
                return "#ERR"
            continue
        tokens.append(ch)
        i += 1

    safe_expr = "".join(tokens)
    safe_expr = safe_expr.replace("SQRT", "sqrt")
    if any(ch not in "0123456789.+-*/() SQRTsqrt" for ch in safe_expr):
        return "#ERR"
    try:
        return str(eval(safe_expr, {"__builtins__": {}}, {"sqrt": sqrt}))
    except Exception:
        return "#ERR"


@dataclass(slots=True)
class EditAction:
    row: int
    col: int
    old: str
    new: str


class QtImports:
    def __init__(self) -> None:
        from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt, Signal, Slot
        from PySide6.QtWidgets import (
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QTableView,
            QVBoxLayout,
            QWidget,
        )

        self.QAbstractTableModel = QAbstractTableModel
        self.QModelIndex = QModelIndex
        self.QObject = QObject
        self.Qt = Qt
        self.Signal = Signal
        self.Slot = Slot
        self.QFileDialog = QFileDialog
        self.QHBoxLayout = QHBoxLayout
        self.QLabel = QLabel
        self.QLineEdit = QLineEdit
        self.QPushButton = QPushButton
        self.QTableView = QTableView
        self.QVBoxLayout = QVBoxLayout
        self.QWidget = QWidget


def create_data_viewer_widget():
    qt = QtImports()

    class CsvTableModel(qt.QAbstractTableModel):
        data_edited = qt.Signal(int)

        def __init__(self) -> None:
            super().__init__()
            self.headers: list[str] = []
            self.rows: list[list[str]] = []
            self.undo_stack: list[EditAction] = []
            self.redo_stack: list[EditAction] = []

        def load_csv(self, path: Path) -> None:
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                records = list(reader)
            self.beginResetModel()
            if records:
                self.headers = records[0]
                self.rows = records[1:]
            else:
                self.headers = []
                self.rows = []
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.endResetModel()

        def rowCount(self, parent=qt.QModelIndex()):  # type: ignore[override]
            return 0 if parent.isValid() else len(self.rows)

        def columnCount(self, parent=qt.QModelIndex()):  # type: ignore[override]
            return 0 if parent.isValid() else len(self.headers)

        def data(self, index, role=qt.Qt.DisplayRole):  # type: ignore[override]
            if not index.isValid():
                return None
            raw = self.rows[index.row()][index.column()]
            if role == qt.Qt.EditRole:
                return raw
            if role == qt.Qt.DisplayRole:
                if isinstance(raw, str) and raw.startswith("="):
                    return evaluate_formula(self.rows, raw, (index.row(), index.column()))
                return raw
            return None

        def setData(self, index, value, role=qt.Qt.EditRole):  # type: ignore[override]
            if not index.isValid() or role != qt.Qt.EditRole:
                return False
            old = self.rows[index.row()][index.column()]
            new = str(value)
            if old == new:
                return False
            self.rows[index.row()][index.column()] = new
            self.undo_stack.append(EditAction(index.row(), index.column(), old, new))
            self.redo_stack.clear()
            top_left = self.index(0, 0) if self.rows and self.headers else index
            bottom_right = self.index(max(len(self.rows) - 1, 0), max(len(self.headers) - 1, 0)) if self.rows and self.headers else index
            self.dataChanged.emit(top_left, bottom_right, [qt.Qt.DisplayRole, qt.Qt.EditRole])
            self.data_edited.emit(len(self.undo_stack))
            return True

        def flags(self, index):  # type: ignore[override]
            return qt.Qt.ItemIsSelectable | qt.Qt.ItemIsEnabled | qt.Qt.ItemIsEditable

        def headerData(self, section, orientation, role=qt.Qt.DisplayRole):  # type: ignore[override]
            if role != qt.Qt.DisplayRole:
                return None
            if orientation == qt.Qt.Horizontal and 0 <= section < len(self.headers):
                return self.headers[section]
            if orientation == qt.Qt.Vertical:
                return str(section + 1)
            return None

        def sort(self, column: int, order):  # type: ignore[override]
            self.layoutAboutToBeChanged.emit()
            self.rows.sort(key=lambda r: r[column] if column < len(r) else "", reverse=order == qt.Qt.DescendingOrder)
            self.layoutChanged.emit()

        def undo(self) -> None:
            if not self.undo_stack:
                return
            action = self.undo_stack.pop()
            self.rows[action.row][action.col] = action.old
            self.redo_stack.append(action)
            idx = self.index(action.row, action.col)
            self.dataChanged.emit(self.index(0, 0), self.index(max(len(self.rows)-1,0), max(len(self.headers)-1,0)), [qt.Qt.DisplayRole, qt.Qt.EditRole])

        def redo(self) -> None:
            if not self.redo_stack:
                return
            action = self.redo_stack.pop()
            self.rows[action.row][action.col] = action.new
            self.undo_stack.append(action)
            idx = self.index(action.row, action.col)
            self.dataChanged.emit(self.index(0, 0), self.index(max(len(self.rows)-1,0), max(len(self.headers)-1,0)), [qt.Qt.DisplayRole, qt.Qt.EditRole])

        def column_stats(self, col: int) -> str:
            values = []
            missing = 0
            for row in self.rows:
                val = row[col] if col < len(row) else ""
                if val == "":
                    missing += 1
                    continue
                try:
                    values.append(float(val))
                except ValueError:
                    pass
            if not values:
                return f"missing={missing}, non-numeric"
            return (
                f"mean={mean(values):.4g}, median={median(values):.4g}, "
                f"min={min(values):.4g}, max={max(values):.4g}, missing={missing}"
            )

    class DataViewerWidget(qt.QWidget):
        selection_changed = qt.Signal(int)

        def __init__(self) -> None:
            super().__init__()
            self.model = CsvTableModel()
            self.proxy = __import__("PySide6.QtCore", fromlist=["QSortFilterProxyModel"]).QSortFilterProxyModel(self)
            self.proxy.setSourceModel(self.model)
            self.proxy.setFilterCaseSensitivity(qt.Qt.CaseInsensitive)
            self.proxy.setFilterKeyColumn(-1)

            root = qt.QVBoxLayout(self)

            top = qt.QHBoxLayout()
            self.open_btn = qt.QPushButton("Open CSV")
            self.open_btn.setToolTip("Open a CSV file for spreadsheet-style inspection and editing.")
            self.open_btn.clicked.connect(self.open_csv)
            top.addWidget(self.open_btn)

            self.search = qt.QLineEdit()
            self.search.setPlaceholderText("Find text across all columns...")
            self.search.textChanged.connect(self.proxy.setFilterFixedString)
            top.addWidget(self.search)

            self.undo_btn = qt.QPushButton("Undo")
            self.undo_btn.clicked.connect(self.model.undo)
            top.addWidget(self.undo_btn)

            self.redo_btn = qt.QPushButton("Redo")
            self.redo_btn.clicked.connect(self.model.redo)
            top.addWidget(self.redo_btn)

            self.export_btn = qt.QPushButton("Export Visible")
            self.export_btn.clicked.connect(self.export_visible)
            top.addWidget(self.export_btn)
            root.addLayout(top)

            self.table = qt.QTableView()
            self.table.setModel(self.proxy)
            self.table.setAlternatingRowColors(True)
            self.table.setSortingEnabled(True)
            self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(self.table.SelectionMode.ExtendedSelection)
            self.table.setToolTip("Use Ctrl/Shift for multi-row selection. Sort by clicking headers.")
            self.table.selectionModel().selectionChanged.connect(self._emit_selection)
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.horizontalHeader().setSectionsMovable(True)
            self.table.horizontalHeader().setToolTip("Column stats available by selecting a column.")
            root.addWidget(self.table)

            bottom = qt.QHBoxLayout()
            self.selection_label = qt.QLabel("Selected rows: 0")
            bottom.addWidget(self.selection_label)
            self.stats_label = qt.QLabel("Column stats: n/a")
            bottom.addWidget(self.stats_label)
            root.addLayout(bottom)

            self.table.clicked.connect(self._show_cell_stats)

        @qt.Slot()
        def open_csv(self) -> None:
            file_name, _ = qt.QFileDialog.getOpenFileName(self, "Open CSV", filter="CSV files (*.csv)")
            if not file_name:
                return
            self.model.load_csv(Path(file_name))
            self.table.resizeColumnsToContents()

        @qt.Slot()
        def export_visible(self) -> None:
            target, _ = qt.QFileDialog.getSaveFileName(self, "Export Visible Data", filter="CSV files (*.csv)")
            if not target:
                return
            with Path(target).open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(self.model.headers)
                for row_idx in range(self.proxy.rowCount()):
                    row = []
                    for col_idx in range(self.proxy.columnCount()):
                        index = self.proxy.index(row_idx, col_idx)
                        row.append(self.proxy.data(index, qt.Qt.DisplayRole))
                    writer.writerow(row)

        def _emit_selection(self, *_args) -> None:
            count = len(self.table.selectionModel().selectedRows())
            self.selection_label.setText(f"Selected rows: {count}")
            self.selection_changed.emit(count)

        def _show_cell_stats(self, index) -> None:  # type: ignore[no-untyped-def]
            src = self.proxy.mapToSource(index)
            self.stats_label.setText(f"Column stats: {self.model.column_stats(src.column())}")

        def load_file(self, path: Path) -> None:
            if path.suffix.lower() == ".csv":
                self.model.load_csv(path)

    return DataViewerWidget
