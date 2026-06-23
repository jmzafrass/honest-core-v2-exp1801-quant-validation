# exp2811 Local PBO/CSCV

Scope: **LOCAL** PBO/CSCV on the two CleanCoreV2A Phase-2 selection grids only. This is not a full-pipeline PBO and must not be read as a complete research-program deflator.

Observation unit: daily closed-deal net PnL from the MT5 HTML deal ledger. No-trade days are zero-filled and all configs share the same calendar-day index. Because CleanCoreV2A does not emit the standard SMC equity CSV, the CSCV selection statistic uses closed-balance daily PnL and closed-balance DD, not tick-level intra-trade equity DD.

Interpretation: the local PBO result is sensitive to S, mixes sequential selection stages, contains duplicate configurations, and covers only 18-20 configurations. It is inconclusive and cannot deflate the full research process.

## exp2800

- N configs: `20`
- T daily observations: `731`
- Primary S: `8`. S=8 gives quarter-sized blocks (~91 days) and 70 train/test combinations; S=6 and S=10 are reported as sensitivity for small-N stability.
- Daily matrix: `experiments/mt5_native/analysis/exp2811_pbo_cscv/exp2800_daily_matrix.csv`
- Primary PBO: `0.014`
- Primary P(OOS loss): `0.014`

### CSCV Sensitivity

| S | blocks | combos | PBO | P(OOS loss) | median logit | mean IS-OOS R/DD degradation |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 121-122 | 20 | 0.000 | 0.050 | 2.996 | 2.311 |
| 8 | 91-92 | 70 | 0.014 | 0.014 | 2.996 | 9.553 |
| 10 | 73-74 | 252 | 0.004 | 0.008 | 2.996 | 0.428 |

### Config Metrics

| config | family/stage | profit | PF | trades | maxDD% | intraDD% | R/DD | daily check |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | baseline | 306.80 | 1.24 | 364 | 13.61 | 14.94 | 20.5355 | 314.11 |
| `target_rr_150` | target_rr | 304.38 | 1.23 | 364 | 13.66 | 14.99 | 20.3055 | 311.69 |
| `target_rr_250` | target_rr | 307.65 | 1.24 | 364 | 13.61 | 14.94 | 20.5924 | 314.96 |
| `sl_buffer_atr_010` | sl_buffer_atr | 322.58 | 1.25 | 364 | 13.34 | 14.67 | 21.9891 | 324.41 |
| `sl_buffer_atr_020` | sl_buffer_atr | 307.66 | 1.24 | 366 | 14.03 | 15.36 | 20.0299 | 314.97 |
| `displ_body_atr_035` | displacement_body_atr | 290.08 | 1.22 | 365 | 14.44 | 15.05 | 19.2744 | 297.39 |
| `displ_body_atr_060` | displacement_body_atr | 124.93 | 1.09 | 365 | 15.16 | 16.45 | 7.5945 | 132.24 |
| `fvg_min_atr_004` | fvg_min_atr | 329.13 | 1.25 | 369 | 13.61 | 14.94 | 22.0301 | 336.44 |
| `fvg_min_atr_008` | fvg_min_atr | 215.49 | 1.16 | 359 | 13.61 | 14.94 | 14.4237 | 222.80 |
| `trail_d003_a045` | trail | 584.87 | 1.98 | 364 | 4.37 | 4.81 | 121.5946 | 584.87 |
| `trail_d003_a150` | trail | 354.94 | 1.20 | 361 | 11.87 | 12.65 | 28.0585 | 362.25 |
| `trail_d020_a045` | trail | 446.33 | 1.74 | 364 | 6.13 | 7.22 | 61.8186 | 448.16 |
| `trail_d020_a090` | trail | 196.58 | 1.15 | 364 | 14.53 | 15.90 | 12.3635 | 203.89 |
| `trail_d020_a150` | trail | 246.80 | 1.14 | 361 | 13.31 | 14.12 | 17.4788 | 254.11 |
| `trail_d060_a045` | trail | 301.22 | 1.49 | 364 | 7.51 | 8.93 | 33.7312 | 303.05 |
| `trail_d060_a090` | trail | 71.95 | 1.06 | 364 | 15.76 | 17.23 | 4.1759 | 79.26 |
| `trail_d060_a150` | trail | 134.92 | 1.08 | 361 | 15.87 | 16.70 | 8.0790 | 142.23 |
| `trail_d120_a045` | trail | 177.48 | 1.22 | 364 | 5.70 | 6.71 | 26.4501 | 179.31 |
| `trail_d120_a090` | trail | -103.69 | 0.92 | 364 | 16.74 | 17.69 | -5.8615 | -96.38 |
| `trail_d120_a150` | trail | 18.78 | 1.01 | 361 | 17.95 | 18.81 | 0.9984 | 26.09 |

## exp2802

- N configs: `18`
- T daily observations: `731`
- Primary S: `8`. S=8 gives quarter-sized blocks (~91 days) and 70 train/test combinations; S=6 and S=10 are reported as sensitivity for small-N stability.
- Daily matrix: `experiments/mt5_native/analysis/exp2811_pbo_cscv/exp2802_daily_matrix.csv`
- Primary PBO: `0.271`
- Primary P(OOS loss): `0.200`

### CSCV Sensitivity

| S | blocks | combos | PBO | P(OOS loss) | median logit | mean IS-OOS R/DD degradation |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 121-122 | 20 | 0.000 | 0.000 | 0.656 | 4.888 |
| 8 | 91-92 | 70 | 0.271 | 0.200 | 0.318 | 26.666 |
| 10 | 73-74 | 252 | 0.254 | 0.071 | 0.318 | 10.440 |

### Config Metrics

| config | family/stage | profit | PF | trades | maxDD% | intraDD% | R/DD | daily check |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `trail_off` | exit | -391.88 | 0.91 | 339 | 38.21 | 39.80 | -9.8462 | -375.42 |
| `trail_d030_a045` | exit | 413.24 | 1.69 | 364 | 6.60 | 7.76 | 53.2526 | 415.07 |
| `trail_d030_a090` | exit | 173.43 | 1.13 | 364 | 15.07 | 16.45 | 10.5429 | 180.74 |
| `trail_d030_a150` | exit | 237.72 | 1.14 | 361 | 13.99 | 14.92 | 15.9330 | 245.03 |
| `trail_d050_a045` | exit | 357.53 | 1.59 | 364 | 7.19 | 8.53 | 41.9144 | 359.36 |
| `trail_d050_a090` | exit | 85.52 | 1.07 | 364 | 15.67 | 17.10 | 5.0012 | 92.83 |
| `trail_d050_a150` | exit | 143.06 | 1.08 | 361 | 16.17 | 16.85 | 8.4902 | 150.37 |
| `trail_d080_a045` | exit | 256.87 | 1.38 | 364 | 5.78 | 6.76 | 37.9985 | 258.70 |
| `trail_d080_a090` | exit | 53.11 | 1.04 | 364 | 12.95 | 14.00 | 3.7936 | 60.42 |
| `trail_d080_a150` | exit | 136.65 | 1.08 | 361 | 15.19 | 16.03 | 8.5246 | 143.96 |
| `target_rr_150_at_selected_exit` | structural | 413.24 | 1.69 | 364 | 6.60 | 7.76 | 53.2526 | 415.07 |
| `target_rr_250_at_selected_exit` | structural | 413.24 | 1.69 | 364 | 6.60 | 7.76 | 53.2526 | 415.07 |
| `sl_buffer_atr_010_at_selected_exit` | structural | 420.97 | 1.71 | 364 | 6.43 | 7.59 | 55.4638 | 422.80 |
| `sl_buffer_atr_020_at_selected_exit` | structural | 424.11 | 1.72 | 366 | 6.85 | 8.00 | 53.0138 | 425.94 |
| `displ_body_atr_035_at_selected_exit` | structural | 419.78 | 1.70 | 365 | 6.60 | 7.76 | 54.0954 | 421.61 |
| `displ_body_atr_060_at_selected_exit` | structural | 327.94 | 1.48 | 365 | 7.07 | 8.23 | 39.8469 | 329.77 |
| `fvg_min_atr_004_at_selected_exit` | structural | 424.40 | 1.71 | 369 | 6.60 | 7.76 | 54.6907 | 426.23 |
| `fvg_min_atr_008_at_selected_exit` | structural | 401.86 | 1.67 | 359 | 6.60 | 7.76 | 51.7861 | 403.69 |

## Limitations

- This is local to 18-20 configs and does not deflate the thousands of broader historical experiments.
- S=8 is the declared primary result; S=6 and S=10 are sensitivity checks.
- exp2802 contains three duplicate configurations with identical aggregate metrics: `trail_d030_a045`, `target_rr_150_at_selected_exit`, and `target_rr_250_at_selected_exit`.
- exp2802 also mixes exit-stage and structural-stage selections, so it is not a single clean simultaneous model-selection family.
- The observation count is daily, but trades are sparse; many days are zero across all configs.
- HTML deal-ledger daily PnL is enough for CSCV rank testing, but it is not an intra-trade drawdown oracle.
- PBO is diagnostic only; it is not used here to pick or re-pick any CleanCore config.

Summary JSON: `/Users/juanma/forex-autoresearch/experiments/mt5_native/analysis/smc_exp2811_local_pbo_cscv_summary.json`
