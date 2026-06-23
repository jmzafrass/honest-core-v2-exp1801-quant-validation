# Quantitative Validation Addendum — exp1801 Evidence Bundle

Start here:

- `01_docs/honest_core_v2_exp1801_quant_validation_addendum_20260622.md`

This repository is an evidence bundle. Its scripts require files, helper modules, EAs, MT5 reports,
generated summaries, and market data from the parent project.

Contents:

- `01_docs/`: corrected addendum, static parameter audit, phase reports, data-manifest CSV, and trial-lineage CSV.
- `02_scripts/`: analysis scripts for exp2810 ablation, exp2811 LOCAL PBO/CSCV, and exp2812 permutation diagnostic.
- `03_data_matrices/`: daily net-PnL series, PBO matrices, and permutation output rows.
- `04_charts/`: PBO logit distribution and permutation null histogram.
- `05_raw_json/`: raw test-output summary JSONs with corrected narrative fields where needed.

Corrected interpretation:

- A4 and A5 are the same bundled intervention by construction; they do not independently isolate a structural core.
- The bundled guard intervention removed approximately 93-96% of fitted absolute PnL while also removing approximately 95-96% of trade activity.
- This establishes fitted-PnL dependence on bundled coordinate-linked and auxiliary production engines, not the causal share of predictive edge attributable to memorized constants.
- The local PBO result is inconclusive and cannot deflate the full research process.
- The permutation p-values apply only to the offline Python surrogate implementation and cannot be used as evidence for or against CleanCoreV2A in MT5.
