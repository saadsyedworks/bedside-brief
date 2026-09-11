# Mechanical metrics

Inputs: 108 (36 base, 36 perturbation pairs, 36 noise variants). Store: 153 verified of 153 extracted; not-quantified share 24.2%; library coverage 83.7% (216/258 targets).

| Metric | A | B | C |
|---|---|---|---|
| Outputs (errors) | 108 (0) | 108 (0) | 108 (0) |
| Items per case (mean) | 5.991 | 7.778 | 28.694 |
| Bedside share [default] | 100.0% | 100.0% | 60.1% |
| Bedside share [ecg_bedside] | 100.0% | 100.0% | 64.5% |
| Bedside share [mar_offbedside] | 100.0% | 100.0% | 58.5% |
| Bedside share [excl. unclassified] | 100.0% | 100.0% | 71.6% |
| Unclassified items | 0 | 0 | 496 |
| Target recall must_have | 68.3% | 66.0% | 71.3% |
|   must_have recall [quantified] (n) | 70.1% (234) | 66.7% (234) | 72.6% (234) |
|   must_have recall [not_quantified] (n) | 88.1% (42) | 90.5% (42) | 69.0% (42) |
|   must_have recall [unmapped] (n) | 22.2% (27) | 22.2% (27) | 63.0% (27) |
| Target recall all | 51.6% | 51.4% | 62.3% |
| Evidence fidelity (A/B) | 100.0% | 100.0% | — |
| Unsupported quantitative claim rate | 0.0% | 0.0% | 88.6% |
|   performance numbers only | 0.0% | 0.0% | 91.4% |
|   vs any verified record (lenient) | 0.0% | 0.0% | 3.7% |
| Perturbation responsiveness | 63.9% | 63.0% | 53.2% |
|   pairs explicit / fallback | 36 / 0 | 36 / 0 | 36 / 0 |
| Noise stability (Jaccard mean) | 0.760 | 0.872 | 0.095 |
| Brevity pass rate | 100.0% | 100.0% | 0.0% |
| should_not_recommend case hit rate | 4.6% | 5.6% | 16.7% |
| Ask-first correctness | 98.1% | 98.1% | 94.4% |
