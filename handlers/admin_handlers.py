import logging
import re
from datetime import timedelta
from enum import Enum

from aiogram import Router, Bot, types, F, exceptions as exc
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, Text
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import Chat
from db.models.chat_mode_restriction import Mode
from db.models.userchat import UserChat
from db.repository.chat_repo import ChatRepo
from db.repository.user_repo import UserRepo
from filters.callback_data import ChatSettings, Action
from filters.chat_type import ChatTypeFilter
from filters.is_admin import IsChatAdmin
from keyboards.keyboard_bot_setup import make_kb_bot_settings

restriction_time_regex = re.compile(r'(\b[1-9][0-9]*)([mhd]\b)')

router: Router = Router()

logger = logging.getLogger(__name__)


@router.message(
    Command(commands=['setup']),
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

    kb = make_kb_bot_settings(chat=chat_settings)

    logger.debug(message.chat)
    user_id = message.from_user.id
    try:
        await bot.send_message(chat_id=user_id, text=f"Настройки чата:<i><b> {message.chat.title} </b></i>",
                               reply_markup=kb)
    except TelegramBadRequest:
        logger.debug(f"User with id:{user_id} not activ")
    await message.reply(text='<b> Настройки чата отправлены в ЛС </b>')
    # await message.answer(text=LEXICON_RU['/help'], reply_markup=yes_no_kb)


@router.message(
    Command(commands=['ban']),
    F.reply_to_message,
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin())
async def process_ban_command(message: Message, session: AsyncSession, bot: Bot):
    # result = await session.execute(
    #     select(UserChat).filter(
    #         and_(UserChat.user_tg_id == message.from_user.id,
    #              UserChat.chat_tg_id == message.chat.id)))
    #
    # # select(UserChat).where(
    # #     and_(
    # #         UserChat.user_tg_id == message.from_user.id,
    # #         UserChat.chat_tg_id == message.chat.id)
    # # ).first()
    # # )
    # user = result.scalars().first()
    # print("_____________________________")
    # if user:
    #     print('from db:')
    #     print('     user: ' + str(user.user_tg_id))
    #     print('     chat: ' + str(user.chat_tg_id))
    #     print('     mute: ' + str(user.mute_time))
    # print('from msg:')
    # print('     user: ' + str(message.from_user.id))
    # print('     chat: ' + str(message.chat.id))
    # print("_____________________________")
    maybe_username = message.reply_to_message.from_user.username
    username = '@' + maybe_username if maybe_username else (message.reply_to_message.from_user.first_name or "")
    str_forever = f"""<i>Пользователь {username} забанен навсегда<i>"""
    str_temporary = "<i>Пользователь {username} забанен до {time} (время серверное)</i>"
    ban_period = get_restriction_period(message.text)
    ban_end_date = message.date + timedelta(seconds=ban_period)

    await bot.ban_chat_member(
        chat_id=message.chat.id,
        user_id=message.reply_to_message.from_user.id,
        until_date=ban_end_date,
    )

    if ban_period == 0:
        await message.reply(str_forever)
    else:
        await message.reply(str_temporary.format(
            username=username,
            time=ban_end_date.strftime("%d.%m.%Y %H:%M")
        ))
    await message.delete()
    delete_msg = await message.answer(text="заглушка ban user" + str(message.from_user.id))
    await delete_msg.delete()


@router.message(
    Command(commands=['mute', 'm']),
    F.reply_to_message,
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_mute_command(message: Message, user_repo: UserRepo, bot: Bot):
    logger.debug(f"start process cmd /mute, user with id:{message.from_user.id}")
    chat_id = message.chat.id
    admin_ids = await user_repo.find_admin_ids_by_chat_id(chat_id=chat_id)
    logger.debug(f"find admins id for chat with id:{chat_id}, result:{admin_ids} ")

    CANT_RESTRICT_ADMIN_MSG = "Нельзя ограничить админа"
    if message.reply_to_message.from_user.id in admin_ids:
        logger.debug(f"Попытка ограничить пользователя с правами администратора .Нельзя ограничить админа")
        await message.reply(CANT_RESTRICT_ADMIN_MSG)
        return

    # If a message is sent on behalf of channel, then we can only ban it
    if message.reply_to_message.sender_chat is not None and message.reply_to_message.is_automatic_forward is None:
        await bot.ban_chat_sender_chat(message.chat.id, message.reply_to_message.sender_chat.id)
        logger.debug(f"Channel with id:{message.reply_to_message.sender_chat.id}  is banned forever")
        await message.reply('Канал забанен навсегда')
        return

    restriction_period = get_restriction_period(message.text)
    restriction_end_date = message.date + timedelta(seconds=restriction_period)

    maybe_username = message.reply_to_message.from_user.username
    username = '@' + maybe_username if maybe_username else (message.reply_to_message.from_user.first_name or "")

    str_forever = f"""<i>Пользователь {username}  переведён в режим «только чтение» навсегда <i>"""
    str_temporary = "<i>Пользователь {username} переведён в режим «только чтение» до {time} (время серверное)</i>"
    permissions = types.ChatPermissions()

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=permissions,
            until_date=restriction_end_date
        )
    except exc.TelegramBadRequest as e:
        logger.debug(
            f"В БД устаревшая информация(после выключения бота). Попытка огрничить права администратора с id:{message.reply_to_message.from_user.id}")
        if e.message.endswith('user is an administrator of the chat'):
            await message.reply(CANT_RESTRICT_ADMIN_MSG)
            await user_repo.add(
                UserChat(chat_tg_id=message.chat.id, user_tg_id=message.reply_to_message.from_user.id, isAdmin=True))

    if restriction_period == 0:
        await message.reply(str_forever)
    else:
        await message.reply(str_temporary.format(
            username=username,
            time=restriction_end_date.strftime("%d.%m.%Y %H:%M")
        ))


@router.message(
    Command(commands=['admins_update', 'au']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_update_admins_command(message: Message, user_repo: UserRepo):
    logger.debug(f"Start process cmd ( '/admins_update' or '/au' ), user with id:{message.from_user.id}")
    admins = await message.chat.get_administrators()
    admin_models = list(map(lambda a: UserChat(user_tg_id=a.user.id, chat_tg_id=message.chat.id, isAdmin=True), admins))
    admin_ids = list(map(lambda a: a.user.id, admins))
    chat_id = message.chat.id
    logger.debug(f"get admins chat with id:{chat_id}, result admin ids:{admin_ids}")
    await user_repo.remove_users_by_chat_id(chat_id=chat_id, user_ids=admin_ids)
    await user_repo.add_all(admin_models)


def get_restriction_period(text: str) -> int:
    """
    Extract restriction period (in seconds) from text using regex search

    :param text: text to parse
    :return: restriction period in seconds (0 if nothing found, which means permanent restriction)
    """
    multipliers = {"m": 60, "h": 3600, "d": 86400}
    if match := re.search(restriction_time_regex, text):
        time, modifier = match.groups()
        return int(time) * multipliers[modifier]
    return 0
