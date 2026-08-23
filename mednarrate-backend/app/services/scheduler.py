import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import AsyncSessionLocal
from app.models.medication_schedule import MedicationSchedule
from app.models.push_token import PushToken
from app.services.fcm_service import send_push_notification
from sqlalchemy import select
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def check_medication_reminders():
    logger.info("Checking medication reminders...")
    async with AsyncSessionLocal() as session:
        # Fetch due schedules (simplified for mock purposes)
        # In a real app we would check active=True and time matching
        stmt = select(MedicationSchedule).where(MedicationSchedule.is_active == True)
        result = await session.execute(stmt)
        schedules = result.scalars().all()
        
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        current_minute = now.minute

        for schedule in schedules:
            for reminder_time in schedule.reminder_times:
                try:
                    h, m = map(int, reminder_time.split(':'))
                    if h == current_hour and m == current_minute:
                        # Find push tokens for this user
                        token_stmt = select(PushToken).where(PushToken.user_id == schedule.user_id)
                        token_res = await session.execute(token_stmt)
                        tokens = token_res.scalars().all()
                        for t in tokens:
                            await send_push_notification(
                                t.token,
                                "Medication Reminder",
                                f"It's time to take {schedule.medication_name} ({schedule.dosage})",
                                {"type": "medication_reminder", "schedule_id": str(schedule.id)}
                            )
                except ValueError:
                    logger.error(f"Invalid reminder time format for schedule {schedule.id}: {reminder_time}")

def start_scheduler():
    scheduler.add_job(check_medication_reminders, 'cron', minute='*')
    scheduler.start()
    logger.info("Started medication reminder scheduler.")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Stopped medication reminder scheduler.")
