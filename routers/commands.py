import datetime
import pytz

from aiogram import Router

from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sqlalchemy import select, delete, update, and_

from models.user import User, TimeRecord

from utils.database import async_session
from utils.specific import get_report
from utils.time import string_timedelta


router = Router()

start_users_cache = set()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id

    if user_id not in start_users_cache:
        async with async_session() as session:
            user = await session.execute(
                select(User).where(User.user_id == user_id)
            )

            if user.scalar_one_or_none() is None:
                session.add(User(user_id=user_id))
                await session.commit()

        start_users_cache.add(user_id)

    await message.answer(
        "\U0001F44B Привет! Введи короткое название занятия или действие, которому ты собираешься уделить время, и таймер начнёт отсчёт.\n\n"
        "Чтобы добавить уже прошедшее событие, просто добавь его длительность перед названием в формате <b>2ч30м</b> или <b>45м</b>.",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("today"))
async def cmd_today(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            user = User(user_id=user_id)
            session.add(user)
            await session.commit()

        today_start = int(
            datetime.datetime.\
                now(tz=pytz.timezone(user.timezone)).\
                replace(hour=0, minute=0, second=0, microsecond=0).\
                timestamp()
        )

        sum, table = await get_report(session, user_id, additional=data, start_from=today_start)

    if not table:
        await message.answer("\u26A0 Записей за день не обнаружено")
        return

    result = [f"\U0001F4CA Суммарное время за день: <b>{string_timedelta(sum)}</b>\n"]

    if data.get("current_task") is not None:
        result.append(f"* Активное занятие: <b>{data['current_task']}</b>\n")

    result.extend(f"<b>{i}</b>: {label} — <b>{string_timedelta(tm)}</b>" for i, (label, tm) in enumerate(table[:10], start=1))
    result.append(f"\nВсего различных занятий: {len(table)}")

    await message.answer("\n".join(result), parse_mode=ParseMode.HTML)


@router.message(Command("week"))
async def cmd_week(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            user = User(user_id=user_id)
            session.add(user)
            await session.commit()

        dt = datetime.datetime.now(tz=pytz.timezone(user.timezone))
        week_start = int(
            (dt - datetime.timedelta(days=dt.weekday())).\
                replace(hour=0, minute=0, second=0, microsecond=0).\
                timestamp()
        )

        sum, table = await get_report(session, user_id, additional=data, start_from=week_start)

    if not table:
        await message.answer("\u26A0 Записей за неделю не обнаружено")
        return

    result = [f"\U0001F4CA Суммарное время за неделю: <b>{string_timedelta(sum)}</b>\n"]

    if data.get("current_task") is not None:
        result.append(f"Активное занятие: <b>{data['current_task']}</b>\n")

    result.extend(f"<b>{i}</b>: {label} — <b>{string_timedelta(tm)}</b>" for i, (label, tm) in enumerate(table[:10], start=1))
    result.append(f"\nВсего различных занятий: {len(table)}")

    await message.answer("\n".join(result), parse_mode=ParseMode.HTML)


@router.message(Command("month"))
async def cmd_month(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            user = User(user_id=user_id)
            session.add(user)
            await session.commit()

        month_start = int(
            datetime.datetime.\
                now(tz=pytz.timezone(user.timezone)).\
                replace(day=1, hour=0, minute=0, second=0, microsecond=0).\
                timestamp()
        )

        sum, table = await get_report(session, user_id, additional=data, start_from=month_start)

    if not table:
        await message.answer("\u26A0 Записей за месяц не обнаружено")
        return

    result = [f"\U0001F4CA Суммарное время за месяц: <b>{string_timedelta(sum)}</b>\n"]

    if data.get("current_task") is not None:
        result.append(f"Активное занятие: <b>{data['current_task']}</b>\n")

    result.extend(f"<b>{i}</b>: {label} — <b>{string_timedelta(tm)}</b>" for i, (label, tm) in enumerate(table[:10], start=1))
    result.append(f"\nВсего различных занятий: {len(table)}")

    await message.answer("\n".join(result), parse_mode=ParseMode.HTML)


@router.message(Command("toggle_sumup"))
async def cmd_toggle_sumups(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            user = User(user_id=user_id)
            session.add(user)

        user.send_sumups = not user.send_sumups
        await session.commit()

    await message.answer(
        f"Уведомления с подведением итогов <b>{'включены' if user.send_sumups else 'выключены'}</b>",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("sumup"))
async def cmd_toggle_sumups(message: Message):
    user_id = message.from_user.id
    bad_format_msg = "Формат ввода: <b>/sumup [HH:MM]</b>"

    a = message.text.split(maxsplit=1)
    if len(a) != 2:
        await message.answer(bad_format_msg, parse_mode=ParseMode.HTML)
        return

    tx = a[1]
    a = a[1].split(":")[:2]
    if len(a) < 2:
        await message.answer(bad_format_msg, parse_mode=ParseMode.HTML)
        return
    
    if not a[0].isdigit() or int(a[0]) < 0 or int(a[0]) > 23 or not a[1].isdigit() or int(a[1]) < 0 or int(a[1]) > 59:
        await message.answer(bad_format_msg, parse_mode=ParseMode.HTML)
        return

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            user = User(user_id=user_id)
            session.add(user)

        user.sumup_time = tx
        await session.commit()

    await message.answer(
        f"Время отправки уведомления <b>обновлено</b>",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("tz"))
async def cmd_timezone(message: Message):
    user_id = message.from_user.id
    bad_format_msg = "Формат ввода: <b>/tz [timezone]</b>\n\nПодробнее про формат часовых поясов можно почитать <a href=\"https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List\">здесь</a>"

    a = message.text.split(maxsplit=1)
    if len(a) != 2:
        await message.answer(bad_format_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return

    try:
        tz = pytz.timezone(a[1])
    except:
        await message.answer(bad_format_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            user = User(user_id=user_id)
            session.add(user)

        user.timezone = a[1]
        await session.commit()

    dt = datetime.datetime.now(tz=tz).strftime("%H:%M")
    await message.answer(
        f"Часовой пояс обновлён. Убедись, что ожидаемое время совпадает с временем часового пояса: <b>{dt}</b>",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    bad_format_msg = \
        "Формат ввода: <b>/clear [when]</b>\n\nВ качестве <code>when</code> можно " + \
        "использовать значения: <code>today</code>, <code>today</code>, <code>month</code> или <code>all</code>.\n\n" + \
        "Эта команда <b>безвозвратно</b> удаляет записи об активностях за указанный период."

    a = message.text.split(maxsplit=1)
    if len(a) != 2:
        await message.answer(bad_format_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user.scalar_one_or_none()

        if user is None:
            return

        tz = pytz.timezone(user.timezone)

        tp = a[1].lower()
        start_from_ts = None
        if tp == "today":
            start_from_ts = int(
                datetime.datetime.\
                    now(tz=tz).\
                    replace(hour=0, minute=0, second=0, microsecond=0).\
                    timestamp()
            )
            delete_statement = and_(TimeRecord.user_id == user_id, TimeRecord.started_ts >= start_from_ts)
        elif tp == "week":
            dt = datetime.datetime.now(tz=tz)
            start_from_ts = int(
                (dt - datetime.timedelta(days=dt.weekday())).\
                    replace(hour=0, minute=0, second=0, microsecond=0).\
                    timestamp()
            )
            delete_statement = and_(TimeRecord.user_id == user_id, TimeRecord.started_ts >= start_from_ts)
        elif tp == "month":
            start_from_ts = int(
                datetime.datetime.\
                    now(tz=pytz.timezone(user.timezone)).\
                    replace(day=1, hour=0, minute=0, second=0, microsecond=0).\
                    timestamp()
            )
            delete_statement = and_(TimeRecord.user_id == user_id, TimeRecord.started_ts >= start_from_ts)
        elif tp == "all":
            delete_statement = TimeRecord.user_id == user_id
        else:
            await message.answer(bad_format_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        await session.execute(delete(TimeRecord).where(delete_statement))
        if start_from_ts is not None:
            await session.execute(
                update(TimeRecord)
                .where(TimeRecord.ended_ts > start_from_ts)
                .values(ended_ts=start_from_ts)
            )

        await session.commit()

        await message.answer("Изменения внесены", parse_mode=ParseMode.HTML)
