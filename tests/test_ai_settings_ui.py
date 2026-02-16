from pathlib import Path


def test_ai_settings_and_assistant_hooks_present() -> None:
    source = Path("src/bioplatform/gui/app.py").read_text(encoding="utf-8")
    assert "AI Assistant" in source
    assert "open_ai_assistant" in source
    assert "AI provider" in source
    assert "ChatGPT API key" in source
    assert "Gemini API key" in source
