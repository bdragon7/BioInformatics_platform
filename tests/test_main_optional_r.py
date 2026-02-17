import main


def test_main_does_not_fail_when_r_missing(monkeypatch) -> None:
    monkeypatch.setattr(main, "ensure_r_installed", lambda: False)
    monkeypatch.setattr(main, "ensure_pymol_installed", lambda: None)
    monkeypatch.setattr(main, "run_app", lambda **kwargs: 0)

    class DummyParser:
        def parse_args(self):
            class Args:
                project = None
                data = None
                workflow = None
                debug = False
                helix_ui = False

            return Args()

    monkeypatch.setattr(main, "build_parser", lambda: DummyParser())
    assert main.main() == 0
