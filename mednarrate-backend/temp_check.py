import asyncio
import sys
from app.core.database import AsyncSessionLocal as SessionLocal
import app.models  # noqa: F401
from app.models.analysis_translation import AnalysisTranslation
from sqlalchemy import select

sys.stdout.reconfigure(encoding="utf-8")


async def main() -> None:
    async with SessionLocal() as db:
        res = await db.execute(select(AnalysisTranslation))
        rows = list(res.scalars())
        print("COUNT", len(rows))
        seen = set()
        for t in rows:
            if t.language in seen:
                continue
            seen.add(t.language)
            print("=" * 20, t.language)
            print(repr(t.patient_summary[:900]))


asyncio.run(main())
