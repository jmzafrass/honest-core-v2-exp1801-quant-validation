# Quantitative Validation Addendum — exp1801

**Date:** 2026-06-22  
**Companion to:** `honest_core_v2_exp1801_parameter_audit_20260622.md`  
**Status:** COMPLETE. Phase 2 controlled ablation, Phase 3 LOCAL PBO/CSCV, and Phase 5
permutation diagnostic were run and audited. Full White/Hansen and true walk-forward analysis are
not testable from the saved research record. No EA is promoted by this addendum.

---

## Corrected Scope

The addendum answers what the saved evidence can support:

- Whether exp1801 fitted PnL depends on coarse production rule families.
- Whether the small CleanCoreV2A config grids show a local PBO signal.
- Whether an offline surrogate-price diagnostic is usable evidence about CleanCoreV2A.
- Which tests are not testable from the saved record.

It does **not** establish the causal share of predictive edge attributable to memorized constants.
The controlled switches disable whole behavior families, not constants alone.

---

## Phase 1 — Data Availability Gate

CSV artifacts:

- `docs/honest_core_v2_quant_validation_data_manifest_20260622.csv`
- `docs/honest_core_v2_quant_validation_trial_lineage_20260622.csv`

Gate results:

| Phase | Test | Gate verdict |
|---|---|---|
| 2 | Controlled block ablation | Runnable; requires switch-gated copy and daily PnL series |
| 3 | Bailey PBO / CSCV | Runnable only as a **LOCAL** diagnostic on the 18-20 CleanCoreV2A config grids |
| 4 | White Reality Check / Hansen SPA | **Not testable** for the full historical universe; missing aligned per-alternative return series and file-drawer-complete alternatives |
| 5 | Aronson permutation | Runnable only as an offline diagnostic; MT5 custom-symbol surrogate path was not viable |
| 6 | Pardo walk-forward | **Not testable** as true WFA; the saved monthly tests are retrospective validation with already-fit parameters |

This repository is an evidence bundle. Its scripts require files, helper modules, EAs, MT5 reports,
and market data from the parent project. Missing external dependencies include the MT5 installation
and tester reports, parent-project backtest helpers, source EAs, tick/OHLC market data, generated
MT5 summaries, and parent `experiments/mt5_native` artifacts.

---

## Phase 2 — exp2810 Controlled Block Ablation

Report: `docs/honest_core_v2_exp2810_exp1801_ablation_phase2_20260622.md`  
Summary JSON: `experiments/mt5_native/analysis/smc_exp2810_exp1801_ablation_phase2_summary.json`

### Toggle Semantics

The toggles are coarse. They disable complete rule families, including coordinate, structural,
sizing, re-entry, add-on, reversal, split, and support-reclaim behavior. Some direct hour checks
were not removed. This is not a constants-only ablation.

A4 and A5 are the same bundled intervention by construction and produce byte-identical daily
series. They do not independently isolate a structural core, and A5 is not proven equivalent to
CleanCoreV2A.

### Required Attribution Metrics

| Window | A0 profit | A0 trades | A0 expectancy/trade | A0 PF | A4/A5 profit | A4/A5 trades | A4/A5 expectancy/trade | A4/A5 PF | PnL removed | Trades removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| long_2017_2026_model1 | 117,958.38 | 7,457 | 15.82 | 5.87 | 8,706.45 | 352 | 24.73 | 4.98 | 109,251.93 (92.62%) | 7,105 (95.28%) |
| rt_2026_jun21_model4 | 46,751.96 | 1,921 | 24.34 | 8.92 | 1,716.58 | 68 | 25.24 | 9.33 | 45,035.38 (96.33%) | 1,853 (96.46%) |

Correct interpretation: the bundled guard intervention removed approximately 93-96% of fitted
absolute PnL while also removing approximately 95-96% of trade activity. This establishes dependence
of fitted PnL volume on the bundled coordinate and auxiliary engines, not the causal share of
predictive edge attributable to memorized constants.

Paired daily block bootstrap CIs show that the A0-vs-A4/A5 fitted PnL difference is large and
positive in the tested fitted-backtest windows. They do not convert the bundled intervention into a
constants-only causal attribution.

---

## Phase 3 — exp2811 LOCAL PBO / CSCV

Report: `docs/honest_core_v2_exp2811_local_pbo_cscv_20260622.md`  
Summary JSON: `experiments/mt5_native/analysis/smc_exp2811_local_pbo_cscv_summary.json`

This is local to the CleanCoreV2A Phase-2 config grids. It does not deflate the full research
process.

### PBO Sensitivity

| Grid | N | T | S=6 PBO | S=8 PBO (declared primary) | S=10 PBO | Primary reading |
|---|---:|---:|---:|---:|---:|---|
| exp2800 | 20 | 731 | 0.000 | 0.014 | 0.004 | Low local PBO on a Model-1 grid that includes the known sub-spread trail artifact |
| exp2802 | 18 | 731 | 0.000 | 0.271 | 0.254 | S-sensitive local result; inconclusive |

The local PBO result is sensitive to S, mixes sequential selection stages, contains duplicate
configurations, and covers only 18 configurations in exp2802. It is inconclusive and cannot deflate
the full research process.

The three duplicate exp2802 configurations are:

- `trail_d030_a045`
- `target_rr_150_at_selected_exit`
- `target_rr_250_at_selected_exit`

These three configurations produce identical aggregate metrics in the saved grid.

---

## Phase 5 — exp2812 Aronson Permutation Diagnostic

Report: `docs/honest_core_v2_exp2812_clean_core_v2a_permutation_20260622.md`  
Summary JSON: `experiments/mt5_native/analysis/smc_exp2812_clean_core_v2a_permutation_summary.json`

The offline Python implementation materially diverged from MT5, including a sign reversal in the
2026 result. The permutation p-values therefore apply only to the Python surrogate implementation
and cannot be used as evidence for or against CleanCoreV2A in MT5.

The permutation test remains documented as an invalidated diagnostic. It does not support Claim #9
or the final conclusion.

| Window | Observed Python profit | Observed Python R/DD | p(profit) | p(R/DD) | Correct status |
|---|---:|---:|---:|---:|---|
| train_2024_2025 | 1,209.38 | 129.30 | 0.657 | 0.836 | Python-surrogate diagnostic only |
| heldout_2026_jun21_sensitivity | 899.35 | 141.06 | 0.451 | 0.451 | Python-surrogate diagnostic only |

MT5 reference cells in the same report show the divergence: train selected config profit 413.24 and
heldout RT profit -329.36. The p-values above do not transfer to the MT5 EA.

---

## Phase 7 — Evidence Table

| # | Claim | Evidence | Correct status |
|---|---|---|---|
| 1 | Hour pins have stable value | A1 removal changes fitted-backtest behavior materially; some direct hour checks remain outside toggles | Fitted-backtest dependence shown; stable value not established |
| 2 | Price pins have stable value | A2 removal reduces fitted PnL and trade activity | Fitted-backtest dependence shown; stable value not established |
| 3 | Slot families have stable value | A3 removal reduces fitted PnL and trade activity | Fitted-backtest dependence shown; stable value not established |
| 4 | Coordinate/auxiliary layer explains most edge | A4/A5 bundled intervention removes 92.62% long fitted PnL and 96.33% RT fitted PnL while removing 95.28% and 96.46% of trades | Bundled fitted-PnL dependence supported; causal edge attribution not established |
| 5 | Structural core is isolated | A4 and A5 are byte-identical and remove complete behavior families | Not isolated by A4/A5 |
| 6 | Configuration-selection overfit is proven | Local PBO is S-sensitive, small-N, duplicate-containing, and limited to two local grids | Inconclusive from local PBO |
| 7 | A surviving rule is superior after multiple-testing correction | Full per-alternative universe is missing | White/Hansen not testable |
| 8 | Fresh-start monthly tests are walk-forward | Parameters were already selected using visible periods | Retrospective validation, not walk-forward |
| 9 | CleanCore has predictive superiority | MT5 post-selection local holdout is adverse for CleanCoreV2A; Python permutation is invalid for MT5 | Not established; permutation invalid for MT5; post-selection MT5 holdout adverse |

---

## Final Conclusion

Exp1801's fitted absolute PnL is heavily dependent on a bundled collection of coordinate-linked and
auxiliary production engines. The current ablation does not cleanly isolate the causal contribution
of memorized constants, because the toggles remove whole behavior families and A4 and A5 are the
same intervention by construction. The local PBO analysis is inconclusive, the full White/Hansen
universe and true walk-forward analysis are not testable from the saved research record, and the
Python permutation results do not transfer to the MT5 EA. CleanCoreV2A's MT5 PF of approximately
0.35 in a research-contaminated post-selection local holdout is adverse evidence for that specific
implementation, but not definitive proof about the broader market thesis.

---

## Deliverable 8 — Charts

- PBO logit distribution (exp2811, S=10, both local grids):
  `experiments/mt5_native/analysis/exp281x_charts/exp2811_pbo_logit_distribution_s10.png`
- Permutation null histogram (exp2812 train 2024-25, 200-surrogate null; profit + R/DD):
  `experiments/mt5_native/analysis/exp281x_charts/exp2812_permutation_train_null_profit_rdd.png`
- Stitched-OOS equity chart: **N/A** — true WFA / stitched OOS is not testable from the saved
  process, so no chart was fabricated.

## Deliverable 9 — Reproduction Commands

- Phase 2 / exp2810 ablation: `python3 scripts/smc_exp2810_exp1801_ablation_phase2.py`
- Phase 3 / exp2811 LOCAL PBO-CSCV: `python3 scripts/smc_exp2811_local_pbo_cscv.py`
- Phase 5 / exp2812 Aronson permutation diagnostic:
  `python3 scripts/smc_exp2812_clean_core_v2a_permutation.py --n-sims=200`
