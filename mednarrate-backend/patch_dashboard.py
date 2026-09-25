import re

with open("app/api/v1/admin_dashboard.py", "r") as f:
    content = f.read()

# Add SupportTicket to imports
if "from app.models.support import SupportTicket, TicketStatus, TicketPriority" not in content:
    content = content.replace("from app.models.report_analysis import ReportAnalysis", "from app.models.report_analysis import ReportAnalysis\nfrom app.models.support import SupportTicket, TicketStatus, TicketPriority")

# Add new time windows
if "today_start = " in content and "this_week_start =" not in content:
    time_code = """    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(
        tzinfo=timezone.utc
    )
    this_week_start = today_start - timedelta(days=today_start.weekday())
    this_month_start = today_start.replace(day=1)"""
    content = content.replace("""    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(
        tzinfo=timezone.utc
    )""", time_code)

# Add new user metrics
if "active_users = (await db.execute(active_users_stmt)).scalar() or 0" in content and "new_users_today =" not in content:
    user_code = """    active_users_stmt = select(func.count(User.id)).where(User.is_active is True)
    active_users = (await db.execute(active_users_stmt)).scalar() or 0

    new_users_today = (await db.execute(select(func.count(User.id)).where(User.created_at >= today_start))).scalar() or 0
    new_users_this_week = (await db.execute(select(func.count(User.id)).where(User.created_at >= this_week_start))).scalar() or 0
    new_users_this_month = (await db.execute(select(func.count(User.id)).where(User.created_at >= this_month_start))).scalar() or 0
    suspended_users = (await db.execute(select(func.count(User.id)).where(User.is_active is False))).scalar() or 0"""
    content = content.replace("""    active_users_stmt = select(func.count(User.id)).where(User.is_active is True)
    active_users = (await db.execute(active_users_stmt)).scalar() or 0""", user_code)

# Add Reports This Week
if "reports_today = (await db.execute(reports_today_stmt)).scalar() or 0" in content and "reports_this_week =" not in content:
    reports_code = """    reports_today = (await db.execute(reports_today_stmt)).scalar() or 0
    reports_this_week = (await db.execute(select(func.count(Report.id)).where(Report.uploaded_at >= this_week_start))).scalar() or 0"""
    content = content.replace("""    reports_today = (await db.execute(reports_today_stmt)).scalar() or 0""", reports_code)

# Add Average Processing Time
if "total_processed = reports_failed + reports_completed" in content and "average_processing_time =" not in content:
    avg_code = """    avg_time_stmt = select(func.avg(Report.processing_time_ms)).where(Report.processing_time_ms.isnot(None), Report.uploaded_at >= time_window_start)
    avg_processing_time = (await db.execute(avg_time_stmt)).scalar() or 0.0

    total_processed = reports_failed + reports_completed"""
    content = content.replace("""    total_processed = reports_failed + reports_completed""", avg_code)

# Replace Support
if '"open_support_tickets": None' in content:
    support_code = """        "open_support_tickets": (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status.in_([TicketStatus.new, TicketStatus.triaged, TicketStatus.investigating, TicketStatus.waiting_user, TicketStatus.waiting_eng])))).scalar() or 0,
            "p1_tickets": (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status.not_in([TicketStatus.resolved, TicketStatus.closed]), SupportTicket.priority == TicketPriority.p1))).scalar() or 0,
            "p2_tickets": (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status.not_in([TicketStatus.resolved, TicketStatus.closed]), SupportTicket.priority == TicketPriority.p2))).scalar() or 0,
            "unassigned_tickets": (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status.not_in([TicketStatus.resolved, TicketStatus.closed]), SupportTicket.assigned_admin_id.is_(None)))).scalar() or 0,
            "waiting_for_user": (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status == TicketStatus.waiting_user))).scalar() or 0,
            "escalated": (await db.execute(select(func.count(SupportTicket.id)).where(SupportTicket.status == TicketStatus.waiting_eng))).scalar() or 0,"""
    content = content.replace('"open_support_tickets": None  # Not currently instrumented', support_code)

# Update return dict
if '"users": {"total_users": total_users, "active_users": active_users}' in content:
    content = content.replace(
        '"users": {"total_users": total_users, "active_users": active_users}',
        '"users": {"total_users": total_users, "active_users": active_users, "new_users_today": new_users_today, "new_users_this_week": new_users_this_week, "new_users_this_month": new_users_this_month, "suspended_users": suspended_users}'
    )
if '"reports_today": reports_today,' in content:
    content = content.replace(
        '"reports_today": reports_today,',
        '"reports_today": reports_today, "reports_this_week": reports_this_week, "average_processing_time_ms": round(avg_processing_time, 2),'
    )

with open("app/api/v1/admin_dashboard.py", "w") as f:
    f.write(content)
