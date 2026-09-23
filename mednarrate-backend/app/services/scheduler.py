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
            for reminder_time in (schedule.times_of_day or []):
                try:
                    # Parse times like "08:00 AM" or "14:30"
                    from dateutil.parser import parse
                    dt = parse(reminder_time)
                    h, m = dt.hour, dt.minute
                    
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
                except Exception as e:
                    logger.error(f"Invalid reminder time format for schedule {schedule.id}: {reminder_time} - {e}")

def start_scheduler():
    scheduler.add_job(check_medication_reminders, 'cron', minute='*', id="medication_reminders")
    scheduler.start()
    logger.info("Started medication reminder scheduler.")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Stopped medication reminder scheduler.")

def get_all_jobs():
    """Returns a list of dictionaries detailing all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "status": "running" if scheduler.running else "stopped"
        })
    return jobs
