"""Summarise how long MedNarrate takes: API requests, report analysis, chat, LLMs.

Usage (from mednarrate-backend, venv active):

    python scripts/timing_report.py            # everything recorded so far
    python scripts/timing_report.py --hours 2  # only the last 2 hours
    python scripts/timing_report.py --tail 15  # also show the 15 slowest events

Sources:
  * logs/timing.jsonl            - written live by the server (HTTP, ANALYSIS, CHAT)
  * llm_diagnostic_events table  - one row per LLM call (provider, model, latency)
No prompts, report text or personal data is read or printed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.timing import timing_log_path  # noqa: E402


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, math.ceil(pct / 100 * len(ordered)) - 1))
    return ordered[rank]


def fmt_ms(ms: float) -> str:
    return f"{ms / 1000:.1f}s" if ms >= 1000 else f"{ms:.0f}ms"


def stats_row(label: str, values: list[float], extra: str = "") -> str:
    return (
        f"  {label:<44} n={len(values):<4} avg={fmt_ms(sum(values) / len(values)):>7} "
        f"p50={fmt_ms(percentile(values, 50)):>7} p95={fmt_ms(percentile(values, 95)):>7} "
        f"max={fmt_ms(max(values)):>7} {extra}"
    ).rstrip()


def load_events(since: datetime | None) -> list[dict]:
    path = timing_log_path()
    events: list[dict] = []
    for candidate in (path.with_suffix(".jsonl.1"), path):
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if since is not None:
                try:
                    when = datetime.fromisoformat(item["ts"])
                except (KeyError, ValueError):
                    continue
                if when < since:
                    continue
            events.append(item)
    return events


def report_events(events: list[dict], tail: int) -> None:
    if not events:
        print("No timing events yet. Start the backend, use the app, then run this again.")
        return

    analysis = [e for e in events if e["kind"] == "ANALYSIS"]
    print("\n== Report generation (whole pipeline, upload -> finished) ==")
    if analysis:
        print(stats_row("report_analysis", [e["total_ms"] for e in analysis]))
        stage_keys = sorted(
            {k for e in analysis for k in e if k.endswith("_ms") and k != "total_ms"}
        )
        print("  where the time goes (average per stage):")
        for key in stage_keys:
            vals = [e[key] for e in analysis if key in e]
            print(f"    {key[:-3]:<22} {fmt_ms(sum(vals) / len(vals)):>8}")
    else:
        print("  (none yet)")

    chat = [e for e in events if e["kind"] == "CHAT"]
    print("\n== AI chat (one answer) ==")
    if chat:
        by_name: dict[str, list[dict]] = defaultdict(list)
        for e in chat:
            by_name[e["name"]].append(e)
        for name, items in sorted(by_name.items()):
            print(stats_row(name, [e["total_ms"] for e in items]))
            llm = [e["llm_ms"] for e in items if "llm_ms" in e]
            if llm:
                print(f"    of which the LLM call averages {fmt_ms(sum(llm) / len(llm))}")
    else:
        print("  (none yet)")

    http = [e for e in events if e["kind"] == "HTTP"]
    print("\n== API requests (slowest endpoints by average) ==")
    if http:
        by_route: dict[str, list[float]] = defaultdict(list)
        for e in http:
            by_route[e["name"]].append(e["total_ms"])
        ranked = sorted(by_route.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:12]
        for name, vals in ranked:
            print(stats_row(name, vals))
    else:
        print("  (none yet)")

    if tail:
        print(f"\n== {tail} slowest events ==")
        for e in sorted(events, key=lambda x: -x["total_ms"])[:tail]:
            print(f"  {fmt_ms(e['total_ms']):>7}  {e['ts']}  {e['kind']:<8} {e['name']}")


async def report_llm(since: datetime | None) -> None:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.llm_telemetry import LLMDiagnosticEvent as Evt

    print("\n== LLM calls by provider / model (from llm_diagnostic_events) ==")
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(
                Evt.provider, Evt.model_name, Evt.status, Evt.latency_ms, Evt.error_category
            )
            if since is not None:
                stmt = stmt.where(Evt.timestamp >= since.replace(tzinfo=None))
            rows = (await session.execute(stmt)).all()
    except Exception as exc:  # DB not reachable / table missing
        print(f"  Could not read the database: {type(exc).__name__}")
        return
    if not rows:
        print("  (none yet)")
        return
    groups: dict[tuple[str, str], list] = defaultdict(list)
    for provider, model, status, latency, category in rows:
        groups[(provider, model or "-")].append((status, latency or 0.0, category))
    for (provider, model), items in sorted(groups.items()):
        ok = [lat for st, lat, _ in items if st == "success" and lat > 0]
        failed = [c or "error" for st, _, c in items if st != "success"]
        label = f"{provider} / {model}"
        if ok:
            print(stats_row(label, ok, f"failures={len(failed)}"))
        else:
            print(f"  {label:<44} n=0    no successful calls, failures={len(failed)}")
        if failed:
            kinds: dict[str, int] = defaultdict(int)
            for kind in failed:
                kinds[kind] += 1
            print("      failure kinds: " + ", ".join(f"{k}x{v}" for k, v in kinds.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hours", type=float, default=None, help="only the last N hours")
    parser.add_argument("--tail", type=int, default=10, help="show the N slowest events")
    args = parser.parse_args()
    since = (
        datetime.now(timezone.utc) - timedelta(hours=args.hours) if args.hours else None
    )
    print(f"Timing file: {timing_log_path()}")
    report_events(load_events(since), args.tail)
    asyncio.run(report_llm(since))


if __name__ == "__main__":
    main()
