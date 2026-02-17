# IsoDesign Ultra — Wet-Lab Scientist Architecture Guide

This guide translates the software architecture into **lab-facing language**.

---

## 1) What this system is (in lab terms)

Think of IsoDesign Ultra as a digital lab team:

- **Lab Coordinator (Orchestrator)**: decides what step runs next.
- **Protocol Library (Plugins)**: each method does one task (e.g., descriptor calculation, stats test, plot generation).
- **DoE Scientist (AutoDoE)**: proposes the next best experimental conditions.
- **Chemistry Safety/Compatibility Checker**: flags likely incompatibilities and formulation risks.
- **Python↔R Translator**: lets Python and R methods work together without manual file shuffling.

---

## 2) What happens during a typical workflow

1. You provide inputs (e.g., SMILES, concentration ranges, organism target, constraints).
2. The Orchestrator checks available plugins and builds a step order.
3. Chemistry/QSAR tools evaluate candidate space.
4. DoE engine suggests next experiments.
5. Results are passed to R/Python statistics/plots.
6. You get recommendations + run-ready factor tables.

---

## 3) Module map (plain language)

### A. `IsoDesign_Ultra/core/kernel.py` — Plugin intake + health checks

**What it does for lab users**
- Autodetects methods dropped into plugin folders (`.py` and `.R`).
- Verifies each method describes inputs/outputs in metadata.
- Checks whether key scientific runtime pieces are available (R, RDKit, rpy2).

**Wet-lab value**
- You can add a new assay-analysis method without rewriting the whole platform.

---

### B. `IsoDesign_Ultra/core/orchestrator.py` — The run coordinator

**What it does for lab users**
- Builds dependency-aware execution order from requested outputs.
- Chains methods so outputs from one step become inputs to the next.

**Wet-lab value**
- Fewer manual handoffs between tools/spreadsheets.

---

### C. `IsoDesign_Ultra/engine/doe.py` — Adaptive DoE planner

**What it does for lab users**
- Accepts variable definitions (continuous/integer/categorical).
- Produces next candidate conditions to test.
- Can evolve to full Bayesian optimization in dependency-rich environments.

**Wet-lab value**
- Faster convergence than static one-shot DoE when targets are multi-objective.

---

### D. `IsoDesign_Ultra/chem/informatics.py` — Chemical intelligence layer

**What it does for lab users**
- Converts SMILES into model-ready feature vectors.
- Provides a formulation validator with Green Solubility Index + Hansen-style distance approximation.

**Wet-lab value**
- Early risk triage before spending bench time on unstable combinations.

---

### E. `IsoDesign_Ultra/data/bridge.py` — Python/R bridge

**What it does for lab users**
- Buffers tabular data and supports Arrow-backed exchange when available.
- Provides `@r_interop` wrapper to send DataFrame-like objects into R workflows.

**Wet-lab value**
- Uses best tool for each job (R stats, Python ML) without manual export/import loops.

---

## 4) What to put in a plugin (minimum)

Every plugin should declare:

- **Name + version**
- **Inputs** (e.g., `SMILES`, `Concentration_Matrix`)
- **Outputs** (e.g., `LogP`, `Binding_Affinity`, `Kill_Log_Reduction`)

This lets the Orchestrator chain methods correctly.

---

## 5) Wet-lab first conventions

Use these conventions so results are reproducible and easy to audit:

- Record organism, strain, inoculum, media, and contact time with every run.
- Keep units explicit (`mg/mL`, `% w/w`, `CFU/mL`, `min`, `°C`).
- For every suggested condition, store pass/fail constraints (toxicity, pH window, stability).
- Keep a single run ID from raw inputs → model outputs → final plots.

---

## 6) Suggested rollout in a real lab

### Phase 1: Assisted planning
- Use tool for compatibility triage + DoE suggestions.
- Human approves all suggested runs.

### Phase 2: Semi-automated cycles
- Import assay outcomes.
- AutoDoE proposes next batch.
- Human confirms batch release.

### Phase 3: Closed-loop optimization
- Batch results automatically feed retraining.
- Engine proposes next best experiments under explicit safety/quality constraints.

---

## 7) Safety and governance notes

- Treat model outputs as **decision support**, not final authority.
- Keep mandatory human review gates for high-risk formulations.
- Require explicit red flags for incompatible chemistries and out-of-domain predictions.

---

## 8) Quick glossary

- **Plugin**: one analysis method.
- **Orchestrator**: decides execution order.
- **DAG**: non-circular workflow graph.
- **DoE**: design of experiments.
- **QSAR**: structure–activity relationship modeling.
- **Interop**: data exchange between Python and R.

