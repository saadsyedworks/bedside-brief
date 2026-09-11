# Mechanical metrics

Inputs: 9 (3 base, 3 perturbation pairs, 3 noise variants). Store: 4 verified of 153 extracted; not-quantified share 25.0%; library coverage 19.0% (4/21 targets).

| Metric | A | B | C |
|---|---|---|---|
| Outputs (errors) | 9 (0) | 9 (0) | 9 (0) |
| Items per case (mean) | 2.333 | 2.333 | 8.000 |
| Bedside share [default] | 100.0% | 100.0% | 62.5% |
| Bedside share [ecg_bedside] | 100.0% | 100.0% | 75.0% |
| Bedside share [mar_offbedside] | 100.0% | 100.0% | 62.5% |
| Unclassified items | 0 | 0 | 0 |
| Target recall must_have | 18.5% | 18.5% | 55.6% |
|   must_have recall [quantified] (n) | 66.7% (3) | 66.7% (3) | 100.0% (3) |
|   must_have recall [not_quantified] (n) | 100.0% (3) | 100.0% (3) | 100.0% (3) |
|   must_have recall [unmapped] (n) | 0.0% (21) | 0.0% (21) | 42.9% (21) |
| Target recall all | 20.6% | 20.6% | 42.9% |
| Evidence fidelity (A/B) | 100.0% | 100.0% | — |
| Unsupported quantitative claim rate | 0.0% | 0.0% | 71.4% |
|   performance numbers only | 0.0% | 0.0% | 66.7% |
|   vs any verified record (lenient) | 0.0% | 0.0% | 42.9% |
| Perturbation responsiveness | 33.3% | 33.3% | 50.0% |
|   pairs explicit / fallback | 3 / 0 | 3 / 0 | 3 / 0 |
| Noise stability (Jaccard mean) | 1.000 | 1.000 | 1.000 |
| Brevity pass rate | 100.0% | 100.0% | 100.0% |
| should_not_recommend case hit rate | 0.0% | 0.0% | 100.0% |
| Ask-first correctness | 100.0% | 100.0% | 100.0% |
