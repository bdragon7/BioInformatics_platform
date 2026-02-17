from pathlib import Path


def test_app_has_new_project_action_and_handler() -> None:
    src = Path('src/bioplatform/gui/app.py').read_text(encoding='utf-8')
    assert 'New Project' in src
    assert 'def create_new_project' in src
    assert 'workspace_manager.create_project' in src
