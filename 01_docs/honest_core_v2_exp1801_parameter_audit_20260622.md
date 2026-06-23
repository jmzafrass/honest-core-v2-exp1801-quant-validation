# Parameter Audit — exp1801 XAUUSDm M5 EA (full constant review)

**Date:** 2026-06-22 · **Subject:** `ea/AutoResearchSMCSweepFVGWindowExp1801_current_margin_final_repair.mq5`
**Method:** every constant assumed guilty until proven structural. No optimization, no tuning, no new EA.
**Review lenses:** Pardo (walk-forward / parameter stability / plateau-vs-spike), Aronson (data-mining bias, OOS, market-logic falsifiability), Bailey-PBO (selection bias after N trials), White Reality-Check / Hansen SPA (false winners from snooping many alternatives).
**Row-level source:** `docs/prereg/honest_core_v1_keep_strip_const_ledger_20260610.csv` (all 1,372 constants, line/name/value). This doc enriches it with category, market-concept, memorization-risk, framework-challenge, and action.

---

## B. CATEGORY SUMMARY WITH COUNTS (1,372 total)

By **mechanism category** (name-pattern):
| Category | Count |
|---|---|
| Time/session filters (hour pins) | **466** |
| Exit / SL / TP / trail | 242 |
| FVG rules | 114 |
| Risk / sizing / margin | 114 |
| Sweep / liquidity | 96 |
| **Memorized slot/cluster families** | 95 |
| ATR / volatility | 76 |
| Other / uncategorized | 95 |
| Price-level pins | 23 (60+ counting in-function `entryPrice>=4600` gates) |
| Displacement / CISD | 19 |
| Retest / mitigation | 14 |
| Lookback / window | 13 |
| Spread filter | 5 |

By **disposition** (existing ledger action → this audit's 5-way class):
| Ledger action | Count | → Classification |
|---|---|---|
| STRIP_OR_DYNAMIC_REPLACE | 370 | Likely memorized (clock) |
| KEEP_CANDIDATE | 322 | Structural? (must still pass ablation) |
| NORMALIZE_OR_KEEP_CORE | 274 | Weakly justified (keep only if normalized) |
| FORMULA_REWRITE | 154 | Convert to adaptive |
| STRIP_OR_RECONSTRUCT | 143 | Likely memorized (slot) |
| REVIEW | 82 | Unclassified |
| STRIP_OR_NORMALIZE | 27 | Likely memorized (price) |

**Headline:** ~**540 constants (370+143+27)** are memorized-coordinate class (clock/slot/price); **466** of the total are exact hour-of-day pins. Only a **small conceptual SMC thesis set (~30–50)** is structurally defensible (ATR-relative SMC mechanics). This static audit identifies memorization risk and rule-family complexity; it does not by itself prove the causal share of predictive edge attributable to memorized constants.

---

## 5-WAY CLASSIFICATION (rollup)

| Class | ≈Count | What's in it |
|---|---|---|
| **Structural** | ~30–50 | ATR-relative SMC mechanics: swing lookback, overshoot-in-ATR, displacement body/ratio, FVG size-in-ATR, sweep-anchored ATR SL, CISD, same-bar reclaim |
| **Weakly justified** | ~270 | Pip/exit thresholds & risk values that *could* be structural if normalized (TP/SL pips, trail pips, min-SL pips, equal-tolerance) |
| **Likely memorized** | ~600+ | 466 hour pins + 95 slot/cluster cells + 60 price pins (≥4600) + narrow ATR/overshoot bands (<0.1 wide) |
| **Dead / redundant / legacy** | ~30–60 | `-1`/`0.0` disabled sentinels, `99999` junk ceilings, dead `if(4==N)` branches, immaterial families (Exp1050 ≈ $66 over 326 trades) |

---

## C. TOP 20 MOST SUSPICIOUS CONSTANTS (historically memorized)

The unifying tell: **coordinate lookups keyed to (exact hour, exact price zone, narrow ATR/overshoot band)** found profitable in the 2017–2026 fit (esp. 2026). White/Hansen: each is a *survivor of many trials* → false winner. Bailey: selection bias. Aronson: no market reason; pure data-mining. Pardo: sharp single-value dependency, no plateau.

1. **Exp1192CFGroupId — 97 group cells** (L10820–11037): OR-chain of 97 exact (price-band × hour-pair × ATR-band × overshoot-band × direction × reason). ~58 cells gated `entryPrice≥4600` = **2026-only**.
2. **Exp1259PortfolioGroupId — 86 group cells** (L11738–12266): 50+ at `entryPrice≥4600`; many `sweepHour==outcomeHour` exact pins; overshoot bands 0.05 wide.
3. **Exp1183LowPriceCF — 20-cluster grid** (L10686–10786): each a hour-pair + price + 0.05-wide overshoot tuple.
4. **`entryPrice≥4600` price pins (60+ sites)**: gold never traded >4,550 before 2026 → these rules do nothing pre-2026 → fitted on 2026 in-sample.
5. **`ask>=4800.00`** (L5943) / **`ask>=4550 && ask<=4570`** (L5975): single-sided / ±10-pip 2026-only price gates (Exp1668LossGuard).
6. **466 hour pins** (header L43–250): e.g. `InpCapBuySLBlockSweepHour=14`, `...EntryDistance4 Sweep14→Entry16`. No market reason hour-14 is special.
7. **`InpTargetBuyBaseDDTrap Sweep7→Entry9`** (L75–77): exact 2h pre-entry slot; breaks across DST.
8. **Exp1145BuyND1112** (L10401): single locked `sweepHour==11 && outcomeHour==12` + overshoot 0.40–0.50.
9. **Exp1160PreBuyRepl1313** (L10502): `hour 13→13` + entryPrice[1600,2200) + ATR[2.5,4.0) → 0.05 lot/1500 SL/5000 TP.
10. **Exp1162FreshPreBin** (L10596): 5 hardcoded bins, all exact hour pairs (8→10, 11→12, …).
11. **Exp1050LowAtrBasket** (L9228): hour + price-ceiling 3000 + overshoot 0.42–0.48 (0.06-wide band).
12. **Narrow overshoot bands `>=0.300 && <0.350`** (80+ sites): 0.05 ATR wide ≈ noise-fit.
13. **`entryATR>=6.00 && entryATR<999.00`** (Exp1259): 999 junk ceiling = artifact.
14. **4+ AND-stacked admission cells** (e.g. L11049): price+dir+reason+hour-pair+CISD+ATR+overshoot = curse of dimensionality.
15. **Exp1786** (L14046): `ask>=4650 && invalidBuyLiveRef>=2500` — price × equity-state compound pin.
16. **Exp1243EntryDt** (L13510): time-of-week × price-tier (`ask>=4500/4600`) gate.
17. **Exp1149Exp1025** (L10383): `entryPrice 3500–4200` + hour pair + ATR constraints (4+ AND).
18. **Day-of-week gates** (e.g. L10675 blocks dow>3): calendar pin, no market logic.
19. **`InpExp1025*` legacy SL/TP pins** (350/500): "first experiment" family, subsumed by later slots.
20. **Sell band `ask>=4500 && ask<=4700` tied to dow** (L13845): ±100 price band × weekday.

---

## D. TOP 20 MOST STRUCTURALLY DEFENSIBLE CONSTANTS

These are ATR-relative / market-structure-relative, broad, and falsifiable. Pardo: robust to volatility regime, plateau-able. Aronson: stateable market logic. (Caveat: still require ablation — see G — because high in-sample PF can survive even on a small param set.)

1. **Swing lookback = 12 bars** — standard pivot/structure detection; broad.
2. **Sweep overshoot 0.1–0.6 ATR** — liquidity run measured in ATR (scales with vol).
3. **Displacement body ≥ 0.45 ATR** — momentum confirmation, volatility-relative.
4. **Displacement body/range ratio ≥ 0.5** — "real" directional candle, unitless.
5. **FVG min size = 0.06 ATR** — gap significance scaled to vol.
6. **FVG formation window (rolling 3-candle)** — structural gap definition.
7. **Sweep-anchored SL + 0.14 ATR buffer** — stop at real invalidation point, vol-scaled.
8. **Same-bar reclaim requirement** — noise filter; defensible discipline.
9. **CISD = close through prior opposite swing** — market-structure-relative change-of-state.
10. **Retest-confirmation close (price returns into FVG + reaction close)** — structural entry trigger.
11. **FVG close-through mitigation invalidation** — setup dies on structural invalidation.
12. **ATR period (volatility base)** — the normalization engine; keep.
13. **RR-to-target as a multiple** (if expressed relative, not fixed pips) — relative payoff.
14. **Max-bars-in-trade (time stop)** — broad holding cap, regime-agnostic *if* not single-tuned.
15. **Equal-high/low tolerance (if expressed in ATR, not fixed pip)** — liquidity-cluster definition.
16. **Trail activation as R-multiple** (if relative) — vol-agnostic profit lock.
17. **Regime/trend gate (if a broad SMA condition exists)** — directional bias, defensible.
18. **Min displacement-to-FVG bar gap (small, broad)** — sequencing discipline.
19. **Spread/cost guard (if expressed vs ATR)** — execution-realism filter.
20. **Direction/structure pairing (buy after bullish CISD, etc.)** — pure logic, no constant to memorize.

---

## E. CONSTANTS THAT CAN LIKELY BE DELETED IMMEDIATELY

- All `-1` / `0.0` disabled sentinel hour/cap constants (~30, L44–241) — dead code.
- `99999.0` / `999.00` junk ceilings in slot bands — artifacts.
- Dead branch selectors (e.g. `if(4==N)` where only `4==4` runs, L10470–10476).
- Immaterial families: Exp1050 (≈$66 / 326 trades ≈ $0.20/trade), legacy Exp1025 SL/TP placeholder pins.
- Duplicated slot logic (Exp1259 ⊇ Exp1192 overlap on the same 4600+ zones).
→ Pure cleanup; zero performance rationale needed (none of these is structural).

## F. CONSTANTS TO CONVERT TO RELATIVE / ADAPTIVE

- **Fixed-pip TP targets (120/500/800/1300)** → ATR-multiple or RR target. *(Pardo: fixed distance is fragile across vol regimes.)*
- **Trail distance = 90 pips, activation fixed** → ATR / R-multiple.
- **Min-SL-distance pips (300/325/2500)** → ATR-multiple floor.
- **`InpMinOvershootPips = 30` floor** → drop the pip floor; keep the ATR band only.
- **Equal-tolerance (1 pip)** → ATR fraction.
- **Any session effect worth keeping** → express as a continuous *session-volatility state*, never an exact hour pin.
- **Spread filter (raw)** → spread ÷ ATR.

## G. CONSTANTS REQUIRING ABLATION BEFORE ANY REBUILD DECISION

Even the "defensible" oddly-precise ones must be ablation-tested for plateau-vs-spike (Pardo) and trial-count deflation (Bailey/White/Hansen):
- **MaxDisplacementBars = 19** (oddly precise — test 12/15/19/24; keep only if a plateau).
- **MaxFVGWaitBars = 128** (= 2^7, suspicious — test 64/96/128).
- **Displacement body 0.45 ATR / ratio 0.5 / FVG 0.06 ATR / SL buffer 0.14 ATR** — confirm each sits on a broad stable region, not a single optimal spike.
- **Swing lookback 12** — confirm 8/12/16 behave similarly.
- **RR target / trail activation** — confirm broad-region stability.
→ Rule: keep ONLY parameters whose performance is flat across a broad neighborhood; reject sharp single-value peaks.

---

## H. MINIMAL CLEAN-MODEL PROPOSAL (description only — NOT to build/optimize yet)

The fewest defensible, ATR-relative parameters that express the SMC thesis with zero memorized coordinates:

**Structure → liquidity → manipulation → displacement → FVG → retest → structural exit**
1. Detect swing structure (lookback ~12).
2. **Sweep**: price runs a prior swing high/low by `overshoot ∈ [0.1, 0.6]·ATR` (equal-level tolerance in ATR).
3. **Reclaim**: same-bar close back through the swept level.
4. **Displacement + CISD**: a candle with body ≥ `0.45·ATR` and body/range ≥ `0.5` that closes through the prior opposite swing (change-of-state).
5. **FVG**: rolling-3-candle gap ≥ `0.06·ATR`, within a small formation window.
6. **Retest**: price returns into the FVG and closes with a reaction; setup invalidates if price closes through the FVG (mitigation).
7. **SL**: anchored at the sweep extreme ± `0.14·ATR`.
8. **Exit**: RR target (multiple) and/or ATR-relative trail; broad time-stop.

**Conceptual parameter budget: ~12–18, mostly ATR-relative or unitless. ZERO hour pins, price pins, or slot/cluster cells.**

Implementation note: this conceptual minimal model is not identical to `CleanCoreV2A`. CleanCoreV2A contains fixed-pip equality tolerance, fixed-pip trail activation, fixed-pip trail distance, and a maximum overshoot of 2.5 ATR. CleanCoreV2A produced approximately PF 0.35 in an MT5 research-contaminated post-selection local holdout. This is materially adverse evidence for that implementation, but it is not pristine forward evidence and should not be generalized to the entire SMC concept.

---

## What the frameworks say, in one line each
- **Pardo:** the model is sharp-single-value-dependent (hours, prices) → fails walk-forward; only the ATR-relative core has plateau robustness.
- **Aronson:** 466 hours × dozens of conditions = massive data-mining; no market reason any exact hour/price is special → reject the lookups.
- **Bailey (PBO):** thousands of (hour×price×ATR×overshoot) cells tried; the survivors are selection-bias artifacts, not edge.
- **White / Hansen:** each slot/hour is a tested alternative; the "best" ones are false winners with no superior predictive ability once the trial count is accounted for.

**Bottom line (claim-labelled per Quant Addendum):** ~540 constants are memorized-coordinate
*class* (`ESTABLISHED BY STATIC CODE ANALYSIS` for what they are; 2026-only price-gated rules + 466
hour pins). The controlled ablation later showed that exp1801's fitted absolute PnL is heavily
dependent on a bundled collection of coordinate-linked and auxiliary production engines. It did not
cleanly isolate the causal contribution of memorized constants, because the toggles remove whole
behavior families and A4 and A5 are the same intervention by construction. CleanCoreV2A's MT5 PF of
approximately 0.35 in a research-contaminated post-selection local holdout is adverse evidence for
that specific implementation, not definitive proof about the broader SMC thesis.
→ See `honest_core_v2_exp1801_quant_validation_addendum_20260622.md` for the data-gated test plan.
