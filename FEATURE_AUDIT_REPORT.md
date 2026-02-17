# FEATURE_AUDIT_REPORT

## Summary
- Passed: 16
- Partial: 2
- Not implemented: 0

### Core Features
- ✅ Project creation and management
- ✅ File import (CSV, Excel, FASTA, PDB, SDF)
- ✅ Data table with formula support
- ✅ Python/R dual execution runtime
- ✅ Workflow DAG builder
- ✅ Plugin system with hot reload

### Analysis Features
- ✅ Differential expression (DESeq2, edgeR)
  - Missing deps: R packages may be optional/missing in local env
- ✅ Growth curve analysis
- ✅ Statistical tests (t-test, ANOVA, etc.)
- ✅ Quality control checks
- ✅ Outlier detection
- ✅ Data normalization

### Visualization Features
- ✅ Basic plots (scatter, line, bar, box)
- ✅ Bioinformatics plots (volcano, MA, Manhattan)
- ✅ Growth curves and kill curves
- ✅ Dose-response curves (IC50)
- ⚠️ PCA/t-SNE dimensionality reduction
  - Notes: PCA/t-SNE UI hooks are not yet exposed in main shell.
- ⚠️ Heatmaps and correlation matrices
  - Notes: Dedicated heatmap/correlation workflow not fully surfaced in main UI.
