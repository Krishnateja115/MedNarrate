from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.medical_profile import MedicalProfile
from app.models.doctor_profile import DoctorProfile
from app.models.caregiver_profile import CaregiverProfile
from app.schemas.user import UserWithProfileOut, UserUpdate

router = APIRouter()

@router.get("/me", response_model=UserWithProfileOut)
async def get_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicalProfile).where(MedicalProfile.user_id == current_user.id)
    medical_profile = (await db.execute(stmt)).scalars().first()
    
    doc_stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
    doctor_profile = (await db.execute(doc_stmt)).scalars().first()
    
    cg_stmt = select(CaregiverProfile).where(CaregiverProfile.user_id == current_user.id)
    caregiver_profile = (await db.execute(cg_stmt)).scalars().first()
    
    current_user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "preferred_language": current_user.preferred_language,
        "date_of_birth": current_user.date_of_birth,
        "gender": current_user.gender,
        "is_active": current_user.is_active,
        "medical_profile": medical_profile,
        "doctor_profile": doctor_profile,
        "caregiver_profile": caregiver_profile
    }
    return current_user_dict

@router.patch("/me", response_model=UserWithProfileOut)
async def update_users_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    medical_profile_data = update_data.pop("medical_profile", None)
    doctor_profile_data = update_data.pop("doctor_profile", None)
    caregiver_profile_data = update_data.pop("caregiver_profile", None)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    stmt = select(MedicalProfile).where(MedicalProfile.user_id == current_user.id)
    medical_profile = (await db.execute(stmt)).scalars().first()

    if medical_profile_data is not None:
        if medical_profile:
            for field, value in medical_profile_data.items():
                setattr(medical_profile, field, value)
        else:
            medical_profile = MedicalProfile(user_id=current_user.id, **medical_profile_data)
            db.add(medical_profile)
            
    doc_stmt = select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
    doctor_profile = (await db.execute(doc_stmt)).scalars().first()

    if doctor_profile_data is not None:
        if doctor_profile:
            for field, value in doctor_profile_data.items():
                setattr(doctor_profile, field, value)
        else:
            doctor_profile = DoctorProfile(user_id=current_user.id, **doctor_profile_data)
            db.add(doctor_profile)
            
    cg_stmt = select(CaregiverProfile).where(CaregiverProfile.user_id == current_user.id)
    caregiver_profile = (await db.execute(cg_stmt)).scalars().first()

    if caregiver_profile_data is not None:
        if caregiver_profile:
            for field, value in caregiver_profile_data.items():
                setattr(caregiver_profile, field, value)
        else:
            caregiver_profile = CaregiverProfile(user_id=current_user.id, **caregiver_profile_data)
            db.add(caregiver_profile)

    await db.commit()
    await db.refresh(current_user)
    if medical_profile: await db.refresh(medical_profile)
    if doctor_profile: await db.refresh(doctor_profile)
    if caregiver_profile: await db.refresh(caregiver_profile)

    current_user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "preferred_language": current_user.preferred_language,
        "date_of_birth": current_user.date_of_birth,
        "gender": current_user.gender,
        "is_active": current_user.is_active,
        "medical_profile": medical_profile,
        "doctor_profile": doctor_profile,
        "caregiver_profile": caregiver_profile,
    }
    return current_user_dict

@router.delete("/me", status_code=204)
async def delete_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.delete(current_user)
    await db.commit()
    return None
