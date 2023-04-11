import logging
import math

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (Message, CallbackQuery)
from magic_filter import F

from config.config import config
from db.models.chat import Chat
from db.repository.chat_repo import ChatRepo
from db.repository.stop_word_repo import StopWordRepo
from filters.chat_type import ChatTypeFilter
from filters.is_admin import IsChatAdmin
from keyboards.bad_word_kb import create_edit_bw_kb, PaginationBadWordCB, ActionPaginationBW, BwCB, ActionBW

router: Router = Router()

logger = logging.getLogger(__name__)


@router.message(
    Command(commands=['sbw']),
    ChatTypeFilter(chat_type=['group', 'supergroup']),
    IsChatAdmin()
)
async def show_bad_words_command(message: Message, sw_repo: StopWordRepo, chat_repo: ChatRepo, bot: Bot):
    chat_id = message.chat.id
    chat_settings: Chat = await chat_repo.find_chat_settings(chat_id=chat_id)
    print(chat_settings)
    count, items = await sw_repo.get_all(chat_id)
    print(count)
    print(items)
    logger.debug(message.chat)
    kb = create_edit_bw_kb(chat_id=chat_id, bad_words=items, current_page=1,
                           total_page=math.ceil(count / config.tg_bot.page_size_stop_word))
    user_id = message.from_user.id
    try:
        await message.delete()
        await bot.send_message(chat_id=user_id,
                               text=f'Список "плохихи слов" для:<i><b> {message.chat.title} </b></i>',
                               reply_markup=kb)
    # await bot.send_message(chat_id=user_id, text='Введите плохое слово:')
    # await state.set_state(FSMFillBadWords.add_stop_word)
    except TelegramBadRequest:
        logger.debug(f"User with id:{user_id} not activ")


@router.callback_query(PaginationBadWordCB.filter(F.action == ActionPaginationBW.next))
async def next_page_press_btn(callback: CallbackQuery, callback_data: PaginationBadWordCB, sw_repo: StopWordRepo):
    page_size = config.tg_bot.page_size_stop_word
    chat_id = callback_data.chat_id
    current_page = callback_data.current_page
    total_counts = await sw_repo.get_counts(chat_id)
    total_page = get_total_page(total_counts=total_counts)

    if current_page < total_page:
        offset = current_page * page_size
        count, next_page_words = await sw_repo.get_all(chat_id, offset=offset, limit=page_size)
        ikb = create_edit_bw_kb(chat_id=chat_id,
                                bad_words=next_page_words,
                                current_page=current_page + 1,
                                total_page=total_page)
        await callback.message.edit_text(text=callback.message.text, reply_markup=ikb)
    await callback.answer()


@router.callback_query(PaginationBadWordCB.filter(F.action == ActionPaginationBW.previous))
async def previous_page_press_btn(callback: CallbackQuery, callback_data: PaginationBadWordCB, sw_repo: StopWordRepo):
    current_page = callback_data.current_page
    if current_page > 1:
        page_size = config.tg_bot.page_size_stop_word
        chat_id = callback_data.chat_id
        total_counts = await sw_repo.get_counts(chat_id)
        total_page = get_total_page(total_counts=total_counts)
        offset = (current_page - 2) * page_size
        print(f'offset___:{current_page}->{offset}')
        count, next_page_words = await sw_repo.get_all(chat_id, offset=offset, limit=page_size)
        ikb = create_edit_bw_kb(chat_id=chat_id,
                                bad_words=next_page_words,
                                current_page=(current_page - 1),
                                total_page=total_page)
        await callback.message.edit_text(text=callback.message.text, reply_markup=ikb)
    await callback.answer()


def get_total_page(total_counts: int, page_size: int = config.tg_bot.page_size_stop_word):
    return math.ceil(total_counts / page_size)


@router.callback_query(BwCB.filter(F.action == ActionBW.delete))
async def delete_stop_word_press_btn(callback: CallbackQuery, callback_data: BwCB,
                                     sw_repo: StopWordRepo):
    page_size = config.tg_bot.page_size_stop_word
    chat_id = callback_data.chat_id
    bad_word = callback_data.bad_word
    await sw_repo.delete(chat_id=chat_id, bad_word=bad_word)
    await callback.answer(f'Стоп-слово:{bad_word} удалено!')
    current_page = callback_data.current_page - 1
    offset = current_page * page_size
    total_counts, next_page_words = await sw_repo.get_all(chat_id, offset=offset, limit=page_size)
    total_page = get_total_page(total_counts=total_counts)
    ikb = create_edit_bw_kb(chat_id=chat_id,
                            bad_words=next_page_words,
                            current_page=current_page,
                            total_page=total_page)
    await callback.message.edit_text(text=callback.message.text, reply_markup=ikb)
