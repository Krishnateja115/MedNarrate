import asyncio
import uuid
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from app.core.database import AsyncSessionLocal
from app.services.analysis_pipeline import run_analysis

async def main():
    report_id = uuid.UUID("1ebb5ebd2a864602a93914489e999123")
    print(f"Running analysis for {report_id}...")
    await run_analysis(report_id)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())
