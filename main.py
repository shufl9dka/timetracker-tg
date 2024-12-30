import asyncio
import datetime
import logging
import pytz
import time

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from sqlalchemy import select

from models.user import User

from routers import commands, tracking

from utils.config import Config
from utils.database import on_startup as db_on_startup, async_session
from utils.time import string_timedelta
from utils.specific import get_report

logging.basicConfig(
    level=logging.INFO
)


async def sumup_task(bot: Bot):
    while True:
        try:
            async with async_session() as session:
                users = await session.execute(
                    select(User)
                )

                for user in users.scalars():
                    if not user.send_sumups:
                        continue

                    h, m = map(int, user.sumup_time.split(":"))
                    to_send = int(datetime.datetime.now(tz=pytz.timezone(user.timezone)).\
                        replace(hour=h, minute=m, second=0, microsecond=0).timestamp())
                    now = int(time.time())

                    if user.last_sumup_ts > to_send or now < to_send:
                        continue

                    sum, table = await get_report(user.user_id, start_from=to_send - h * 3600 - m * 60, session=session)

                    if table:
                        result = [f"\U0001F4CA Суммарное время за день: <b>{string_timedelta(sum)}</b>\n"]
                        result.extend(f"<b>{i}</b>: {label} — <b>{string_timedelta(tm)}</b>" for i, (label, tm) in enumerate(table[:10], start=1))
                        result.append(f"\nВсего различных занятий: {len(table)}")
                    else:
                        result = [
                            "\u26A0 Записей за день не обнаружено\n",
                            "* Если хочется отписаться от таких уведомлений, введи команду /toggle_sumup",
                        ]

                    try:
                        await bot.send_message(user.user_id, "\n".join(result), parse_mode=ParseMode.HTML)
                        user.last_sumup_ts = now
                    except Exception as ex:
                        logging.warning(f"Can't send a message to user {user.user_id}: {ex}")
                        if not table:
                            user.last_sumup_ts = now

                    await asyncio.sleep(0.3)

                await session.commit()
        except Exception as ex:
            logging.warning(f"Some exception in sumup_task: {ex}")

        await asyncio.sleep(15)


async def main():
    storage = RedisStorage.from_url(Config.REDIS_URI)

    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=storage)

    dp.include_routers(
        commands.router,
        tracking.router,
    )

    logging.info("Setting up database")
    await db_on_startup()

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    except Exception:
        logging.info("bye-bye")


if __name__ == "__main__":
    asyncio.run(main())
