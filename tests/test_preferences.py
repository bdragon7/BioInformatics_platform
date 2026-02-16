from pathlib import Path

from bioplatform.core.preferences import PreferencesManager, UserPreferences


def test_preferences_roundtrip(tmp_path: Path) -> None:
    manager = PreferencesManager(tmp_path / "config" / "user_preferences.json")
    current = manager.load()
    assert current.project_root
    assert current.output_dir

    manager.save(UserPreferences(project_root="my_projects", output_dir="my_outputs"))
    loaded = manager.load()
    assert loaded.project_root == "my_projects"
    assert loaded.output_dir == "my_outputs"
