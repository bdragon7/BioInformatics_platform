# Portable Bioinformatics Analysis Platform — Detailed Implementation Plan

## 1) Product Vision & Scope

Build a **Windows-portable, dual-language bioinformatics workbench** that launches from a folder (no installer wizard, no admin rights), integrates **Python + R**, and provides:

- GUI-first workflows for bioinformaticians and wet-lab scientists
- Visual pipeline builder with reusable templates
- Rich interactive plotting + in-place graph editing
- Broad bioinformatics file format support and batch import
- Built-in tools plus extensible plugin ecosystem (PyPI/Conda/CRAN/Bioconductor/GitHub)

---

## 2) Recommended Architecture

## 2.1 High-level component model

1. **Desktop Shell (GUI)**
   - Framework: **PySide6 (Qt for Python)**
   - Responsibilities: windows, dialogs, workflow builder, project navigation, import wizard, plot editor panels, plugin manager UI, tooltips/help overlays.

2. **Execution Orchestrator**
   - Python service in-process (or local subprocess) handling job scheduling, provenance, logs, cancellation, and environment dispatch.
   - Executes analysis nodes as Python/R tasks through a standardized task contract.

3. **Dual-language Runtime Bridge**
   - **Python-first host** + R integration through one of:
     - `rpy2` for tight in-process calls (best for small to medium operations)
     - `subprocess` + `Rscript` wrappers for isolation/reliability on heavy jobs
   - Recommended: **hybrid model** (default subprocess for robustness; optional rpy2 for interactive transformations).

4. **Data Layer / Project Workspace**
   - Project folder structure inside app directory:
     - `/projects/<project_id>/raw`, `/intermediate`, `/results`, `/figures`, `/logs`, `/metadata`
   - Metadata DB: SQLite (`project.db`) for pipeline definitions, execution history, graph style templates, plugin registry cache.

5. **Plugin Subsystem**
   - Local plugin manifest registry + searchable package index adapter.
   - Supports Python and R package lifecycle and external GitHub-source plugins.

6. **Visualization & Graph Editing Engine**
   - Interactive plotting canvas with element selection, property inspector, layer manager, undo/redo command stack, and export module.

---

## 2.2 Suggested technology stack

- **GUI**: PySide6 + Qt Designer assets
- **Workflow canvas**: Qt Graphics View or Qt Quick (node editor style); optional library: `qtpynodeeditor`
- **Interactive plotting**:
  - Primary: **Plotly + Dash embedded via Qt WebEngine** for high interactivity
  - Secondary: `pyqtgraph` for large scatter/real-time performance
  - R graphics editing path: render through `ggplot2` + editable schema bridge (see section 5)
- **Python bio stack**: pandas, polars, numpy, scipy, scikit-learn, statsmodels, biopython, pysam, scanpy, anndata
- **R bio stack**: tidyverse, data.table, BiocManager + core Bioconductor sets
- **Background tasks**: `concurrent.futures` + `QThreadPool`, optional `celery`-like local queue abstraction
- **Configuration**: `pydantic` + YAML/TOML
- **Logging**: structured JSON logs + GUI log viewer
- **Testing**: pytest + Qt test harness + Playwright-like UI automation equivalent for desktop (squish/pytest-qt)

---

## 3) GUI Design Blueprint

## 3.1 Primary UI surfaces

1. **Home/Project Dashboard**
   - Recent projects, templates, recovery prompts, environment health status.

2. **Data Import Studio**
   - Drag-and-drop dropzone
   - Source selector (local file, folder batch, Google Sheets URL)
   - Preview grid + inferred schema + type correction dropdowns
   - Validation panel with warnings/errors

3. **Workflow Builder**
   - Node palette grouped by domain (RNA-seq, metagenomics, cytometry, microscopy, QC)
   - Drag-to-canvas, connect ports, validate DAG, run all/selected
   - Node configuration panels with embedded docs and examples

4. **Results & Visualization Workbench**
   - Multi-tab plot/table output
   - Graph editor side panel (context-sensitive controls)
   - Layer manager and style template browser

5. **Plugin Manager**
   - Search across PyPI/Conda/CRAN/Bioconductor + GitHub import
   - Install/update/remove; compatibility matrix; dependency graph

6. **Help & Tooltips System**
   - Context tooltips on hover for every action/control
   - “What does this do?” inline info icons linked to docs
   - Guided tours for first-time users and domain-specific workflow walkthroughs

## 3.2 Usability principles for mixed audiences

- Domain language presets (“Wet-lab mode” vs “Advanced mode”)
- Minimal default complexity with expandable advanced options
- Preset pipelines with clear biological interpretations
- Immediate visual feedback for every user action

---

## 4) Data Import & Format Handling Strategy

## 4.1 Tabular import

- Excel (`.xlsx`, `.xls`) multi-sheet support via `openpyxl`/`xlrd`
- CSV/TSV autodetect delimiter/encoding
- Google Sheets via published/export URL + API mode when credentials available
- LibreOffice/OpenOffice through ODS readers
- Preview: first N rows + schema inference (numeric/categorical/date/text)
- Column mapping templates saved per lab/project

## 4.2 Bioinformatics formats

- FASTA/FASTQ: `biopython`
- BAM/SAM/VCF/BCF: `pysam`
- GFF/GTF/BED: parser adapters (`gffutils`, custom loaders)
- FCS (flow cytometry): `FlowCal`, `fcsparser`
- Microscopy formats: `tifffile`, `aicsimageio`
- Batch import with file-set validator and manifest generation

---

## 5) Interactive Graph Editing Design

## 5.1 Element selection model

- Click-to-select support for: points, lines, bars, axes, legends, labels, annotations, arrows, confidence regions.
- Selection represented as object IDs in a plot scene graph.

## 5.2 Real-time property editor

Editable properties (with instant redraw):
- Color picker + palettes
- Shapes and marker symbols
- Line styles and stroke widths
- Fill patterns/textures
- Opacity sliders
- Arrow style, size, direction
- Font family/size/weight/color
- Axis formatting and scales

## 5.3 Layer & history system

- Layer tree (lock/hide/reorder/group)
- Undo/redo implemented with command pattern (`QUndoStack`)
- Snapshot-based autosave for recoverability

## 5.4 Publication exports

- Native export: PNG, TIFF, SVG, PDF
- Optional journal presets (DPI, CMYK workflow notes, font embedding checks)

---

## 6) Analysis Capability Bundles (pre-installed)

1. **Sequence analysis**
   - QC, alignment wrappers, assembly hooks, annotation helpers
2. **RNA-seq/transcriptomics**
   - Count import, normalization, DE analysis, enrichment
3. **Metagenomics/microbiome**
   - Taxonomic profiles, diversity metrics, ordination
4. **Flow cytometry**
   - Gating, compensation, population statistics
5. **Microscopy image analysis**
   - Segmentation, feature extraction, intensity quantification
6. **Statistical plotting/QC**
   - Batch QC reports, PCA/UMAP, clustering, hypothesis tests

Each bundle is delivered as workflow templates + callable Python/R tasks.

---

## 7) Plugin Architecture (including “find all plugins” requirement)

## 7.1 Plugin package model

- Plugin = manifest + runtime hooks + optional GUI panels
- Manifest fields:
  - id, name, version, language (python/r/mixed), source, entrypoint
  - dependencies, compatible app versions, docs URL, license

## 7.2 Multi-source plugin discovery

Implement **Plugin Index Aggregator** with connectors:

1. **Python**
   - PyPI search API + simple package index scraping fallback
   - Conda channels (bioconda/conda-forge) metadata queries
2. **R**
   - CRAN packages index
   - Bioconductor package list + release compatibility
3. **GitHub import (required fallback path)**
   - User can provide GitHub URL/repo
   - If not found in package repositories, import plugin from GitHub directly
   - Support private repos via PAT token entry
4. **Local plugin zip/folder import**

## 7.3 Dependency and version resolution

- Build an internal solver layer that delegates to:
  - `pip`/`uv` for Python
  - `conda` optional environment mode for complex binaries
  - `Rscript` + `install.packages`/`BiocManager::install` for R
- Conflict detection shown pre-install with mitigation suggestions.

## 7.4 Safety and governance

- Plugin signing/checksum support
- Permission model (filesystem/network/process)
- Sandboxed execution option for untrusted plugins

## 7.5 Documentation integration and tooltips

- Auto-ingest README/docs from plugin source
- Generate structured help cards and inline tooltips for plugin-exposed functions
- Every function must define: purpose, inputs, outputs, example usage

---

## 8) Windows Portable Packaging Strategy

## 8.1 Distribution layout

```
BioPlatform/
  BioPlatform.exe
  runtime/
    python/
    R/
    libs/
  plugins/
  projects/
  config/
  logs/
```

## 8.2 Packaging approach

1. **Python portable runtime**
   - Embed CPython distribution + wheels pre-bundled
2. **R portable runtime**
   - Ship portable R folder with required packages pre-installed
3. **App executable launcher**
   - Build with PyInstaller/Nuitka to `BioPlatform.exe`
   - Launcher sets local env vars (`PATH`, `R_HOME`, cache dirs)
4. **No installer wizard**
   - Zip release; user extracts and launches `.exe`
5. **No-admin operation**
   - Write only to app-local directories
6. **Optional self-update**
   - In-app updater downloads new zip and swaps versions safely

## 8.3 Handling heavy dependencies

- Offer “core” and “extended” portable bundles
- Lazy-install optional toolchains into local `runtime/` on first use

---

## 9) Reliability, Autosave, and Recovery

- Autosave project metadata + open plots + workflow state every N minutes
- Journal file for active runs to recover after crashes
- Reproducibility manifest for every pipeline run (package versions, parameters, input hashes)

---

## 10) Security & Compliance Baseline

- Signed binaries for release trust
- Dependency vulnerability scanning in CI
- Optional offline mode for regulated labs
- Audit logs for plugin install/execution events

---

## 11) Development Roadmap

## Phase 0 (2–3 weeks): Foundations
- Requirements finalization with target user personas
- UX wireframes and interaction specs
- Architecture skeleton, project workspace model, logging

## Phase 1 (4–6 weeks): Core App MVP
- Project dashboard, import studio (CSV/Excel/TSV), basic workflows
- Python + R execution bridge
- Initial plotting + export (PNG/SVG/PDF)

## Phase 2 (5–7 weeks): Bioinformatics Core Packs
- Add FASTA/FASTQ/BAM/VCF/GFF importers
- Deliver RNA-seq + metagenomics + QC starter workflows
- Add result provenance and reproducibility metadata

## Phase 3 (5–6 weeks): Advanced Graph Editor
- Element selection, property inspector, layer manager
- Undo/redo and style templates
- Publication-grade export refinements (TIFF, high DPI presets)

## Phase 4 (4–5 weeks): Plugin Ecosystem
- Plugin manager UI
- PyPI/Conda/CRAN/Bioconductor indexing
- GitHub fallback importer + docs ingestion + tooltips autogen

## Phase 5 (3–4 weeks): Portable Windows Hardening
- Bundle Python+R runtimes
- Optimize startup time and package footprint
- No-admin validation matrix across Windows versions

## Phase 6 (3–4 weeks): QA & Pilot
- Automated tests + usability testing with scientists
- Performance profiling on large datasets
- Pilot deployment and feedback loop

---

## 12) Recommended GUI Framework Decision

### Primary recommendation: **PySide6 + Plotly (embedded) + pyqtgraph**

Why this best fits your requirements:
- Strong native desktop UX for complex multi-panel scientific apps
- Excellent control for workflow canvas, plugin manager, and dockable editors
- Plotly gives rich interactive editing potential; pyqtgraph handles high-volume data
- Mature Windows packaging story with PyInstaller/Nuitka
- Easy integration with Python orchestration and R bridge

Alternative:
- **Electron + Python/R backend**: high UI flexibility but larger footprint and higher packaging complexity for a portable scientific runtime.

---

## 13) Implementation Deliverables Checklist

- [ ] Portable Windows zip build (no installer)
- [ ] Python + R runtime bundle and health checks
- [ ] GUI: dashboard, import wizard, workflow builder, result studio
- [ ] Interactive graph editor with full property controls + layers + undo/redo
- [ ] Plugin manager with searchable repositories and GitHub import fallback
- [ ] Built-in contextual tooltips/help for every function
- [ ] Pre-installed bioinformatics workflow bundles
- [ ] Project autosave/recovery and reproducibility manifests
- [ ] Export suite (PDF/SVG/PNG/TIFF)

