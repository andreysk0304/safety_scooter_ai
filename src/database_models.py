"""
SQLAlchemy модели для БД
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    """Base class для всех моделей"""
    pass


class Applications(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int]
    key: Mapped[str] = mapped_column(String(255))  # S3 ключ видео
    status: Mapped[str] = mapped_column(String(32))  # pending/processing/completed/failed
    gps_longitude: Mapped[str] = mapped_column(String(32))
    gps_width: Mapped[str] = mapped_column(String(32))
    record_time: Mapped[datetime] = mapped_column(DateTime())
    is_delete: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime())
    last_change: Mapped[datetime] = mapped_column(DateTime())


class Verdicts(Base):
    __tablename__ = "verdicts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(255))  # Тип нарушения
    scooter_type: Mapped[str] = mapped_column(String(64), nullable=True)  # Тип самоката (Yandex/Whoosh/Urent)
    object_id: Mapped[int] = mapped_column(nullable=True)  # ID объекта из YOLO tracking
    timestamp: Mapped[float] = mapped_column(nullable=True)  # Время в видео (секунды)
    coordinates: Mapped[str] = mapped_column(String(255), nullable=True)  # Координаты на кадре
    created_at: Mapped[datetime] = mapped_column(DateTime())