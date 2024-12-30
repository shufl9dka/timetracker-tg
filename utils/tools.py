import asyncio

from typing import Coroutine


def postpone_task_noexcept(task: Coroutine, *, delay: float) -> asyncio.Task:
    async def _f():
        try:
            await asyncio.sleep(delay=delay)
            await task
        except Exception:
            pass

    return asyncio.create_task(_f())
