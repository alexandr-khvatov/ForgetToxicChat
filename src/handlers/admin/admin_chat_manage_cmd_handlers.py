import asyncio
import logging
import pprint
import re
from datetime import timedelta

from aiogram import Router, Bot, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, User as AiUser, Chat as AiChat

from src.db.database import Database
from src.db.models.chat import Chat
from src.db.models.userchat import UserChat
from src.db.repository.chat_repo import ChatRepo
from src.db.repository.user_repo import UserRepo
from src.filters.chat_type import ChatTypeFilter
from src.filters.is_admin import IsChatAdmin
from src.keyboards.keyboard_bot_setup import make_kb_bot_settings
from src.lexicon.lexicon_ru import LEXICON_COMMANDS

restriction_time_regex = re.compile(r'(\b[1-9][0-9]*)([mhd]\b)')

router: Router = Router()

logger = logging.getLogger(__name__)


@router.message(
    Command(commands=['setup']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_setup_command(message: Message, chat_repo: ChatRepo, bot: Bot):
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


@router.message(
    Command(commands=['unban']),
    F.reply_to_message,
    ChatTypeFilter(chat_type=["supergroup"]),
    IsChatAdmin())
async def process_unban_command(message: Message, bot: Bot):
    maybe_username_actor = message.from_user.username
    username_unban_actor = '@' + maybe_username_actor if maybe_username_actor else (
            message.from_user.first_name or "")

    maybe_username_unban_user = message.reply_to_message.from_user.username
    username_unban_user = '@' + maybe_username_unban_user if maybe_username_unban_user else (
            message.reply_to_message.from_user.first_name or "")
    await bot.unban_chat_member(
        chat_id=message.chat.id,
        user_id=message.reply_to_message.from_user.id,
        only_if_banned=True,
    )
    delete_msg = await message.answer(text=f'{username_unban_actor} разблокировал {username_unban_user}')


@router.message(
    Command(commands=['ban']),
    F.reply_to_message,
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin())
async def process_ban_command(message: Message, db: Database, bot: Bot):
    CANT_RESTRICT_ADMIN_MSG = "Нельзя ограничить админа"
    # if message.reply_to_message.from_user.id in admin_ids:
    isAdmin = await db.user.is_admin(user_id=message.reply_to_message.from_user.id, chat_id=message.chat.id)
    if isAdmin:
        logger.debug("Попытка ограничить пользователя с правами администратора .Нельзя ограничить админа")
        await message.reply(CANT_RESTRICT_ADMIN_MSG)
        return

    maybe_username = message.reply_to_message.from_user.username
    username = '@' + maybe_username if maybe_username else (message.reply_to_message.from_user.first_name or "")
    str_forever = f"""<i>Пользователь {username} забанен навсегда</i>"""
    str_temporary = "<i>Пользователь {username} забанен</i>"
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
            # time=ban_end_date.strftime("%d.%m.%Y %H:%M")
        ))


@router.message(
    Command(commands=['unmute', 'um']),
    F.reply_to_message,
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_unmute_command(message: Message, user_repo: UserRepo, bot: Bot):
    logger.debug("start process cmd /mute, user with id: %s", message.from_user.id)
    chat_id = message.chat.id
    admin_ids = await user_repo.find_admin_ids_by_chat_id(chat_id=chat_id)
    logger.debug("find admins id for chat with id:{%s}, result:{%s} ", chat_id, admin_ids)

    CANT_RESTRICT_ADMIN_MSG = "Нельзя ограничить админа"
    if message.reply_to_message.from_user.id in admin_ids:
        logger.debug("Попытка ограничить пользователя с правами администратора .Нельзя ограничить админа")
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

    str_forever = f"""<i>Пользователь {username}  переведён в режим «только чтение» навсегда </i>"""
    str_temporary = "<i>Пользователь {username} переведён в режим «только чтение» </i>"
    permissions = types.ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=permissions,
            # until_date=restriction_end_date
        )
    except TelegramBadRequest as e:
        logger.debug(
            f"В БД устаревшая информация(после выключения бота). Попытка огрничить права администратора с id:{message.reply_to_message.from_user.id}")
        if e.message.endswith('user is an administrator of the chat'):
            await message.reply(CANT_RESTRICT_ADMIN_MSG)
            await user_repo.add(
                UserChat(chat_tg_id=message.chat.id, user_tg_id=message.reply_to_message.from_user.id, isAdmin=True))

    await message.reply(text=f'Режим "только чтение" выкл. для пользователя: {username}')


@router.message(
    Command(commands=['mute', 'm']),
    F.reply_to_message,
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_mute_command(message: Message, db: Database, bot: Bot):
    logger.debug("start process cmd /mute, user with id: %s", message.from_user.id)
    chat_id = message.chat.id
    # admin_ids = await user_repo.find_admin_ids_by_chat_id(chat_id=chat_id)
    # logger.debug("find admins id for chat with id:{%s}, result:{%s} ", chat_id, admin_ids)

    CANT_RESTRICT_ADMIN_MSG = "Нельзя ограничить админа"
    # if message.reply_to_message.from_user.id in admin_ids:
    isAdmin = await db.user.is_admin(user_id=message.reply_to_message.from_user.id, chat_id=message.chat.id)
    if isAdmin:
        logger.debug("Попытка ограничить пользователя с правами администратора .Нельзя ограничить админа")
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

    str_forever = f"""<i>Пользователь {username}  переведён в режим «только чтение» навсегда </i>"""
    str_temporary = "<i>Пользователь {username} переведён в режим «только чтение» </i>"
    permissions = types.ChatPermissions()

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.reply_to_message.from_user.id,
            permissions=permissions,
            until_date=restriction_end_date
        )
    except TelegramBadRequest as e:
        logger.debug(
            f"В БД устаревшая информация(после выключения бота). Попытка огрничить права администратора с id:{message.reply_to_message.from_user.id}")
        if e.message.endswith('user is an administrator of the chat'):
            await message.reply(CANT_RESTRICT_ADMIN_MSG)
            await db.user.add(
                UserChat(chat_tg_id=message.chat.id, user_tg_id=message.reply_to_message.from_user.id, isAdmin=True))

    if restriction_period == 0:
        await message.reply(str_forever)
    else:
        await message.reply(str_temporary.format(
            username=username,
            # time=restriction_end_date.strftime("%d.%m.%Y %H:%M")
        ))


@router.message(
    Command(commands=['info', 'i']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_info_command(message: Message, db: Database, bot: Bot):
    if message.reply_to_message:
        replay_user = message.reply_to_message.from_user
        if bot.id == replay_user.id:
            delete_stat_msg = await message.reply(text="(???___???)", parse_mode='HTML')
            await asyncio.sleep(10)
            await message.delete()
            await delete_stat_msg.delete()
            return
        user_id = replay_user.id
        chat_id = message.chat.id
        user: UserChat = await db.user.find_user(user_id=user_id, chat_id=chat_id)
        user_warnings_active = user.num_warnings
        user_total_warnings = user.total_warnings
        user_sent_messages = user.message_counter

        username = get_username(replay_user)
    else:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user: UserChat = await db.user.find_user(user_id=user_id, chat_id=chat_id)
        user_warnings_active = user.num_warnings
        user_total_warnings = user.total_warnings
        user_sent_messages = user.message_counter
        username = get_username(message.from_user)

    user_info_stat_msg = f'''
📌    <b>Пользователь</b>
{username} [id : <b><code>{user_id}</code></b>]

<b>Активных предупреждений:</b>
⚠️  →  <b>{user_warnings_active}</b>

<b>Предупреждений всего:</b>
⚠️  →  <b>{user_total_warnings}</b>

<b>Сообщений обработано:</b>
📨   →  <b>{user_sent_messages}</b>'''
    delete_stat_msg = await message.reply(text=user_info_stat_msg, parse_mode='HTML')
    await asyncio.sleep(10)
    await message.delete()
    await delete_stat_msg.delete()


@router.message(
    Command(commands=['chatinfo', 'ci']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_chatinfo_command(message: Message, db: Database):
    user_id = message.from_user.id
    chat_id = message.chat.id

    chat_warnings_active = await db.user.get_chat_warnings_active(chat_id=chat_id)
    logger.debug(f'chat_warnings_active: {chat_warnings_active}')
    chat_total_warnings = await db.user.get_chat_warnings_total(chat_id=chat_id)
    logger.debug(f'chat_total_warnings: {chat_total_warnings}')
    chat_sent_messages = await db.user.get_chat_num_messages(chat_id=chat_id)

    chat_username = get_chat_username(message.chat)
    chat_info_stat_msg = f'''
📌   <b>Чат</b> 
<b>{chat_username}</b>
[id : <b><code>{chat_id}</code></b>]

<b>Активных предупреждений:</b>
⚠️  →  <b>{chat_warnings_active}</b>

<b>Предупреждений всего:</b>
⚠️  →  <b>{chat_total_warnings}</b>

<b>Сообщений обработано:</b>
📨   →  <b>{chat_sent_messages}</b>'''
    await message.answer(text=chat_info_stat_msg, parse_mode='HTML')


@router.message(
    Command(commands=['ping']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_ping_command(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    ping_msg = f'Пользователь id : <b>{user_id}</b>\nЧат id: <b>{chat_id}</b>'
    await message.answer(text=ping_msg, parse_mode='HTML')


@router.message(
    Command(commands=['help']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_help_command(message: Message):
    cmd = ['<b>Список команд бота\n</b>']
    for key, value in LEXICON_COMMANDS.items():
        cmd.append(f'{key} - {value}')
    help_msg = '\n'.join(cmd)
    await message.answer(text=help_msg, parse_mode='HTML')


@router.message(
    Command(commands=['admins_update', 'au']),
    ChatTypeFilter(chat_type=["group", "supergroup"]),
    IsChatAdmin()
)
async def process_update_admins_command(message: Message, user_repo: UserRepo):
    logger.debug(f"Start process cmd ( '/admins_update' or '/au' ), user with id:{message.from_user.id}")
    admins = await message.chat.get_administrators()
    pprint.pprint(admins)
    chat_id = message.chat.id
    new_admins: list[UserChat] = list(
        map(lambda a: UserChat(user_tg_id=a.user.id, chat_tg_id=chat_id, isAdmin=True), admins))
    new_admin_ids = list(map(lambda x: x.user_tg_id, new_admins))

    old_admins: list[UserChat] = await user_repo.find_admins_by_chat_id(chat_id=chat_id)

    for old_admin in old_admins:
        if old_admin.user_tg_id not in new_admin_ids:
            print(f'user id: {old_admin.user_tg_id}, isAdmin: {old_admin.isAdmin}')
            new_admins.append(UserChat(user_tg_id=old_admin.user_tg_id, chat_tg_id=old_admin.chat_tg_id, isAdmin=False))

    for a in new_admins:
        print(f'user id: {a.user_tg_id}, isAdmin: {a.isAdmin}')
    await user_repo.update_or_insert_all(new_admins)

    await message.delete()


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


def get_username(user: AiUser) -> str:
    maybe_username = user.username
    username = '@' + maybe_username if maybe_username else (user.first_name or "")
    return username


def get_chat_username(chat: AiChat) -> str:
    maybe_username = chat.title
    username = maybe_username if maybe_username else ('@' + chat.username or chat.first_name or "")
    return username
