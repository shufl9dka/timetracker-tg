import time
import pytimeparse

from aiogram import Router, F

from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from sqlalchemy import select

from models.user import User, TimeRecord

from utils.config import Config
from utils.database import async_session
from utils.specific import is_stop_text, get_stop_text
from utils.time import string_timedelta


router = Router()

sent_pro_tip_users = set()


def parse_another_task(text: str) -> tuple[int | None, str]:
    a = text.split(maxsplit=1)

    if len(a) == 2:
        tm = pytimeparse.parse(a[0].lower().replace("ч", "h").replace("м", "m"), granularity="minutes")
        if tm is None:
            return None, text.capitalize()
        return int(tm), a[1].capitalize()

    return None, text.capitalize()


@router.message(StateFilter(None), F.text)
async def text_message(message: Message, state: FSMContext):
    now_ts = int(time.time())
    seconds, task = parse_another_task(message.html_text.strip("\u25B6 "))
    is_stop_task = is_stop_text(task)
    user_id = message.from_user.id

    if len(task) > 64:
        await message.answer("Строка не должна быть длинее 64 символов")
        return

    if seconds is not None:
        if is_stop_task:
            await message.answer("нифига он умный")
            return

        if seconds == 0:
            await message.answer("\U0001F60F Так сделать не получится :)")
            return

        if seconds < 0:
            await message.answer(f"\U0001FAE8 Отрицательные значения здесь <i>пока</i> не поддерживаются", parse_mode=ParseMode.HTML)
            return

        started_ts = now_ts - seconds

        async with async_session() as session:
            session.add(TimeRecord(
                user_id=user_id,
                label=task,
                started_ts=started_ts,
                ended_ts=now_ts,
            ))
            await session.commit()

        await message.answer(
            f"Добавлено <b>{string_timedelta(seconds)}</b> к занятию <b>{task}</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    state_data = await state.get_data()

    if is_stop_task and state_data.get("current_task") is None:
        await message.answer("Сейчас нет активных задач.")
        return

    if task == state_data.get("current_task"):
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=f"\U0001F928 <b>{task}</b> уже в процессе",
            parse_mode=ParseMode.HTML,
        )
        return

    answer = ""
    reply_markup = None

    if state_data.get("current_task") is not None:
        current_task = state_data["current_task"]
        started_ts = state_data["started_ts"]
        delta = now_ts - state_data["started_ts"]

        async with async_session() as session:
            user = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user.scalar_one_or_none()

            if user is None:
                user = User(user_id=user_id)
                session.add(user)

            user.most_recent_labels = [current_task] + list(filter(lambda x: x != current_task, user.most_recent_labels))
            if len(user.most_recent_labels) > Config.MAX_RECENT_LABELS:
                user.most_recent_labels = user.most_recent_labels[:Config.MAX_RECENT_LABELS]

            session.add(TimeRecord(
                user_id=user_id,
                label=current_task,
                started_ts=started_ts,
                ended_ts=now_ts,
            ))
            recent_labels = user.most_recent_labels[:Config.MAX_RECENT_LABELS]

            await session.commit()

        if is_stop_task:
            await state.clear()

        answer = f"\u270D Остановили <b>{current_task}</b>: прошло <b>{string_timedelta(delta)}</b>\n\n"
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="\u25B6 " + line)] for line in recent_labels],
            resize_keyboard=True,
            is_persistent=True,
        )

    if not is_stop_task:
        await state.update_data({
            "current_task": task,
            "started_ts": now_ts,
            "message_id": message.message_id,
        })

        need_pro_tip = not bool(answer) and user_id not in sent_pro_tip_users

        answer += f"\U0001F31F Начали <b>{task}</b>. Для остановки таймера нажми кнопку <b>\"Стоп\"</b>"
        if need_pro_tip:
            answer += "\n\n<b>Pro tip:</b> Если хочешь переключиться на другое занятие, необязательно нажимать <b>\"Стоп\"</b> перед этим: просто введи занятие, на которое переключаешься."
            sent_pro_tip_users.add(user_id)

        reply_markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=get_stop_text())]],
            resize_keyboard=True,
            is_persistent=True,
        )

    await message.answer(answer, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
