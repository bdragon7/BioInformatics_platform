from pathlib import Path

from bioplatform.llm.doe_assistant import DoEAssistant
from bioplatform.llm.local_engine import GemmaLoader


def test_gemma_loader_scans_models(tmp_path: Path) -> None:
    model_dir = tmp_path / "models" / "llm"
    model_dir.mkdir(parents=True)
    (model_dir / "gemma-2b-it.gguf").write_bytes(b"123")
    (model_dir / "gemma-7b-it.gguf").write_bytes(b"1234")

    loader = GemmaLoader(models_dir=model_dir)
    models = loader.list_models()
    assert len(models) == 2
    defaults = loader.resolve_default_model_paths()
    assert defaults["gemma_2b"] is not None
    assert defaults["gemma_7b"] is not None


def test_doe_assistant_local_status_and_fallback() -> None:
    bot = DoEAssistant(provider="local")
    status = bot.local_models_status()
    assert "available" in status

    message = bot.chat("suggest a DoE")
    assert "Local Gemma" in message or "replicate" in message


def test_launch_scripts_check_llama_cpp_dependency() -> None:
    sh = Path("launch_bioinfostudio.sh").read_text(encoding="utf-8")
    bat = Path("launch_bioinfostudio.bat").read_text(encoding="utf-8")
    assert "import llama_cpp" in sh
    assert "import llama_cpp" in bat
