import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class TicketCategory(str, enum.Enum):
    login = "Login/Account"
    report = "Report Processing"
    ai = "AI/Analysis"
    chat = "Chat"
    translation = "Translation"
    notifications = "Notifications"
    medication = "Medication Reminder"
    performance = "Performance"
    security = "Security"
    privacy = "Privacy"
    other = "Other"


class TicketPriority(str, enum.Enum):
    p1 = "P1 Critical"
    p2 = "P2 High"
    p3 = "P3 Normal"
    p4 = "P4 General"


class TicketStatus(str, enum.Enum):
    new = "New"
    triaged = "Triaged"
    investigating = "Investigating"
    waiting_user = "Waiting for User"
    waiting_eng = "Waiting for Engineering"
    resolved = "Resolved"
    closed = "Closed"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    category = Column(
        Enum(TicketCategory), nullable=False, default=TicketCategory.other
    )
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.p3)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.new)

    assigned_admin_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    related_report_id = Column(
        String(36), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )
    related_request_id = Column(String(100), nullable=True)
    related_incident_id = Column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="support_tickets"
    )
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id])
    messages = relationship(
        "SupportTicketMessage", back_populates="ticket", cascade="all, delete-orphan"
    )
    events = relationship(
        "SupportTicketEvent", back_populates="ticket", cascade="all, delete-orphan"
    )
    report = relationship("Report", foreign_keys=[related_report_id])
    article_links = relationship(
        "SupportTicketHelpArticle",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


class SupportTicketMessage(Base):
    __tablename__ = "support_ticket_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(
        String(36), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False
    )

    sender_id = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_internal = Column(Boolean, default=False, nullable=False)
    content = Column(Text, nullable=False)

    # Store references to help articles (slug or ID)
    help_article_ref = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])


class SupportTicketEvent(Base):
    """System-generated events and diagnostic snapshots for a ticket"""

    __tablename__ = "support_ticket_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(
        String(36), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False
    )

    event_type = Column(
        String(50), nullable=False
    )  # e.g. "status_change", "diagnostic_snapshot", "escalation"
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("SupportTicket", back_populates="events")


class SupportTicketHelpArticle(Base):
    """A durable link between a support ticket and a published help article."""

    __tablename__ = "support_ticket_help_articles"

    ticket_id = Column(
        String(36),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    article_id = Column(
        String(36),
        ForeignKey("help_articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    attached_by = Column(String(36), nullable=False)
    attached_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("SupportTicket", back_populates="article_links")
    article = relationship("HelpArticle", back_populates="ticket_links")
