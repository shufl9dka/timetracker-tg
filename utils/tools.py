import asyncio

from sqlalchemy.types import TypeDecorator, String

from rfernet import Fernet
from typing import Coroutine


def postpone_task_noexcept(task: Coroutine, *, delay: float) -> asyncio.Task:
    async def _f():
        try:
            await asyncio.sleep(delay=delay)
            await task
        except Exception:
            pass

    return asyncio.create_task(_f())


class EncryptedString(TypeDecorator):
    impl = String
    cipher = Fernet(key)

    def process_bind_param(self, value, _dialect):
        if value is not None:
            value = self.cipher.encrypt(value.encode("utf-8")).decode("utf-8")
        return value

    def process_result_value(self, value, _dialect):
        if value is not None:
            value = self.cipher.decrypt(value.encode("utf-8")).decode("utf-8")
        return value
