from bioplatform.plugins.base import PluginContext
from bioplatform.plugins.microbiology_plugin import MicrobiologyPlugin


def test_microbiology_plugin_outliers_and_growth() -> None:
    plugin = MicrobiologyPlugin()
    ui = plugin.register_ui(PluginContext(app_name="Bioinformatics Studio", workspace="default"))
    assert ui["title"] == "Microbiology"

    outlier_res = plugin.execute_logic({"mode": "outliers", "values": [0.1, 0.12, 0.09, 1.0]})
    assert "outlier_indices" in outlier_res

    growth_res = plugin.execute_logic({"mode": "growth", "time_hours": [0, 1, 2, 3], "od600": [0.03, 0.04, 0.12, 0.3]})
    assert growth_res["mu_max"] > 0
    assert "flags" in growth_res


def test_microbiology_plugin_ast() -> None:
    plugin = MicrobiologyPlugin()
    zone_res = plugin.execute_logic(
        {"mode": "ast_zone", "organism": "escherichia_coli", "antibiotic": "ciprofloxacin", "zone_mm": 28}
    )
    assert zone_res["interpretation"] == "Susceptible"

    mic_res = plugin.execute_logic(
        {"mode": "ast_mic", "organism": "escherichia_coli", "antibiotic": "ciprofloxacin", "mic_ug_ml": 2.0}
    )
    assert mic_res["interpretation"] == "Resistant"
