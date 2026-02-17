from __future__ import annotations

"""Advanced formulation engine for mass-volume-molarity, density correction, and pH/ionic strength.

Scientific references:
- Henderson-Hasselbalch equation (buffer pH estimation), standard biochemistry texts.
- Ionic strength: I = 0.5 * Σ(c_i * z_i^2), IUPAC analytical chemistry conventions.
- Arrhenius context and solution preparation best-practices from physical chemistry handbooks.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal


UnitMode = Literal["molar", "mass_per_volume", "w_w_percent"]


@dataclass(slots=True)
class IngredientSpec:
    name: str
    molecular_weight: float
    density_g_ml: float
    purity_fraction: float = 1.0
    pka: float | None = None
    charge: int = 0
    role: str = "solute"


@dataclass(slots=True)
class IngredientTarget:
    name: str
    mode: UnitMode
    value: float


@dataclass(slots=True)
class MixtureComponentResult:
    name: str
    mass_g: float
    volume_ml: float
    moles: float
    effective_molarity_m: float


@dataclass(slots=True)
class FormulationResult:
    final_volume_ml: float
    estimated_density_g_ml: float
    theoretical_ph: float
    ionic_strength_m: float
    components: List[MixtureComponentResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FormulationManager:
    """Manage multi-component formulations with density and equilibrium approximations."""

    def __init__(self, ingredient_catalog: Dict[str, IngredientSpec] | None = None) -> None:
        self.ingredient_catalog: Dict[str, IngredientSpec] = ingredient_catalog or {}

    def register_ingredient(self, spec: IngredientSpec) -> None:
        self.ingredient_catalog[spec.name.lower()] = spec

    def solve_mass_from_molarity(
        self,
        ingredient: IngredientSpec,
        target_molarity_m: float,
        final_volume_ml: float,
    ) -> float:
        """Solve mass (g) for given molarity and final volume.

        mass = M * V(L) * MW / purity
        """
        if target_molarity_m < 0 or final_volume_ml <= 0:
            raise ValueError("target molarity must be >= 0 and final volume must be > 0")
        if ingredient.molecular_weight <= 0 or ingredient.purity_fraction <= 0:
            raise ValueError("molecular weight and purity must be > 0")
        return target_molarity_m * (final_volume_ml / 1000.0) * ingredient.molecular_weight / ingredient.purity_fraction

    def solve_molarity_from_mass(self, ingredient: IngredientSpec, mass_g: float, final_volume_ml: float) -> float:
        if mass_g < 0 or final_volume_ml <= 0:
            raise ValueError("mass must be >= 0 and final volume > 0")
        if ingredient.molecular_weight <= 0:
            raise ValueError("molecular weight must be > 0")
        moles = (mass_g * ingredient.purity_fraction) / ingredient.molecular_weight
        return moles / (final_volume_ml / 1000.0)

    def solve_volume_from_mass_and_molarity(self, ingredient: IngredientSpec, mass_g: float, target_molarity_m: float) -> float:
        if mass_g < 0 or target_molarity_m <= 0:
            raise ValueError("mass must be >= 0 and target molarity > 0")
        moles = (mass_g * ingredient.purity_fraction) / ingredient.molecular_weight
        volume_l = moles / target_molarity_m
        return volume_l * 1000.0

    @staticmethod
    def density_corrected_volume_ml(solute_volume_ml: float, concentration_w_w: float, solvent: str = "water") -> float:
        """Approximate non-linear mixing contraction/expansion.

        Uses polynomial-style contraction for common viscous solutes in water-like systems.
        """
        if solute_volume_ml < 0:
            raise ValueError("solute_volume_ml must be >= 0")
        c = max(0.0, min(concentration_w_w, 1.0))
        # contraction factor for glycerol/PEG-like concentrated systems
        contraction = 1.0 - (0.08 * c + 0.03 * (c**2))
        if solvent.lower() in {"ethanol", "isopropanol"}:
            contraction -= 0.01 * c
        return solute_volume_ml * max(0.75, contraction)

    @staticmethod
    def henderson_hasselbalch(ph_acid_m: float, ph_base_m: float, pka: float) -> float:
        if ph_acid_m <= 0 or ph_base_m <= 0:
            raise ValueError("acid/base concentrations must be > 0")
        import math

        return pka + math.log10(ph_base_m / ph_acid_m)

    @staticmethod
    def ionic_strength(ion_concentrations_m: Dict[int, float]) -> float:
        return 0.5 * sum(conc * (charge**2) for charge, conc in ion_concentrations_m.items() if conc > 0)

    def formulate(self, targets: List[IngredientTarget], final_volume_ml: float, temperature_c: float = 25.0) -> FormulationResult:
        if final_volume_ml <= 0:
            raise ValueError("final_volume_ml must be > 0")
        if temperature_c < -10 or temperature_c > 120:
            raise ValueError("temperature_c outside practical liquid range")

        warnings: List[str] = []
        components: List[MixtureComponentResult] = []
        total_mass = 0.0
        corrected_total_volume = 0.0

        ion_map: Dict[int, float] = {}
        acid_for_ph: float | None = None
        base_for_ph: float | None = None
        pka_for_ph: float | None = None

        for item in targets:
            spec = self.ingredient_catalog.get(item.name.lower())
            if spec is None:
                warnings.append(f"Unknown ingredient: {item.name}")
                continue
            if item.value < 0:
                raise ValueError(f"Negative target value for {item.name}")

            if item.mode == "molar":
                mass_g = self.solve_mass_from_molarity(spec, item.value, final_volume_ml)
                molarity = item.value
            elif item.mode == "mass_per_volume":
                mass_g = item.value * (final_volume_ml / 1000.0)
                molarity = self.solve_molarity_from_mass(spec, mass_g, final_volume_ml)
            else:  # w_w_percent
                mass_g = (item.value / 100.0) * final_volume_ml  # assumes ~1 g/mL base liquid
                molarity = self.solve_molarity_from_mass(spec, mass_g, final_volume_ml)

            volume_ml_raw = mass_g / max(spec.density_g_ml, 1e-6)
            volume_ml = self.density_corrected_volume_ml(volume_ml_raw, min(1.0, mass_g / max(1.0, final_volume_ml)))
            moles = (mass_g * spec.purity_fraction) / max(spec.molecular_weight, 1e-9)

            components.append(
                MixtureComponentResult(
                    name=spec.name,
                    mass_g=mass_g,
                    volume_ml=volume_ml,
                    moles=moles,
                    effective_molarity_m=molarity,
                )
            )

            total_mass += mass_g
            corrected_total_volume += volume_ml
            if spec.charge != 0:
                ion_map[spec.charge] = ion_map.get(spec.charge, 0.0) + molarity

            if spec.pka is not None and spec.role in {"acid", "base", "buffer"}:
                if spec.role == "acid":
                    acid_for_ph = (acid_for_ph or 0.0) + molarity
                    pka_for_ph = spec.pka
                else:
                    base_for_ph = (base_for_ph or 0.0) + molarity
                    pka_for_ph = spec.pka

        est_density = total_mass / max(corrected_total_volume, 1e-6)
        if est_density > 1.35:
            warnings.append("High-density formulation; verify pipetting and mixing strategy.")

        theoretical_ph = 7.0
        if acid_for_ph and base_for_ph and pka_for_ph is not None:
            theoretical_ph = self.henderson_hasselbalch(acid_for_ph, base_for_ph, pka_for_ph)
        elif acid_for_ph and not base_for_ph:
            theoretical_ph = max(1.0, 3.0 - min(1.5, acid_for_ph))
        elif base_for_ph and not acid_for_ph:
            theoretical_ph = min(13.0, 11.0 + min(1.0, base_for_ph))

        ionic = self.ionic_strength(ion_map)
        if ionic > 0.7:
            warnings.append("High ionic strength may impact protein stability or antimicrobial readouts.")

        return FormulationResult(
            final_volume_ml=final_volume_ml,
            estimated_density_g_ml=est_density,
            theoretical_ph=theoretical_ph,
            ionic_strength_m=ionic,
            components=components,
            warnings=warnings,
        )
