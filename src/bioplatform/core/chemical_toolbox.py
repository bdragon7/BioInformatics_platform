from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Literal


ApplicationDomain = Literal[
    "cosmetics",
    "cleaning",
    "disinfection",
    "antimicrobial",
    "antiviral",
    "antifungal",
]


@dataclass(slots=True)
class ChemicalRecord:
    name: str
    smiles: str
    category: str
    charge: str
    pH_window: tuple[float, float]
    applications: tuple[ApplicationDomain, ...]
    notes: str




@dataclass(slots=True)
class DoEPlan:
    factors: list[str]
    level_table: dict[str, list[str]]
    runs_preview: list[dict[str, str]]
    visual_map: str

@dataclass(slots=True)
class FormulationRiskReport:
    found: list[ChemicalRecord]
    unknown: list[str]
    incompatibilities: list[str]
    qsar_notes: list[str]
    industrial_guidance: list[str]


class ChemicalToolbox:
    """Chemical informatics helper for formulation design and DoE planning.

    Provides:
    - local chemical lookup with SMILES support
    - compatibility checks for common formulation conflicts
    - lightweight QSAR-style heuristic notes
    - domain-specific DoE factor suggestions
    """

    def __init__(self) -> None:
        self._records = self._build_database()
        self._by_name = {r.name.lower(): r for r in self._records}
        self._by_smiles = {r.smiles: r for r in self._records}

    @staticmethod
    def _build_database() -> list[ChemicalRecord]:
        return [
            ChemicalRecord(
                name="Benzalkonium chloride",
                smiles="C[N+](C)(C)CCCCCc1ccccc1",
                category="quat",
                charge="cationic",
                pH_window=(5.0, 9.0),
                applications=("disinfection", "antimicrobial", "antiviral"),
                notes="Cationic disinfectant; can be deactivated by anionic surfactants.",
            ),
            ChemicalRecord(
                name="Sodium lauryl sulfate",
                smiles="CCCCCCCCCCCCOS(=O)(=O)[O-].[Na+]",
                category="surfactant",
                charge="anionic",
                pH_window=(5.5, 8.5),
                applications=("cleaning", "cosmetics"),
                notes="Strong foaming anionic surfactant.",
            ),
            ChemicalRecord(
                name="Cocamidopropyl betaine",
                smiles="CCCCCCCCCCCC(=O)NCCC[N+](C)(C)CC([O-])=O",
                category="surfactant",
                charge="zwitterionic",
                pH_window=(4.5, 8.5),
                applications=("cleaning", "cosmetics"),
                notes="Mild amphoteric co-surfactant; often used for irritation reduction.",
            ),
            ChemicalRecord(
                name="EDTA",
                smiles="N(CCN(CCN(CC(=O)O)CC(=O)O)CC(=O)O)CC(=O)O",
                category="chelator",
                charge="anionic",
                pH_window=(4.0, 11.0),
                applications=("cleaning", "cosmetics", "disinfection"),
                notes="Chelator improving hard-water performance and preservative robustness.",
            ),
            ChemicalRecord(
                name="Citric acid",
                smiles="OC(=O)CC(O)(CC(=O)O)C(=O)O",
                category="acid",
                charge="anionic",
                pH_window=(2.0, 6.5),
                applications=("cleaning", "cosmetics"),
                notes="pH adjuster and mild chelating buffer.",
            ),
            ChemicalRecord(
                name="Sodium hypochlorite",
                smiles="[Na+].[O-]Cl",
                category="oxidizer",
                charge="anionic",
                pH_window=(10.5, 13.0),
                applications=("disinfection", "antimicrobial", "antiviral", "antifungal"),
                notes="Strong oxidizer; avoid mixing with acids and amines.",
            ),
            ChemicalRecord(
                name="Hydrogen peroxide",
                smiles="OO",
                category="oxidizer",
                charge="neutral",
                pH_window=(2.5, 6.5),
                applications=("disinfection", "antimicrobial", "antiviral", "antifungal"),
                notes="Oxidizing biocide; stability influenced by metals and pH.",
            ),
            ChemicalRecord(
                name="Ethanol",
                smiles="CCO",
                category="solvent",
                charge="neutral",
                pH_window=(4.0, 9.0),
                applications=("disinfection", "cleaning", "cosmetics", "antiviral"),
                notes="Fast-acting solvent and disinfectant support, high volatility.",
            ),
            ChemicalRecord(
                name="Chlorhexidine",
                smiles="CN(C)CCCNc1nc(NC(N)=N)nc(NC(N)=N)n1",
                category="biguanide",
                charge="cationic",
                pH_window=(5.5, 8.5),
                applications=("disinfection", "antimicrobial", "antifungal"),
                notes="Broad-spectrum antimicrobial often incompatible with anionic systems.",
            ),
        ]

    def lookup(self, name_or_smiles: str) -> ChemicalRecord | None:
        key = name_or_smiles.strip()
        if not key:
            return None
        by_name = self._by_name.get(key.lower())
        if by_name:
            return by_name
        return self._by_smiles.get(key)

    def estimate_qsar(self, smiles: str) -> dict[str, str]:
        token_count = sum(1 for ch in smiles if ch.isalpha())
        aromatic = "aromatic-rich" if "c1" in smiles or "c" in smiles else "aliphatic-dominant"
        cationic = "+" in smiles or "[N+]" in smiles
        acidic = "C(=O)O" in smiles or "[O-]" in smiles

        logp_hint = "high" if token_count > 22 else "moderate" if token_count > 12 else "low"
        toxicity_flag = "elevated" if cationic and aromatic == "aromatic-rich" else "moderate"
        biodegradation = "slower" if aromatic == "aromatic-rich" else "faster"
        antimicrobial = "likely" if cationic or "OO" in smiles or "Cl" in smiles else "possible"

        return {
            "lipophilicity": logp_hint,
            "topology": aromatic,
            "reactivity": "acid/base active" if acidic else "neutral",
            "toxicity_screen": toxicity_flag,
            "biodegradation": biodegradation,
            "antimicrobial_signal": antimicrobial,
        }

    def analyze_formulation(self, chemicals: list[str], target: ApplicationDomain = "cleaning") -> FormulationRiskReport:
        found: list[ChemicalRecord] = []
        unknown: list[str] = []
        incompatibilities: list[str] = []
        qsar_notes: list[str] = []

        for item in chemicals:
            rec = self.lookup(item)
            if rec is None:
                unknown.append(item)
                continue
            found.append(rec)
            qsar = self.estimate_qsar(rec.smiles)
            qsar_notes.append(
                f"{rec.name}: lipophilicity={qsar['lipophilicity']}, toxicity_screen={qsar['toxicity_screen']}, antimicrobial_signal={qsar['antimicrobial_signal']}"
            )

        categories = {r.category for r in found}
        charges = {r.charge for r in found}

        if "oxidizer" in categories and "acid" in categories:
            incompatibilities.append("Oxidizer + acid combination can release hazardous species; separate or control process conditions.")
        if "cationic" in charges and "anionic" in charges:
            incompatibilities.append("Cationic/anionic actives in same phase may neutralize efficacy or precipitate.")
        if "quat" in categories and "surfactant" in categories and "anionic" in charges:
            incompatibilities.append("Quaternary ammonium disinfectants are often deactivated by anionic surfactants.")
        if "oxidizer" in categories and any(r.category == "biguanide" for r in found):
            incompatibilities.append("Biguanides with strong oxidizers can degrade and lose antimicrobial performance.")

        industrial_guidance = self._industrial_guidance(found, unknown, target)
        return FormulationRiskReport(
            found=found,
            unknown=unknown,
            incompatibilities=incompatibilities,
            qsar_notes=qsar_notes,
            industrial_guidance=industrial_guidance,
        )

    def _industrial_guidance(
        self,
        found: list[ChemicalRecord],
        unknown: list[str],
        target: ApplicationDomain,
    ) -> list[str]:
        guidance = [
            f"Target domain: {target}.",
            "Design DoE around pH, active concentration, contact time, and temperature.",
            "Use response metrics: kill-log reduction, stability after aging, viscosity/foam, and substrate compatibility.",
        ]
        if target in {"antimicrobial", "antiviral", "antifungal", "disinfection"}:
            guidance.append("Include challenge-organism panel and neutralization controls in protocol design.")
        if target in {"cosmetics", "cleaning"}:
            guidance.append("Track sensory/foaming/rinse profile and skin-surface residue during optimization.")

        if found:
            pmin = max(r.pH_window[0] for r in found)
            pmax = min(r.pH_window[1] for r in found)
            if pmin <= pmax:
                guidance.append(f"Shared operating pH window estimate: {pmin:.1f}-{pmax:.1f}.")
            else:
                guidance.append("No overlapping pH window across selected actives; consider phase separation or reformulation.")

        if unknown:
            guidance.append(
                "Unknown entries detected: provide SMILES + intended concentration so QSAR and compatibility can be estimated collaboratively."
            )
        return guidance

    def suggest_doe_factors(
        self,
        target: ApplicationDomain,
        include_soiling: bool = False,
        include_hard_water: bool = False,
        target_organism: str | None = None,
    ) -> list[str]:
        common = [
            "pH",
            "active_concentration",
            "temperature",
            "contact_time",
            "ionic_strength",
        ]
        extras: list[str] = []
        if target == "cosmetics":
            extras.extend(["skin_feel_score", "foam_height", "preservative_system"])
        if target == "cleaning":
            extras.extend(["rinse_cycles"]) 
        if target in {"disinfection", "antimicrobial", "antiviral", "antifungal"}:
            extras.extend(["microbial_load", "organic_interference", "surface_type"])

        if include_soiling:
            extras.append("soil_load")
        if include_hard_water:
            extras.append("water_hardness")
        if target_organism and target_organism.lower() in {"e. coli", "s. aureus"}:
            extras.append("target_organism")

        deduped: list[str] = []
        for factor in [*common, *extras]:
            if factor not in deduped:
                deduped.append(factor)
        return deduped

    def build_doe_plan(
        self,
        target: ApplicationDomain,
        include_soiling: bool = False,
        include_hard_water: bool = False,
        target_organism: str | None = None,
    ) -> DoEPlan:
        factors = self.suggest_doe_factors(
            target,
            include_soiling=include_soiling,
            include_hard_water=include_hard_water,
            target_organism=target_organism,
        )
        level_table: dict[str, list[str]] = {
            "pH": ["low", "mid", "high"],
            "active_concentration": ["0.25x", "1x", "2x"],
            "temperature": ["ambient", "30C", "45C"],
            "contact_time": ["1 min", "5 min", "10 min"],
            "ionic_strength": ["low", "mid"],
            "rinse_cycles": ["1", "3"],
            "soil_load": ["none", "light", "heavy"],
            "water_hardness": ["soft", "moderate", "hard"],
            "microbial_load": ["1e5", "1e6", "1e7 CFU/mL"],
            "organic_interference": ["0%", "1% BSA", "5% serum"],
            "surface_type": ["steel", "polymer", "glass"],
            "skin_feel_score": ["panel-low", "panel-high"],
            "foam_height": ["low", "high"],
            "preservative_system": ["A", "B"],
            "target_organism": [target_organism or "E. coli"],
        }

        preview_axes = [f for f in factors if f in {"pH", "active_concentration", "contact_time", "soil_load", "water_hardness", "target_organism"}][:3]
        runs_preview: list[dict[str, str]] = []
        if preview_axes:
            levels = [level_table[a][:2] for a in preview_axes]
            for combo in list(product(*levels))[:8]:
                runs_preview.append(dict(zip(preview_axes, combo)))

        visual_map = self.render_doe_visual_map(factors)
        return DoEPlan(factors=factors, level_table={k: level_table[k] for k in factors if k in level_table}, runs_preview=runs_preview, visual_map=visual_map)

    @staticmethod
    def render_doe_visual_map(factors: list[str]) -> str:
        if not factors:
            return "(no factors selected)"
        top = factors[:6]
        header = "      " + " ".join(f"{i+1:>2}" for i in range(len(top)))
        rows = [header]
        for i, name in enumerate(top):
            cells = []
            for j in range(len(top)):
                if i == j:
                    cells.append("◉ ")
                elif i < j:
                    cells.append("● ")
                else:
                    cells.append("· ")
            rows.append(f"{i+1:>2} {name[:16]:<16}" + "".join(cells))
        legend = "Legend: ◉ self-factor | ● interaction candidate | · mirrored cell"
        return "\n".join([*rows, legend])
