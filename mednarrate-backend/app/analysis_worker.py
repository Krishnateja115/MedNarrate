"""Durable PostgreSQL-backed report worker; run separately from the API.

The /process endpoint marks reports as processing. This process scans those
rows, claims them with PostgreSQL advisory locks, and resumes them after a
worker crash. Locks prevent duplicate work across worker instances.
"""

import argparse
import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, engine
from app.models.report import ProcessingStatus, Report
from app.services.analysis_pipeline import run_analysis


logger = logging.getLogger(__name__)
WORKER_HEARTBEAT_KEY = "mednarrate:analysis-worker:heartbeat"


async def publish_heartbeat() -> None:
    """Let the API distinguish a live worker from a stopped container."""
    redis_url = os.environ.get("RATE_LIMIT_STORAGE_URI")
    if not redis_url or not redis_url.startswith("redis://"):
        return
    try:
        async with redis.from_url(
            redis_url, socket_connect_timeout=1, socket_timeout=1
        ) as client:
            await client.set(
                WORKER_HEARTBEAT_KEY,
                datetime.now(timezone.utc).isoformat(),
                ex=30,
            )
    except Exception:
        logger.warning("Could not publish report worker heartbeat")


def advisory_key(report_id: uuid.UUID) -> int:
    """Map UUID to a signed 64-bit PostgreSQL advisory-lock key."""
    value = report_id.int & ((1 << 64) - 1)
    return value if value < (1 << 63) else value - (1 << 64)


async def process_pending_once(limit: int = 25) -> int:
    """Claim and process at most ``limit`` pending reports in this sweep."""
    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            select(Report.id)
            .where(Report.processing_status == ProcessingStatus.processing)
            .order_by(Report.updated_at)
            .limit(limit)
        )
        ids = list(rows.scalars())

    processed = 0
    for report_id in ids:
        key = advisory_key(report_id)
        async with engine.connect() as connection:
            claimed = await connection.scalar(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
            )
            if not claimed:
                continue
            try:
                async with AsyncSessionLocal() as session:
                    current = await session.get(Report, report_id)
                    if (current is None or current.processing_status != ProcessingStatus.processing):
                        continue
                await run_analysis(report_id)
                processed += 1
            finally:
                await connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": key}
                )
    return processed


async def main(once: bool, interval_seconds: float) -> None:
    """Run one bounded sweep or continuously poll for queued reports."""
    while True:
        try:
            processed = await process_pending_once()
            await publish_heartbeat()
            logger.info("Processed %s queued reports in this sweep", processed)
        except Exception:
            logger.exception("Report worker sweep failed; will retry")
            if once:
                raise
        if once:
            return
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedNarrate report analysis worker")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=3.0)
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(arguments.once, arguments.interval))
