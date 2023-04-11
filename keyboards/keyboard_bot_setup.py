from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.models.chat import Chat
from db.models.chat_mode_restriction import Mode
from filters.callback_data import ChatSettings, Action


def make_kb_bot_settings(chat: Chat, width: int = 3) -> InlineKeyboardMarkup:
    # cb_chat_settings = CallbackData('ch_st', "id")
    chat_id = chat.chat_tg_id
    print("-----------------")
    print(chat_id)
    print(type(chat_id))
    print("-----------------")
    ban_mode_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Режим: Бан',
        callback_data=ChatSettings(action=Action.ban_mode, chat_id=chat_id).pack())

    mute_mode_btn: InlineKeyboardButton = InlineKeyboardButton(
        text='Режим: Только чтение',
        callback_data=ChatSettings(action=Action.mute_mode, chat_id=chat_id).pack())

    remove_mode_btn: InlineKeyboardButton = InlineKeyboardButton(
        text="Режим: Удаление",
        callback_data=ChatSettings(action=Action.remove_mode, chat_id=chat_id).pack())

    warning_btn: InlineKeyboardButton = InlineKeyboardButton(
        text=f"Кол-во предупреждений",
        callback_data='ignore')

    show_warning_num_btn: InlineKeyboardButton = InlineKeyboardButton(
        text=f"{chat.num_warnings}",
        callback_data='ignore')

    warning_btn_plus: InlineKeyboardButton = InlineKeyboardButton(
        text="+",
        callback_data=ChatSettings(action=Action.warning_plus, chat_id=chat_id).pack())

    warning_btn_minus: InlineKeyboardButton = InlineKeyboardButton(
        text="-",
        callback_data=ChatSettings(action=Action.warning_minus, chat_id=chat_id).pack())

    show_mute_time_btn: InlineKeyboardButton = InlineKeyboardButton(
        text=f"Время:{int(chat.mute_time / 60)}",
        callback_data='ignore')

    mute_btn_plus: InlineKeyboardButton = InlineKeyboardButton(
        text="+",
        callback_data=ChatSettings(action=Action.mute_plus, chat_id=chat_id).pack())

    mute_btn_minus: InlineKeyboardButton = InlineKeyboardButton(
        text="-",
        callback_data=ChatSettings(action=Action.mute_minus, chat_id=chat_id).pack())

    mute_mode_btns = [[mute_mode_btn], [show_mute_time_btn, mute_btn_plus, mute_btn_minus]]

    mode = {
        Mode.mute.name: mute_mode_btns,
        Mode.ban.name: [[ban_mode_btn]],
        Mode.remove.name: [[remove_mode_btn]]
    }

    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [warning_btn],
            [show_warning_num_btn, warning_btn_plus, warning_btn_minus],
            *mode[chat.mode]
        ])

    return keyboard
