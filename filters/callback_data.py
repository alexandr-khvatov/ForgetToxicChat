from enum import Enum

from aiogram.filters.callback_data import CallbackData


class Action(str, Enum):
    ban_mode = 'ba'
    mute_mode = 'mu'
    remove_mode = 'rm'

    warning_plus = "wp"
    warning_minus = "wm"

    mute_plus = "mp"
    mute_minus = "mm"


class ChatSettings(CallbackData, prefix="chat_stg"):
    action: Action
    chat_id: int
