import logging
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.medication_schedule import MedicationSchedule
from app.models.push_token import PushToken
from app.services.notification_service import send_push_notification

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def check_and_send_medication_reminders():
    """Runs every minute to check if any active medications need a reminder right now."""
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    
    logger.info(f"Checking medication reminders for time: {current_time_str}")
    
    async with AsyncSessionLocal() as db:
        # Fetch active schedules
        stmt = select(MedicationSchedule).where(MedicationSchedule.is_active == True)
        result = await db.execute(stmt)
        schedules = result.scalars().all()
        
        for schedule in schedules:
            if current_time_str in schedule.times_of_day:
                # Fetch tokens for this user
                token_stmt = select(PushToken).where(PushToken.user_id == schedule.user_id)
                token_result = await db.execute(token_stmt)
                tokens = token_result.scalars().all()
                
                title = "Medication Reminder"
                body = f"Time to take {schedule.medication_name}"
                if schedule.dosage:
                    body += f" ({schedule.dosage})"
                if schedule.notes:
                    body += f"\nNote: {schedule.notes}"
                    
                for tk in tokens:
                    await send_push_notification(db, str(schedule.user_id), tk.device_token, title, body)

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(check_and_send_medication_reminders, 'cron', minute='*')
        scheduler.start()
        logger.info("Notification scheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Notification scheduler stopped.")
