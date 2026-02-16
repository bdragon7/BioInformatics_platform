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


def test_doe_factor_suggestions_are_domain_specific() -> None:
    box = ChemicalToolbox()
    cleaning = box.suggest_doe_factors("cleaning")
    anti = box.suggest_doe_factors("antiviral")
    assert "water_hardness" in cleaning
    assert "microbial_load" in anti
