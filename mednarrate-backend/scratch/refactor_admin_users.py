import re

with open("app/api/v1/admin_users.py", "r") as f:
    content = f.read()

# 1. Remove the local definition of log_admin_action
pattern = re.compile(r"async def log_admin_action\([^)]+\):.*?await db\.commit\(\)\n*", re.DOTALL)
content = pattern.sub("", content)

# 2. Add import for canonical log_admin_action
content = content.replace("from app.models.user import User, UserRole\n", "from app.models.user import User, UserRole\nfrom app.services.audit import log_admin_action\n")

# 3. Use regex to replace ALL calls of log_admin_action
# The old calls look like:
# await log_admin_action(
#     db, admin_ctx, "ACTION", "resource", "id", {...}, request
# )
# or spread across lines.

def replace_log_admin_action(match):
    args = match.group(1).split(",", 6)
    db = args[0].strip()
    admin_ctx = args[1].strip()
    action = args[2].strip()
    resource_type = args[3].strip()
    resource_id = args[4].strip()
    
    # Metadata and request might be split in a weird way, let's just use string parsing
    rest = args[5] + "," + args[6]
    # find request which is usually at the end
    rest = rest.strip()
    if rest.endswith("request"):
        metadata = rest[:-len("request")].strip().rstrip(",")
        req = "request"
    else:
        metadata = rest
        req = "request"

    new_call = (f"await log_admin_action(\n"
                f"        db={db},\n"
                f"        action={action},\n"
                f"        actor_admin_id={admin_ctx}.user_id,\n"
                f"        resource_type={resource_type},\n"
                f"        resource_id={resource_id},\n"
                f"        metadata={metadata},\n"
                f"        request={req}\n"
                f"    )")
    
    return new_call

content = re.sub(r"await log_admin_action\((.*?)\)(?!\s*await db\.commit\(\))", lambda m: replace_log_admin_action(m) + "\n    await db.commit()", content, flags=re.DOTALL)
content = re.sub(r"await log_admin_action\((.*?)\)\s*await db\.commit\(\)", lambda m: replace_log_admin_action(m) + "\n    await db.commit()", content, flags=re.DOTALL)

with open("app/api/v1/admin_users.py", "w") as f:
    f.write(content)
