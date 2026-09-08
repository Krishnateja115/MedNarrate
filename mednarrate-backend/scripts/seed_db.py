import asyncio
import os
import sys

# Add backend directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.models.medical_profile import MedicalProfile
from app.models.report import Report
from app.core.security import hash_password
from datetime import datetime, timezone

async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Create a test user
        hashed_password = hash_password("password123")
        test_user = User(
            email="test@mednarrate.com",
            hashed_password=hashed_password,
            full_name="Test User",
            is_active=True
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)

        # Create a medical profile
        profile = MedicalProfile(
            user_id=test_user.id,
            blood_group="O+",
            known_allergies="Penicillin",
            chronic_conditions="Hypertension"
        )
        session.add(profile)
        
        # Create sample reports
        reports = [
            Report(
                user_id=test_user.id,
                title="Annual Blood Test",
                report_type="LAB_RESULT",
                status="COMPLETED",
                original_text="Blood test results: Glucose 90 mg/dL, Cholesterol 180 mg/dL"
            ),
            Report(
                user_id=test_user.id,
                title="Knee MRI",
                report_type="IMAGING",
                status="COMPLETED",
                original_text="MRI of the right knee shows mild osteoarthritis."
            ),
            Report(
                user_id=test_user.id,
                title="Discharge Summary",
                report_type="DISCHARGE_SUMMARY",
                status="COMPLETED",
                original_text="Patient admitted for hypertension observation. Discharged with lisinopril."
            )
        ]
        session.add_all(reports)
        await session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
