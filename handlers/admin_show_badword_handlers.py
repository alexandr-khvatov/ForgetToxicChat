import logging

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.chat import Chat
from db.repository.chat_repo import ChatRepo
from filters.chat_type import ChatTypeFilter
from filters.is_admin import IsChatAdmin
from handlers.admin_add_badword_handlers import BadWordCB

router: Router = Router()

logger = logging.getLogger(__name__)


@router.message(
    Command(commands=['sbw']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def show_bad_words_command(message: Message, chat_repo: ChatRepo, bot: Bot):
    chat_id = message.chat.id
    chat_settings: Chat = await chat_repo.find_chat_settings(chat_id=chat_id)
    print(chat_settings)

    builder = InlineKeyboardBuilder()
    builder.button(text='Показать',
                   callback_data=BadWordCB(chat_id=chat_id).pack())

    logger.debug(message.chat)
    user_id = message.from_user.id
    try:
        await message.delete()
        await bot.send_message(chat_id=user_id,
                               text=f'Список "плохихи слов" для:<i><b> {message.chat.title} </b></i>',
                               reply_markup=builder.as_markup())
    # await bot.send_message(chat_id=user_id, text='Введите плохое слово:')
    # await state.set_state(FSMFillBadWords.add_stop_word)
    except TelegramBadRequest:
        logger.debug(f"User with id:{user_id} not activ")
