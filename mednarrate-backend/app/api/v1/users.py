from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.medical_profile import MedicalProfile
from app.schemas.user import UserWithProfileOut, UserUpdate

router = APIRouter()

@router.get("/me", response_model=UserWithProfileOut)
async def get_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicalProfile).where(MedicalProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    medical_profile = result.scalars().first()
    
    current_user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "preferred_language": current_user.preferred_language,
        "date_of_birth": current_user.date_of_birth,
        "gender": current_user.gender,
        "is_active": current_user.is_active,
        "medical_profile": medical_profile
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

    for field, value in update_data.items():
        setattr(current_user, field, value)

    stmt = select(MedicalProfile).where(MedicalProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    medical_profile = result.scalars().first()

    if medical_profile_data is not None:
        if medical_profile:
            for field, value in medical_profile_data.items():
                setattr(medical_profile, field, value)
        else:
            medical_profile = MedicalProfile(user_id=current_user.id, **medical_profile_data)
            db.add(medical_profile)

    await db.commit()
    await db.refresh(current_user)
    if medical_profile:
        await db.refresh(medical_profile)

    current_user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "preferred_language": current_user.preferred_language,
        "date_of_birth": current_user.date_of_birth,
        "gender": current_user.gender,
        "is_active": current_user.is_active,
        "medical_profile": medical_profile
    }
    return current_user_dict
