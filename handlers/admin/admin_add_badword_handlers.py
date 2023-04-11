import logging
from enum import Enum

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (Message, CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F

from db.models.chat import Chat
from db.repository.chat_repo import ChatRepo
from db.repository.stop_word_repo import StopWordRepo
from filters.chat_type import ChatTypeFilter
from filters.is_admin import IsChatAdmin


class ActionBadWord(str, Enum):
    add = 'add'
    show = 'show'
    rm = 'rm'


class BadWordCB(CallbackData, prefix='_bw'):
    action: ActionBadWord
    chat_id: int


class FSMFillBadWords(StatesGroup):
    add_chat_id = State()  # Состояние ожидания ввода стоп-слова
    add_stop_word = State()  # Состояние ожидания ввода стоп-слова


router: Router = Router()

logger = logging.getLogger(__name__)


@router.callback_query(BadWordCB.filter(F.action == ActionBadWord.add))
async def ban_user(callback: CallbackQuery, state: FSMContext, callback_data: BadWordCB, bot: Bot):
    await state.set_state(FSMFillBadWords.add_chat_id)
    await state.update_data(chat_id=callback_data.chat_id)
    await state.update_data(bad_words=set())
    await callback.message.answer(text='Введите плохое слово:')
    # await bot.send_message(chat_id=user_id, )
    await state.set_state(FSMFillBadWords.add_stop_word)


@router.message(
    Command(commands=['add_sw']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_setup_command(message: Message, chat_repo: ChatRepo, bot: Bot):
    # #####################
    # # Создаем объекты инлайн-кнопок
    # template_mode = 'Режим: {mode}'
    # big_button_1: InlineKeyboardButton = InlineKeyboardButton(
    #     text=template_mode.format(mode='Бан'),
    #     callback_data='big_button_1_pressed')
    #
    # big_button_2: InlineKeyboardButton = InlineKeyboardButton(
    #     text=template_mode.format(mode='Только чтение'),
    #     callback_data='big_button_2_pressed')
    #
    # big_button_3: InlineKeyboardButton = InlineKeyboardButton(
    #     text=template_mode.format(mode='Удаление'),
    #     callback_data='big_button_2_pressed')
    #
    # show_warning_num_btn: InlineKeyboardButton = InlineKeyboardButton(
    #     text="Предупреждений:{num}",
    #     callback_data='show_warning_num_btn')
    #
    # warning_btn_plus: InlineKeyboardButton = InlineKeyboardButton(
    #     text="+",
    #     callback_data='warning_btn_plus')
    #
    # warning_btn_minus: InlineKeyboardButton = InlineKeyboardButton(
    #     text="-",
    #     callback_data='warning_btn_minus')
    #
    # show_mute_time_btn: InlineKeyboardButton = InlineKeyboardButton(
    #     text="Время:{time}",
    #     callback_data='show_mute_time_btn')
    #
    # mute_btn_plus: InlineKeyboardButton = InlineKeyboardButton(
    #     text="+",
    #     callback_data='mute_btn_plus')
    #
    # mute_btn_minus: InlineKeyboardButton = InlineKeyboardButton(
    #     text="-",
    #     callback_data='mute_btn_minus')
    #
    # # Создаем объект инлайн-клавиатуры
    # keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [show_warning_num_btn, warning_btn_plus, warning_btn_minus],
    #         [big_button_1],
    #         [big_button_2],
    #         [big_button_3],
    #         [show_mute_time_btn, mute_btn_plus, mute_btn_minus]
    #     ])
    #
    # #####################
    chat_id = message.chat.id
    chat_settings: Chat = await chat_repo.find_chat_settings(chat_id=chat_id)
    print(chat_settings)

    builder = InlineKeyboardBuilder()
    builder.button(text='Добавить',
                   callback_data=BadWordCB(chat_id=chat_id).pack())

    logger.debug(message.chat)
    user_id = message.from_user.id
    try:
        await message.delete()
        await bot.send_message(chat_id=user_id,
                               text=f'Добавление плохих слов для бота:<i><b> {message.chat.title} </b></i>',
                               reply_markup=builder.as_markup())
    # await bot.send_message(chat_id=user_id, text='Введите плохое слово:')
    # await state.set_state(FSMFillBadWords.add_stop_word)
    except TelegramBadRequest:
        logger.debug(f"User with id:{user_id} not activ")


@router.message(Command(commands='stop'), StateFilter(FSMFillBadWords.add_stop_word))
async def process_stop_command_state(message: Message, state: FSMContext, sw_repo: StopWordRepo):
    state_data = await state.get_data()
    print('_______________________')
    print(state_data)
    print('_______________________')

    bad_words = list(state_data['bad_words'])
    bad_words_len = len(bad_words)
    state_chat_id = state_data['chat_id']
    if bad_words_len > 0:
        if state_chat_id is not None:
            # 0 - 100  70
            count = await sw_repo.get_counts(state_chat_id)
            print(f"count_bad_words_exist:{count}")
            bound = 100 - count
            # to_sw = lambda x: StopWord(state_chat_id, x)
            add_bad_words = set()
            for bw in bad_words[:bound]:
                print(bw)
                add_bad_words.add(bw)
            # add_bad_words = list(map(to_sw, bad_words_len[:bound]))
            await sw_repo.add_all(chat_id=state_chat_id, bad_words=add_bad_words)

    await message.answer(text='''Добавление плохих слов завершено''')
    await message.answer(text=f'{state_data["bad_words"]}')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='''Вы вышли из состояния
    Чтобы снова перейти к добалению плохих - слов
    отправьте: /add_sw в нужной группе''')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста
@router.message(StateFilter(FSMFillBadWords.add_stop_word))
async def process_name_sent(message: Message, state: FSMContext, sw_repo: StopWordRepo):
    # Cохраняем введенное имя в хранилище по ключу "name"

    data = await state.get_data()
    print('____________________')
    print(data)
    print(type(data))
    print('____________________')
    if len(data['bad_words']) < 100:
        data['bad_words'].add(message.text)
        await state.update_data(bad_words=data['bad_words'])
        res1 = state.get_data()
        print(res1)
        # async with state.proxy() as data:
        #     if len(data['bad_words']) <= 100:
        #         data['bad_words'].append(message.text)
        await message.answer(text='Добавьте ещё стоп-слова. '
                                  'Завершить: /stop '
                                  'Отменить всё: /cancel')
        # Устанавливаем состояние ожидания ввода возраста
        await state.set_state(FSMFillBadWords.add_stop_word)
    else:
        await process_cancel_command_state(message, state)


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@router.message(StateFilter(FSMFillBadWords.add_stop_word))
async def warning_not_name(message: Message):
    await message.answer(text='То, что вы отправили не похоже на стоп-слово\n\n'
                              'Пожалуйста, введите ваше стоп-слово\n\n'
                              'Для выхода: /cancel')


# Этот хэндлер будет срабатывать на любые сообщения, кроме тех
# для которых есть отдельные хэндлеры, вне состояний
@router.message(StateFilter(default_state), ~ChatTypeFilter(chat_type=["group", "supergroup", "channel"]), )
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')
