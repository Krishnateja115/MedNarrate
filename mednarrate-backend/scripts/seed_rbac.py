import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.admin import AdminRole, AdminPermission, AdminRolePermission, AdminRoleAssignment
from app.models.user import User

async def seed():
    async with AsyncSessionLocal() as session:
        # 1. Create or get super_admin permission
        stmt = select(AdminPermission).where(AdminPermission.name == "super_admin")
        perm = (await session.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name="super_admin", description="Full access to all systems")
            session.add(perm)
            await session.commit()
            await session.refresh(perm)
            print("Created super_admin permission.")

        # 2. Create or get Super Admin role
        stmt = select(AdminRole).where(AdminRole.name == "Super Admin")
        role = (await session.execute(stmt)).scalars().first()
        if not role:
            role = AdminRole(name="Super Admin", description="Administrator with full access")
            session.add(role)
            await session.commit()
            await session.refresh(role)
            print("Created Super Admin role.")

        # 3. Link permission to role
        stmt = select(AdminRolePermission).where(
            AdminRolePermission.role_id == role.id,
            AdminRolePermission.permission_id == perm.id
        )
        role_perm = (await session.execute(stmt)).scalars().first()
        if not role_perm:
            role_perm = AdminRolePermission(role_id=role.id, permission_id=perm.id)
            session.add(role_perm)
            await session.commit()
            print("Linked super_admin permission to Super Admin role.")

        # 4. Assign role to our seeded admin user
        stmt = select(User).where(User.email == "admin@mednarrate.com")
        admin_user = (await session.execute(stmt)).scalars().first()
        if admin_user:
            stmt = select(AdminRoleAssignment).where(
                AdminRoleAssignment.user_id == admin_user.id,
                AdminRoleAssignment.role_id == role.id
            )
            assignment = (await session.execute(stmt)).scalars().first()
            if not assignment:
                assignment = AdminRoleAssignment(user_id=admin_user.id, role_id=role.id)
                session.add(assignment)
                await session.commit()
                print("Assigned Super Admin role to admin@mednarrate.com.")
            else:
                print("admin@mednarrate.com already has Super Admin role.")
        else:
            print("Admin user not found. Did you run create_admin.py?")

if __name__ == "__main__":
    asyncio.run(seed())
