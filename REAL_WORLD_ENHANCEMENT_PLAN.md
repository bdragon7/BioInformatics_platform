# Real-World Enhancement Plan: Optional R, QC Algorithms, Metadata, and Error Prevention

## 1) R Integration Strategy (Python-first, R optional)

## Design principles
- Core application must function fully with Python stack only.
- R is an optional accelerator for specific methods (DESeq2/edgeR/limma, etc.).
- Every R-gated feature must have a visible Python alternative.

## Architecture
1. **Capability registry**
   - Each feature tagged as `python`, `r`, or `hybrid`.
   - UI renders `R Required` badge for unavailable R features.
2. **Runtime detection**
   - Detect `Rscript` in PATH, then portable `./R/bin/Rscript.exe`.
   - Show status banner and feature matrix on launch.
3. **Installer subsystem**
   - In-app portable R installer (download/extract/validate/install packages).
   - No restart required; hot-refresh capability table.
4. **Project-level environment lock**
   - Save Python and R package versions per project snapshot.

## User flow
- First run without R:
  - show warning banner + “Install R later” CTA
  - allow all Python workflows immediately
- user opens R feature:
  - prompt: install R now or run Python alternative

## Implemented foundation in code
- `RIntegrationManager` supports detection, feature availability messaging, and installer plan metadata.
- Feature mapping already includes Python alternatives for key workflows.

---

## 2) QC Check Algorithms (real-world sample validation)

## Layered QC pipeline
1. **Input integrity**
   - sample ID collisions, missing metadata, schema mismatch
2. **Distribution and outlier screening**
   - z-score or robust MAD outlier detection
3. **Sample identity checks**
   - within-group correlation expected > between-group
   - flag potential mix-ups when opposite-group correlation dominates
4. **Batch signal checks**
   - unsupervised projections (PCA/UMAP) + metadata coloring
   - quantify batch separation metrics and warnings
5. **Traffic-light scoring**
   - green/yellow/red aggregate from individual rules

## Minimum algorithms
- **Outliers**: z-score threshold (configurable)
- **Mix-up detection**: nearest-neighbor correlation with group mismatch detection
- **QC severity model**: warning vs error with actionable recommendations

## Future algorithm modules
- sex verification from chrX/chrY markers
- contamination estimation (species mix, rRNA, adapters)
- RNA-seq artifacts (5'/3' bias, GC bias, duplication)

## Implemented foundation in code
- `detect_outliers`, `detect_sample_mixup_by_correlation`, and `qc_traffic_light` added.

---

## 3) Metadata Schema Design

## Core schema
Required fields:
- `sample_id` (unique)
- `group` (primary contrast factor)

Recommended fields:
- `batch`, `timepoint`, `sex`, `replicate_type`, `platform`, `operator`, `collection_date`

## Schema capabilities
- field typing: categorical, numeric, date, text
- per-field validation rules
- ontology mapping/normalization (e.g., tumour → tumor)
- duplicate detection and completeness scoring

## Storage model
- project-local metadata table + schema manifest
- versioned metadata snapshots with diff capability

## Implemented foundation in code
- `MetadataSchemaManager`, `MetadataRecord`, and validation result model.
- duplicate and required-field checks, unknown-field warnings, category standardization helper.

---

## 4) Error Prevention System Architecture

## Guardrail engine
1. pre-analysis checklist generator
2. automatic rule evaluation
3. blocking/non-blocking recommendation model
4. user acknowledgement and audit log

## Checklist dimensions
- normalization status
- batch effect review
- outlier review
- sample size/power adequacy
- statistical assumption diagnostics

## Decision policy
- critical failures block run by default (configurable)
- non-critical failures allow “Proceed with caution” and require acknowledgment

## UX patterns
- traffic-light indicators per checklist item
- one-click “Fix now” shortcuts (normalize, run assumption checks, apply correction)
- explanation panel: why this check matters biologically

## Implemented foundation in code
- `AnalysisGuardrails` with checklist model and recommendation logic.

---

## 5) Delivery plan (aligned with revised priority)

## Phase 0 (month 1)
- finalize Python-first capability matrix
- ship optional R installer workflow and status UX
- implement QC v1 (outlier + mix-up)
- implement metadata v1 and pre-analysis guardrails

## Phase 1 (months 2-3)
- advanced checklist + assumption tests
- script import/export with parameter extraction
- crash checkpoint/resume

## Phase 2 (months 4-6)
- contamination, sex verification, batch diagnostics expansion
- format conversion/validation engine
- power analysis tooling

## Phase 3+ (months 7-12)
- HPC/LIMS integration, provenance graph, cloud/repository integration, domain packs

---

## 6) Validation strategy
- deterministic unit tests for all guards/QC rules
- adversarial tests with messy metadata and mislabeled samples
- replay tests to ensure checks are captured in provenance
- pilot testing with wet-lab and computational users for false-positive tuning
