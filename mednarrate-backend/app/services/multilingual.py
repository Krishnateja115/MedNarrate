import logging
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
    
    # 1. Check cache
    stmt = select(ReportTranslation).where(
        ReportTranslation.report_id == report_id,
        ReportTranslation.language_code == target_language
    )
    result = await db.execute(stmt)
    cached = result.scalars().first()
    
    if cached:
        return cached.translated_text
        
    # 2. Translate using Gemini
    from app.services.llm_client import generate
    
    prompt = f"""Translate the following medical summary into {language_name}. 
Preserve all medical values and numbers exactly. 
Keep the structure (headings, bullet points). 
Use simple, everyday language understandable by a non-medical person. 
Do not add information not present in the original.

Original Summary:
{summary_text}
"""
    
    try:
        translated_text = await generate(prompt)
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise e
        
    # 3. Cache the translation
    translation = ReportTranslation(
        report_id=report_id,
        language_code=target_language,
        translated_text=translated_text
    )
    db.add(translation)
    await db.commit()
    
    return translated_text
