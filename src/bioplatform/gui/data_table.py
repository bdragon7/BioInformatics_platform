from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median


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
            if role in (qt.Qt.DisplayRole, qt.Qt.EditRole):
                return self.rows[index.row()][index.column()]
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
            self.dataChanged.emit(index, index, [qt.Qt.DisplayRole])
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
            self.dataChanged.emit(idx, idx, [qt.Qt.DisplayRole])

        def redo(self) -> None:
            if not self.redo_stack:
                return
            action = self.redo_stack.pop()
            self.rows[action.row][action.col] = action.new
            self.undo_stack.append(action)
            idx = self.index(action.row, action.col)
            self.dataChanged.emit(idx, idx, [qt.Qt.DisplayRole])

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
