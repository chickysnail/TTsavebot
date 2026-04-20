from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика", callback_data="panel:stats")
    builder.button(text="Последние логи", callback_data="panel:logs")
    builder.button(text="Blacklist", callback_data="panel:blacklist")
    builder.adjust(1)
    return builder.as_markup()


def build_blacklist_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Заблокировать ID", callback_data="panel:deny")
    builder.button(text="Разблокировать ID", callback_data="panel:allow")
    builder.button(text="Список заблокированных", callback_data="panel:users")
    builder.button(text="Назад", callback_data="panel:back")
    builder.adjust(1)
    return builder.as_markup()

