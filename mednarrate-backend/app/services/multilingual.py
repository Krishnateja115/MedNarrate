import logging
import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report_translation import ReportTranslation

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi"
}

async def translate_report_summary(report_id: str, summary_text: str, target_language: str, db: AsyncSession) -> str:
    if target_language not in LANGUAGE_MAP:
        raise ValueError(f"Unsupported language code: {target_language}")
        
    language_name = LANGUAGE_MAP[target_language]
    
    report_uuid = uuid.UUID(str(report_id)) if not isinstance(report_id, uuid.UUID) else report_id

    # 1. Check cache
    stmt = select(ReportTranslation).where(
        ReportTranslation.report_id == report_uuid,
        ReportTranslation.language_code == target_language
    )
    result = await db.execute(stmt)
    cached = result.scalars().first()
    
    if cached:
        return cached.translated_text
        
    # 2. Translate using IndicTrans2
    from app.services.llm_orchestrator import translate_text_indic
    
    try:
        translated_text = await translate_text_indic(summary_text, target_language)
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise e
        
    # 3. Cache the translation
    translation = ReportTranslation(
        report_id=report_uuid,
        language_code=target_language,
        translated_text=translated_text
    )
    db.add(translation)
    await db.commit()
    
    return translated_text
