from __future__ import annotations

import ast
import csv
import math
import operator
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
import statistics

from ..core.error_prevention import SpreadsheetValueGuard
from ..core.workspace import WorkspaceManager
from ..visualization.editor_state import GraphEditorState, GraphElement
from .interactive_plot import create_interactive_plot_widget


_AST_OPS: dict[type[ast.AST], object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

EXCEL_FUNCTIONS: dict[str, object] = {
    "SUM": sum,
    "ABS": abs,
    "SQRT": math.sqrt,
    "LOG": math.log10,
    "LN": math.log,
    "EXP": math.exp,
    "PI": lambda: math.pi,
    "AVERAGE": statistics.mean,
    "MEDIAN": statistics.median,
    "STDEV": statistics.stdev,
    "STDEV.S": statistics.stdev,
    "STDDEV": statistics.stdev,
    "STDEV.P": statistics.pstdev,
    "STDEV_P": statistics.pstdev,
    "VAR": statistics.variance,
    "MAX": max,
    "MIN": min,
    "COUNT": len,
}


def _format_number(value: float | int) -> str:
    if isinstance(value, float):
        return str(float(value))
    return str(value)


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


def evaluate_formula(
    rows: list[list[str]],
    formula: str,
    current_cell: tuple[int, int],
    depth: int = 0,
    visited: set[tuple[int, int]] | None = None,
) -> str:
    if depth > 24:
        return "#CYCLE"
    expr = formula.strip()
    if not expr.startswith("="):
        return formula

    seen = set() if visited is None else set(visited)
    if current_cell in seen:
        return "#CYCLE"
    seen.add(current_cell)

    body = expr[1:].strip().replace("^", "**")
    body = body.replace("STDEV.P(", "STDEV_P(")

    def cell_value(r: int, c: int) -> float:
        if r < 0 or c < 0 or r >= len(rows) or c >= len(rows[r]):
            return 0.0
        if (r, c) in seen:
            raise ValueError("cycle")
        raw = rows[r][c]
        if isinstance(raw, str) and raw.startswith("="):
            nested = evaluate_formula(rows, raw, (r, c), depth + 1, seen)
            if nested == "#CYCLE":
                raise ValueError("cycle")
            return _safe_float(nested)
        return _safe_float(str(raw))

    def range_values(start_ref: str, end_ref: str | None = None) -> list[float]:
        if end_ref is None:
            r, c = _cell_ref_to_pos(start_ref)
            return [cell_value(r, c)]
        r1, c1 = _cell_ref_to_pos(start_ref)
        r2, c2 = _cell_ref_to_pos(end_ref)
        rs = range(min(r1, r2), max(r1, r2) + 1)
        cs = range(min(c1, c2), max(c1, c2) + 1)
        vals: list[float] = []
        for rr in rs:
            for cc in cs:
                vals.append(cell_value(rr, cc))
        return vals

    def _flatten(items: list[float | list[float]]) -> list[float]:
        out: list[float] = []
        for item in items:
            if isinstance(item, list):
                out.extend(item)
            else:
                out.append(float(item))
        return out

    def _call_function(fn_name: str, args: list[float | list[float]]) -> float:
        normalized = fn_name.upper()
        fn = EXCEL_FUNCTIONS.get(normalized)
        if fn is None:
            raise ValueError("unsupported function")

        flat_args = _flatten(args)
        if normalized in {"PI"}:
            return float(fn())  # type: ignore[misc]
        if normalized in {"SUM"}:
            return float(fn(flat_args))  # type: ignore[misc]
        if normalized in {"AVERAGE", "MEDIAN", "STDEV", "STDEV.S", "STDDEV", "STDEV.P", "STDEV_P", "VAR", "MAX", "MIN"}:
            if not flat_args:
                return 0.0
            return float(fn(flat_args))  # type: ignore[misc]
        if normalized in {"COUNT"}:
            return float(fn(flat_args))  # type: ignore[misc]
        if normalized in {"ABS", "SQRT", "LOG", "LN", "EXP"}:
            value = flat_args[0] if flat_args else 0.0
            return float(fn(value))  # type: ignore[misc]
        raise ValueError("unsupported function")

    def _eval_ast(node: ast.AST) -> float | list[float]:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            try:
                rr, cc = _cell_ref_to_pos(node.id)
                return cell_value(rr, cc)
            except ValueError as exc:
                if "cycle" in str(exc).lower():
                    raise
                raise ValueError("invalid name") from exc
            except Exception as exc:
                raise ValueError("invalid name") from exc
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = _eval_ast(node.operand)
            scalar = value[0] if isinstance(value, list) and value else value
            v = float(scalar)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp):
            op = _AST_OPS.get(type(node.op))
            if op is None:
                raise ValueError("unsupported operation")
            left = _eval_ast(node.left)
            right = _eval_ast(node.right)
            lval = float(left[0] if isinstance(left, list) and left else left)
            rval = float(right[0] if isinstance(right, list) and right else right)
            return float(op(lval, rval))  # type: ignore[misc]
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__RANGE__":
                if len(node.args) != 2 or not all(isinstance(arg, ast.Constant) for arg in node.args):
                    raise ValueError("invalid range")
                start_ref = str(node.args[0].value)
                end_ref = str(node.args[1].value)
                return range_values(start_ref, end_ref)
            if not isinstance(node.func, ast.Name):
                raise ValueError("invalid call")
            args = [_eval_ast(arg) for arg in node.args]
            return _call_function(node.func.id, args)
        raise ValueError("unsupported syntax")

    translated = []
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
            if i < len(body) and body[i] == ":":
                i += 1
                right_start = i
                while i < len(body) and body[i].isalpha():
                    i += 1
                while i < len(body) and body[i].isdigit():
                    i += 1
                right_ref = body[right_start:i]
                if not right_ref:
                    return "#ERR"
                translated.append(f'__RANGE__("{ref}","{right_ref}")')
                continue
            translated.append(ref)
            continue
        translated.append(ch)
        i += 1

    safe_expr = "".join(translated)
    if any(ch not in '0123456789.+-*/() eE,_"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' for ch in safe_expr):
        return "#ERR"

    try:
        tree = ast.parse(safe_expr, mode="eval")
        result = _eval_ast(tree.body)
        scalar = float(result[0] if isinstance(result, list) and result else result)
        return _format_number(scalar)
    except ZeroDivisionError:
        return "#DIV/0!"
    except statistics.StatisticsError:
        return "#NUM!"
    except ValueError as exc:
        return "#CYCLE" if "cycle" in str(exc).lower() else "#ERR"
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
        from PySide6.QtGui import QAction, QGuiApplication, QKeySequence
        from PySide6.QtWidgets import (
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMenu,
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
        self.QAction = QAction
        self.QGuiApplication = QGuiApplication
        self.QKeySequence = QKeySequence
        self.QFileDialog = QFileDialog
        self.QHBoxLayout = QHBoxLayout
        self.QLabel = QLabel
        self.QLineEdit = QLineEdit
        self.QMenu = QMenu
        self.QPushButton = QPushButton
        self.QTableView = QTableView
        self.QVBoxLayout = QVBoxLayout
        self.QWidget = QWidget


def create_data_viewer_widget():
    qt = QtImports()

    class CsvTableModel(qt.QAbstractTableModel):
        data_edited = qt.Signal(int)
        data_edited_point = qt.Signal(int, int, str)

        def __init__(self) -> None:
            super().__init__()
            self.headers: list[str] = []
            self.rows: list[list[str]] = []
            self.undo_stack: list[EditAction] = []
            self.redo_stack: list[EditAction] = []
            self._value_guard = SpreadsheetValueGuard()
            self._workspace_manager = WorkspaceManager(Path.cwd() / ".bioplatform_workspace")

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

            header = self.headers[index.column()] if 0 <= index.column() < len(self.headers) else ""
            ok, _detail = self._value_guard.validate(header, new)
            if not ok:
                return False

            self.rows[index.row()][index.column()] = new
            action = EditAction(index.row(), index.column(), old, new)
            self.undo_stack.append(action)
            self.redo_stack.clear()
            top_left = self.index(0, 0) if self.rows and self.headers else index
            bottom_right = self.index(max(len(self.rows) - 1, 0), max(len(self.headers) - 1, 0)) if self.rows and self.headers else index
            self.dataChanged.emit(top_left, bottom_right, [qt.Qt.DisplayRole, qt.Qt.EditRole])
            self.data_edited.emit(len(self.undo_stack))
            self.data_edited_point.emit(index.row(), index.column(), new)
            self._workspace_manager.append_audit_entry(
                event="spreadsheet_edit",
                payload={"row": action.row, "col": action.col, "old": action.old, "new": action.new},
            )
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

        def insert_row(self, row_idx: int) -> None:
            target = max(0, min(row_idx, len(self.rows)))
            self.beginInsertRows(qt.QModelIndex(), target, target)
            empty_row = [""] * max(len(self.headers), 1)
            self.rows.insert(target, empty_row)
            self.endInsertRows()

        def delete_row(self, row_idx: int) -> None:
            if row_idx < 0 or row_idx >= len(self.rows):
                return
            self.beginRemoveRows(qt.QModelIndex(), row_idx, row_idx)
            self.rows.pop(row_idx)
            self.endRemoveRows()

        def undo(self) -> None:
            if not self.undo_stack:
                return
            action = self.undo_stack.pop()
            self.rows[action.row][action.col] = action.old
            self.redo_stack.append(action)
            self.dataChanged.emit(self.index(0, 0), self.index(max(len(self.rows)-1,0), max(len(self.headers)-1,0)), [qt.Qt.DisplayRole, qt.Qt.EditRole])

        def redo(self) -> None:
            if not self.redo_stack:
                return
            action = self.redo_stack.pop()
            self.rows[action.row][action.col] = action.new
            self.undo_stack.append(action)
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

    class ExcelLikeTableView(qt.QTableView):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setContextMenuPolicy(qt.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_context_menu)

        def keyPressEvent(self, event):  # type: ignore[override]
            if event.matches(qt.QKeySequence.Copy):
                self.copy_to_clipboard()
                event.accept()
                return
            if event.matches(qt.QKeySequence.Paste):
                self.paste_from_clipboard()
                event.accept()
                return
            super().keyPressEvent(event)

        def copy_to_clipboard(self) -> None:
            selection = self.selectionModel()
            if selection is None or not selection.hasSelection():
                return
            indexes = selection.selectedIndexes()
            if not indexes:
                return
            cells: dict[int, dict[int, str]] = {}
            for idx in indexes:
                cells.setdefault(idx.row(), {})[idx.column()] = str(idx.data(qt.Qt.DisplayRole) or "")
            lines: list[str] = []
            for row in sorted(cells):
                cols = cells[row]
                ordered_cols = [cols[c] for c in sorted(cols)]
                lines.append("\t".join(ordered_cols))
            qt.QGuiApplication.clipboard().setText("\n".join(lines))

        def paste_from_clipboard(self) -> None:
            clipboard_text = qt.QGuiApplication.clipboard().text()
            if not clipboard_text:
                return
            model = self.model()
            selection = self.selectionModel().selectedIndexes() if self.selectionModel() is not None else []
            start_row = selection[0].row() if selection else 0
            start_col = selection[0].column() if selection else 0

            for r_offset, row_text in enumerate(clipboard_text.splitlines()):
                if not row_text:
                    continue
                for c_offset, cell_value in enumerate(row_text.split("\t")):
                    proxy_idx = model.index(start_row + r_offset, start_col + c_offset)
                    if not proxy_idx.isValid():
                        continue
                    source_idx = model.mapToSource(proxy_idx) if hasattr(model, "mapToSource") else proxy_idx
                    source_model = model.sourceModel() if hasattr(model, "sourceModel") else model
                    source_model.setData(source_idx, cell_value, qt.Qt.EditRole)

        def _show_context_menu(self, position) -> None:  # type: ignore[no-untyped-def]
            menu = qt.QMenu(self)
            insert_action = menu.addAction("Insert Row Above")
            delete_action = menu.addAction("Delete Selected Row(s)")
            action = menu.exec(self.viewport().mapToGlobal(position))
            if action not in {insert_action, delete_action}:
                return

            selected_rows = self.selectionModel().selectedRows() if self.selectionModel() is not None else []
            if not selected_rows:
                return
            model = self.model()
            source_model = model.sourceModel() if hasattr(model, "sourceModel") else model
            source_rows = []
            for idx in selected_rows:
                src_idx = model.mapToSource(idx) if hasattr(model, "mapToSource") else idx
                source_rows.append(src_idx.row())

            if action == insert_action:
                source_model.insert_row(min(source_rows))
            elif action == delete_action:
                for row in sorted(set(source_rows), reverse=True):
                    source_model.delete_row(row)

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

            self.table = ExcelLikeTableView()
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

            self.graph_editor_state = GraphEditorState()
            self.graph_editor_state.upsert(GraphElement(id="series-main", kind="line", properties={"line_width": 2, "color": "#38BDF8"}))
            InteractivePlotWidget = create_interactive_plot_widget()
            self.plot_widget = InteractivePlotWidget() if InteractivePlotWidget is not None else None
            if self.plot_widget is not None:
                root.addWidget(self.plot_widget)
                self.model.data_edited_point.connect(self.plot_widget.on_model_data_edited)
                self.plot_widget.pointEdited.connect(self._edit_from_plot)
                self.plot_widget.pointSelected.connect(self._select_from_plot)

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

        def _edit_from_plot(self, row: int, col: int, value: str) -> None:
            idx = self.model.index(row, col)
            self.model.setData(idx, value)
            self.graph_editor_state.set_property("series-main", "last_edited_row", row)

        def _emit_selection(self, *_args) -> None:
            selected_rows = self.table.selectionModel().selectedRows()
            count = len(selected_rows)
            self.selection_label.setText(f"Selected rows: {count}")
            if self.plot_widget is not None and selected_rows:
                src_idx = self.proxy.mapToSource(selected_rows[0])
                self.plot_widget.highlight_point(src_idx.row())
            self.selection_changed.emit(count)

        def _select_from_plot(self, row: int, _col: int) -> None:
            idx = self.model.index(row, 0)
            proxy_idx = self.proxy.mapFromSource(idx)
            if proxy_idx.isValid():
                self.table.selectRow(proxy_idx.row())

        def _show_cell_stats(self, index) -> None:  # type: ignore[no-untyped-def]
            src = self.proxy.mapToSource(index)
            self.stats_label.setText(f"Column stats: {self.model.column_stats(src.column())}")

        def load_file(self, path: Path) -> None:
            if path.suffix.lower() == ".csv":
                self.model.load_csv(path)
                if self.plot_widget is not None:
                    values = []
                    for row in self.model.rows:
                        try:
                            values.append(float(row[0]))
                        except Exception:
                            values.append(0.0)
                    self.plot_widget.set_values(values)

    return DataViewerWidget
