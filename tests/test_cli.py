from main import build_parser


def test_cli_parser_options() -> None:
    parser = build_parser()
    args = parser.parse_args(["--workflow", "rna_seq", "--debug"])
    assert args.workflow == "rna_seq"
    assert args.debug is True
