from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.help_center import ArticleStatus, HelpArticle


STARTER_HELP_ARTICLES = [
    {
        "title": "Why is my report still processing?",
        "slug": "why-is-my-report-still-processing",
        "category": "Reports",
        "summary": "What the processing state means and what information to include when asking support for help.",
        "content": """MedNarrate processes an uploaded report before its analysis is available. Keep the report ID shown in the app and refresh the report after a short wait.

If the report remains in a processing state, open a support ticket and include the report ID. Support can inspect the processing diagnostics without requiring you to upload the report again. Do not paste private medical text into the ticket description.""",
    },
    {
        "title": "Understanding a MedNarrate report analysis",
        "slug": "understanding-report-analysis",
        "category": "Report Analysis",
        "summary": "How to read summaries and extracted findings without treating them as a diagnosis.",
        "content": """MedNarrate can extract text and generate plain-language summaries from supported medical reports. The analysis helps you review the document; it does not replace the original report or advice from a qualified clinician.

Check important values against the source report. If an extraction or summary appears incorrect, keep the report ID and contact support so the processing result can be investigated.""",
    },
    {
        "title": "Using AI chat with your report",
        "slug": "using-ai-chat-with-your-report",
        "category": "AI/Chat",
        "summary": "Practical guidance for asking questions and checking AI-generated answers.",
        "content": """Use the report chat to ask focused questions about information available in your MedNarrate report. Include the name of the test, section, or value you want explained.

AI responses can be incomplete or incorrect. Verify important details against the original report and ask a clinician before making medical decisions. If the chat fails, contact support with the request ID when one is displayed.""",
    },
    {
        "title": "Managing medication reminders",
        "slug": "managing-medication-reminders",
        "category": "Medication Reminders",
        "summary": "How reminder schedules and notification delivery work in MedNarrate.",
        "content": """Medication reminders use the schedules saved in MedNarrate and the notification settings on your device. Confirm that the medication schedule, time, and active state are correct.

If a reminder is not delivered, check that notifications are enabled for MedNarrate at both the app and device level. A reminder is not a substitute for medical instructions; contact your clinician when a prescription or schedule is unclear.""",
    },
    {
        "title": "Protecting privacy when contacting support",
        "slug": "protecting-privacy-when-contacting-support",
        "category": "Privacy",
        "summary": "Share identifiers support can use while avoiding unnecessary medical details.",
        "content": """When contacting support, share the report ID, ticket ID, or request ID shown by MedNarrate. Avoid copying full report text, passwords, access tokens, or other sensitive medical information into a ticket.

Administrative access to sensitive report content is restricted and audited. Support may ask for a specific identifier so the issue can be investigated through the protected administration tools.""",
    },
]


async def seed_help_center_if_empty(db: AsyncSession) -> int:
    """Add factual starter articles only when the Help Center has no content."""
    article_count = (await db.execute(select(func.count(HelpArticle.id)))).scalar_one()
    if article_count:
        return 0

    published_at = datetime.now(timezone.utc).replace(tzinfo=None)
    for starter in STARTER_HELP_ARTICLES:
        db.add(
            HelpArticle(
                **starter,
                status=ArticleStatus.published,
                created_by="system",
                published_at=published_at,
            )
        )
    await db.commit()
    return len(STARTER_HELP_ARTICLES)
