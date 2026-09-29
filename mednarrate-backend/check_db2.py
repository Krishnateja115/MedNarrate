import asyncio, json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.analysis_translation import AnalysisTranslation
from sqlalchemy import select

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(bind=engine)

async def run():
    async with SessionLocal() as db:
        res = await db.execute(select(AnalysisTranslation))
        t = res.scalars().first()
        if t:
            print('MEDS:', json.dumps(t.medications_json))
            print('FINDINGS:', json.dumps(t.findings_json))
            print('SUMMARY:', t.patient_summary[:50])
        else:
            print('None')

asyncio.run(run())
