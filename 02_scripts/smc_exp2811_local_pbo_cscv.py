#!/usr/bin/env python3
"""exp2811 local PBO/CSCV for CleanCoreV2A phase-2 selection grids.

This is deliberately labelled LOCAL: it tests only the 20-config exp2800 grid
and 18-config exp2802 grid, not the full research pipeline.
"""
from __future__ import annotations

import configparser
import html
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.smc_exp2800_clean_core_v2a_phase2_selection as exp2800
import scripts.smc_exp2802_clean_core_v2a_phase2r_selection as exp2802

CONFIG_DIR = ROOT / "experiments" / "mt5_native" / "configs" / "autoresearch_smc_candidate"
ARTIFACT_DIR = ROOT / "experiments" / "mt5_native"
REPORT_DIR = ARTIFACT_DIR / "reports"
ANALYSIS_DIR = ARTIFACT_DIR / "analysis"
OUT_DIR = ANALYSIS_DIR / "exp2811_pbo_cscv"
SUMMARY = ANALYSIS_DIR / "smc_exp2811_local_pbo_cscv_summary.json"
DOC = ROOT / "docs" / "honest_core_v2_exp2811_local_pbo_cscv_20260622.md"
LOG = ROOT / "experiments" / "experiment_log.jsonl"
MT5_ROOT = (
    Path.home()
    / "Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5"
)

DEPOSIT = 1600.0
TRAIN_START = pd.Timestamp("2024-01-01")
TRAIN_END = pd.Timestamp("2026-01-01")
DATE_INDEX = pd.date_range(TRAIN_START, TRAIN_END - pd.Timedelta(days=1), freq="D")


@dataclass(frozen=True)
class GridRun:
    grid: str
    name: str
    family: str
    changes: dict[str, str]
    stage: str | None = None

    @property
    def run_id(self) -> str:
        return f"smc_exp2811_{self.grid}_{self.name}_train_2024_2025_dep1600"


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


def read_common() -> dict[str, str]:
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    with exp2800.COMMON_SOURCE.open(encoding="utf-8") as handle:
        parser.read_file(handle)
    return dict(parser.items("Common"))


def fmt_input(value: str) -> str:
    return f"{value}||{value}||0||{value}||N"


def grid_runs() -> dict[str, list[GridRun]]:
    exp2800_runs = [
        GridRun("exp2800", v.name, v.family, dict(v.changes), None) for v in exp2800.variants()
    ]
    exit_rows = exp2802.exit_variants()
    selected_exit = next(v for v in exit_rows if v.name == "trail_d030_a045")
    exp2802_runs = [
        GridRun("exp2802", v.name, v.family, dict(v.changes), v.stage)
        for v in (exit_rows + exp2802.structural_variants(dict(selected_exit.changes)))
    ]
    return {"exp2800": exp2800_runs, "exp2802": exp2802_runs}


def inputs_for(run: GridRun) -> dict[str, str]:
    defaults = dict(exp2800.DEFAULT_INPUTS)
    defaults.update(run.changes)
    return defaults


def write_ini(run: GridRun) -> Path:
    common = read_common()
    path = CONFIG_DIR / f"{run.run_id}.ini"
    lines = [
        "[Common]",
        f"Login={common.get('Login', '')}",
        f"Server={common.get('Server', '')}",
        "Pass" + f"word={common.get('Password', '')}",
        "",
        "[Tester]",
        "Expert=CleanCoreV2A",
        "Symbol=XAUUSDm",
        "Period=M5",
        "Deposit=1600",
        "Currency=AED",
        "Leverage=200",
        "Model=1",
        "Optimization=0",
        "OptimizationCriterion=4",
        "UseLocal=1",
        "UseRemote=0",
        "UseCloud=0",
        "FromDate=2024.01.01",
        "ToDate=2026.01.01",
        "ForwardMode=0",
        f"Report=run_{run.run_id}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "Visual=0",
        "",
        "[TesterInputs]",
    ]
    for key, value in inputs_for(run).items():
        lines.append(f"{key}={fmt_input(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def valid_summary(summary: Path) -> bool:
    if not summary.exists():
        return False
    try:
        payload = json.loads(summary.read_text(encoding="utf-8"))
    except Exception:
        return False
    return payload.get("outcome") in {"success", "timeout"}


def run_mt5(run: GridRun, force: bool, timeout: int) -> Path:
    ini = write_ini(run)
    summary = ARTIFACT_DIR / f"{run.run_id}_summary.json"
    if valid_summary(summary) and not force:
        print(f"[reuse] {run.run_id}", flush=True)
        return summary
    cmd = [
        sys.executable,
        "scripts/run_mt5_safe_backtest.py",
        str(ini),
        "--run-id",
        run.run_id,
        "--timeout",
        str(timeout),
        "--multi-agent-capture",
    ]
    print(f"[run] {run.run_id}", flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)
    if not summary.exists():
        raise RuntimeError(f"missing summary after run: {summary}")
    return summary


def report_path(run_id: str) -> Path | None:
    candidates = [
        REPORT_DIR / f"run_{run_id}.htm",
        REPORT_DIR / f"{run_id}.htm",
        MT5_ROOT / f"run_{run_id}.htm",
        MT5_ROOT / f"{run_id}.htm",
    ]
    for path in candidates:
        if path.exists():
            return path
    globbed = sorted(REPORT_DIR.glob(f"*{run_id}*.htm")) + sorted(MT5_ROOT.glob(f"*{run_id}*.htm"))
    return globbed[-1] if globbed else None


def parse_num(raw: str | None) -> float:
    if raw is None:
        return 0.0
    cleaned = html.unescape(str(raw)).replace("\xa0", " ").replace(" ", "").replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    return float(match.group(0)) if match else 0.0


def html_text(path: Path) -> str:
    raw = path.read_bytes()
    text = raw.decode("utf-16", errors="ignore")
    if "<html" not in text.lower():
        text = raw.decode("utf-8", errors="ignore")
    return text


def report_value(text: str, label: str) -> str | None:
    match = re.search(re.escape(label) + r":</td>\s*<td[^>]*><b>([^<]+)</b>", text)
    return html.unescape(match.group(1)).strip() if match else None


def parse_pct(raw: str | None) -> float:
    if not raw:
        return 0.0
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)%", raw)
    return float(match.group(1)) if match else 0.0


def parse_report_metrics(run_id: str) -> dict[str, Any]:
    path = report_path(run_id)
    if path is None:
        return {"report": None, "report_exists": False}
    text = html_text(path)
    profit = parse_num(report_value(text, "Total Net Profit"))
    pf = parse_num(report_value(text, "Profit Factor"))
    trades = int(parse_num(report_value(text, "Total Trades")))
    balance_dd = parse_pct(report_value(text, "Balance Drawdown Maximal"))
    equity_dd = parse_pct(report_value(text, "Equity Drawdown Maximal"))
    return {
        "report": str(path),
        "report_exists": True,
        "profit": round(profit, 2),
        "profit_factor": round(pf, 6),
        "trades": trades,
        "max_dd_pct": balance_dd,
        "intra_dd_pct": equity_dd,
        "return_per_dd": round(profit / equity_dd, 6) if equity_dd > 0 else 0.0,
    }


def html_closed_deals(run_id: str) -> pd.DataFrame:
    path = report_path(run_id)
    if path is None:
        return pd.DataFrame(columns=["datetime", "profit"])
    text = html_text(path)
    idx = text.find("<b>Deals</b>")
    if idx < 0:
        return pd.DataFrame(columns=["datetime", "profit"])
    rows: list[dict[str, Any]] = []
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text[idx:], flags=re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", match.group(1), flags=re.S | re.I)
        if len(cells) < 13:
            continue
        values = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
        if values[4].lower() != "out":
            continue
        rows.append(
            {
                "datetime": pd.to_datetime(values[0], format="%Y.%m.%d %H:%M:%S", errors="coerce"),
                "profit": parse_num(values[10]),
                "comment": values[12],
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["datetime", "profit", "comment"])
    return out.dropna(subset=["datetime"])


def daily_series(run_id: str) -> pd.Series:
    deals = html_closed_deals(run_id)
    series = pd.Series(0.0, index=DATE_INDEX, name=run_id)
    if deals.empty:
        return series
    deals = deals[(deals["datetime"] >= TRAIN_START) & (deals["datetime"] < TRAIN_END)].copy()
    if deals.empty:
        return series
    by_day = deals.groupby(deals["datetime"].dt.normalize())["profit"].sum()
    series.loc[series.index.intersection(by_day.index)] = by_day.loc[series.index.intersection(by_day.index)]
    return series


def perf_stats(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {"profit": 0.0, "max_dd_pct": 0.0, "return_per_dd": 0.0}
    pnl = pd.Series(values).fillna(0.0)
    equity = DEPOSIT + pnl.cumsum()
    peak = equity.cummax()
    dd_pct = ((peak - equity) / peak.replace(0, np.nan) * 100.0).fillna(0.0)
    profit = float(pnl.sum())
    max_dd = float(dd_pct.max())
    return {
        "profit": profit,
        "max_dd_pct": max_dd,
        "return_per_dd": profit / max_dd if max_dd > 0 else (profit / 1e-9 if profit > 0 else profit),
    }


def block_labels(t: int, s: int) -> np.ndarray:
    edges = np.linspace(0, t, s + 1, dtype=int)
    labels = np.empty(t, dtype=int)
    for block in range(s):
        labels[edges[block] : edges[block + 1]] = block
    return labels


def cscv(matrix: pd.DataFrame, s: int) -> dict[str, Any]:
    data = matrix.to_numpy(dtype=float)
    t, n = data.shape
    labels = block_labels(t, s)
    half = s // 2
    rows: list[dict[str, Any]] = []
    all_blocks = tuple(range(s))
    for combo in combinations(all_blocks, half):
        is_mask = np.isin(labels, combo)
        oos_mask = ~is_mask
        is_stats = [perf_stats(data[is_mask, j]) for j in range(n)]
        oos_stats = [perf_stats(data[oos_mask, j]) for j in range(n)]
        is_rdd = np.array([x["return_per_dd"] for x in is_stats])
        oos_rdd = np.array([x["return_per_dd"] for x in oos_stats])
        oos_profit = np.array([x["profit"] for x in oos_stats])
        best_idx = int(np.argmax(is_rdd))
        order = np.argsort(oos_rdd)
        rank_ascending = int(np.where(order == best_idx)[0][0]) + 1  # 1=worst, N=best
        omega = rank_ascending / (n + 1.0)
        logit = math.log(omega / (1.0 - omega))
        median_oos = float(np.median(oos_rdd))
        rows.append(
            {
                "is_blocks": list(combo),
                "selected_config": matrix.columns[best_idx],
                "is_return_per_dd": float(is_rdd[best_idx]),
                "oos_return_per_dd": float(oos_rdd[best_idx]),
                "oos_profit": float(oos_profit[best_idx]),
                "oos_rank_ascending": rank_ascending,
                "oos_rank_pct": omega,
                "logit": logit,
                "under_oos_median": bool(oos_rdd[best_idx] < median_oos),
                "oos_loss": bool(oos_profit[best_idx] < 0),
                "degradation_return_per_dd": float(is_rdd[best_idx] - oos_rdd[best_idx]),
            }
        )
    logits = np.array([row["logit"] for row in rows], dtype=float)
    degrad = np.array([row["degradation_return_per_dd"] for row in rows], dtype=float)
    return {
        "S": s,
        "block_size_days_min": int(min(np.bincount(labels))),
        "block_size_days_max": int(max(np.bincount(labels))),
        "combinations": len(rows),
        "PBO": float(np.mean([row["under_oos_median"] for row in rows])) if rows else None,
        "P_OOS_loss": float(np.mean([row["oos_loss"] for row in rows])) if rows else None,
        "logit_summary": {
            "min": float(np.min(logits)) if logits.size else None,
            "p25": float(np.percentile(logits, 25)) if logits.size else None,
            "median": float(np.median(logits)) if logits.size else None,
            "p75": float(np.percentile(logits, 75)) if logits.size else None,
            "max": float(np.max(logits)) if logits.size else None,
        },
        "degradation_return_per_dd": {
            "mean": float(np.mean(degrad)) if degrad.size else None,
            "median": float(np.median(degrad)) if degrad.size else None,
            "p25": float(np.percentile(degrad, 25)) if degrad.size else None,
            "p75": float(np.percentile(degrad, 75)) if degrad.size else None,
        },
        "rows": rows,
    }


def run_grid(name: str, runs: list[GridRun], force: bool, timeout: int) -> dict[str, Any]:
    matrix_cols: dict[str, pd.Series] = {}
    run_rows = []
    for run in runs:
        summary = run_mt5(run, force=force, timeout=timeout)
        metrics = parse_report_metrics(run.run_id)
        series = daily_series(run.run_id)
        matrix_cols[run.name] = series.rename(run.name)
        run_rows.append(
            {
                "name": run.name,
                "family": run.family,
                "stage": run.stage,
                "changes": run.changes,
                "run_id": run.run_id,
                "summary": str(summary.relative_to(ROOT)),
                "metrics": metrics,
                "daily_profit_check": round(float(series.sum()), 2),
            }
        )
    matrix = pd.DataFrame(matrix_cols, index=DATE_INDEX).fillna(0.0)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix_path = OUT_DIR / f"{name}_daily_matrix.csv"
    matrix.to_csv(matrix_path, index_label="date")

    sensitivity = {str(s): cscv(matrix, s) for s in (6, 8, 10)}
    primary = sensitivity["8"]
    return {
        "grid": name,
        "N": int(matrix.shape[1]),
        "T": int(matrix.shape[0]),
        "daily_matrix": str(matrix_path.relative_to(ROOT)),
        "runs": run_rows,
        "primary_S": 8,
        "primary_reason": "S=8 gives quarter-sized blocks (~91 days) and 70 train/test combinations; S=6 and S=10 are reported as sensitivity for small-N stability.",
        "cscv": sensitivity,
    }


def md_metric_table(grid: dict[str, Any]) -> str:
    lines = [
        "| config | family/stage | profit | PF | trades | maxDD% | intraDD% | R/DD | daily check |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in grid["runs"]:
        m = row["metrics"]
        stage = row.get("stage") or row.get("family") or ""
        lines.append(
            f"| `{row['name']}` | {stage} | {m.get('profit', 0):.2f} | {m.get('profit_factor', 0):.2f} | "
            f"{m.get('trades', 0)} | {m.get('max_dd_pct', 0):.2f} | {m.get('intra_dd_pct', 0):.2f} | "
            f"{m.get('return_per_dd', 0):.4f} | {row['daily_profit_check']:.2f} |"
        )
    return "\n".join(lines)


def md_cscv_table(grid: dict[str, Any]) -> str:
    lines = [
        "| S | blocks | combos | PBO | P(OOS loss) | median logit | mean IS-OOS R/DD degradation |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s, result in grid["cscv"].items():
        lines.append(
            f"| {s} | {result['block_size_days_min']}-{result['block_size_days_max']} | {result['combinations']} | "
            f"{result['PBO']:.3f} | {result['P_OOS_loss']:.3f} | {result['logit_summary']['median']:.3f} | "
            f"{result['degradation_return_per_dd']['mean']:.3f} |"
        )
    return "\n".join(lines)


def write_doc(payload: dict[str, Any]) -> None:
    lines = [
        "# exp2811 Local PBO/CSCV",
        "",
        "Scope: **LOCAL** PBO/CSCV on the two CleanCoreV2A Phase-2 selection grids only. This is not a full-pipeline PBO and must not be read as a complete research-program deflator.",
        "",
        "Observation unit: daily closed-deal net PnL from the MT5 HTML deal ledger. No-trade days are zero-filled and all configs share the same calendar-day index. Because CleanCoreV2A does not emit the standard SMC equity CSV, the CSCV selection statistic uses closed-balance daily PnL and closed-balance DD, not tick-level intra-trade equity DD.",
        "",
    ]
    for key in ("exp2800", "exp2802"):
        grid = payload["grids"][key]
        primary = grid["cscv"][str(grid["primary_S"])]
        lines.extend(
            [
                f"## {key}",
                "",
                f"- N configs: `{grid['N']}`",
                f"- T daily observations: `{grid['T']}`",
                f"- Primary S: `{grid['primary_S']}`. {grid['primary_reason']}",
                f"- Daily matrix: `{grid['daily_matrix']}`",
                f"- Primary PBO: `{primary['PBO']:.3f}`",
                f"- Primary P(OOS loss): `{primary['P_OOS_loss']:.3f}`",
                "",
                "### CSCV Sensitivity",
                "",
                md_cscv_table(grid),
                "",
                "### Config Metrics",
                "",
                md_metric_table(grid),
                "",
            ]
        )
    lines.extend(
        [
            "## Limitations",
            "",
            "- This is local to 18-20 configs and does not deflate the thousands of broader historical experiments.",
            "- The observation count is daily, but trades are sparse; many days are zero across all configs.",
            "- HTML deal-ledger daily PnL is enough for CSCV rank testing, but it is not an intra-trade drawdown oracle.",
            "- PBO is diagnostic only; it is not used here to pick or re-pick any CleanCore config.",
            "",
            f"Summary JSON: `{SUMMARY}`",
        ]
    )
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def log_experiment(payload: dict[str, Any]) -> None:
    row = {
        "id": "exp_2811",
        "date": "2026-06-22",
        "era": "honest_core_v2_quant_addendum",
        "phase": "quant_addendum_phase3",
        "category": "analysis",
        "baseline_id": "CleanCoreV2A",
        "hypothesis": "Local CSCV/PBO quantifies overfit risk inside the two CleanCoreV2A phase-2 config grids using daily MT5 deal-ledger PnL per config.",
        "decision": "observe",
        "metrics": {
            "exp2800_N": payload["grids"]["exp2800"]["N"],
            "exp2800_T": payload["grids"]["exp2800"]["T"],
            "exp2800_primary_pbo": payload["grids"]["exp2800"]["cscv"]["8"]["PBO"],
            "exp2802_N": payload["grids"]["exp2802"]["N"],
            "exp2802_T": payload["grids"]["exp2802"]["T"],
            "exp2802_primary_pbo": payload["grids"]["exp2802"]["cscv"]["8"]["PBO"],
        },
        "artifact": str(DOC.relative_to(ROOT)),
        "summary_json": str(SUMMARY.relative_to(ROOT)),
        "why": "Measurement-only local PBO/CSCV; no config selected or promoted.",
        "next": "Use together with exp2812 permutation diagnostic; no new model implied.",
    }
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(clean(row), sort_keys=True) + "\n")


def main() -> int:
    force = "--force" in sys.argv
    timeout = 900
    for arg in sys.argv[1:]:
        if arg.startswith("--timeout="):
            timeout = int(arg.split("=", 1)[1])

    runs = grid_runs()
    payload = {
        "experiment": "exp2811_local_pbo_cscv",
        "label": "LOCAL",
        "ea": "ea/CleanCoreV2A.mq5",
        "window": "2024.01.01-2026.01.01",
        "model": 1,
        "deposit": DEPOSIT,
        "force": force,
        "observation": "daily closed-deal net PnL from MT5 HTML reports; no-trade days zero-filled",
        "grids": {
            name: run_grid(name, grid, force=force, timeout=timeout) for name, grid in runs.items()
        },
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_doc(payload)
    log_experiment(payload)
    print(f"[done] wrote {SUMMARY}")
    print(f"[done] wrote {DOC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
