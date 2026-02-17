from pathlib import Path

from bioplatform.core.preferences import PreferencesManager, UserPreferences


def test_preferences_roundtrip(tmp_path: Path) -> None:
    manager = PreferencesManager(tmp_path / "config" / "user_preferences.json")
    current = manager.load()
    assert current.project_root
    assert current.output_dir
    assert current.ai_provider in {"chatgpt", "gemini"}

    manager.save(
        UserPreferences(
            project_root="my_projects",
            output_dir="my_outputs",
            ai_provider="gemini",
            openai_api_key="",
            gemini_api_key="g-key",
        )
    )
    loaded = manager.load()
    assert loaded.project_root == "my_projects"
    assert loaded.output_dir == "my_outputs"
    assert loaded.ai_provider == "gemini"
    assert loaded.gemini_api_key == "g-key"
