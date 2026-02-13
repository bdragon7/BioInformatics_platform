from bioplatform.llm.doe_assistant import DoEAssistant


def test_missing_key_message() -> None:
    bot = DoEAssistant(provider="chatgpt", api_key=None)
    msg = bot.chat("Design an MIC experiment")
    assert "API key missing" in msg


def test_factorial_design_shape() -> None:
    bot = DoEAssistant(provider="gemini", api_key="dummy")
    design = bot.generate_factorial_design(["temp", "ph"], [2, 3])
    assert len(design) == 6
    assert set(design[0].keys()) == {"temp", "ph"}


def test_reset_conversation() -> None:
    bot = DoEAssistant(provider="chatgpt", api_key=None)
    bot.chat("hello")
    assert bot.history
    bot.reset_conversation()
    assert bot.history == []
