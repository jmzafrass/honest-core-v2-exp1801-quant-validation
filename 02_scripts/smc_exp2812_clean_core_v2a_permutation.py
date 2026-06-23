#!/usr/bin/env python3
"""exp2812 Aronson-style permutation diagnostic for CleanCoreV2A.

MT5 custom-symbol surrogate injection is parked/not viable on this setup, so
this script uses a compact offline Python reimplementation of CleanCoreV2A.
It is diagnostic only and explicitly reports the Python-vs-MT5 fidelity gap.
"""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.smc_exp2802_clean_core_v2a_phase2r_selection import parse_report

EA = ROOT / "ea" / "CleanCoreV2A.mq5"
OHLC = ROOT / "data" / "ohlc" / "xauusdm_m5_ohlc_full.csv"
ANALYSIS_DIR = ROOT / "experiments" / "mt5_native" / "analysis"
OUT_DIR = ANALYSIS_DIR / "exp2812_permutation"
SUMMARY = ANALYSIS_DIR / "smc_exp2812_clean_core_v2a_permutation_summary.json"
DOC = ROOT / "docs" / "honest_core_v2_exp2812_clean_core_v2a_permutation_20260622.md"
LOG = ROOT / "experiments" / "experiment_log.jsonl"

DEPOSIT = 1600.0
PIP_SIZE = 0.01
SPREAD = 0.30
AED_PER_DOLLAR_PER_001_LOT = 3.675
SEED = 2812

PARAMS = {
    "swing_lookback": 12,
    "equal_tolerance_pips": 20.0,
    "min_overshoot_atr": 0.10,
    "max_overshoot_atr": 2.50,
    "max_displacement_bars": 19,
    "displacement_body_atr": 0.45,
    "displacement_body_ratio": 0.50,
    "min_fvg_size_atr": 0.06,
    "fvg_max_formation_bars": 10,
    "fvg_max_wait_bars": 128,
    "retest_tolerance_pips": 0.0,
    "sl_buffer_atr": 0.14,
    "target_rr": 2.00,
    "trail_activation_pips": 45.0,
    "trail_distance_pips": 30.0,
    "max_bars_in_trade": 32,
    "market_close_minute_of_week": 7195,
    "no_new_trade_before_close_minutes": 240,
}

SIM_HIGH: np.ndarray | None = None
SIM_LOW: np.ndarray | None = None
SIM_TIME: list[pd.Timestamp] | None = None
WORKER_DF: pd.DataFrame | None = None

WINDOWS = {
    "train_2024_2025": ("2024-01-01", "2026-01-01"),
    "heldout_2026_jun21_sensitivity": ("2026-01-01", "2026-06-22"),
}


@dataclass
class Swing:
    price: float
    time: pd.Timestamp
    is_high: bool
    active: bool = True


@dataclass
class Setup:
    direction: int = 0
    stage: int = 0
    sweep_time: pd.Timestamp | None = None
    displacement_time: pd.Timestamp | None = None
    fvg_time: pd.Timestamp | None = None
    swept_swing_index: int = -1
    bars_in_state: int = 0
    swept_to_displacement_bars: int = 0
    displacement_to_fvg_bars: int = 0
    fvg_to_retest_bars: int = 0
    swept_level: float = 0.0
    sweep_extreme: float = 0.0
    sweep_atr: float = 0.0
    overshoot_atr: float = 0.0
    cisd_level: float = 0.0
    cisd_passed: bool = False
    displacement_body_atr: float = 0.0
    displacement_body_ratio: float = 0.0
    fvg_bottom: float = 0.0
    fvg_top: float = 0.0
    fvg_size_atr: float = 0.0

    def reset(self) -> None:
        self.__dict__.update(Setup().__dict__)


def clean(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    if isinstance(x, tuple):
        return [clean(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        xf = float(x)
        return xf if math.isfinite(xf) else None
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, pd.Timestamp):
        return x.isoformat()
    return x


def load_bars(start: str, end: str) -> pd.DataFrame:
    df = pd.read_csv(OHLC)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y.%m.%d %H:%M", errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime")
    out = df[(df["datetime"] >= pd.Timestamp(start)) & (df["datetime"] < pd.Timestamp(end))].copy()
    out = out.reset_index(drop=True)
    return out[["datetime", "open", "high", "low", "close"]]


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df = df.copy()
    df["atr"] = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    return df


def minutes_of_week(ts: pd.Timestamp) -> int:
    # Python Monday=0; MQL Sunday=0.
    mql_dow = (int(ts.dayofweek) + 1) % 7
    return mql_dow * 1440 + int(ts.hour) * 60 + int(ts.minute)


def entries_blocked_by_close(ts: pd.Timestamp) -> bool:
    mins = PARAMS["no_new_trade_before_close_minutes"]
    if mins <= 0:
        return False
    now = minutes_of_week(ts)
    close_minute = PARAMS["market_close_minute_of_week"]
    diff = close_minute - now
    if diff < 0:
        diff += 7 * 1440
    return diff <= mins


def find_cisd(swings: list[Swing], swept_idx: int, want_high: bool) -> float:
    if swept_idx < 0 or swept_idx >= len(swings):
        return 0.0
    swept_time = swings[swept_idx].time
    for i in range(len(swings) - 1, -1, -1):
        if i == swept_idx:
            continue
        s = swings[i]
        if not s.active or s.is_high != want_high or s.time >= swept_time:
            continue
        return s.price
    return 0.0


def start_setup(setup: Setup, direction: int, swing_idx: int, prev: pd.Series, atr: float, swings: list[Swing]) -> None:
    setup.reset()
    setup.direction = direction
    setup.stage = 1
    setup.swept_swing_index = swing_idx
    setup.swept_level = swings[swing_idx].price
    setup.sweep_time = prev["datetime"]
    setup.sweep_atr = atr
    if direction > 0:
        setup.sweep_extreme = float(prev["low"])
        setup.overshoot_atr = (setup.swept_level - float(prev["low"])) / atr
        setup.cisd_level = find_cisd(swings, swing_idx, True)
    else:
        setup.sweep_extreme = float(prev["high"])
        setup.overshoot_atr = (float(prev["high"]) - setup.swept_level) / atr
        setup.cisd_level = find_cisd(swings, swing_idx, False)
    setup.cisd_passed = setup.cisd_level == 0.0
    swings[swing_idx].active = False


def update_swings(df: pd.DataFrame, i: int, swings: list[Swing]) -> None:
    global SIM_HIGH, SIM_LOW, SIM_TIME
    if SIM_HIGH is None or SIM_LOW is None or SIM_TIME is None:
        raise RuntimeError("simulate() did not initialize swing arrays")
    lb = int(PARAMS["swing_lookback"])
    check_idx = i - (lb + 1)
    if check_idx - lb < 0 or check_idx + lb >= i:
        return
    highs = SIM_HIGH
    lows = SIM_LOW
    times = SIM_TIME
    high = float(highs[check_idx])
    low = float(lows[check_idx])
    swing_high = bool(
        np.max(highs[check_idx - lb : check_idx]) < high
        and np.max(highs[check_idx + 1 : check_idx + lb + 1]) < high
    )
    swing_low = bool(
        np.min(lows[check_idx - lb : check_idx]) > low
        and np.min(lows[check_idx + 1 : check_idx + lb + 1]) > low
    )
    tolerance = PARAMS["equal_tolerance_pips"] * PIP_SIZE
    ts = times[check_idx]
    if swing_high:
        if not any(s.is_high and abs(s.price - high) <= tolerance and abs((s.time - ts).total_seconds()) <= 300 for s in swings[-50:]):
            swings.append(Swing(high, ts, True))
    if swing_low:
        if not any((not s.is_high) and abs(s.price - low) <= tolerance and abs((s.time - ts).total_seconds()) <= 300 for s in swings[-50:]):
            swings.append(Swing(low, ts, False))
    if len(swings) > 700:
        # Diagnostic speed guard: retain the most recent active liquidity map.
        swings[:] = swings[-550:]


def same_bar_reclaimed(direction: int, level: float, prev: pd.Series) -> bool:
    if direction > 0:
        return float(prev["close"]) > level and float(prev["close"]) > float(prev["open"])
    return float(prev["close"]) < level and float(prev["close"]) < float(prev["open"])


def check_for_sweeps(df: pd.DataFrame, i: int, buy: Setup, sell: Setup, swings: list[Swing]) -> None:
    prev = df.iloc[i - 1]
    atr = float(prev["atr"])
    if not math.isfinite(atr) or atr <= 0:
        return
    best_buy = -1
    best_sell = -1
    best_buy_score = -1.0
    best_sell_score = -1.0
    scan_floor = max(0, len(swings) - 350)
    for idx in range(len(swings) - 1, scan_floor - 1, -1):
        s = swings[idx]
        if not s.active:
            continue
        level = s.price
        if s.is_high:
            if float(prev["high"]) <= level:
                continue
            overshoot = (float(prev["high"]) - level) / atr
            if overshoot < PARAMS["min_overshoot_atr"] or overshoot > PARAMS["max_overshoot_atr"]:
                continue
            if not same_bar_reclaimed(-1, level, prev):
                continue
            if overshoot > best_sell_score:
                best_sell_score = overshoot
                best_sell = idx
        else:
            if float(prev["low"]) >= level:
                continue
            overshoot = (level - float(prev["low"])) / atr
            if overshoot < PARAMS["min_overshoot_atr"] or overshoot > PARAMS["max_overshoot_atr"]:
                continue
            if not same_bar_reclaimed(1, level, prev):
                continue
            if overshoot > best_buy_score:
                best_buy_score = overshoot
                best_buy = idx
    if best_buy >= 0 and buy.stage != 3:
        start_setup(buy, 1, best_buy, prev, atr, swings)
    if best_sell >= 0 and sell.stage != 3:
        start_setup(sell, -1, best_sell, prev, atr, swings)


def process_swept(setup: Setup, prev: pd.Series, atr: float) -> None:
    setup.bars_in_state += 1
    if setup.bars_in_state > PARAMS["max_displacement_bars"]:
        setup.reset()
        return
    rng = float(prev["high"]) - float(prev["low"])
    body = abs(float(prev["close"]) - float(prev["open"]))
    if atr <= 0 or rng <= 0:
        return
    if body < PARAMS["displacement_body_atr"] * atr:
        return
    if body / rng < PARAMS["displacement_body_ratio"]:
        return
    bullish = float(prev["close"]) > float(prev["open"])
    if setup.direction > 0 and not bullish:
        return
    if setup.direction < 0 and bullish:
        return
    if setup.cisd_level != 0.0:
        if setup.direction > 0 and float(prev["close"]) <= setup.cisd_level:
            return
        if setup.direction < 0 and float(prev["close"]) >= setup.cisd_level:
            return
    setup.cisd_passed = True
    setup.displacement_time = prev["datetime"]
    setup.swept_to_displacement_bars = setup.bars_in_state
    setup.displacement_body_atr = body / atr
    setup.displacement_body_ratio = body / rng
    setup.stage = 2
    setup.bars_in_state = 0


def process_fvg_watch(setup: Setup, df: pd.DataFrame, i: int, atr: float) -> None:
    setup.bars_in_state += 1
    if setup.bars_in_state > max(1, int(PARAMS["fvg_max_formation_bars"])):
        setup.reset()
        return
    if atr <= 0 or i < 3:
        return
    r1 = df.iloc[i - 1]
    r3 = df.iloc[i - 3]
    fvg_top = 0.0
    fvg_bottom = 0.0
    if setup.direction > 0:
        if float(r3["high"]) < float(r1["low"]):
            fvg_top = float(r1["low"])
            fvg_bottom = float(r3["high"])
    else:
        if float(r3["low"]) > float(r1["high"]):
            fvg_top = float(r3["low"])
            fvg_bottom = float(r1["high"])
    if fvg_top == 0.0 and fvg_bottom == 0.0:
        return
    size = fvg_top - fvg_bottom
    if size < PARAMS["min_fvg_size_atr"] * atr:
        setup.reset()
        return
    setup.fvg_top = fvg_top
    setup.fvg_bottom = fvg_bottom
    setup.fvg_size_atr = size / atr
    setup.fvg_time = r1["datetime"]
    setup.displacement_to_fvg_bars = setup.bars_in_state
    setup.stage = 3
    setup.bars_in_state = 0


def retest_confirmed(setup: Setup, prev: pd.Series) -> bool:
    tol = PARAMS["retest_tolerance_pips"] * PIP_SIZE
    if setup.direction > 0:
        return (
            float(prev["low"]) <= setup.fvg_top + tol
            and float(prev["open"]) > setup.fvg_bottom - tol
            and float(prev["close"]) > float(prev["open"])
            and float(prev["close"]) > setup.fvg_bottom
        )
    return (
        float(prev["high"]) >= setup.fvg_bottom - tol
        and float(prev["open"]) < setup.fvg_top + tol
        and float(prev["close"]) < float(prev["open"])
        and float(prev["close"]) < setup.fvg_top
    )


def send_order(setup: Setup, df: pd.DataFrame, i: int, atr: float, open_position: dict[str, Any] | None) -> dict[str, Any] | None:
    if open_position is not None or entries_blocked_by_close(df.at[i, "datetime"]):
        return None
    bid_open = float(df.at[i, "open"])
    ask_open = bid_open + SPREAD
    entry = ask_open if setup.direction > 0 else bid_open
    sl = setup.sweep_extreme - PARAMS["sl_buffer_atr"] * atr if setup.direction > 0 else setup.sweep_extreme + PARAMS["sl_buffer_atr"] * atr
    risk = abs(entry - sl)
    if risk <= 0:
        return None
    tp = entry + risk * PARAMS["target_rr"] if setup.direction > 0 else entry - risk * PARAMS["target_rr"]
    return {
        "direction": setup.direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "lot": 0.01,
        "open_i": i,
        "open_time": df.at[i, "datetime"],
    }


def process_retest(setup: Setup, df: pd.DataFrame, i: int, atr: float, open_position: dict[str, Any] | None) -> dict[str, Any] | None:
    setup.bars_in_state += 1
    if setup.bars_in_state > max(1, int(PARAMS["fvg_max_wait_bars"])):
        setup.reset()
        return None
    prev = df.iloc[i - 1]
    if setup.direction > 0 and float(prev["close"]) < setup.fvg_bottom:
        setup.reset()
        return None
    if setup.direction < 0 and float(prev["close"]) > setup.fvg_top:
        setup.reset()
        return None
    if not retest_confirmed(setup, prev):
        return None
    setup.fvg_to_retest_bars = setup.bars_in_state
    pos = send_order(setup, df, i, atr, open_position)
    setup.reset()
    return pos


def advance_setup(setup: Setup, df: pd.DataFrame, i: int, open_position: dict[str, Any] | None) -> dict[str, Any] | None:
    if setup.stage == 0:
        return None
    prev = df.iloc[i - 1]
    atr = float(prev["atr"])
    if not math.isfinite(atr) or atr <= 0:
        return None
    if setup.stage == 1:
        process_swept(setup, prev, atr)
    elif setup.stage == 2:
        process_fvg_watch(setup, df, i, atr)
    elif setup.stage == 3:
        return process_retest(setup, df, i, atr, open_position)
    return None


def close_profit(pos: dict[str, Any], exit_price: float) -> float:
    direction = pos["direction"]
    points = (exit_price - pos["entry"]) * direction
    return points * (pos["lot"] / 0.01) * AED_PER_DOLLAR_PER_001_LOT


def manage_position(pos: dict[str, Any] | None, df: pd.DataFrame, i: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if pos is None:
        return None, None
    row = df.iloc[i]
    bid_open = float(row["open"])
    bid_high = float(row["high"])
    bid_low = float(row["low"])
    ask_open = bid_open + SPREAD
    ask_high = bid_high + SPREAD
    ask_low = bid_low + SPREAD
    bars = i - int(pos["open_i"])
    if PARAMS["max_bars_in_trade"] > 0 and bars >= PARAMS["max_bars_in_trade"]:
        exit_price = bid_open if pos["direction"] > 0 else ask_open
        return None, {"time": row["datetime"], "profit": close_profit(pos, exit_price), "reason": "max_bars"}
    if pos["direction"] > 0:
        if bid_low <= pos["sl"]:
            return None, {"time": row["datetime"], "profit": close_profit(pos, pos["sl"]), "reason": "sl"}
        if bid_high >= pos["tp"]:
            return None, {"time": row["datetime"], "profit": close_profit(pos, pos["tp"]), "reason": "tp"}
        if (bid_high - pos["entry"]) / PIP_SIZE >= PARAMS["trail_activation_pips"]:
            new_sl = max(pos["sl"], bid_high - PARAMS["trail_distance_pips"] * PIP_SIZE)
            if bid_low <= new_sl:
                return None, {"time": row["datetime"], "profit": close_profit(pos, new_sl), "reason": "trail"}
            pos["sl"] = new_sl
    else:
        if ask_high >= pos["sl"]:
            return None, {"time": row["datetime"], "profit": close_profit(pos, pos["sl"]), "reason": "sl"}
        if ask_low <= pos["tp"]:
            return None, {"time": row["datetime"], "profit": close_profit(pos, pos["tp"]), "reason": "tp"}
        if (pos["entry"] - ask_low) / PIP_SIZE >= PARAMS["trail_activation_pips"]:
            new_sl = min(pos["sl"], ask_low + PARAMS["trail_distance_pips"] * PIP_SIZE)
            if ask_high >= new_sl:
                return None, {"time": row["datetime"], "profit": close_profit(pos, new_sl), "reason": "trail"}
            pos["sl"] = new_sl
    return pos, None


def simulate(df: pd.DataFrame) -> dict[str, Any]:
    global SIM_HIGH, SIM_LOW, SIM_TIME
    if "atr" not in df.columns:
        df = add_atr(df)
    SIM_HIGH = df["high"].to_numpy(dtype=float)
    SIM_LOW = df["low"].to_numpy(dtype=float)
    SIM_TIME = list(pd.to_datetime(df["datetime"]))
    swings: list[Swing] = []
    buy = Setup()
    sell = Setup()
    position: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    start_i = max(80, int(PARAMS["swing_lookback"]) * 3)
    for i in range(start_i, len(df)):
        position, closed = manage_position(position, df, i)
        if closed is not None:
            trades.append(closed)
        update_swings(df, i, swings)
        new_pos = advance_setup(buy, df, i, position)
        if new_pos is not None and position is None:
            position = new_pos
        new_pos = advance_setup(sell, df, i, position)
        if new_pos is not None and position is None:
            position = new_pos
        check_for_sweeps(df, i, buy, sell, swings)
    if position is not None and len(df):
        exit_price = float(df.iloc[-1]["close"]) if position["direction"] > 0 else float(df.iloc[-1]["close"]) + SPREAD
        trades.append({"time": df.iloc[-1]["datetime"], "profit": close_profit(position, exit_price), "reason": "end"})
    profits = pd.Series([t["profit"] for t in trades], dtype=float)
    total = float(profits.sum()) if len(profits) else 0.0
    wins = profits[profits > 0]
    losses = profits[profits < 0]
    equity = DEPOSIT + profits.cumsum() if len(profits) else pd.Series([DEPOSIT])
    peak = equity.cummax()
    dd = ((peak - equity) / peak.replace(0, np.nan) * 100.0).fillna(0.0)
    max_dd = float(dd.max()) if len(dd) else 0.0
    return {
        "profit": total,
        "return_per_dd": total / max_dd if max_dd > 0 else 0.0,
        "max_dd_pct": max_dd,
        "pf": float(wins.sum() / -losses.sum()) if len(losses) and float(-losses.sum()) > 0 else (float("inf") if len(wins) else 0.0),
        "trades": int(len(trades)),
        "win_rate_pct": float((profits > 0).mean() * 100.0) if len(profits) else 0.0,
        "reason_counts": pd.Series([t["reason"] for t in trades]).value_counts().to_dict() if trades else {},
    }


def block_permute(df: pd.DataFrame, block_len: int, rng: np.random.Generator) -> pd.DataFrame:
    n = len(df)
    blocks = [(i, min(i + block_len, n)) for i in range(0, n, block_len)]
    order = rng.permutation(len(blocks))
    synthetic_rows: list[pd.DataFrame] = []
    current = float(df.iloc[0]["open"])
    for block_idx in order:
        start, end = blocks[block_idx]
        block = df.iloc[start:end].copy()
        first_open = float(block.iloc[0]["open"])
        scale = current / first_open if first_open > 0 else 1.0
        b = block[["open", "high", "low", "close"]].astype(float) * scale
        # Reorder columns and carry the synthetic path forward from this block close.
        b["datetime"] = block["datetime"].values
        b = b[["datetime", "open", "high", "low", "close"]]
        current = float(b.iloc[-1]["close"])
        synthetic_rows.append(b)
    out = pd.concat(synthetic_rows, ignore_index=True)
    out["datetime"] = df["datetime"].values[: len(out)]
    return out


def run_null(df: pd.DataFrame, block_len: int, n_sims: int, seed: int) -> dict[str, Any]:
    workers = max(1, min(8, (os.cpu_count() or 4) - 2))
    rows: list[dict[str, Any]] = []
    seeds = [seed + 1000003 * i for i in range(n_sims)]
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=mp.get_context("fork"),
        initializer=_init_worker,
        initargs=(df,),
    ) as pool:
        futures = {
            pool.submit(_worker_one_surrogate, block_len, sim_idx, sim_seed): sim_idx
            for sim_idx, sim_seed in enumerate(seeds)
        }
        for done_count, fut in enumerate(as_completed(futures), start=1):
            rows.append(fut.result())
            if done_count % 25 == 0 or done_count == n_sims:
                print(f"[null] block={block_len} sim {done_count}/{n_sims}", flush=True)
    rows.sort(key=lambda row: row["sim"])
    return {"block_len": block_len, "n_sims": n_sims, "seed": seed, "rows": rows}


def _init_worker(df: pd.DataFrame) -> None:
    global WORKER_DF
    WORKER_DF = df


def _worker_one_surrogate(block_len: int, sim_idx: int, sim_seed: int) -> dict[str, Any]:
    if WORKER_DF is None:
        raise RuntimeError("worker dataframe not initialized")
    rng = np.random.default_rng(sim_seed)
    surrogate = block_permute(WORKER_DF, block_len, rng)
    stats = simulate(surrogate)
    stats["sim"] = sim_idx
    return stats


def p_value(null_values: np.ndarray, observed: float) -> float:
    return float((1 + np.sum(null_values >= observed)) / (len(null_values) + 1))


def summarize_null(observed: dict[str, Any], null: dict[str, Any]) -> dict[str, Any]:
    profits = np.array([row["profit"] for row in null["rows"]], dtype=float)
    rdds = np.array([row["return_per_dd"] for row in null["rows"]], dtype=float)
    return {
        "block_len": null["block_len"],
        "n_sims": null["n_sims"],
        "seed": null["seed"],
        "observed": observed,
        "profit_null": {
            "mean": float(np.mean(profits)),
            "p025": float(np.percentile(profits, 2.5)),
            "median": float(np.median(profits)),
            "p975": float(np.percentile(profits, 97.5)),
            "max": float(np.max(profits)),
            "empirical_p_ge_observed": p_value(profits, float(observed["profit"])),
        },
        "return_per_dd_null": {
            "mean": float(np.mean(rdds)),
            "p025": float(np.percentile(rdds, 2.5)),
            "median": float(np.median(rdds)),
            "p975": float(np.percentile(rdds, 97.5)),
            "max": float(np.max(rdds)),
            "empirical_p_ge_observed": p_value(rdds, float(observed["return_per_dd"])),
        },
    }


def mt5_reference() -> dict[str, Any]:
    refs = {
        "train_exp2802_selected": ROOT
        / "experiments/mt5_native/smc_exp2802_clean_core_v2a_phase2r_trail_d030_a045_train_2024_2025_dep1600_summary.json",
        "heldout_rt_exp2804_core_a": ROOT
        / "experiments/mt5_native/smc_exp2804_clean_core_v2a_phase3_core_a_heldout_rt_2026_jun13_dep1600_summary.json",
    }
    out: dict[str, Any] = {}
    for name, summary in refs.items():
        if not summary.exists():
            out[name] = {"exists": False}
            continue
        run_id = summary.name[: -len("_summary.json")]
        report = parse_report(run_id)
        out[name] = {
            "exists": True,
            "profit": report.get("profit"),
            "pf": report.get("profit_factor"),
            "trades": report.get("trades"),
            "max_dd_pct": report.get("max_dd_pct"),
            "intra_dd_pct": report.get("intra_dd_pct"),
            "return_per_dd": (report.get("profit") or 0.0) / (report.get("intra_dd_pct") or 1.0),
        }
    return out


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_doc(payload: dict[str, Any]) -> None:
    primary = payload["windows"]["train_2024_2025"]["primary"]
    lines = [
        "# exp2812 Aronson Permutation Diagnostic",
        "",
        "Scope: dependence-preserving surrogate-price diagnostic for frozen CleanCoreV2A. This is **not MT5 ground truth** because the custom-symbol surrogate route is not viable on this setup; the test uses a compact Python port of CleanCoreV2A.",
        "",
        "## Hash Note",
        "",
        f"- Actual `ea/CleanCoreV2A.mq5` SHA256: `{payload['ea_sha256']}`",
        "- User-provided short hash `9f177a49` points to CleanCoreV1 in the local docs/artifacts, not the current CleanCoreV2A file. This run therefore uses the actual CleanCoreV2A source used by exp2800/exp2802/exp2804 and flags the mismatch.",
        "",
        "## Method",
        "",
        "- Feasible path chosen: offline Python reimplementation, not MT5 custom-symbol injection.",
        "- Primary window: train 2024-2025, selected executable exit config (`trail distance=30`, `activation=45`, tilt off).",
        "- Surrogate design: block-permute contiguous M5 OHLC blocks, preserving within-block serial dependence and volatility clustering while breaking the global signal-return arrangement.",
        f"- Primary block length: `{primary['block_len']}` bars; simulations: `{primary['n_sims']}`; seed: `{primary['seed']}`.",
        "- Costs: fixed 0.30 spread and AED conversion calibrated from CleanCoreV2A MT5 deals (~3.675 AED per $1 XAU move at 0.01 lot).",
        "",
        "## Primary Result",
        "",
        f"- Observed offline profit: `{primary['observed']['profit']:.2f}`",
        f"- Observed offline R/DD: `{primary['observed']['return_per_dd']:.4f}`",
        f"- Profit null median / 97.5%: `{primary['profit_null']['median']:.2f}` / `{primary['profit_null']['p975']:.2f}`",
        f"- R/DD null median / 97.5%: `{primary['return_per_dd_null']['median']:.4f}` / `{primary['return_per_dd_null']['p975']:.4f}`",
        f"- Empirical p(profit null >= observed): `{primary['profit_null']['empirical_p_ge_observed']:.4f}`",
        f"- Empirical p(R/DD null >= observed): `{primary['return_per_dd_null']['empirical_p_ge_observed']:.4f}`",
        "",
        "## Sensitivity",
        "",
        "| window | block bars | sims | obs profit | p_profit | obs R/DD | p_R/DD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for window, info in payload["windows"].items():
        for name, result in info.items():
            if not isinstance(result, dict) or "observed" not in result:
                continue
            lines.append(
                f"| {window}/{name} | {result['block_len']} | {result['n_sims']} | "
                f"{result['observed']['profit']:.2f} | {result['profit_null']['empirical_p_ge_observed']:.4f} | "
                f"{result['observed']['return_per_dd']:.4f} | {result['return_per_dd_null']['empirical_p_ge_observed']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## MT5 Fidelity Caveat",
            "",
            "The Python port is close enough to exercise the same structural thesis but not close enough to replace MT5 scoring. Known gaps: M5-bar intrabar ordering for SL/TP/trail, fixed spread rather than true tick spread, no broker execution microstructure, and a bounded recent-swing cache for speed.",
            "",
            "MT5 reference cells for the selected V2A config:",
            "",
            "```json",
            json.dumps(payload["mt5_reference"], indent=2, sort_keys=True),
            "```",
            "",
            f"Summary JSON: `{SUMMARY}`",
        ]
    )
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def log_experiment(payload: dict[str, Any]) -> None:
    primary = payload["windows"]["train_2024_2025"]["primary"]
    row = {
        "id": "exp_2812",
        "date": "2026-06-22",
        "era": "honest_core_v2_quant_addendum",
        "phase": "quant_addendum_phase5",
        "category": "analysis",
        "baseline_id": "CleanCoreV2A",
        "hypothesis": "Aronson-style surrogate-price diagnostic tests whether frozen CleanCoreV2A performance beats a dependence-preserving block-permutation null.",
        "decision": "observe",
        "metrics": {
            "diagnostic_only_not_mt5": True,
            "primary_n_sims": primary["n_sims"],
            "primary_block_len": primary["block_len"],
            "observed_profit": primary["observed"]["profit"],
            "observed_return_per_dd": primary["observed"]["return_per_dd"],
            "profit_empirical_p": primary["profit_null"]["empirical_p_ge_observed"],
            "return_per_dd_empirical_p": primary["return_per_dd_null"]["empirical_p_ge_observed"],
            "ea_sha256": payload["ea_sha256"],
            "hash_mismatch_user_9f177a49_points_to_v1": True,
        },
        "artifact": str(DOC.relative_to(ROOT)),
        "summary_json": str(SUMMARY.relative_to(ROOT)),
        "why": "Diagnostic surrogate test completed with documented Python-MT5 fidelity limitations; no model promoted.",
        "next": "Use with exp2811 local PBO in Claude/Juan audit.",
    }
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(clean(row), sort_keys=True) + "\n")


def main() -> int:
    n_sims = 200
    for arg in sys.argv[1:]:
        if arg.startswith("--n-sims="):
            n_sims = int(arg.split("=", 1)[1])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "experiment": "exp2812_clean_core_v2a_permutation",
        "ea": "ea/CleanCoreV2A.mq5",
        "ea_sha256": sha256(EA),
        "user_requested_sha_note": "9f177a49 is CleanCoreV1 locally; actual CleanCoreV2A hash is reported above.",
        "params": PARAMS,
        "method": "offline_python_reimplementation_block_permutation_diagnostic",
        "mt5_custom_symbol_path": "not used; parked/not viable on this setup",
        "windows": {},
        "mt5_reference": mt5_reference(),
    }
    for window_name, (start, end) in WINDOWS.items():
        print(f"[load] {window_name}", flush=True)
        bars = add_atr(load_bars(start, end))
        observed = simulate(bars)
        window_sims = n_sims if window_name == "train_2024_2025" else max(50, n_sims // 4)
        primary_null = run_null(bars, block_len=288, n_sims=window_sims, seed=SEED)
        primary = summarize_null(observed, primary_null)
        window_payload: dict[str, Any] = {"primary": primary}
        # Lighter sensitivity: enough to show direction without pretending full precision.
        for block_len, seed_offset in ((144, 144), (576, 576)):
            sens_null = run_null(bars, block_len=block_len, n_sims=max(20, n_sims // 10), seed=SEED + seed_offset)
            window_payload[f"sensitivity_block_{block_len}"] = summarize_null(observed, sens_null)
        payload["windows"][window_name] = window_payload

        rows = pd.DataFrame(primary_null["rows"])
        rows.to_csv(OUT_DIR / f"{window_name}_primary_null_rows.csv", index=False)
    SUMMARY.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_doc(payload)
    log_experiment(payload)
    print(f"[done] wrote {SUMMARY}")
    print(f"[done] wrote {DOC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
