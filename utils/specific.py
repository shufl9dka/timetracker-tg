import logging
import time

from collections import defaultdict

from sqlalchemy import select
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
    user_id: int,
    *,
    start_from: int,
    up_to: int = None,
    additional: dict = None,
    session: AsyncSession = None,
) -> tuple[int, list[dict[str, int]]]:
    table = defaultdict(int)

    if additional is not None and additional.get("current_task") is not None:
        table[additional["current_task"]] = int(time.time()) - additional["started_ts"]

    statement = TimeRecord.user_id == user_id and (TimeRecord.started_ts >= start_from or TimeRecord.ended_ts >= start_from)
    if up_to is not None:
        statement = statement and (TimeRecord.started_ts < up_to)

    records = await session.execute(
        select(TimeRecord).where(statement)
    )

    for record in records.scalars():
        table[record.label] += max(start_from, record.ended_ts) - (record.started_ts if up_to is None else min(up_to, record.started_ts))

    key = lambda x: x[1]
    logging.warning(f"{table.items()}")
    return sum(map(key, table.items())), sorted(table.items(), key=key, reverse=True)
