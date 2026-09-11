# Mechanical metrics

Inputs: 108 (36 base, 36 perturbation pairs, 36 noise variants). Store: 153 verified of 153 extracted; not-quantified share 24.2%; library coverage 83.7% (216/258 targets).

| Metric | A | B | C |
|---|---|---|---|
| Outputs (errors) | 108 (0) | 108 (0) | 108 (0) |
| Items per case (mean) | 5.500 | 7.759 | 28.694 |
| Bedside share [default] | 100.0% | 100.0% | 60.1% |
| Bedside share [ecg_bedside] | 100.0% | 100.0% | 64.5% |
| Bedside share [mar_offbedside] | 100.0% | 100.0% | 58.5% |
| Bedside share [excl. unclassified] | 100.0% | 100.0% | 71.6% |
| Unclassified items | 0 | 0 | 496 |
| Target recall must_have | 67.7% | 65.7% | 71.3% |
|   must_have recall [quantified] (n) | 70.9% (234) | 66.7% (234) | 72.6% (234) |
|   must_have recall [not_quantified] (n) | 85.7% (42) | 88.1% (42) | 69.0% (42) |
|   must_have recall [unmapped] (n) | 11.1% (27) | 22.2% (27) | 63.0% (27) |
| Target recall all | 50.9% | 51.2% | 62.3% |
| Evidence fidelity (A/B) | 100.0% | 100.0% | — |
| Unsupported quantitative claim rate | 0.0% | 0.0% | 88.6% |
|   performance numbers only | 0.0% | 0.0% | 91.4% |
|   vs any verified record (lenient) | 0.0% | 0.0% | 3.7% |
| Perturbation responsiveness | 57.9% | 63.4% | 53.2% |
|   pairs explicit / fallback | 36 / 0 | 36 / 0 | 36 / 0 |
| Noise stability (Jaccard mean) | 0.722 | 0.834 | 0.095 |
| Brevity pass rate | 100.0% | 100.0% | 0.0% |
| should_not_recommend case hit rate | 0.0% | 2.8% | 13.0% |
| Ask-first correctness | 96.3% | 97.2% | 94.4% |
