# exp2812 Aronson Permutation Diagnostic

Scope: dependence-preserving surrogate-price diagnostic for a Python reimplementation of CleanCoreV2A. This is **not MT5 ground truth** because the custom-symbol surrogate route is not viable on this setup; the test uses a compact Python port of CleanCoreV2A.

Correct interpretation: the offline Python implementation materially diverged from MT5, including a sign reversal in the 2026 result. The permutation p-values therefore apply only to the Python surrogate implementation and cannot be used as evidence for or against CleanCoreV2A in MT5. This report is retained as an invalidated diagnostic, not as an evidence claim about the EA.

## Hash Note

- Actual `ea/CleanCoreV2A.mq5` SHA256: `67bdf0f66d04e30992fd34603d0f70af5f42ab7515bdb44a04fe7c0a1f4786cc`
- User-provided short hash `9f177a49` points to CleanCoreV1 in the local docs/artifacts, not the current CleanCoreV2A file. This run therefore uses the actual CleanCoreV2A source used by exp2800/exp2802/exp2804 and flags the mismatch.

## Method

- Feasible path chosen: offline Python reimplementation, not MT5 custom-symbol injection.
- Primary window: train 2024-2025, selected executable exit config (`trail distance=30`, `activation=45`, tilt off).
- Surrogate design: block-permute contiguous M5 OHLC blocks, preserving within-block serial dependence and volatility clustering while breaking the global signal-return arrangement.
- Primary block length: `288` bars; simulations: `200`; seed: `2812`.
- Costs: fixed 0.30 spread and AED conversion calibrated from CleanCoreV2A MT5 deals (~3.675 AED per $1 XAU move at 0.01 lot).

## Primary Result

- Observed offline profit: `1209.38`
- Observed offline R/DD: `129.3039`
- Profit null median / 97.5%: `1334.24` / `1965.68`
- R/DD null median / 97.5%: `197.8765` / `493.5125`
- Empirical p(profit null >= observed): `0.6567`
- Empirical p(R/DD null >= observed): `0.8358`

## Sensitivity

| window | block bars | sims | obs profit | p_profit | obs R/DD | p_R/DD |
|---|---:|---:|---:|---:|---:|---:|
| train_2024_2025/primary | 288 | 200 | 1209.38 | 0.6567 | 129.3039 | 0.8358 |
| train_2024_2025/sensitivity_block_144 | 144 | 20 | 1209.38 | 0.6667 | 129.3039 | 0.9048 |
| train_2024_2025/sensitivity_block_576 | 576 | 20 | 1209.38 | 0.4286 | 129.3039 | 0.5238 |
| heldout_2026_jun21_sensitivity/primary | 288 | 50 | 899.35 | 0.4510 | 141.0570 | 0.4510 |
| heldout_2026_jun21_sensitivity/sensitivity_block_144 | 144 | 20 | 899.35 | 0.4286 | 141.0570 | 0.3810 |
| heldout_2026_jun21_sensitivity/sensitivity_block_576 | 576 | 20 | 899.35 | 0.3333 | 141.0570 | 0.2381 |

## MT5 Fidelity Caveat

The Python port is not close enough to support inference about the MT5 EA. Known gaps: M5-bar intrabar ordering for SL/TP/trail, fixed spread rather than true tick spread, no broker execution microstructure, and a bounded recent-swing cache for speed. The observed divergence is material: train profit is 1209.38 in the Python port versus 413.24 in the MT5 reference cell, and the 2026 sensitivity direction reverses versus the MT5 RT reference (Python positive, MT5 negative).

MT5 reference cells for the selected V2A config:

```json
{
  "heldout_rt_exp2804_core_a": {
    "exists": true,
    "intra_dd_pct": 28.05,
    "max_dd_pct": 27.72,
    "pf": 0.36,
    "profit": -329.36,
    "return_per_dd": -11.741889483065954,
    "trades": 87
  },
  "train_exp2802_selected": {
    "exists": true,
    "intra_dd_pct": 7.76,
    "max_dd_pct": 6.6,
    "pf": 1.69,
    "profit": 413.24,
    "return_per_dd": 53.25257731958763,
    "trades": 364
  }
}
```

Summary JSON: `/Users/juanma/forex-autoresearch/experiments/mt5_native/analysis/smc_exp2812_clean_core_v2a_permutation_summary.json`
