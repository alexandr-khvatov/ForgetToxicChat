from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon.lexicon_ru import LEXICON


class ActionBW(str, Enum):
    add = 'a'
    read = 'r'
    delete = 'd'
    cancel = 'c'


class BwCB(CallbackData, prefix='bwe'):
    action: ActionBW
    chat_id: int
    bad_word: str


class ActionPaginationBW(str, Enum):
    next = 'n'
    previous = 'p'


class PaginationBadWordCB(CallbackData, prefix='pbw'):
    action: ActionPaginationBW
    chat_id: int
    current_page: int
    total_page: int


def create_edit_bw_kb(chat_id, bad_words: list, current_page=1, total_page=100) -> InlineKeyboardMarkup:
    # Создаем объект клавиатуры
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Наполняем клавиатуру кнопками-закладками в порядке возрастания
    for b_word in bad_words:
        print(f'b_word:{b_word}')
        print(BwCB(action=ActionBW.delete, chat_id=chat_id, bad_word=str(b_word)).pack())
        kb_builder.row(InlineKeyboardButton(
            text=f'{LEXICON["del"]} {b_word}',
            callback_data=BwCB(action=ActionBW.delete, chat_id=chat_id, bad_word=str(b_word)).pack()))
        # Добавляем в конец клавиатуры кнопку "Отменить"
    kb_builder.row(InlineKeyboardButton(
        text=LEXICON['cancel'],
        callback_data='cancel'))
    kb_builder.row(*[
        InlineKeyboardButton(text=LEXICON['previous'],
                             callback_data=PaginationBadWordCB(action=ActionPaginationBW.previous,
                                                               chat_id=chat_id,
                                                               current_page=current_page,
                                                               total_page=total_page).pack()),
        InlineKeyboardButton(text=f'{current_page} / {total_page}',
                             callback_data='ignore'),
        InlineKeyboardButton(text=LEXICON['next'],
                             callback_data=PaginationBadWordCB(action=ActionPaginationBW.next,
                                                               chat_id=chat_id,
                                                               current_page=current_page,
                                                               total_page=total_page).pack()),
    ])

    # ####
    # testttt=PaginationBadWordCB(action=ActionPaginationBW.previous,
    #                     chat_id=chat_id,
    #                     current_page=current_page,
    #                     total_page=total_page).pack()
    # print("cb check:")
    # print(testttt)
    # res = len(testttt.encode('utf-8'))
    # print(f'len:{res}')
    # ####
    return kb_builder.as_markup()
