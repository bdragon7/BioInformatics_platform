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


## Real-world enhancements plan

See `REAL_WORLD_ENHANCEMENT_PLAN.md` for detailed implementation plans covering optional R integration, QC algorithms, metadata schema, and error-prevention architecture.


## Biophysics + microbiology regulatory integration plan

See `BIOPHYSICS_MICROBIOLOGY_INTEGRATION_PLAN.md` for detailed curve-fitting, QC, and module-integration architecture covering EN 1276/ASTM biofilm standards and biophysics workflows (FA/ITC/SPR/IC50).


## Downloadable executable builds (GitHub Actions)

This repository now includes CI packaging to generate downloadable artifacts:

- Windows portable zip with executable: `BioinformaticsStudio-portable-windows.zip`
- Linux portable tarball: `BioinformaticsStudio-portable-linux.tar.gz`

How to get it from GitHub:
1. Open the **Actions** tab.
2. Run **Build Portable Executables** (or use artifacts from a recent run).
3. Download the artifact zip/tarball from the workflow run page.

If you want persistent download links, create a GitHub Release and attach the generated artifacts.


## AI DoE assistant providers

The DoE assistant is wired for **ChatGPT** or **Gemini** providers (not Claude-specific APIs):

- ChatGPT: set `OPENAI_API_KEY`
- Gemini: set `GEMINI_API_KEY`

Implemented in `src/bioplatform/llm/doe_assistant.py`.
