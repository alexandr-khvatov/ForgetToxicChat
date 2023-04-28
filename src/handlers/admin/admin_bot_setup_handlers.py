import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from src.db.models.chat_mode_restriction import Mode
from src.db.repository.chat_repo import ChatRepo
from src.filters.callback_data import ChatSettings, Action
from src.keyboards.keyboard_bot_setup import make_kb_bot_settings

router: Router = Router()

logger = logging.getLogger(__name__)


# @router.callback_query(Text(text=['big_button_1_pressed']))
# async def process_button_1_press(callback: CallbackQuery):
#     logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")
#     if callback.message.text != 'Была нажата БОЛЬШАЯ КНОПКА 1':
#         await callback.message.edit_text(
#             text='Была нажата БОЛЬШАЯ КНОПКА 1',
#             reply_markup=callback.message.reply_markup)
#     await callback.answer()

@router.callback_query(ChatSettings.filter(F.action == Action.ban_mode))
async def ban_mode_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, mode=Mode.remove.name)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChatSettings.filter(F.action == Action.mute_mode))
async def mute_mode_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, mode=Mode.ban.name)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChatSettings.filter(F.action == Action.remove_mode))
async def remove_mode_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, mode=Mode.mute.name)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChatSettings.filter(F.action == Action.warning_plus))
async def warning_plus_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, warning_action=Action.warning_plus)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChatSettings.filter(F.action == Action.warning_minus))
async def warning_minus_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, warning_action=Action.warning_minus)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChatSettings.filter(F.action == Action.mute_plus))
async def mute_plus_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, mute_action=Action.mute_plus)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()


@router.callback_query(ChatSettings.filter(F.action == Action.mute_minus))
async def mute_minus_press_btn(callback: CallbackQuery, callback_data: ChatSettings, chat_repo: ChatRepo):
    logger.debug(f"press ban mode for chat with id:{callback.message.chat.id}")

    updated_chat = await chat_repo.update(chat_id=callback_data.chat_id, mute_action=Action.mute_minus)

    kb = make_kb_bot_settings(updated_chat)
    try:
        await callback.message.edit_text(
            text=callback.message.text,
            reply_markup=kb)
    except TelegramBadRequest:
        await callback.answer()

# @router.message(CommandStart())
# async def process_start_command(message: Message):
#     await message.answer(text=LEXICON_RU['/start'], reply_markup=yes_no_kb)
#
#
# @router.message(Command(commands=['help']))
# async def process_help_command(message: Message):
#     await message.answer(text=LEXICON_RU['/help'], reply_markup=yes_no_kb)

# chat_settings = CallbackData("ch_stg", "id")
#
#
# def make_cb_chat_settings(chat_id: int):
#     return chat_settings.new(id=chat_id)
