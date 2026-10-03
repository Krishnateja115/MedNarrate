import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.models.analysis_translation import AnalysisTranslation

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        stmt = select(AnalysisTranslation).where(AnalysisTranslation.language == "hi")
        res = await session.execute(stmt)
        translations = res.scalars().all()
        with open("hi_translations.txt", "w", encoding="utf-8") as f:
            for t in translations:
                f.write(f"ID: {t.id} - Schema: {t.schema_version}\n")
                f.write(f"Summary: {t.patient_summary[:500]}\n")
                f.write(f"Findings: {t.findings_json}\n")
                f.write(f"UI Labels: {t.ui_labels}\n")
                f.write("="*40 + "\n")

asyncio.run(main())
