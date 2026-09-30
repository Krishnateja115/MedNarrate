from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.feature_flag import FeatureFlag
import hashlib

async def evaluate_flag(db: AsyncSession, flag_name: str, target_environment: str = "production", user_id: str = None) -> bool:
    stmt = select(FeatureFlag).where(FeatureFlag.name == flag_name)
    res = await db.execute(stmt)
    flag = res.scalar_one_or_none()
    
    if not flag:
        return False
        
    if not flag.enabled:
        return False
        
    if flag.target_environment != "all" and flag.target_environment != target_environment:
        return False
        
    if flag.rollout_percentage < 100:
        if not user_id:
            return False
        # Deterministic rollout
        hash_val = int(hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest(), 16)
        if (hash_val % 100) >= flag.rollout_percentage:
            return False
            
    return True
