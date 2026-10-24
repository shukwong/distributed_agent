| Target | Control mean | Perturbed mean | Perturbed − control |
|---|---:|---:|---:|
| SYNTH_ALPHA | 10.0 | 14.0 | +4.0 readout units |
| SYNTH_BETA | 10.0 | 10.0 | 0.0 readout units |

- **SYNTH_ALPHA:** control values `[9, 10, 11]`; perturbed values `[13, 14, 15]`, with three constructed samples per group. [SYNTH_ALPHA:F001 → SYNTH_ALPHA:E001]
- **SYNTH_BETA:** both groups contain `[9, 10, 11]`, again with three labeled samples per group. [SYNTH_BETA:F001 → SYNTH_BETA:E001, SYNTH_BETA:E002]
- **Cross-target contrast:** SYNTH_ALPHA’s difference exceeds SYNTH_BETA’s by **4.0 units**: `(+4.0) − (0.0) = +4.0`. [SYNTH_ALPHA:F002 → SYNTH_ALPHA:E001, SYNTH_ALPHA:E002]

These citations are deliberately target-scoped because finding and evidence IDs are local to each report target. Thus `SYNTH_ALPHA:E001` and `SYNTH_BETA:E001` are different records. No external references were linked.

Limits: these are invented scalar observations for a software smoke test. The readout’s meaning and units are unspecified; the labels are not biological genes; samples are not established biological replicates; and there are no cell types, target-engagement measurements, inferential statistics, genuine perturbations, or independent validation. The reports derive from the same synthetic input and are not independent replication. “High” confidence is author-assigned—not a probability—and supports neither statistical significance nor biological, mechanistic, or clinical conclusions.