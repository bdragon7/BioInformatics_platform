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

- Windows portable zip with executable: `BioinformaticsStudio-windows-noexe.zip`
- Linux portable tarball: `BioinformaticsStudio-linux-script.tar.gz`

How to get it from GitHub:
1. Open the **Actions** tab.
2. Run **Build Portable Packages** (or use artifacts from a recent run).
3. Download the artifact zip/tarball from the workflow run page.

If you want persistent download links, create a GitHub Release and attach the generated artifacts.


## AI DoE assistant providers

The DoE assistant is wired for **ChatGPT** or **Gemini** providers (not Claude-specific APIs):

- ChatGPT: set `OPENAI_API_KEY`
- Gemini: set `GEMINI_API_KEY`

Implemented in `src/bioplatform/llm/doe_assistant.py`.


## Premium UI refresh

The desktop UX has been upgraded with an Adobe-inspired workspace style:
- Gradient action buttons and polished light/dark/high-contrast themes
- Hero header card with project state and global quick-search
- Professional toolbar + inspector layout with command shortcuts (`Ctrl+K`, `Ctrl+L`)
- Card-based panels and refined typography for improved readability during long analysis sessions


## Windows without .exe

The Windows package is script-based (no compiled `.exe`).

1. Download `BioinformaticsStudio-windows-noexe.zip` from GitHub Actions artifacts.
2. Extract it.
3. Run `setup_windows_env.bat` once to create `.venv` and install dependencies.
4. Launch with `run_windows_noexe.bat`.

This avoids `.exe` binaries while remaining double-click runnable via batch scripts.



## Windows executable alternative (.exe)

A compiled Windows package is also available when a native executable is preferred:

1. Download `BioinformaticsStudio-windows-exe` artifact from GitHub Actions (file: `BioinformaticsStudio-portable-windows.zip`).
2. Extract the zip.
3. Start the app using `BioinformaticsStudio.exe` from the extracted folder.

To build locally on Windows:

```powershell
./scripts/build_windows_portable.ps1
```

## Launch with Anaconda / Miniconda

If the app does not launch with system Python, use Conda:

### Windows
1. Run `scripts\setup_conda_env.bat` (creates env `bioinfostudio` by default).
2. Launch using `launch_conda.bat`.

### Linux/macOS
1. Run `./scripts/setup_conda_env.sh`.
2. Launch using `./launch_conda.sh`.

Optional custom env name:
- `scripts\setup_conda_env.bat myenv` then `launch_conda.bat myenv`
- `./scripts/setup_conda_env.sh myenv` then `./launch_conda.sh myenv`


## Launch with Spyder (corporate-friendly fallback)

If Conda execution is blocked by corporate policies but Spyder is available:

### Windows
- Double-click `launch_spyder.bat` (opens `main.py` in Spyder).

### Linux/macOS
- Run `./launch_spyder.sh`.

Then run `main.py` from Spyder (Run ▶ Run file). This uses Spyder's interpreter while keeping project paths configured.


### Spyder setup helper (no Conda required)

If corporate policy blocks Conda activation, use:

- Windows: `scripts\setup_spyder_env.bat`
- Linux/macOS: `./scripts/setup_spyder_env.sh`

Then start Spyder with `launch_spyder.bat` / `./launch_spyder.sh`.


## Helix-UI (ChromeOS/Aluminium aesthetic)

A new PySide6 workspace skeleton is included with glassmorphic styling and bioinformatics-focused layout:
- translucent Aluminium-style window and glass panels
- dynamic tonal palette generation (Material You compatible; fallback included)
- 24px rounded controls and 12px data-table geometry
- bottom floating shelf (Sequence Viewer, BLAST, 3D model, Open File)
- high-density sequence viewer (`QPlainTextEdit` + `QSyntaxHighlighter` for A/C/G/T)
- vertical splitter layout: sequence viewer (top) + variant table (bottom)
- background file parsing via `QThread` to keep UI responsive
- standard easing panel animations + spring-style completion modal
- DNA selection “biological bloom” glow effect

Launch it with:

```bash
python main.py --helix-ui
```

## Aluminium-Bio plugin architecture

The desktop shell now includes the first pass of a hot-swappable local plugin runtime:

- Local plugin directory convention: `plugins/<plugin_name>/manifest.json` + `plugins/<plugin_name>/plugin.py`
- `plugin.py` should expose `Plugin` deriving from `bioplatform.plugins.BioPlugin`
- Enable/disable states are persisted to `config/plugins_enabled.json`
- UI productivity features include `Ctrl+K` Command Palette, drag-and-drop file suggestions, and a Plugin Marketplace dialog

Minimal plugin sketch:

```python
from bioplatform.plugins import BioPlugin

class Plugin(BioPlugin):
    plugin_id = "demo.plugin"
    plugin_name = "Demo Plugin"

    def register_ui(self, context):
        return {"title": context.app_name}

    def execute_logic(self, payload):
        return {"ok": True}
```


## Microbiology intelligence upgrade

The platform now includes microbiology-focused automation primitives:

- Z-score outlier detection for biological replicates (`|Z| > 2.5` configurable)
- Standard-curve linear regression with `R^2` summary output
- Growth curve auto-analysis: `μmax`, generation time, carrying capacity (`K`), lag phase estimate
- Contamination spike flags for negative-control traces
- Built-in `MicrobiologyPlugin` with AST interpretation (zone and MIC) against local JSON standards


### PyMOL auto-load from GitHub during Windows builds

Windows build scripts now attempt to auto-install PyMOL from GitHub:
- `git+https://github.com/schrodinger/pymol-open-source.git`

Disable auto-load by setting environment variable before running build/setup:

```powershell
$env:BIOPLATFORM_AUTOLOAD_PYMOL = "0"
```

```
set BIOPLATFORM_AUTOLOAD_PYMOL=0
```

## Structure integrations (PyMOL + AlphaFold)

Yes — the app now includes a lightweight structure-integration module:

- **PyMOL detection** to check whether `pymol-open-source` is available in your environment.
- **AlphaFold connection helper** that builds direct EBI AlphaFold entry URLs from UniProt IDs.
- A **Structure** toolbar action in the desktop app to show integration status and open an AlphaFold entry in the browser.

Install PyMOL module (optional):

```bash
pip install pymol-open-source
```


### Spreadsheet formula support

The built-in data grid now supports Excel/Google-Sheets style formulas in editable cells, including:
- cell references (example: `=A1+B1`)
- range functions: `SUM`, `AVERAGE`, `MIN`, `MAX`, `STDDEV`/`STDEV` (example: `=SUM(A1:B5)`)
- numeric functions: `SQRT` (example: `=SQRT(A1)` or `=SQRT(9)`)
- arithmetic operations with cell references (`+`, `-`, `*`, `/`)

Formula text is preserved during edit, while the computed value is shown in display mode.

### New Project creation

The desktop toolbar now includes a **New Project** action that creates a full project folder structure under your configured project root (raw/intermediate/results/figures/logs/metadata).

### Path preferences in Settings

The desktop **Settings** dialog now includes persistent path preferences:
- **Project root** location
- **Output directory** location

These are saved in `config/user_preferences.json` and used by the app for default project/file workflow locations.

## Toolkit Integrator (open-source wrappers)

A new integrator layer wraps best-in-class open-source libraries behind a plugin-style interface with a universal result schema:

- Universal result object: `{ "data": ..., "plots": ..., "outliers": [...] }`
- Data-cleaning middleware: sequence sanitization, growth-value sanitization, and LOF outlier detection
- Optional wrappers for: **GSEAPY**, **BioPandas**, **CobraPy**, and **Statsmodels**
- UI toggle panel under **Settings** to enable/disable these integrated tools

These wrappers are optional-safe: if a dependency is unavailable, the tool returns an error payload without crashing the app.


## Analysis Library (R + Python)

A built-in analysis library is now available from the desktop toolbar (**Analysis Library**) with curated functions/templates inspired by common modern bioinformatics workflows:

- **Python executable functions** (run directly in-app): mean, median, sample stddev, growth-rate estimate, IC50 approximation, GC content
- **R templates** (copy/use quickly): DESeq2 differential expression, limma batch correction, microbial growth `nls` fitting
- **Cross-domain coverage**: bioinformatics, genomics, pharmacology, microbiology

The dialog lets you select a function, run Python functions on numeric payloads, or preview R templates instantly.


## Automated Python/R Pipelines

The app now includes a **Pipelines** runner in the toolbar for end-to-end automation:

1. **Clean data** (NaN repair and normalization-ready values)
2. **Calculate stats** (mean/median/stddev + outlier detection)
3. **Generate figure** (editable Matplotlib figure object)
4. **Export high quality** outputs to `PNG` (600 dpi), `SVG`, and `PDF`

The pipeline dialog also provides an R pipeline template (`ggplot2`) for reproducible R-side execution.

