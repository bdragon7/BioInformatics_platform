from bioplatform.core.chemical_toolbox import ChemicalToolbox


def test_formulation_report_detects_known_unknown_and_conflicts() -> None:
    box = ChemicalToolbox()
    report = box.analyze_formulation([
        "Benzalkonium chloride",
        "Sodium lauryl sulfate",
        "mystery_agent",
    ], target="disinfection")

    found_names = {item.name for item in report.found}
    assert "Benzalkonium chloride" in found_names
    assert "Sodium lauryl sulfate" in found_names
    assert "mystery_agent" in report.unknown
    assert any("Cationic/anionic" in msg or "deactivated by anionic" in msg for msg in report.incompatibilities)
    assert any("Unknown entries" in msg for msg in report.industrial_guidance)


def test_qsar_estimate_contains_expected_keys() -> None:
    box = ChemicalToolbox()
    qsar = box.estimate_qsar("CCO")
    assert set(qsar.keys()) == {
        "lipophilicity",
        "topology",
        "reactivity",
        "toxicity_screen",
        "biodegradation",
        "antimicrobial_signal",
    }


def test_doe_factor_suggestions_are_conditional() -> None:
    box = ChemicalToolbox()
    base_cleaning = box.suggest_doe_factors("cleaning")
    assert "water_hardness" not in base_cleaning
    assert "soil_load" not in base_cleaning

    extended = box.suggest_doe_factors(
        "cleaning",
        include_soiling=True,
        include_hard_water=True,
        target_organism="E. coli",
    )
    assert "water_hardness" in extended
    assert "soil_load" in extended
    assert "target_organism" in extended


def test_doe_plan_visual_and_preview_present() -> None:
    box = ChemicalToolbox()
    plan = box.build_doe_plan(
        "disinfection",
        include_soiling=True,
        include_hard_water=True,
        target_organism="S. aureus",
    )
    assert plan.runs_preview
    assert "Legend:" in plan.visual_map
    assert "target_organism" in plan.factors
