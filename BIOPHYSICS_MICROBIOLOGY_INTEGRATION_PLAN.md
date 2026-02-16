# Biophysics + Antimicrobial Regulatory Integration Plan

## Skill usage note
No external skill used in this turn (request is domain architecture/implementation, not skill creation/installation).

## 1) Curve fitting algorithms implementation plan

## 1.1 Core fitting stack
- Use `scipy.optimize.least_squares` for robust nonlinear fitting.
- Add `lmfit` wrappers for constrained/global fitting (shared Kd across datasets).
- Standardize model interface:
  - parameters dict
  - forward model function
  - bounds/constraints
  - fit diagnostics and covariance

## 1.2 Technique-specific models

### Fluorescence anisotropy (FA)
- 1:1 quadratic binding for ligand depletion.
- Hill/cooperative extension.
- Competition model with IC50 to Ki conversion (Cheng–Prusoff).
- Time-resolved kinetic fits:
  - association: `r(t)=r_eq-(r_eq-r0)e^{-kobs t}`
  - dissociation: `r(t)=r_inf+(r0-r_inf)e^{-koff t}`

### ITC
- Independent site model (Kd/Ka, n, ΔH).
- Sequential two-site extension with parameter correlation checks.
- C-value driven design checks and model confidence flags.

### SPR/BLI
- 1:1 Langmuir kinetic fits for kon/koff.
- Steady-state affinity fallback when kinetics are unresolved.
- Two-state and mass-transport-limited model options.

### IC50 universal
- 4PL as default.
- 3PL and 5PL variants.
- Hill slope sanity checks and outlier-resistant refit option.

## 1.3 Model selection and diagnostics
- AIC/BIC ranking between competing models.
- Residual whiteness checks and leverage/outlier analysis.
- Bootstrap CIs + profile likelihood intervals for key parameters.

---

## 2) Quality control metrics plan

## 2.1 Regulatory antimicrobial QC
- EN 1276 validity:
  - water control viability (±0.5 log)
  - neutralization effectiveness (>50% recovery)
  - pass criterion (≥5 log reduction)
- ASTM biofilm checks:
  - untreated biofilm minimum burden
  - sterility controls
  - recovery efficiency checks
  - biofilm vs planktonic susceptibility gap

## 2.2 Biophysics QC
- FA:
  - G-factor range checks
  - photobleaching trend alerts
  - inner filter effect screening
- ITC:
  - c-value warnings (<1 or >1000)
  - injection baseline drift and saturation checks
- SPR:
  - reference subtraction quality
  - non-specific binding and rebinding signatures
  - RI artifact detection

## 2.3 Cross-technique consistency QC
- Compare Kd across FA/ITC/SPR/MST.
- Flag >3-fold disagreement and prompt root-cause checklist.
- Track confidence score weighted by model fit + QC pass rates.

---

## 3) Integration architecture between microbiology and biophysics modules

## 3.1 Shared domain model
- `ExperimentRecord` (technique/protocol/sample IDs/controls)
- `ResultRecord` (primary endpoints + uncertainty)
- `QCRecord` (rule, severity, recommendation)
- `ProvenanceRecord` (inputs, params, versions, seed)

## 3.2 Service-oriented module boundaries
- `core.antimicrobial_standards`:
  - EN 1276 + ASTM calculators, compliance checks, templated reports
- `core.biophysics`:
  - kinetic/thermodynamic equations, fitting primitives, quality diagnostics
- `core.error_prevention` + `core.qc_checks`:
  - reusable rule engine and traffic-light scoring

## 3.3 Unified analysis pipeline
1. Import + format detect/validate
2. Protocol template load (EN/ASTM/FA/ITC/SPR/IC50)
3. Rule-based QC pre-check
4. Fit/compute + confidence metrics
5. Cross-technique validation
6. Provenance snapshot + report generation

## 3.4 UI integration
- Technique/protocol selector cards in a single dashboard.
- Shared parameter editor, QC panel, residuals panel, and report preview.
- “Explain this warning” links to contextual teaching snippets.

## 3.5 Reporting and compliance
- GLP/GMP-oriented audit trail fields:
  - operator, timestamp, instrument, calibration state
- Generated report sections:
  - protocol compliance checklist
  - raw/processed data summary
  - model equation + fit metrics
  - QC outcomes and deviations

---

## 4) Implemented code foundations in this iteration

- `src/bioplatform/core/antimicrobial_standards.py`
  - EN 1276 evaluator and validity checks
  - biofilm log-reduction and planktonic-vs-biofilm interpretation
  - replicate summary (`mean/sd/95% CI`)
- `src/bioplatform/core/biophysics.py`
  - core kinetic/thermodynamic helpers
  - FA anisotropy formula
  - 4PL and Cheng–Prusoff conversion
  - ITC c-value assessment and fit-quality utilities

These utilities are ready for wiring into GUI workflows and report generators.

---

## 5) Next engineering milestones

1. Add SciPy/lmfit-backed optimizers and uncertainty propagation.
2. Build EN 1276 and ASTM template wizards with strict data-entry schemas.
3. Add FA/ITC/SPR workspace widgets with residual diagnostics.
4. Implement cross-technique Kd comparison dashboard.
5. Generate regulatory report templates (PDF/HTML) with signed audit trails.
