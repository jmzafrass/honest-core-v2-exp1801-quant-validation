# Quantitative Validation Addendum — exp1801 (2026-06-22)
START HERE: 01_docs/honest_core_v2_exp1801_quant_validation_addendum_20260622.md (Phases 0-7, evidence table, final conclusion)
- 01_docs/  : addendum + static parameter audit + 3 phase reports (ablation/PBO/permutation) + data-manifest CSV + trial-lineage CSV
- 02_scripts/ : reproducible analysis scripts (exp2810 ablation, 2811 PBO/CSCV, 2812 permutation)
- 03_data_matrices/ : daily net-PnL series (ablation) + PBO T×N matrices + permutation outputs
- 04_charts/ : PBO logit distribution, permutation null histogram
- 05_raw_json/ : raw test-output summaries

## ⚠️ CORRECTIONS (2026-06-23, post independent audit)
The addendum's original conclusions were OVERSTATED. Verified corrections (see the boxed
"INDEPENDENT AUDIT CORRECTIONS" block at the top of the addendum):
- A4 == A5 (byte-identical) = construction artifact, not independent isolation; A5 ≠ proven CleanCoreV2A.
- "93–96%" = PnL VOLUME, not edge: ~95–96% of TRADES were also removed; residual core has HIGHER per-trade expectancy.
- Toggles disable whole rule families (not only coordinate predicates).
- Permutation (offline Python) materially diverges from MT5 (2026 sign reverses) → p-values do NOT transfer to the MT5 EA.
- Repo = evidence bundle, NOT standalone-reproducible; 2026 = research-contaminated local holdout, not pristine OOS.
Corrected bottom line: the experiment does NOT cleanly isolate the causal contribution of memorized CONSTANTS; it shows exp1801's fitted PnL is heavily dependent on a BUNDLED set of coordinate + auxiliary engines.
