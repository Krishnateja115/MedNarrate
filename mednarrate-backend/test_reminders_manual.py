import asyncio

from app.core.database import AsyncSessionLocal
from app.models.medication_schedule import MedicationSchedule
from app.models.user import User


async def run_test():
    async with AsyncSessionLocal() as session:
        # get first user
        from sqlalchemy import select

        res = await session.execute(select(User).limit(1))
        user = res.scalars().first()
        if not user:
            print("No user found")
            return

        # Test 1: Manual Reminder
        med1 = MedicationSchedule(
            user_id=user.id,
            medication_name="Manual Med 1",
            dosage="500mg",
            frequency="Twice daily",
            times_of_day=["08:00", "20:00"],
        )
        session.add(med1)
        await session.commit()
        print(f"Created manual med: {med1.id}")


if __name__ == "__main__":
    asyncio.run(run_test())
