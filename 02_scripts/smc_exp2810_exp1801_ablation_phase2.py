#!/usr/bin/env python3
"""exp2810 controlled coordinate-block ablation for production exp1801.

Builds an isolated ablation copy, proves A0 parity against the protected
production source on a sample, then runs A0-A5 on the required MT5 windows.
"""

from __future__ import annotations

import configparser
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.smc_exp2553_2554_hc_v2_round5_verified_filters_runner as r5

EXP_ID = "exp_2810"
ORIGINAL = ROOT / "ea" / "AutoResearchSMCSweepFVGWindowExp1801_current_margin_final_repair.mq5"
ABLATED = ROOT / "ea" / "AutoResearchSMCSweepFVGWindowExp1801_ablation.mq5"
ORIGINAL_EXPERT = ORIGINAL.stem
ABLATED_EXPERT = ABLATED.stem
CONFIG_DIR = ROOT / "experiments" / "mt5_native" / "configs" / "autoresearch_smc_candidate"
ANALYSIS_DIR = ROOT / "experiments" / "mt5_native" / "analysis"
SERIES_DIR = ANALYSIS_DIR / "exp2810_daily_series"
SUMMARY = ANALYSIS_DIR / "smc_exp2810_exp1801_ablation_phase2_summary.json"
DOC = ROOT / "docs" / "honest_core_v2_exp2810_exp1801_ablation_phase2_20260622.md"
LOG = ROOT / "experiments" / "experiment_log.jsonl"

DEPOSIT = 1600
BOOT_REPS = 5000
BOOT_BLOCK_DAYS = 10
BOOT_SEED = 2810

WINDOWS: dict[str, tuple[str, str, str]] = {
    "long_2017_2026_model1": ("2017.01.01", "2026.06.22", "1"),
    "rt_2026_jun21_model4": ("2026.01.01", "2026.06.22", "4"),
}
PARITY_WINDOW = ("2026.06.01", "2026.06.22", "4")

VARIANTS: dict[str, dict[str, Any]] = {
    "A0_full_copy": {
        "label": "A0 all coordinate layers ON",
        "overrides": {
            "InpAblDisableHourPins": False,
            "InpAblDisablePricePins": False,
            "InpAblDisableSlots": False,
            "InpAblCoreOnly": False,
        },
    },
    "A1_no_hourpins": {
        "label": "A1 disable exact hour pins",
        "overrides": {"InpAblDisableHourPins": True},
    },
    "A2_no_pricepins": {
        "label": "A2 disable absolute price-pin families",
        "overrides": {"InpAblDisablePricePins": True},
    },
    "A3_no_slots": {
        "label": "A3 disable slot/cluster families",
        "overrides": {"InpAblDisableSlots": True},
    },
    "A4_no_coordinate_layers": {
        "label": "A4 disable hour+price+slot coordinate layers",
        "overrides": {
            "InpAblDisableHourPins": True,
            "InpAblDisablePricePins": True,
            "InpAblDisableSlots": True,
        },
    },
    "A5_core_only": {
        "label": "A5 structural core only",
        "overrides": {"InpAblCoreOnly": True},
    },
}


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
    return x


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"expected one anchor, found {count}: {old[:160]!r}")
    return source.replace(old, new, 1)


def insert_after_function_open(source: str, name: str, code: str) -> str:
    pattern = re.compile(rf"((?:bool|double|int|void)\s+{re.escape(name)}\s*\([^{{]*\)\s*\{{)", re.S)
    match = pattern.search(source)
    if not match:
        raise RuntimeError(f"function not found for guard insertion: {name}")
    start = match.end()
    if code.strip() in source[start : start + 500]:
        return source
    return source[:start] + "\n" + code.rstrip() + "\n" + source[start:]


def generate_ablation_ea() -> dict[str, Any]:
    source = ORIGINAL.read_text(encoding="utf-8")
    original_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()

    source = replace_once(
        source,
        "input bool   InpWriteSessionSummaryCSV = true;\nconst bool   InpWriteResearchTelemetryCSV = false;",
        """input bool   InpWriteSessionSummaryCSV = true;
input bool   InpAblDisableHourPins = false;    // exp2810: disable exact hour-of-day coordinate gates
input bool   InpAblDisablePricePins = false;   // exp2810: disable absolute price-coordinate families
input bool   InpAblDisableSlots = false;       // exp2810: disable slot/cluster/basket families
input bool   InpAblCoreOnly = false;           // exp2810: structural SMC core only
const bool   InpWriteResearchTelemetryCSV = false;""",
    )
    source = replace_once(
        source,
        "#define SETUP_SELL        1\n\n//-- Enums",
        """#define SETUP_SELL        1

bool AblHourPinsActive() { return !InpAblCoreOnly && !InpAblDisableHourPins; }
bool AblPricePinsActive() { return !InpAblCoreOnly && !InpAblDisablePricePins; }
bool AblSlotsActive() { return !InpAblCoreOnly && !InpAblDisableSlots; }
bool AblCoordinateLayersActive()
{
   return !InpAblCoreOnly &&
      !(InpAblDisableHourPins && InpAblDisablePricePins && InpAblDisableSlots);
}

//-- Enums""",
    )
    source = replace_once(
        source,
        "bool HourMatchesWindow(int hour, int minHour, int maxHour)\n{\n   if(minHour >= 0 && hour < minHour) return false;",
        "bool HourMatchesWindow(int hour, int minHour, int maxHour)\n{\n   if(!AblHourPinsActive()) return true;\n   if(minHour >= 0 && hour < minHour) return false;",
    )

    bool_slot = [
        "Exp1015InvalidBuyAdmissionMatches",
        "Exp1015InvalidSellAdmissionMatches",
        "Exp1050LowAtrBasketMatches",
        "Exp1050LowAtrSlotExact",
        "Exp1025SlotMatches",
        "Exp1083HighRunnerBasketMatches",
        "Exp1083HighRunnerSlotMatches",
        "Exp1085CappedND1416Matches",
        "Exp1092ND1618EntryATRMatches",
        "Exp1095SellRepl1314Matches",
        "Exp1097SellND67HighATRMatches",
        "Exp1099SellRepl1212LowOvershootMatches",
        "Exp1105SellRepl1213PostRepairMatches",
        "Exp1107BuyND1820RunnerMatches",
        "Exp1109MicroScalperMatches",
        "Exp1111SellRepl1313DDRepairMatches",
        "Exp1114Repl1414BuyTightMatches",
        "Exp1114Repl1414SellHighMatches",
        "Exp1114Repl1414SellLowMatches",
        "Exp1114Repl1414StackMatches",
        "Exp1116FreshSourceMatches",
        "Exp1120ComboRepl2222ND1516Matches",
        "Exp1122CrossWindowProfitMatches",
        "Exp1126Buy2323Matches",
        "Exp1126Sell1313Matches",
        "Exp1126Buy1011Matches",
        "Exp1126ComboStackMatches",
        "Exp1129ND1112RepairMatches",
        "Exp1130Repl1212PreRepairMatches",
        "Exp1130Repl1111RTRepairMatches",
        "Exp1130PreRepairStackMatches",
        "Exp1132HighMFE2026Matches",
        "Exp1138BuyRepl01ATRRepairMatches",
        "Exp1138SellND02AddonMatches",
        "Exp1138ATRRepairMatches",
        "Exp1145BuyND1112ATRRepairMatches",
        "Exp1025InvalidatedBasketMatches",
        "Exp1074BlockWeakExp1025OverlapBuy",
        "Exp1068Buy2223MaxPositionBypass",
    ]
    bool_price = [
        "Exp1147SellRepl56PriceRegimeMatches",
        "Exp1160PreBuyRepl1313Matches",
        "Exp1161PreSellMatches",
        "Exp1162FreshPreBinMatches",
        "Exp1183LowPriceCFMatches",
        "Exp1192CFMatches",
        "Exp1239BroadPreBinMatches",
        "Exp1259PortfolioMatches",
        "Exp1371PortfolioMatches",
    ]
    double_slot = [
        "Exp1145BuyND1112Lot",
        "Exp1145BuyND1112SLPips",
        "Exp1145BuyND1112TPPips",
        "Exp1378Exp1280TPPips",
    ]
    double_price = [
        "Exp1160PreBuyRepl1313Lot",
        "Exp1160PreBuyRepl1313SLPips",
        "Exp1160PreBuyRepl1313TPPips",
        "Exp1161PreSellLot",
        "Exp1161PreSellSLPips",
        "Exp1161PreSellTPPips",
        "Exp1162FreshPreLot",
        "Exp1162FreshPreSLPips",
        "Exp1162FreshPreTPPips",
        "Exp1183LowPriceCFLot",
        "Exp1183LowPriceCFSLPips",
        "Exp1183LowPriceCFTPPips",
        "Exp1192CFLot",
        "Exp1192CFSLPips",
        "Exp1192CFTPPips",
        "Exp1239BroadPreLot",
        "Exp1239BroadPreSLPips",
        "Exp1239BroadPreTPPips",
        "Exp1259PortfolioLot",
        "Exp1259PortfolioSLPips",
        "Exp1259PortfolioTPPips",
        "Exp1371PortfolioLot",
        "Exp1371PortfolioSLPips",
        "Exp1371PortfolioTPPips",
    ]
    int_price = ["Exp1192CFGroupId", "Exp1259PortfolioGroupId", "Exp1371PortfolioGroupId"]

    for fn in bool_slot:
        source = insert_after_function_open(source, fn, "   if(!AblSlotsActive()) return false;")
    for fn in bool_price:
        source = insert_after_function_open(source, fn, "   if(!AblPricePinsActive()) return false;")
    for fn in double_slot:
        source = insert_after_function_open(source, fn, "   if(!AblSlotsActive()) return 0.0;")
    for fn in double_price:
        source = insert_after_function_open(source, fn, "   if(!AblPricePinsActive()) return 0.0;")
    for fn in int_price:
        source = insert_after_function_open(source, fn, "   if(!AblPricePinsActive()) return 0;")

    # Core-only and all-coordinate-off guards: keep the structural lifecycle, remove
    # re-entry/add-on/split/source families without touching their default A0 logic.
    core_false = [
        "UseBuySelectiveLot",
        "UseSellSelectiveLot",
        "UseInvalidatedBuyEntry",
        "UseInvalidatedSellEntry",
        "ExecuteMitigationFlipEntry",
        "Exp1333TryOpenSupportReclaim",
        "Exp1663TryOpenLegacySupportReclaim",
        "TryDeferredBuyMFERetry",
        "TryBuyMFEAddOn",
        "TryBuyMFESecondAddOn",
        "TrySellMFEAddOn",
        "TryBuyExitReversalSell",
        "TrySellExitReversalBuy",
    ]
    for fn in core_false:
        source = insert_after_function_open(source, fn, "   if(!AblCoordinateLayersActive()) return false;")
    source = insert_after_function_open(source, "BuildSplitLots", "   if(!AblCoordinateLayersActive()) return false;")
    source = insert_after_function_open(source, "Exp1637TryOpenMicro", "   if(!AblCoordinateLayersActive()) return;")
    source = insert_after_function_open(source, "Exp1546ManageSessionDeferredRetry", "   if(!AblCoordinateLayersActive()) return;")
    source = insert_after_function_open(source, "Exp1421ManageDeferredSplits", "   if(!AblCoordinateLayersActive()) return;")

    # Dynamic block slots are exact entry/sweep-hour coordinate gates; disable with hour pins.
    source = insert_after_function_open(source, "BlockBuyDynamicSlotMatches", "   if(!AblHourPinsActive()) return false;")
    source = insert_after_function_open(source, "BlockSellDynamicSlotMatches", "   if(!AblHourPinsActive()) return false;")

    ABLATED.write_text(source, encoding="utf-8")
    return {
        "original": str(ORIGINAL.relative_to(ROOT)),
        "ablation": str(ABLATED.relative_to(ROOT)),
        "original_sha256": original_sha,
        "ablation_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "switches": [
            "InpAblDisableHourPins",
            "InpAblDisablePricePins",
            "InpAblDisableSlots",
            "InpAblCoreOnly",
        ],
        "input_count": r5.input_count(ABLATED),
        "a6_coordinate_only": "not meaningful: coordinate families gate/size/re-enter around structural lifecycle and do not form standalone entries.",
    }


def compile_ea(source: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["scripts/compile_ea.sh", str(source.relative_to(ROOT))],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stdout + "\n" + result.stderr
    return {
        "source": str(source.relative_to(ROOT)),
        "returncode": result.returncode,
        "clean": result.returncode == 0 and "Result: 0 errors, 0 warnings" in output,
        "tail": output[-6000:],
    }


def fixed_inputs(source: Path, overrides: dict[str, Any] | None = None) -> dict[str, str]:
    values = r5.input_defaults(source)
    for key, value in (overrides or {}).items():
        values[key] = str(value).lower() if isinstance(value, bool) else str(value)
    return {key: f"{value}||{value}||0||{value}||N" for key, value in values.items()}


def write_ini(path: Path, *, expert: str, source: Path, window: tuple[str, str, str], deposit: int, overrides: dict[str, Any] | None = None) -> None:
    from_date, to_date, model = window
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    with r5.TEMPLATE_INI.open(encoding="utf-8") as handle:
        parser.read_file(handle)
    parser.set("Tester", "Expert", expert)
    parser.set("Tester", "Symbol", "XAUUSDm")
    parser.set("Tester", "Period", "M5")
    parser.set("Tester", "Deposit", str(deposit))
    parser.set("Tester", "Currency", "AED")
    parser.set("Tester", "Leverage", "200")
    parser.set("Tester", "Model", model)
    parser.set("Tester", "Optimization", "0")
    parser.set("Tester", "FromDate", from_date)
    parser.set("Tester", "ToDate", to_date)
    parser.set("Tester", "Report", f"run_{path.stem}")
    parser.set("Tester", "ReplaceReport", "1")
    parser.set("Tester", "ShutdownTerminal", "1")
    parser.set("Tester", "Visual", "0")
    if parser.has_section("TesterInputs"):
        parser.remove_section("TesterInputs")
    parser.add_section("TesterInputs")
    for key, value in fixed_inputs(source, overrides).items():
        parser.set("TesterInputs", key, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\r\n") as handle:
        parser.write(handle, space_around_delimiters=False)


def valid_summary(summary: Path) -> bool:
    if not summary.exists():
        return False
    try:
        data = json.loads(summary.read_text(encoding="utf-8"))
    except Exception:
        return False
    smc = data.get("validation", {}).get("smc", {})
    return data.get("outcome") == "success" or (smc.get("ok") and smc.get("trade_rows", 0) >= 0)


def run_backtest(run_id: str, expert: str, source: Path, window: tuple[str, str, str], deposit: int, timeout: int, overrides: dict[str, Any] | None = None, force: bool = False) -> Path:
    ini = CONFIG_DIR / f"{run_id}.ini"
    write_ini(ini, expert=expert, source=source, window=window, deposit=deposit, overrides=overrides)
    summary = ROOT / "experiments" / "mt5_native" / f"{run_id}_summary.json"
    if valid_summary(summary) and not force:
        print(f"skip existing {run_id}", flush=True)
        return summary
    result = subprocess.run(
        [sys.executable, "scripts/run_mt5_ini_backtest.py", str(ini), "--run-id", run_id, "--timeout", str(timeout), "--multi-agent-capture"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 and not valid_summary(summary):
        raise RuntimeError(f"{run_id} failed rc={result.returncode}\n{result.stdout[-8000:]}\n{result.stderr[-8000:]}")
    return summary


def csv_path(summary_path: Path, name: str) -> Path | None:
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    rel = data.get("artifact_paths", {}).get("csvs", {}).get(name)
    return (ROOT / rel) if rel and not str(rel).startswith("/") else (Path(rel) if rel else None)


def read_run_csv(summary_path: Path, name: str) -> pd.DataFrame:
    path = csv_path(summary_path, name)
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def equity_stats(equity: pd.DataFrame, deposit: int) -> dict[str, Any]:
    if equity.empty:
        return {"max_dd_pct": 0.0, "max_dd_time": None, "intra_dd_pct": 0.0}
    eq = pd.to_numeric(equity.get("equity", pd.Series(dtype=float)), errors="coerce").ffill().fillna(float(deposit))
    peak = eq.cummax()
    dd = ((peak - eq) / peak.replace(0, np.nan) * 100.0).fillna(0.0)
    dd_idx = int(dd.idxmax()) if len(dd) else 0
    bal = pd.to_numeric(equity.get("balance", pd.Series(dtype=float)), errors="coerce").ffill()
    openpos = pd.to_numeric(equity.get("open_positions", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    intra = 0.0
    mask = (openpos > 0) & (bal > 0)
    if mask.any():
        intra = float(((bal[mask] - eq[mask]) / bal[mask] * 100.0).clip(lower=0).max())
    return {
        "max_dd_pct": round(float(dd.max()), 6),
        "max_dd_time": str(equity.iloc[dd_idx].get("datetime")) if len(equity) else None,
        "intra_dd_pct": round(intra, 6),
    }


def daily_series(trades: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    s = datetime.strptime(start, "%Y.%m.%d").date()
    e = datetime.strptime(end, "%Y.%m.%d").date() - timedelta(days=1)
    idx = pd.date_range(s, e, freq="D")
    series = pd.Series(0.0, index=idx)
    if not trades.empty and "datetime" in trades and "profit" in trades:
        dt = pd.to_datetime(trades["datetime"], errors="coerce")
        profit = pd.to_numeric(trades["profit"], errors="coerce").fillna(0.0)
        grouped = profit.groupby(dt.dt.floor("D")).sum()
        for k, v in grouped.items():
            if pd.notna(k) and k in series.index:
                series.loc[k] += float(v)
    return pd.DataFrame({"date": series.index.date.astype(str), "net_pnl": series.values})


def metrics(summary_path: Path, window: tuple[str, str, str], variant: str, window_name: str, deposit: int = DEPOSIT) -> tuple[dict[str, Any], pd.DataFrame]:
    trades = read_run_csv(summary_path, "AutoResearch_SMC_trades.csv")
    equity = read_run_csv(summary_path, "AutoResearch_SMC_equity.csv")
    profits = pd.to_numeric(trades.get("profit", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    wins = profits[profits > 0]
    losses = profits[profits < 0]
    profit = float(profits.sum())
    eqs = equity_stats(equity, deposit)
    expectancy = float(profits.mean()) if len(profits) else 0.0
    pf = float(wins.sum() / -losses.sum()) if float(-losses.sum()) > 0 else (float("inf") if float(wins.sum()) > 0 else 0.0)
    wr = float((profits > 0).mean() * 100.0) if len(profits) else 0.0
    ds = daily_series(trades, window[0], window[1])
    daily_std = float(ds["net_pnl"].std(ddof=1)) if len(ds) > 1 else 0.0
    daily_sharpe = float(ds["net_pnl"].mean() / daily_std * math.sqrt(252.0)) if daily_std > 0 else 0.0
    by_year = {}
    by_month = {}
    long_short = {}
    concentration = {"top_positive_month_share_pct": None, "top_positive_year_share_pct": None}
    if not trades.empty:
        dt = pd.to_datetime(trades["datetime"], errors="coerce")
        tr = trades.copy()
        tr["_profit"] = profits
        tr["_year"] = dt.dt.year
        tr["_month"] = dt.dt.strftime("%Y-%m")
        for y, grp in tr.groupby("_year", dropna=True):
            p = pd.to_numeric(grp["_profit"], errors="coerce").fillna(0.0)
            by_year[str(int(y))] = {
                "profit_aed": round(float(p.sum()), 2),
                "trades": int(len(grp)),
                "pf": round(float(p[p > 0].sum() / -p[p < 0].sum()), 6) if float(-p[p < 0].sum()) > 0 else None,
            }
        for m, grp in tr.groupby("_month", dropna=True):
            p = pd.to_numeric(grp["_profit"], errors="coerce").fillna(0.0)
            by_month[str(m)] = {
                "profit_aed": round(float(p.sum()), 2),
                "trades": int(len(grp)),
                "pf": round(float(p[p > 0].sum() / -p[p < 0].sum()), 6) if float(-p[p < 0].sum()) > 0 else None,
            }
        if "direction" in tr:
            for direction, grp in tr.groupby("direction", dropna=False):
                p = pd.to_numeric(grp["_profit"], errors="coerce").fillna(0.0)
                long_short[str(direction)] = {
                    "profit_aed": round(float(p.sum()), 2),
                    "trades": int(len(grp)),
                    "pf": round(float(p[p > 0].sum() / -p[p < 0].sum()), 6) if float(-p[p < 0].sum()) > 0 else None,
                }
        pos_month = [v["profit_aed"] for v in by_month.values() if v["profit_aed"] > 0]
        pos_year = [v["profit_aed"] for v in by_year.values() if v["profit_aed"] > 0]
        if sum(pos_month) > 0:
            concentration["top_positive_month_share_pct"] = round(max(pos_month) / sum(pos_month) * 100.0, 6)
        if sum(pos_year) > 0:
            concentration["top_positive_year_share_pct"] = round(max(pos_year) / sum(pos_year) * 100.0, 6)
    row = {
        "variant": variant,
        "window": window_name,
        "summary": str(summary_path.relative_to(ROOT)),
        "profit_aed": round(profit, 2),
        "pf": round(pf, 6) if math.isfinite(pf) else None,
        "expectancy_aed": round(expectancy, 6),
        "trades": int(len(trades)),
        "win_rate_pct": round(wr, 6),
        "max_dd_pct": eqs["max_dd_pct"],
        "max_dd_time": eqs["max_dd_time"],
        "intra_dd_pct": eqs["intra_dd_pct"],
        "return_per_dd": round(profit / eqs["max_dd_pct"], 6) if eqs["max_dd_pct"] > 0 else 0.0,
        "daily_sharpe_aed": round(daily_sharpe, 6),
        "by_year": by_year,
        "by_month": by_month,
        "long_short": long_short,
        "concentration": concentration,
    }
    return row, ds


def compare_trade_for_trade(orig_summary: Path, copy_summary: Path) -> dict[str, Any]:
    a = read_run_csv(orig_summary, "AutoResearch_SMC_trades.csv")
    b = read_run_csv(copy_summary, "AutoResearch_SMC_trades.csv")
    cols = [
        "datetime",
        "entry_time",
        "direction",
        "entry_price",
        "exit_price",
        "profit",
        "actual_lot",
        "lot_source",
    ]
    missing = [c for c in cols if c not in a.columns or c not in b.columns]
    if missing:
        cols = [c for c in cols if c in a.columns and c in b.columns]
    same_rows = len(a) == len(b)
    exact = same_rows
    max_profit_diff = 0.0
    mismatch_index = None
    if same_rows and cols:
        for idx, (ra, rb) in enumerate(zip(a[cols].astype(str).to_dict("records"), b[cols].astype(str).to_dict("records"))):
            if ra != rb:
                exact = False
                mismatch_index = idx
                break
        pa = pd.to_numeric(a.get("profit", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        pb = pd.to_numeric(b.get("profit", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
        max_profit_diff = float((pa - pb).abs().max()) if len(pa) and len(pa) == len(pb) else 0.0
    else:
        exact = False
    return {
        "original_summary": str(orig_summary.relative_to(ROOT)),
        "copy_summary": str(copy_summary.relative_to(ROOT)),
        "original_trades": int(len(a)),
        "copy_trades": int(len(b)),
        "columns_compared": cols,
        "trade_for_trade_exact": bool(exact),
        "mismatch_index": mismatch_index,
        "max_profit_diff": round(max_profit_diff, 10),
        "original_profit": round(float(pd.to_numeric(a.get("profit", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()), 2),
        "copy_profit": round(float(pd.to_numeric(b.get("profit", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()), 2),
    }


def moving_block_bootstrap(diff: np.ndarray, block_len: int, reps: int, seed: int) -> dict[str, Any]:
    n = len(diff)
    if n == 0:
        return {"point": 0.0, "ci95": [0.0, 0.0], "p_gt_0": None}
    rng = np.random.default_rng(seed)
    starts = np.arange(n)
    totals = np.empty(reps)
    blocks_needed = int(math.ceil(n / block_len))
    for i in range(reps):
        pieces = []
        chosen = rng.choice(starts, size=blocks_needed, replace=True)
        for s in chosen:
            idx = (np.arange(s, s + block_len) % n)
            pieces.append(diff[idx])
        sample = np.concatenate(pieces)[:n]
        totals[i] = sample.sum()
    return {
        "point": round(float(diff.sum()), 6),
        "ci95": [round(float(np.percentile(totals, 2.5)), 6), round(float(np.percentile(totals, 97.5)), 6)],
        "p_gt_0": round(float((totals > 0).mean()), 6),
        "block_len_days": block_len,
        "reps": reps,
        "seed": seed,
    }


def log_row(payload: dict[str, Any]) -> None:
    row = {
        "id": EXP_ID,
        "date": date.today().isoformat(),
        "era": "honest_core_v2_forensics",
        "phase": "quant_addendum_phase2",
        "category": "validation",
        "hypothesis": "Controlled switches on an exp1801 copy attribute production profit to coordinate layers versus the structural SMC core using paired daily-PnL ablations.",
        "baseline_id": "exp_1801",
        "decision": "observe",
        "why": "Measurement-only controlled ablation; causal interpretation is in the report and bootstrap CIs, no candidate promoted.",
        "metrics": payload.get("headline_metrics", {}),
        "artifact": str(DOC.relative_to(ROOT)),
        "surprise": payload.get("surprise", ""),
        "next": "Claude audits EA-copy diff, A0 parity, and block-bootstrap attribution before any conclusion.",
        "git_ref": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, capture_output=True).stdout.strip(),
    }
    existing = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    lines = [line for line in existing.splitlines() if line.strip()]
    if any(json.loads(line).get("id") == EXP_ID for line in lines):
        LOG.write_text("\n".join(line for line in lines if json.loads(line).get("id") != EXP_ID) + "\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(clean(row), sort_keys=True) + "\n")


def write_report(payload: dict[str, Any]) -> None:
    def fmt(x: Any) -> str:
        if x is None:
            return "NA"
        if isinstance(x, float):
            return f"{x:.2f}"
        return str(x)

    lines: list[str] = []
    lines.append("# exp2810 - exp1801 Controlled Block Ablation Phase 2")
    lines.append("")
    lines.append(f"Date: {date.today().isoformat()}")
    lines.append("")
    lines.append("## Build + Parity")
    lines.append("")
    lines.append(f"- Original: `{payload['build']['original']}`")
    lines.append(f"- Ablation copy: `{payload['build']['ablation']}`")
    lines.append(f"- Original SHA256: `{payload['build']['original_sha256']}`")
    lines.append(f"- Ablation SHA256: `{payload['build']['ablation_sha256']}`")
    lines.append(f"- Input count: {payload['build']['input_count']}")
    lines.append(f"- Original compile clean: {payload['compile']['original']['clean']}")
    lines.append(f"- Ablation compile clean: {payload['compile']['ablation']['clean']}")
    p = payload["parity"]
    lines.append(
        f"- A0 parity sample 2026-06-01..2026-06-21: exact={p['trade_for_trade_exact']}, "
        f"trades original/copy={p['original_trades']}/{p['copy_trades']}, "
        f"profit original/copy={p['original_profit']}/{p['copy_profit']}"
    )
    lines.append("")
    lines.append("A6 coordinate-only was not run: the coordinate layer is not a standalone entry engine; it gates, sizes, routes, and re-enters around the structural lifecycle.")
    lines.append("")
    lines.append("## Aggregate Results")
    lines.append("")
    for window_name in WINDOWS:
        lines.append(f"### {window_name}")
        lines.append("")
        lines.append("| Variant | Profit | PF | Exp/trade | Trades | MaxDD% | IntraDD% | R/DD | Daily Sharpe | dProfit vs A0 | dProfit vs A5 |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for variant in VARIANTS:
            row = payload["results"][window_name][variant]
            d0 = payload["deltas"][window_name][variant]["vs_A0_full_copy"]
            d5 = payload["deltas"][window_name][variant]["vs_A5_core_only"]
            lines.append(
                f"| {variant} | {fmt(row['profit_aed'])} | {fmt(row['pf'])} | {fmt(row['expectancy_aed'])} | "
                f"{row['trades']} | {fmt(row['max_dd_pct'])} | {fmt(row['intra_dd_pct'])} | {fmt(row['return_per_dd'])} | "
                f"{fmt(row['daily_sharpe_aed'])} | {fmt(d0['profit_aed'])} | {fmt(d5['profit_aed'])} |"
            )
        lines.append("")
    lines.append("## Paired Daily Block-Bootstrap CIs")
    lines.append("")
    lines.append(f"Method: circular moving-block bootstrap on aligned daily net-PnL differences, block length {BOOT_BLOCK_DAYS} calendar days, {BOOT_REPS} reps, seed {BOOT_SEED}. CI is for total PnL difference over the window.")
    lines.append("")
    lines.append("| Window | Variant | vs | Point | 95% CI | P(diff>0) |")
    lines.append("|---|---|---|---:|---:|---:|")
    for window_name, rows in payload["bootstrap"].items():
        for key, ci in rows.items():
            variant, base = key.split("__vs__")
            lines.append(f"| {window_name} | {variant} | {base} | {fmt(ci['point'])} | [{fmt(ci['ci95'][0])}, {fmt(ci['ci95'][1])}] | {fmt(ci['p_gt_0'])} |")
    lines.append("")
    lines.append("## Year / Month / Direction Detail")
    lines.append("")
    for window_name in WINDOWS:
        lines.append(f"### {window_name}")
        for variant in VARIANTS:
            row = payload["results"][window_name][variant]
            lines.append(f"- `{variant}` years={row['by_year']} months={row['by_month']} long_short={row['long_short']} concentration={row['concentration']}")
        lines.append("")
    lines.append("## Switch Semantics")
    lines.append("")
    lines.append("- `InpAblDisableHourPins`: shared hour-window matcher returns pass-through, and dynamic hour block slots are disabled. Direct literal hour checks outside shared helpers are not rewritten unless they are inside a gated slot/source family.")
    lines.append("- `InpAblDisablePricePins`: absolute-price source families and price-coordinate portfolio routers are disabled. Mechanical bid/ask execution and structural price math remain intact.")
    lines.append("- `InpAblDisableSlots`: Exp1025/1050/1145/1160/1162/1183/1192/1259/1280-style basket/slot families cannot admit entries or assign lots.")
    lines.append("- `InpAblCoreOnly`: disables the coordinate families plus invalidated re-entry, selective lots, split/add-on/reversal/support-reclaim side engines, leaving the structural sweep-reclaim-displacement-FVG-retest lifecycle.")
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    force = "--force" in sys.argv
    timeout_long = 14400
    timeout_rt = 7200
    timeout_sample = 3600
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    SERIES_DIR.mkdir(parents=True, exist_ok=True)

    build = generate_ablation_ea()
    compile_payload = {
        "original": compile_ea(ORIGINAL),
        "ablation": compile_ea(ABLATED),
    }
    if not compile_payload["original"]["clean"] or not compile_payload["ablation"]["clean"]:
        payload = {"build": build, "compile": compile_payload, "error": "compile failed"}
        SUMMARY.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise RuntimeError("compile failed; see summary JSON")

    orig_parity = run_backtest(
        "smc_exp2810_original_parity_sample",
        ORIGINAL_EXPERT,
        ORIGINAL,
        PARITY_WINDOW,
        DEPOSIT,
        timeout_sample,
        force=force,
    )
    copy_parity = run_backtest(
        "smc_exp2810_A0_copy_parity_sample",
        ABLATED_EXPERT,
        ABLATED,
        PARITY_WINDOW,
        DEPOSIT,
        timeout_sample,
        overrides=VARIANTS["A0_full_copy"]["overrides"],
        force=force,
    )
    parity = compare_trade_for_trade(orig_parity, copy_parity)
    if not parity["trade_for_trade_exact"]:
        payload = {"build": build, "compile": compile_payload, "parity": parity, "error": "A0 parity failed"}
        SUMMARY.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise RuntimeError(f"A0 parity failed: {parity}")

    results: dict[str, dict[str, Any]] = {w: {} for w in WINDOWS}
    series: dict[str, dict[str, pd.DataFrame]] = {w: {} for w in WINDOWS}
    run_summaries: dict[str, dict[str, str]] = {w: {} for w in WINDOWS}

    for window_name, window in WINDOWS.items():
        timeout = timeout_long if "long" in window_name else timeout_rt
        for variant, meta in VARIANTS.items():
            run_id = f"smc_exp2810_{variant}_{window_name}_dep{DEPOSIT}"
            summary = run_backtest(
                run_id,
                ABLATED_EXPERT,
                ABLATED,
                window,
                DEPOSIT,
                timeout,
                overrides=meta["overrides"],
                force=force,
            )
            row, ds = metrics(summary, window, variant, window_name, DEPOSIT)
            results[window_name][variant] = row
            series[window_name][variant] = ds
            run_summaries[window_name][variant] = str(summary.relative_to(ROOT))
            ds_path = SERIES_DIR / f"smc_exp2810_{variant}_{window_name}_daily.csv"
            ds.to_csv(ds_path, index=False)
            row["daily_series_csv"] = str(ds_path.relative_to(ROOT))
            print(f"{window_name} {variant}: profit={row['profit_aed']} trades={row['trades']} pf={row['pf']}", flush=True)

    deltas: dict[str, dict[str, Any]] = {}
    bootstrap: dict[str, dict[str, Any]] = {}
    for window_name in WINDOWS:
        deltas[window_name] = {}
        bootstrap[window_name] = {}
        a0 = results[window_name]["A0_full_copy"]
        a5 = results[window_name]["A5_core_only"]
        s0 = series[window_name]["A0_full_copy"]["net_pnl"].to_numpy(dtype=float)
        s5 = series[window_name]["A5_core_only"]["net_pnl"].to_numpy(dtype=float)
        for variant in VARIANTS:
            row = results[window_name][variant]
            deltas[window_name][variant] = {
                "vs_A0_full_copy": {
                    k: round(float(row.get(k, 0.0) or 0.0) - float(a0.get(k, 0.0) or 0.0), 6)
                    for k in ("profit_aed", "pf", "expectancy_aed", "trades", "max_dd_pct", "intra_dd_pct", "return_per_dd", "daily_sharpe_aed")
                },
                "vs_A5_core_only": {
                    k: round(float(row.get(k, 0.0) or 0.0) - float(a5.get(k, 0.0) or 0.0), 6)
                    for k in ("profit_aed", "pf", "expectancy_aed", "trades", "max_dd_pct", "intra_dd_pct", "return_per_dd", "daily_sharpe_aed")
                },
            }
            sv = series[window_name][variant]["net_pnl"].to_numpy(dtype=float)
            bootstrap[window_name][f"{variant}__vs__A0_full_copy"] = moving_block_bootstrap(sv - s0, BOOT_BLOCK_DAYS, BOOT_REPS, BOOT_SEED)
            bootstrap[window_name][f"{variant}__vs__A5_core_only"] = moving_block_bootstrap(sv - s5, BOOT_BLOCK_DAYS, BOOT_REPS, BOOT_SEED + 5)

    headline = {
        "a0_long_profit": results["long_2017_2026_model1"]["A0_full_copy"]["profit_aed"],
        "a4_long_delta_vs_a0": deltas["long_2017_2026_model1"]["A4_no_coordinate_layers"]["vs_A0_full_copy"]["profit_aed"],
        "a5_long_delta_vs_a0": deltas["long_2017_2026_model1"]["A5_core_only"]["vs_A0_full_copy"]["profit_aed"],
        "a0_rt_profit": results["rt_2026_jun21_model4"]["A0_full_copy"]["profit_aed"],
        "a4_rt_delta_vs_a0": deltas["rt_2026_jun21_model4"]["A4_no_coordinate_layers"]["vs_A0_full_copy"]["profit_aed"],
        "a5_rt_delta_vs_a0": deltas["rt_2026_jun21_model4"]["A5_core_only"]["vs_A0_full_copy"]["profit_aed"],
        "mt5_verified": True,
    }
    payload = {
        "id": EXP_ID,
        "build": build,
        "compile": compile_payload,
        "parity": parity,
        "variants": VARIANTS,
        "windows": WINDOWS,
        "deposit": DEPOSIT,
        "results": results,
        "deltas": deltas,
        "bootstrap": bootstrap,
        "run_summaries": run_summaries,
        "headline_metrics": headline,
        "surprise": "A0 parity passed; coordinate attribution measured with switch-gated copy and paired daily block bootstrap.",
        "report": str(DOC.relative_to(ROOT)),
        "summary_json": str(SUMMARY.relative_to(ROOT)),
    }
    SUMMARY.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload)
    log_row(payload)
    print(json.dumps(clean({"report": str(DOC), "summary": str(SUMMARY), "headline": headline}), indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
