from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now():
    return datetime.now(timezone.utc)

class Broker(Base):
    __tablename__ = "brokers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    management_url: Mapped[str] = mapped_column(String(500))
    management_user: Mapped[str] = mapped_column(String(200))
    management_password: Mapped[str] = mapped_column(String(500))
    messaging_host: Mapped[str] = mapped_column(String(200))
    internal_messaging_host: Mapped[str] = mapped_column(String(200), default="artemis")
    stomp_port: Mapped[int]
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    secret_hash: Mapped[str] = mapped_column(String(500))
    broker_password: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class QueueResource(Base):
    __tablename__ = "queue_resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(255))
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.client_id"), index=True)
    broker_id: Mapped[int] = mapped_column(ForeignKey("brokers.id"))
    can_create: Mapped[bool] = mapped_column(Boolean, default=True)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=True)
    can_produce: Mapped[bool] = mapped_column(Boolean, default=True)
    can_consume: Mapped[bool] = mapped_column(Boolean, default=True)
    durable: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("name", "client_id", name="uq_queue_client"),)
