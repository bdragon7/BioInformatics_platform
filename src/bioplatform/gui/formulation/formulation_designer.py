from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from ...core.formulation_engine import FormulationManager, IngredientSpec, IngredientTarget
from ...core.solubility_checker import SolubilityChecker
from ...tooltips import TOOLTIPS


@dataclass(slots=True)
class IngredientRow:
    name: str
    mode: str
    value: float


class _LookupWorker:
    """Lightweight worker façade to support QThread pattern when PySide6 is available."""

    def __init__(self, callback):  # type: ignore[no-untyped-def]
        self.callback = callback

    def run(self, query: str) -> None:
        self.callback(query)


def _seed_manager() -> FormulationManager:
    manager = FormulationManager()
    manager.register_ingredient(IngredientSpec("Glycerol", molecular_weight=92.09, density_g_ml=1.261, role="solute"))
    manager.register_ingredient(IngredientSpec("Citric Acid", molecular_weight=192.12, density_g_ml=1.66, pka=3.13, charge=-1, role="acid"))
    manager.register_ingredient(IngredientSpec("Sodium Citrate", molecular_weight=258.06, density_g_ml=1.70, pka=3.13, charge=1, role="base"))
    manager.register_ingredient(IngredientSpec("Sodium Chloride", molecular_weight=58.44, density_g_ml=2.16, charge=1, role="salt"))
    manager.register_ingredient(IngredientSpec("Benzalkonium Chloride", molecular_weight=340.0, density_g_ml=0.98, charge=1, role="buffer"))
    return manager


def open_formulation_designer(parent: Any = None) -> None:
    """Open the Helix-style formulation designer dialog.

    UI conventions:
    - Emerald (`#2ECC71`) indicates stable/acceptable state.
    - Alizarin (`#E74C3C`) indicates warnings.
    """
    try:
        from PySide6.QtCore import QThread, Signal, QObject
        from PySide6.QtWidgets import (
            QAbstractItemView,
            QComboBox,
            QDialog,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QTextEdit,
            QVBoxLayout,
        )
    except Exception:
        return

    manager = _seed_manager()
    checker = SolubilityChecker()

    class LookupWorker(QObject):
        finished = Signal(str)

        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

        def run(self) -> None:
            # Placeholder asynchronous search bridge; replace with RDKit/PubChem API in production.
            self.finished.emit(self.query)

    class FormulationDialog(QDialog):
        def dragEnterEvent(self, event) -> None:  # type: ignore[no-untyped-def]
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def dropEvent(self, event) -> None:  # type: ignore[no-untyped-def]
            urls = event.mimeData().urls()
            paths = [Path(u.toLocalFile()) for u in urls if u.toLocalFile()]
            on_drop(paths)

    dlg = FormulationDialog(parent)
    dlg.setWindowTitle("Formulation Engineering Suite")
    dlg.setAcceptDrops(True)
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("Design robust formulations with live safety and physicochemical checks."))

    grid = QTableWidget(0, 4)
    grid.setHorizontalHeaderLabels(["Ingredient", "Mode", "Value", "Unit"])
    grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    grid.setToolTip(TOOLTIPS.get("formulation.ionic_strength", "Ionic strength affects buffering and biological response."))
    layout.addWidget(grid)

    controls = QHBoxLayout()
    add_btn = QPushButton("Add Ingredient")
    import_btn = QPushButton("Import .csv/.sdf")
    solve_btn = QPushButton("Solve Formulation")
    sds_btn = QPushButton("Generate Lab Handling Sheet (PDF)")
    controls.addWidget(add_btn)
    controls.addWidget(import_btn)
    controls.addWidget(solve_btn)
    controls.addWidget(sds_btn)
    layout.addLayout(controls)

    status = QLabel("Ready")
    layout.addWidget(status)

    report = QTextEdit()
    report.setReadOnly(True)
    layout.addWidget(report)

    viz = QTextEdit()
    viz.setReadOnly(True)
    viz.setPlaceholderText("Live visualization summary: mass pie + formulation space coordinates")
    layout.addWidget(viz)

    def add_row(name: str = "", mode: str = "molar", value: float = 0.0) -> None:
        row = grid.rowCount()
        grid.insertRow(row)
        grid.setItem(row, 0, QTableWidgetItem(name))

        mode_box = QComboBox()
        mode_box.addItems(["molar", "mass_per_volume", "w_w_percent"])
        mode_box.setCurrentText(mode)
        grid.setCellWidget(row, 1, mode_box)

        grid.setItem(row, 2, QTableWidgetItem(f"{value:.6g}"))

        unit_box = QComboBox()
        unit_box.addItems(["M", "g/L", "% w/w"])
        grid.setCellWidget(row, 3, unit_box)

    def parse_rows() -> List[IngredientTarget]:
        targets: List[IngredientTarget] = []
        for row in range(grid.rowCount()):
            item = grid.item(row, 0)
            val_item = grid.item(row, 2)
            if item is None or val_item is None:
                continue
            name = item.text().strip()
            if not name:
                continue
            mode_box = grid.cellWidget(row, 1)
            mode = mode_box.currentText() if mode_box else "molar"  # type: ignore[attr-defined]
            try:
                value = float(val_item.text().strip())
            except Exception:
                value = 0.0
            targets.append(IngredientTarget(name=name, mode=mode, value=value))
        return targets

    def solve() -> None:
        targets = parse_rows()
        if not targets:
            report.setPlainText("No ingredient rows to solve.")
            return
        result = manager.formulate(targets, final_volume_ml=1000.0, temperature_c=25.0)

        warnings = list(result.warnings)
        warnings.extend(checker.check_incompatibilities([t.name for t in targets]))

        sol_warnings = []
        for comp in result.components:
            warning = checker.check_solubility(comp.name, concentration_g_l=(comp.mass_g / result.final_volume_ml) * 1000.0)
            if warning:
                sol_warnings.append(warning.warning)
        warnings.extend(sol_warnings)

        status.setText("Stable" if not warnings else "Warnings detected")
        status.setStyleSheet(f"color: {'#2ECC71' if not warnings else '#E74C3C'}; font-weight: 600;")

        lines = [
            f"Final volume: {result.final_volume_ml:.2f} mL",
            f"Estimated density: {result.estimated_density_g_ml:.4f} g/mL",
            f"Theoretical pH: {result.theoretical_ph:.2f}",
            f"Ionic strength: {result.ionic_strength_m:.3f} M",
            "",
            "Components:",
        ]
        for comp in result.components:
            lines.append(
                f"- {comp.name}: mass={comp.mass_g:.3f} g, volume={comp.volume_ml:.3f} mL, molarity={comp.effective_molarity_m:.4f} M"
            )
        if warnings:
            lines.extend(["", "Warnings:", *[f"- {w}" for w in warnings]])
        report.setPlainText("\n".join(lines))

        total_mass = sum(c.mass_g for c in result.components) or 1.0
        viz_lines = ["Mass distribution (proxy pie):"]
        for comp in result.components:
            frac = (comp.mass_g / total_mass) * 100.0
            viz_lines.append(f"- {comp.name}: {frac:.1f}%")
        viz_lines.append("\nFormulation-space point: [density, pH, ionic_strength]")
        viz_lines.append(f"[{result.estimated_density_g_ml:.3f}, {result.theoretical_ph:.3f}, {result.ionic_strength_m:.3f}]")
        viz.setPlainText("\n".join(viz_lines))

    def import_file() -> None:
        path, _ = QFileDialog.getOpenFileName(
            dlg,
            "Import ingredient list",
            "",
            "Chemical Lists (*.csv *.sdf);;All Files (*.*)",
        )
        if not path:
            return
        load_ingredient_file(Path(path))

    def load_ingredient_file(path: Path) -> None:
        if path.suffix.lower() == ".csv":
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                parts = [x.strip() for x in line.split(",")]
                if len(parts) >= 3:
                    try:
                        value = float(parts[2])
                    except Exception:
                        value = 0.0
                    add_row(parts[0], parts[1] if parts[1] in {"molar", "mass_per_volume", "w_w_percent"} else "molar", value)
        elif path.suffix.lower() == ".sdf":
            # Scientific drag/drop helper: each SDF record title line becomes an ingredient placeholder.
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for i in range(0, len(lines), 4):
                title = lines[i].strip() if i < len(lines) else ""
                if title:
                    add_row(title, "molar", 0.0)

    def generate_sds_pdf() -> None:
        out = Path("lab_handling_sheet.pdf")
        rows = parse_rows()
        lines = ["Lab Handling Sheet", "=================", ""]
        for r in rows:
            lines.append(f"Ingredient: {r.name}")
            lines.append("- PPE: gloves, eye protection, coat")
            lines.append("- Storage: tightly sealed, controlled temperature")
            lines.append("- Spill response: absorbent + disposal per local SOP")
            lines.append("")
        text = "\n".join(lines)
        try:
            from PySide6.QtGui import QTextDocument
            from PySide6.QtPrintSupport import QPrinter

            doc = QTextDocument()
            doc.setPlainText(text)
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(str(out))
            doc.print(printer)
        except Exception:
            # Fallback in reduced environments lacking print support.
            out = Path("lab_handling_sheet.txt")
            out.write_text(text, encoding="utf-8")
        status.setText(f"Lab Handling Sheet generated: {out}")

    def do_async_lookup() -> None:
        if grid.rowCount() == 0:
            return
        first = grid.item(0, 0)
        query = first.text().strip() if first else ""
        if not query:
            return
        status.setText("Helix-Pulse: resolving properties…")
        status.setStyleSheet("color: #2ECC71;")

        thread = QThread(dlg)
        worker = LookupWorker(query)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        def finished(name: str) -> None:
            status.setText(f"Lookup complete for: {name}")
            thread.quit()
            worker.deleteLater()
            thread.deleteLater()

        worker.finished.connect(finished)
        thread.start()

    def on_drop(paths: List[Path]) -> None:
        for p in paths:
            if p.suffix.lower() in {".csv", ".sdf"}:
                load_ingredient_file(p)

    add_btn.clicked.connect(lambda: add_row("", "molar", 0.0))
    import_btn.clicked.connect(import_file)
    solve_btn.clicked.connect(solve)
    sds_btn.clicked.connect(generate_sds_pdf)
    grid.itemChanged.connect(lambda _item: do_async_lookup())

    add_row("Glycerol", "mass_per_volume", 50.0)
    add_row("Sodium Chloride", "mass_per_volume", 9.0)

    dlg.resize(1120, 820)
    dlg.exec()
