# Open-Source Benchmark Report

Generated: 2026-02-16T18:04:21.037901+00:00
Python: 3.10.19
Platform: Linux-6.12.47-x86_64-with-glibc2.39

## Library availability

- numpy: no
- pandas: no
- sklearn: no

> Note: benchmark comparisons include the strongest available open-source implementation in this environment.

## Results

| Category | Function | Implementation | Seconds | Relative to fastest |
|---|---|---|---:|---:|
| statistics | mean | BioPlatform | 0.665117 | 1.13x |
| statistics | mean | stdlib.statistics.mean | 0.586939 | 1.00x |
| statistics | median | BioPlatform | 0.021826 | 1.00x |
| statistics | median | stdlib.statistics.median | 0.021797 | 1.00x |
| statistics | stddev | BioPlatform | 0.102977 | 1.00x |
| data_cleaning | growth_sanitize | BioPlatform.smart_sanitize_growth_values | 0.007326 | 1.00x |
| outliers | lof | BioPlatform.lof_outliers | 0.029489 | 1.00x |

## Reproduce

```bash
python scripts/benchmark_open_source.py
```
