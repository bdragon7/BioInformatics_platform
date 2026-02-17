# BUGFIX_CHANGELOG

## Scope
This change set hardens production-readiness foundations for stability, error guidance, and workflow correctness.

## Fixes delivered

### 1) Large CSV ingestion resilience
- **Before:** No chunked CSV loading helper existed for large files, risking high-memory reads.
- **After:** Added `ChunkedCSVReader.read_csv()` that streams with `pandas.read_csv(..., chunksize=...)` and optional progress callbacks.
- **Verification:** Added automated test for chunked read and progress notifications.

### 2) Pipeline step ordering correctness (DAG)
- **Before:** No dedicated DAG execution primitive with topological sort was available.
- **After:** Added `WorkflowDAGExecutor` with deterministic topological ordering and cycle detection.
- **Verification:** Added tests for ordered execution and cycle detection.

### 3) User-facing error handling quality
- **Before:** Multiple UI paths surfaced generic `Execution error: ...` style messages.
- **After:** Added centralized `WorkplaceErrorHandler` catalog and plaintext guidance output; integrated into pipeline-runner and formulation toolbox error paths in GUI.
- **Verification:** Added tests validating templated, actionable error messages and snapshot metadata.

### 4) Feature audit deliverable
- **Before:** No explicit feature-audit artifact in repo.
- **After:** Added `FeatureAudit` engine + script to produce `FEATURE_AUDIT_REPORT.md` for repeatable status snapshots.
- **Verification:** Added tests for report generation and key content.

## Notes
- This changelog documents implemented fixes in this iteration and establishes scaffolding for the remaining enterprise checklist items.
