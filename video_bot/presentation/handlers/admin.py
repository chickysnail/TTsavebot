from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from video_bot.containers import AppContainer
from video_bot.core.errors import ValidationError
from video_bot.core.interfaces import DownloadLogRecord, DownloadStats
from video_bot.presentation.keyboards.admin_panel import build_admin_panel_keyboard, build_blacklist_keyboard

router = Router(name="admin")


class BlacklistStates(StatesGroup):
    waiting_for_blacklist_id = State()
    waiting_for_unblacklist_id = State()


@dataclass(slots=True, frozen=True)
class ParsedTelegramID:
    telegram_id: int


class EditableCallbackMessage(Protocol):
    def edit_text(self, text: str, **kwargs: object) -> Awaitable[object]:
        ...


class AnswerableCallbackMessage(Protocol):
    def answer(self, text: str, **kwargs: object) -> Awaitable[object]:
        ...


def _parse_telegram_id(raw_value: str) -> ParsedTelegramID:
    value = raw_value.strip()
    if not value:
        raise ValidationError("Укажите Telegram ID числом.")
    try:
        return ParsedTelegramID(telegram_id=int(value))
    except ValueError as exc:
        raise ValidationError("Telegram ID должен быть числом.") from exc


def _format_stats(app_stats: DownloadStats) -> str:
    return (
        "Статистика:\n"
        f"Всего запросов: {app_stats.total}\n"
        f"Успешно: {app_stats.success}\n"
        f"Ошибки: {app_stats.failed}\n"
        f"Отклонено: {app_stats.rejected}\n"
        f"Слишком большие: {app_stats.oversize}\n"
        f"TikTok: {app_stats.tiktok}\n"
        f"Instagram: {app_stats.instagram}"
    )


def _format_logs(logs: Sequence[DownloadLogRecord]) -> str:
    if not logs:
        return "Логи пока пусты."

    lines = []
    for item in logs:
        lines.append(
            f"#{item.id} | {item.status.value} | user={item.telegram_id} | "
            f"{item.platform.value if item.platform else 'n/a'} | {item.url}"
        )
    return "\n".join(lines)


def _get_callback_message(callback: CallbackQuery, attribute_name: str) -> object | None:
    message = callback.message
    if message is None or not hasattr(message, attribute_name):
        return None
    return message


async def _edit_callback_message(
    callback: CallbackQuery,
    text: str,
    reply_markup_factory: Callable[[], object],
) -> bool:
    message = _get_callback_message(callback, "edit_text")
    if message is None:
        await callback.answer("Message is unavailable.", show_alert=True)
        return False

    editable_message = cast(EditableCallbackMessage, message)
    await editable_message.edit_text(text, reply_markup=reply_markup_factory())
    return True


async def _answer_callback_message(callback: CallbackQuery, text: str) -> bool:
    message = _get_callback_message(callback, "answer")
    if message is None:
        await callback.answer("Message is unavailable.", show_alert=True)
        return False

    answerable_message = cast(AnswerableCallbackMessage, message)
    await answerable_message.answer(text)
    return True


@router.message(Command("panel"))
async def panel_handler(message: Message) -> None:
    await message.answer("Админ-панель", reply_markup=build_admin_panel_keyboard())


@router.message(Command("stats"))
async def stats_handler(message: Message, app_container: AppContainer) -> None:
    stats = await app_container.admin_get_stats_use_case.execute()
    await message.answer(_format_stats(stats))


@router.message(Command("logs"))
async def logs_handler(message: Message, app_container: AppContainer) -> None:
    logs = await app_container.admin_get_logs_use_case.execute(limit=10)
    await message.answer(_format_logs(logs))


@router.message(Command("unblacklist"))
async def allow_handler(message: Message, app_container: AppContainer) -> None:
    try:
        raw_args = (message.text or "").partition(" ")[2]
        target = _parse_telegram_id(raw_args)
        user = await app_container.admin_allow_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {user.telegram_id} удалён из blacklist.")
    except ValidationError as exc:
        await message.answer(str(exc))


@router.message(Command("blacklist"))
async def deny_handler(message: Message, app_container: AppContainer) -> None:
    try:
        raw_args = (message.text or "").partition(" ")[2]
        target = _parse_telegram_id(raw_args)
        await app_container.admin_deny_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {target.telegram_id} добавлен в blacklist.")
    except ValidationError as exc:
        await message.answer(str(exc))


@router.callback_query(F.data == "panel:stats")
async def panel_stats_handler(callback: CallbackQuery, app_container: AppContainer) -> None:
    stats = await app_container.admin_get_stats_use_case.execute()
    if not await _edit_callback_message(callback, _format_stats(stats), build_admin_panel_keyboard):
        return
    await callback.answer()


@router.callback_query(F.data == "panel:logs")
async def panel_logs_handler(callback: CallbackQuery, app_container: AppContainer) -> None:
    logs = await app_container.admin_get_logs_use_case.execute(limit=10)
    if not await _edit_callback_message(callback, _format_logs(logs), build_admin_panel_keyboard):
        return
    await callback.answer()


@router.callback_query(F.data == "panel:blacklist")
async def panel_blacklist_handler(callback: CallbackQuery) -> None:
    if not await _edit_callback_message(callback, "Управление blacklist", build_blacklist_keyboard):
        return
    await callback.answer()


@router.callback_query(F.data == "panel:back")
async def panel_back_handler(callback: CallbackQuery) -> None:
    if not await _edit_callback_message(callback, "Админ-панель", build_admin_panel_keyboard):
        return
    await callback.answer()


@router.callback_query(F.data == "panel:allow")
async def panel_allow_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BlacklistStates.waiting_for_unblacklist_id)
    if not await _answer_callback_message(
        callback,
        "Отправьте Telegram ID, который нужно удалить из blacklist.",
    ):
        return
    await callback.answer()


@router.callback_query(F.data == "panel:deny")
async def panel_deny_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BlacklistStates.waiting_for_blacklist_id)
    if not await _answer_callback_message(
        callback,
        "Отправьте Telegram ID, который нужно добавить в blacklist.",
    ):
        return
    await callback.answer()


@router.callback_query(F.data == "panel:users")
async def panel_users_handler(callback: CallbackQuery, app_container: AppContainer) -> None:
    users = await app_container.access_repository.list_inactive_users()
    if not users:
        text = "Blacklist пуст."
    else:
        text = "\n".join(f"{user.telegram_id} | {user.role.value}" for user in users)

    if not await _answer_callback_message(callback, text):
        return
    await callback.answer()


@router.message(BlacklistStates.waiting_for_unblacklist_id)
async def process_allow_id(message: Message, state: FSMContext, app_container: AppContainer) -> None:
    try:
        target = _parse_telegram_id(message.text or "")
        await app_container.admin_allow_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {target.telegram_id} удалён из blacklist.")
        await state.clear()
    except ValidationError as exc:
        await message.answer(str(exc))


@router.message(BlacklistStates.waiting_for_blacklist_id)
async def process_deny_id(message: Message, state: FSMContext, app_container: AppContainer) -> None:
    try:
        target = _parse_telegram_id(message.text or "")
        await app_container.admin_deny_user_use_case.execute(target.telegram_id)
        await message.answer(f"Пользователь {target.telegram_id} добавлен в blacklist.")
        await state.clear()
    except ValidationError as exc:
        await message.answer(str(exc))
