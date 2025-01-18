from typing import List

import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from utils.tools import EncryptedString


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    timezone: Mapped[str] = mapped_column(nullable=False, default="Europe/Moscow")

    sumup_time: Mapped[str] = mapped_column(nullable=True, default="21:00")
    last_sumup_ts: Mapped[int] = mapped_column(sa.BigInteger, nullable=False, default=0)
    send_sumups: Mapped[bool] = mapped_column(nullable=False, default=True)

    records: Mapped[List["TimeRecord"]] = relationship()
    most_recent_labels: Mapped[List[str]] = mapped_column(ARRAY(EncryptedString), nullable=False, default=[])


class TimeRecord(Base):
    __tablename__ = "records"

    record_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.BigInteger, sa.ForeignKey("users.user_id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(EncryptedString, nullable=False)

    started_ts: Mapped[int] = mapped_column(sa.BigInteger, index=True)
    ended_ts: Mapped[int] = mapped_column(sa.BigInteger, index=True)

    __table_args__ = (
        sa.Index("ix_started_ts_user_id", "started_ts", "user_id"),
    )
