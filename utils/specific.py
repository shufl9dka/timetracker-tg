import logging
import time

from collections import defaultdict

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import TimeRecord


STOP_TEXTS = [
    "Стоп \u270B"
]
set_STOP_TEXTS = set(STOP_TEXTS)


def get_stop_text():
    return STOP_TEXTS[-1]


def is_stop_text(text: str):
    return text in set_STOP_TEXTS


async def get_report(
    session: AsyncSession,
    user_id: int,
    *,
    start_from: int,
    up_to: int = None,
    additional: dict = None,
) -> tuple[int, list[dict[str, int]]]:
    table = defaultdict(int)

    if additional is not None and additional.get("current_task") is not None:
        table[additional["current_task"]] = int(time.time()) - additional["started_ts"]

    logging.info(f"Get report: start_from={start_from}")

    statement = sa.and_(
        TimeRecord.user_id == user_id,
        sa.or_(
            TimeRecord.started_ts >= start_from,
            TimeRecord.ended_ts >= start_from,
        ),
    )
    if up_to is not None:
        statement = sa.and_(statement, TimeRecord.started_ts < up_to)

    records = await session.execute(
        sa.select(TimeRecord).where(statement)
    )

    for record in records.scalars():
        logging.info(f"Get report: {record.label}: {record.started_ts} -> {record.ended_ts}, added {max(start_from, record.ended_ts) - (record.started_ts if up_to is None else min(up_to, record.started_ts))}")
        table[record.label] += max(start_from, record.ended_ts) - (record.started_ts if up_to is None else min(up_to, record.started_ts))

    key = lambda x: x[1]
    return sum(map(key, table.items())), sorted(table.items(), key=key, reverse=True)
