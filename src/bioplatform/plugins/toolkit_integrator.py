from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.data_cleaning import lof_outliers, smart_sanitize_growth_values, smart_sanitize_sequence, universal_result
from .base import BioPlugin, PluginContext


@dataclass(slots=True)
class IntegratorTool:
    key: str
    enabled: bool


class ToolSettingsManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(
                json.dumps(
                    {
                        "gseapy": True,
                        "biopandas": True,
                        "cobrapy": True,
                        "statsmodels": True,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

    def load(self) -> dict[str, bool]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, settings: dict[str, bool]) -> None:
        self.path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


class ToolkitIntegratorPlugin(BioPlugin):
    plugin_id = "toolkit.integrator"
    plugin_name = "Toolkit Integrator"

    def register_ui(self, context: PluginContext) -> dict[str, str]:
        return {
            "title": "Toolkit Integrator",
            "subtitle": "Gold-standard wrappers for genomics/proteomics/microbiology/stats",
            "workspace": context.workspace,
        }

    def execute_logic(self, payload: dict[str, object]) -> dict[str, object]:
        mode = str(payload.get("mode", ""))
        if mode == "sanitize_sequence":
            seq = str(payload.get("sequence", ""))
            sanitized = smart_sanitize_sequence(seq)
            return universal_result(sanitized.data, warnings=sanitized.warnings)
        if mode == "sanitize_growth":
            values = [v if v is None else float(v) for v in payload.get("values", [])]  # type: ignore[arg-type]
            sanitized = smart_sanitize_growth_values(values)
            outliers = lof_outliers([float(v) for v in sanitized.data]) if sanitized.data else []
            return universal_result(sanitized.data, outliers=outliers, warnings=sanitized.warnings)
        if mode == "gseapy":
            return self._run_gseapy(payload)
        if mode == "biopandas":
            return self._run_biopandas(payload)
        if mode == "cobrapy":
            return self._run_cobrapy(payload)
        if mode == "statsmodels":
            return self._run_statsmodels(payload)
        raise ValueError("Unsupported toolkit integrator mode")

    def _run_gseapy(self, payload: dict[str, object]) -> dict[str, object]:
        try:
            import gseapy as gp  # type: ignore

            genes = [str(g) for g in payload.get("genes", [])]
            if not genes:
                return universal_result([], error="No genes provided")
            enr = gp.enrichr(gene_list=genes, gene_sets="KEGG_2016", no_plot=True, outdir=None)
            data = enr.results.head(10).to_dict(orient="records")
            return universal_result(data, provider="gseapy")
        except Exception as exc:
            return universal_result([], error=f"gseapy unavailable: {exc}")

    def _run_biopandas(self, payload: dict[str, object]) -> dict[str, object]:
        try:
            from biopandas.pdb import PandasPdb  # type: ignore

            pdb_path = str(payload.get("pdb_path", ""))
            ppdb = PandasPdb().read_pdb(pdb_path)
            atom_count = len(ppdb.df.get("ATOM", []))
            return universal_result({"atom_count": atom_count}, provider="biopandas")
        except Exception as exc:
            return universal_result({}, error=f"biopandas unavailable: {exc}")

    def _run_cobrapy(self, payload: dict[str, object]) -> dict[str, object]:
        try:
            from cobra.io import load_json_model  # type: ignore

            model_path = str(payload.get("model_path", ""))
            model = load_json_model(model_path)
            solution = model.optimize()
            return universal_result({"objective": float(solution.objective_value)}, provider="cobrapy")
        except Exception as exc:
            return universal_result({}, error=f"cobrapy unavailable: {exc}")

    def _run_statsmodels(self, payload: dict[str, object]) -> dict[str, object]:
        try:
            import statsmodels.api as sm  # type: ignore

            x = [float(v) for v in payload.get("x", [])]
            y = [float(v) for v in payload.get("y", [])]
            if len(x) != len(y) or len(x) < 2:
                return universal_result({}, error="Need at least 2 paired x/y values")
            model = sm.OLS(y, sm.add_constant(x)).fit()
            data: dict[str, Any] = {
                "params": model.params.tolist(),
                "r_squared": float(model.rsquared),
            }
            return universal_result(data, provider="statsmodels")
        except Exception as exc:
            return universal_result({}, error=f"statsmodels unavailable: {exc}")
