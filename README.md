# BioPlatform MVP Scaffold

This repository now contains an executable implementation scaffold for a portable bioinformatics platform with:

- Dual-runtime bridge for Python and R execution
- Project workspace manager (portable app-local folders)
- File import inspector for spreadsheet + bioinformatics formats
- Workflow DAG model with cycle validation
- Graph editor state model with undo/redo support
- Plugin discovery aggregator with CRAN/Bioconductor search and GitHub fallback import
- GUI prototype (PySide6) with built-in tooltips for core actions

## Run (GUI)

```bash
pip install -e '.[gui,dev]'
python -m bioplatform
```

## Run tests

```bash
pip install -e '.[dev]'
pytest
```

## Portable packaging direction

This scaffold is designed for a future Windows portable bundle layout (`BioPlatform.exe`, bundled Python/R runtime, app-local config/projects/logs) as described in `IMPLEMENTATION_PLAN.md`.


## Enhanced roadmap

See `ENHANCED_IMPLEMENTATION_ROADMAP.md` for the research-grade 12-month roadmap, risk register, and phase-by-phase testing strategy.


## Portable launchers

```bash
./launch_bioinfostudio.sh --help
python main.py --help
```

Windows:

```bat
launch_bioinfostudio.bat --help
```

## UI/UX plan

See `UI_UX_IMPLEMENTATION_PLAN.md` for detailed widget designs, color palette specs, icon requirements, and UI/UX testing strategy.
