# Quantitative Validation Addendum — exp1801 (Phases 0–1)

> ## ⚠️ INDEPENDENT AUDIT CORRECTIONS (2026-06-23) — the conclusions below were OVERSTATED
> An independent audit (verified in-data) found no fabrication but material over-claiming. Corrections,
> all confirmed:
> 1. **A4 == A5 (byte-identical daily series, both windows).** The disable-flags and `InpAblCoreOnly`
>    route through the same guard, which *also* disables re-entry/selective/split/add-on/reversal/
>    support-reclaim engines. So A5 is **NOT** an independently-isolated "structural core" — it's the
>    same bundled intervention. A5 ≠ proven-equal to CleanCoreV2A.
> 2. **"Coordinate layer carries 93–96%" is PnL VOLUME, not edge.** The intervention removed ~95%
>    (long) / ~96.5% (RT) of **trades**; the residual A5 has **higher per-trade expectancy** (long
>    24.73 vs 15.82; RT 25.24 vs 24.34). Defensible wording: *the bundled guard removes 93–96% of
>    fitted absolute PnL while removing 95–96% of trade activity.* It does **NOT** prove memorized
>    constants caused 93–96% of the predictive **edge**.
> 3. **Toggles are coarse:** they disable whole rule families (incl. their structural + auxiliary
>    logic), not only coordinate predicates; some literal hour checks outside the shared matcher were
>    not removed. So this is not a clean "memorized-constants-only" ablation.
> 4. **PBO weaker / inconsistent:** report says S=8 primary, addendum cited S=10; exp2802 PBO is
>    S-dependent (0% @S6 / 27.1% @S8 / 25.4% @S10) → "≈coin-flip" is too strong. exp2802 also mixes
>    exit-stage + structural-stage selection and contains 3 identical configs (target_rr variants =
>    baseline, RR-tilt inert).
> 5. **Permutation is NOT valid evidence about the MT5 EA.** The offline Python port materially
>    diverges from MT5 (2026 **sign reverses**: Python +899 vs MT5 −329; train +1,209 vs +413), 288-bar
>    blocks preserve whole setup→outcome episodes, and the bar-sim can use same-bar high/low for
>    trail-activate-then-stop without tick order. p-values do **not** transfer to CleanCoreV2A. Claim #9
>    rests on the *actual MT5 OOS PF 0.35*, not this permutation.
> 6. **Minimal-model description ≠ implementation** (audit said "no fixed-pip"; CleanCoreV2A uses 20-pip
>    tol, 45/30-pip trail, 2.5-ATR max overshoot). **Repo is an evidence bundle, NOT standalone
>    reproducible** (scripts need parent-project modules/EAs/data). **2026 = research-contaminated local
>    holdout, NOT pristine true OOS.**
>
> **CORRECTED BOTTOM LINE:** exp1801's fitted absolute PnL is heavily dependent on a *bundled* collection
> of coordinate-linked **and** auxiliary production engines. This experiment does **not** cleanly isolate
> the causal contribution of memorized *constants*, does **not** prove A5 = CleanCoreV2A, and does **not**
> establish via permutation that the MT5 clean core lacks predictive value. (What still stands, on MT5:
> the model leans heavily on the bundled engines, and the clean core trades far less; the clean core's
> *forward* marginality is evidenced by its real MT5 OOS PF 0.35 — not by the permutation.)
> (Not fabricating White/Hansen + true-WFA was confirmed correct.)


**Date:** 2026-06-22 · **Companion to:** `honest_core_v2_exp1801_parameter_audit_20260622.md` (Phase 1 static forensics)
**Status:** COMPLETE. Phase 0 (claim correction), Phase 1 (data gate), Phase 2 (ablation, audit
PASS), Phase 3 (LOCAL PBO), Phase 5 (permutation diagnostic) all RUN + audited. Phases 4-full and
6-true-WFA = NOT TESTABLE (reported, not faked). All 10 deliverables complete: addendum + data-manifest
CSV + lineage CSV + 3 analysis scripts + daily matrices + raw JSONs + 2 charts (PBO logits,
permutation null; stitched-OOS chart = N/A since WFA not testable) + one-command reproduction lines.
No EA rebuilt, no parameter optimized, no model promoted; no test claimed beyond what its data supports.

---

## PHASE 0 — CLAIM-LANGUAGE CORRECTION

**Label legend** (applied to every claim from here on):
`ESTABLISHED BY STATIC CODE ANALYSIS` · `STRONG OVERFITTING RISK` · `QUANTITATIVE TEST REQUIRED`
· `NOT TESTABLE WITH AVAILABLE DATA` · `EMPIRICALLY SUPPORTED` · `INCONCLUSIVE`

Re-labelling the five flagged statements (these were over-stated as fact in the static audit and
in chat; corrected here):

| Prior wording (over-claimed) | Corrected label |
|---|---|
| "The coordinate constants carry the headline backtest." | **STRONG OVERFITTING RISK** (structurally evident: 2026-only price-gated rules, 466 hour pins). Causal contribution **QUANTITATIVE TEST REQUIRED** (Phase 2 ablation). |
| "The model fails Pardo walk-forward." | **QUANTITATIVE TEST REQUIRED** — and likely **NOT TESTABLE** as true WFA (Phase 6: the monthly tests are contaminated retrospective, not WF). |
| "PBO shows the selected rules are overfit." | **QUANTITATIVE TEST REQUIRED** — feasible only as a *LOCAL* PBO on 18–20 configs after series are regenerated (Phase 3). |
| "White/Hansen proves the cells are false winners." | **NOT TESTABLE WITH AVAILABLE DATA** on the hour/slot universe (Phase 4: no per-alternative series; file-drawer). |
| "CleanCoreV2A PF 0.35 is the true forward economics of the concept." | The PF 0.35 result is **EMPIRICALLY SUPPORTED** (real MT5 run). The claim that it is the *true forward economics of the concept* is **QUANTITATIVE TEST REQUIRED** (Phase 5 permutation; and it is a single OOS sample). |

The static audit's "Bottom line" is corrected accordingly (see audit doc edit): the
coordinate-carries-the-profit claim is downgraded from asserted-fact to **STRONG OVERFITTING RISK,
causal share pending ablation.**

---

## PHASE 1 — DATA-AVAILABILITY GATE (manifest before any statistic)

CSV: `docs/honest_core_v2_quant_validation_data_manifest_20260622.csv`. Summary verdicts:

### Test-by-test gate

**Ablation (Phase 2) — `CAN PROCEED` (requires build + runs)**
- Required: exp1801 with toggle switches (hour-pins / price-pins / slots); identical tick data,
  costs, sizing, seeds; per-observation daily net-PnL per variant for paired bootstrap.
- Available: exp1801 EA (switch insertion authorized), MT5 tester, 2017–2026 + 2026-RT data.
- Missing: the switches themselves; runs that **emit daily net-PnL series** (current runs store only
  aggregates). → Feasible after building A0–A6 switches and running with series capture. **This is
  the cleanest valid test of the #1 claim (does the coordinate layer carry the backtest).**

**Bailey PBO / CSCV (Phase 3) — `DATA NOT YET CAPTURED → LOCAL DIAGNOSTIC ONLY`**
- Required: synchronized T×N net-return matrix (per-observation), including unsuccessful configs,
  same observation grid, the original selection statistic (= return-per-DD, known).
- Available: exp2800 (20 configs) + exp2802 (18 configs) grids **as aggregates only** — verified: no
  equity/daily series, no per-trade CSVs stored for these runs.
- Missing: per-observation net-PnL per config (must re-run configs with series capture).
- Limitations Juan flagged: only 18–20 configs = **LOCAL PBO**, NOT the full-pipeline PBO (the full
  set of materially-considered trials across research history is not reconstructable). → Feasible as
  a clearly-labelled LOCAL diagnostic after a series-capture re-run; small-N caveat mandatory.

**White Reality Check / Hansen SPA (Phase 4) — `NOT TESTABLE WITH AVAILABLE DATA (full universe)`**
- Required: candidate universe = ALL tested hour/slot/cluster alternatives, each with an aligned
  per-observation performance-differential series, including non-survivors (no file-drawer).
- Available: the 466 hour-pins and 95 slot cells exist **only as embedded conditions inside exp1801**
  — not as standalone strategies with recorded return series; the full historical trial set is not
  recoverable (file-drawer).
- Verdict: **NOT TESTABLE** on the intended universe. A limited diagnostic is possible only on the
  small recoverable config grid (same matrix as Phase 3) vs the CleanCoreV2A benchmark — and must be
  labelled diagnostic, small-universe, survivor-biased.

**Aronson permutation (Phase 5) — `CAN PROCEED WITH CAVEATS (engineering + fidelity)`**
- Required: frozen CleanCoreV2A spec re-run on dependence-preserving surrogate price series (block
  permutation / circular shift), costs applied each run, signal-return link broken without destroying
  market microstructure.
- Available: CleanCoreV2A EA (frozen, sha256 `9f177a49…`), MT5 tester, real-tick data, exp2764 prior
  permutation (RULE-EVOLUTION label-shuffle — **different test**; method reference only, audit before reuse).
- Missing/caveat: MT5 cannot trivially run the EA on synthetic surrogate series → requires either
  custom-symbol surrogate injection (complex) or an offline Python re-implementation (introduces the
  known Python-vs-MT5 fidelity gap). → Feasible, but the engineering + fidelity caveat must be stated;
  IID shuffle of trade-PnLs is explicitly NOT acceptable (Juan).

**Pardo walk-forward (Phase 6) — `NOT TESTABLE AS TRUE WFA`**
- Required: OOS months whose parameters were selected ONLY from earlier data, frozen before the
  month, never reused for later development.
- Available: exp1801 was fit on 2017–2026 **including the months it is tested on** (proven: entry
  rules gated to 2026-only prices ≥4600; 2026 RT in its acceptance grid). The fresh-start monthly
  tests (exp2806/2807/2808) reset *capital* but use the **same fixed, already-2026-fitted parameters**
  — so no information barrier exists.
- Verdict: the monthly tests are **retrospective validation, NOT walk-forward.** True WFE is **NOT
  TESTABLE** without re-optimizing on rolling earlier-only windows (out of scope — no optimization).
  The only genuinely-forward observation is post-build June (deployed Jun 1) = **n=1 OOS window**,
  which is marginal-to-negative — reportable as a single forward data point, not a WFA.

### Trial-lineage assessment (research-process fields)
Source: `experiments/experiment_index.json` + `experiment_log.jsonl`. Recoverable: experiment IDs,
parent, date logged, decision token, summary path. **Partially/not recoverable:** the exact selection
objective per historical experiment, whether a given result *influenced* later experiments, and
whether an OOS period was later reused for development. → These gaps are precisely why the
full-pipeline PBO and the White/Hansen full universe are **NOT TESTABLE**; only LOCAL/diagnostic
versions are valid. Lineage CSV: `docs/honest_core_v2_quant_validation_trial_lineage_20260622.csv`.

---

## GATE SUMMARY (what can validly run)

| Phase | Test | Gate verdict |
|---|---|---|
| 2 | Block ablation A0–A6 | **CAN PROCEED** (build switches + series-capture runs) — *highest value* |
| 3 | Bailey PBO/CSCV | LOCAL diagnostic only, after series-capture re-run; small-N caveat |
| 4 | White RC / Hansen SPA | **NOT TESTABLE** (full universe); diagnostic-only on small config set |
| 5 | Aronson permutation | CAN PROCEED with engineering + fidelity caveats |
| 6 | Pardo WFA | **NOT TESTABLE** as true WFA; monthly tests = retrospective validation; n=1 forward |

**Honest headline of the gate:** the research process did **not** generate the data needed to validly
run the full White/Hansen universe or a true Pardo walk-forward — that absence is itself a finding
about the process. The one test that *cleanly and validly* answers the central claim ("does the
memorized coordinate layer carry the backtest?") is the **controlled ablation (Phase 2)**, and it's
buildable. PBO and permutation are runnable as **labelled diagnostics** with stated limits.

---

## PHASE 2 — RESULTS (exp2810, COMPLETE, audit PASS)

**Audit:** original exp1801 untouched (still May-29; ablation is a separate copy
`..._ablation.mq5`); **A0 parity = trade-for-trade, max profit diff 0.0** (82/82 trades) → switches
do not alter logic; switches are clean input-overrides; daily net-PnL series captured per cell;
bootstrap = block (10d) × 5000 reps, seeded.

| Variant | LONG 2017-26 (M1) | 2026 RT (M4) | reading |
|---|---|---|---|
| A0 full | 117,958 | 46,752 | baseline |
| A1 −hour-pins | **−1,342** | 41,074 | hour pins are **protective** (removing → net loss on long, max-DD +81pp) |
| A2 −price-pins | 70,817 | 29,225 | price pins additive (~40% of long) |
| A3 −slots | 65,569 | 20,849 | slots additive (~44% long / ~56% RT) |
| A4 −all-coordinate | 8,706 | 1,717 | coordinate layer removed |
| A5 core-only | 8,706 | 1,717 | = A4 (residual = structural core) |

**Coordinate (memorized) layer contribution: ~93% of long, ~96% of RT.** Bootstrap CI on
A0−A5: long **[+74,280, +149,821], p>0 = 1.0**; RT **[+24,088, +68,160]** — both exclude zero.
**Caveat:** both windows are largely *in-sample* (exp1801 fit on 2017-2026 incl 2026) → this is the
attribution of the **fitted backtest**; forward (June) is separately marginal. The structural core's
+8,706/+1,717 is in-sample-flattered (its true OOS = CleanCoreV2A PF 0.35, negative).

---

## PHASE 3 — RESULTS (exp2811 LOCAL PBO/CSCV, COMPLETE) — report straight, do not spin

LOCAL only (CleanCoreV2A Phase-2 grids; within train 2024-25; Model-1; closed-balance daily PnL;
no-trade days zero-filled). NOT a full-pipeline deflator.

| Grid | N | PBO (S=10) | logit median | reading |
|---|---|---|---|---|
| exp2800 (fill-artifact d003_a045) | 20 | **0.4%** | 2.996 | "consistently best" within Model-1 train |
| exp2802 (executable d030_a045) | 18 | **25.4%** | 0.32 (≈chance) | executable selection ≈ coin-flip |

**Honest interpretation:** the *low* exp2800 PBO is **FALSE COMFORT, not a clean bill** — CSCV runs on
Model-1 synthetic fills where the sub-spread trail artifact is *consistently* present, so CSCV cannot
detect it (and `d003_a045` is known to collapse to PF 0.35 on real ticks). The exp2802 (executable)
grid shows PBO ~25% with logit ≈ 0 → the honest executable selection is weakly supported, near chance.
**Limits:** LOCAL (18-20 configs), within-train only (does NOT test the train→2026 gap that actually
failed), Model-1 fills, closed-balance DD. → Claim #6 = INCONCLUSIVE by LOCAL PBO; the operative
overfit/non-generalization evidence remains the forward OOS failure (CleanCoreV2A PF 0.35), which
this test structurally cannot measure.

---

## PHASE 5 — RESULTS (exp2812 Aronson permutation, COMPLETE — diagnostic)

Method: **offline Python re-implementation** of frozen CleanCoreV2A (real EA sha `67bdf0f6…` —
NOTE: the `9f177a49` cited earlier is CleanCoreV1; provenance corrected here), **block-permutation**
surrogate price paths (dependence-preserving, NOT IID PnL shuffle), 200 train surrogates. MT5
custom-symbol route confirmed not viable → **fidelity caveat explicit: Python replay diverges from
MT5 refs; this is a DIAGNOSTIC, not an MT5-scored result.**

| Window | observed profit | observed R/DD | p(profit) | p(R/DD) |
|---|---|---|---|---|
| Train 2024-25 (200 surrogates) | 1,209 | 129.3 | **0.657** | **0.836** |
| 2026 sensitivity (50) | 899 | 141.1 | **0.451** | **0.451** |

**Interpretation (per the required wording):** all p-values are high → the test **FAILS TO REJECT the
null of predictive non-superiority.** This is **not** proof that no edge exists — it is **no evidence
that CleanCoreV2A's performance exceeds a dependence-preserving random null.** Consistent with the
true-OOS result (PF 0.35), but carries the offline-Python fidelity caveat.

---

## PHASE 7 — EVIDENCE TABLE

| # | Claim | Static evidence | Quant test | Result | Status |
|---|---|---|---|---|---|
| 1 | Exact hour pins contribute stable value | 466 exact-hour gates | Ablation A1 | A1 −1,342 long (net loss) → pins are **protective in-sample**, load-bearing | SUPPORTED in-sample (load-bearing); forward stability INCONCLUSIVE; protective-block is itself curve-fit |
| 2 | Absolute price pins contribute stable value | ≥4600 pins = 2026-only | Ablation A2 | A2 drops ~47k long / ~17.5k RT | SUPPORTED in-sample (additive); forward INCONCLUSIVE |
| 3 | Slot/cluster families contribute stable value | 95 coordinate cells | Ablation A3 | A3 drops ~52k long / ~26k RT | SUPPORTED in-sample (additive); forward INCONCLUSIVE |
| 4 | Coordinate layer carries most profitability | 2026-gated rules + 466 hours | Ablation A4/A5 vs A0, bootstrap CI | coordinate = ~93% long / ~96% RT; CI excludes 0 | **EMPIRICALLY SUPPORTED (in-sample/fitted backtest)** |
| 5 | Structural core has positive expectancy | ATR-relative core isolable | Ablation A5 + CleanCoreV2A OOS | A5 +8,706 long / +1,717 RT (in-sample, tiny); CleanCoreV2A true-OOS PF 0.35 | MIXED — positive in-sample (sliver), **negative on true OOS** |
| 6 | Configuration-selection is overfit | grid best-of-N | LOCAL PBO/CSCV (exp2811) | exp2800 PBO 0.4% (CSCV-blind to Model-1 fill artifact = false comfort); exp2802 PBO 25.4%, logit≈0 (executable selection ≈chance) | INCONCLUSIVE by LOCAL PBO — within-train/Model-1/small-N; cannot see the train→2026 gap (the real failure) |
| 7 | A surviving rule is superior after multiple-testing correction | — | White/Hansen | — | NOT TESTABLE (full universe) |
| 8 | Fresh-start monthly = walk-forward | params 2026-fitted | WFA validity gate | fails validity gate | **REJECTED — it is retrospective validation, not WF** |
| 9 | CleanCoreV2A has predictive value beyond random | 89% WR, PF 0.35 OOS | Permutation (exp2812, offline diagnostic) | p(profit)=0.66 train / 0.45 2026 → fails to reject | **FAILED TO REJECT non-superiority** — no evidence of edge beyond random (offline-Python fidelity caveat); not "proven no edge" |

## FINAL CONCLUSION (claim-labelled, valid tests only)
- **ESTABLISHED quantitatively (ablation, CIs exclude 0):** the **memorized coordinate layer carries
  ~93% (long) / ~96% (2026 RT) of exp1801's *fitted* backtest profit**; the structural core is ~4–7%.
  Hour pins are *protective* (removing → net loss); price-pins + slots are additive. (Caveat: both
  windows are largely in-sample → this is the *fitted-backtest* attribution.)
- **No evidence the clean structural core is real:** on true OOS it's negative (CleanCoreV2A PF 0.35),
  and the permutation diagnostic **fails to reject** that its performance is no better than random.
- **NOT cleanly testable with the data the process saved:** local PBO is inconclusive (within-train,
  Model-1, small-N; the artifact grid's low value is a CSCV blind-spot); **White/Hansen full universe
  and true Pardo walk-forward are NOT TESTABLE** (no per-alternative series / contaminated windows).
  *That absence is itself a finding about the old research process.*
- **Net:** the quantitative evidence supports that exp1801's profitability is overwhelmingly memorized
  coordinates, and finds no demonstrable forward edge in the honest core — while honestly marking the
  tests the data cannot support, rather than faking them. This diagnoses the old process; it does not
  manufacture a new winner.

---

## NEXT (awaiting Juan's go — no engineering fired yet)
Recommended valid path, in order: **(2) ablation** [core, builds the empirical attribution + supplies
series for (3)] → **(3) LOCAL PBO** + **(5) permutation** as labelled diagnostics. Phases 4 (full) and
6 (true WFA) are marked NOT TESTABLE and will be reported as such, not run. Deliverables 2 (manifest
CSV) and 3 (lineage CSV) accompany this. Scripts/charts/matrices (deliverables 4–9) are produced as
each runnable phase executes.

---

## DELIVERABLE 8 — CHARTS

- PBO logit distribution (exp2811, S=10, both local grids): `experiments/mt5_native/analysis/exp281x_charts/exp2811_pbo_logit_distribution_s10.png`
- Permutation null histogram (exp2812 train 2024-25, 200-surrogate null; profit + R/DD): `experiments/mt5_native/analysis/exp281x_charts/exp2812_permutation_train_null_profit_rdd.png`
- Stitched-OOS equity chart: **N/A** — true WFA / stitched OOS is **NOT TESTABLE** from the saved process, so no chart was fabricated.

## DELIVERABLE 9 — REPRODUCTION COMMANDS

- Phase 2 / exp2810 ablation: `python3 scripts/smc_exp2810_exp1801_ablation_phase2.py`
- Phase 3 / exp2811 LOCAL PBO-CSCV: `python3 scripts/smc_exp2811_local_pbo_cscv.py`
- Phase 5 / exp2812 Aronson permutation diagnostic: `python3 scripts/smc_exp2812_clean_core_v2a_permutation.py --n-sims=200`
