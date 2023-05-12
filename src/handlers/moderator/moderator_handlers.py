import asyncio
import datetime
import logging
from datetime import timedelta

from aiogram import Router, Bot, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiohttp import ServerDisconnectedError

from src.config.config import config
from src.db.database import Database
from src.db.models.chat import Chat
from src.db.models.chat_message import ChatMessage
from src.db.models.chat_mode_restriction import Mode
from src.db.models.userchat import UserChat
from src.filters.chat_type import ChatTypeFilter
from src.filters.is_admin import IsChatAdmin
from src.httpclient.http_client import HttpClient

router: Router = Router()

logger = logging.getLogger(__name__)


@router.message(ChatTypeFilter(chat_type=["group", "supergroup"]), F.text)
async def process_moderator_new_msg(message: Message, httpclient: HttpClient, db: Database, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # keep statistics of sent messages
    await db.user.messages_increment(user_id=user_id, chat_id=chat_id)
    await db.msg.add(ChatMessage(user_tg_id=user_id,
                                 chat_tg_id=chat_id,
                                 message_id=message.message_id,
                                 message_text=message.text,
                                 message_len=len(message.text.split())))

    is_admin = await check_is_admin(message=message, db=db)
    logger.debug('check_is_admin, result={%s} user_id=%s,\n chat_id=%s,\n message.chat.type=%s', is_admin, user_id,
                 chat_id,
                 message.chat.type, )
    logger.debug(not is_admin)
    if not is_admin:
        logger.debug('run _process_moderator user_id=%s,\n chat_id=%s,\n message.chat.type=%s', user_id,
                     chat_id,
                     message.chat.type, )
        await _process_moderator(message=message, httpclient=httpclient, db=db, bot=bot)


@router.edited_message(ChatTypeFilter(chat_type=["group", "supergroup"]), F.text, ~IsChatAdmin())
async def process_moderator_edit_msg(message: Message, httpclient: HttpClient, db: Database, bot: Bot):
    logger.debug(f"LOG: {httpclient._base_url}")
    await _process_moderator(message=message, httpclient=httpclient, db=db, bot=bot)


async def _process_moderator(message: Message, httpclient: HttpClient, db: Database, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.debug('call _process_moderator user_id=%s,\n chat_id=%s,\n message.chat.type=%s,\n message.text=%s', user_id,
                 chat_id,
                 message.chat.type, message.text)
    chat_settings: Chat = await db.chat.find_chat_settings(chat_id=chat_id)
    user: UserChat = await db.user.find_user(user_id=user_id, chat_id=chat_id)

    start_time = datetime.datetime.now()
    msg_sentiment = await check_toxicity(httpclient, message)
    end_time = datetime.datetime.now()
    latency = (end_time - start_time).total_seconds() * 1000
    logger.debug('call toxic service with message.text %s', message.text)
    if msg_sentiment['sentiment'] == 1:
        await handle_toxicity(
            message=message,
            user=user,
            chat_settings=chat_settings,
            db=db,
            bot=bot)
        await db.msg.mark_msg_as_toxic(user_id=user_id, chat_id=chat_id, msg_id=message.message_id)

    # send debug message
    msg = f'''
        <b>
        probs: {list(map(lambda x: format(x, '.2f'), msg_sentiment['probabilities']))}\n
        label: {msg_sentiment['sentiment']}
        latency: {latency:.3f} ms
        </b>
        '''
    logger.debug(msg)
    # del_msg = await message.answer(text=msg, parse_mode='HTML')
    # clear debug message
    # await asyncio.sleep(5)
    # await del_msg.delete()

    # send debug message



async def check_toxicity(httpclient, message):
    try:
        result = await httpclient.post(url='/predict', json={'text': message.text})
        logger.debug('check_toxicity result:', result)
    except ServerDisconnectedError:
        logger.error('toxicity service ServerDisconnectedError ')
        result = await httpclient.post(url='/predict', json={'text': message.text})
    logger.debug('check_toxicity result:', result)
    return result


async def handle_toxicity(message: Message, user: UserChat, chat_settings: Chat, db: Database, bot: Bot):
    mode = chat_settings.mode
    if mode == Mode.remove.name:
        await message.delete()
        return

    limit = chat_settings.num_warnings
    rating = user.num_warnings

    if not (rating < limit):
        match mode:
            case Mode.mute.name:
                if message.chat.type in ["supergroup"]:
                    logger.debug("Mode: {%s}", Mode.mute.name)
                    restriction_period = chat_settings.mute_time
                    restriction_end_date = message.date + timedelta(seconds=restriction_period)

                    maybe_username = message.from_user.username
                    username = '@' + maybe_username if maybe_username else (
                            message.from_user.first_name or "")

                    str_forever = f"""<i>{username}  переведён в режим «только чтение» навсегда </i>"""
                    str_temporary = "<i>{username} переведён в режим «только чтение» </i>"
                    permissions = types.ChatPermissions()
                    try:
                        await bot.restrict_chat_member(
                            chat_id=message.chat.id,
                            user_id=message.from_user.id,
                            permissions=permissions,
                            until_date=restriction_end_date
                        )
                    except TelegramBadRequest as e:
                        if e.message.endswith('user is an administrator of the chat'):
                            logger.debug(
                                f"В БД устаревшая информация(после выключения бота). Попытка огрничить права администратора с id:{message.from_user.id}")
                            CANT_RESTRICT_ADMIN_MSG = "Нельзя ограничить админа"
                            await message.reply(CANT_RESTRICT_ADMIN_MSG)
                            await db.user.add(
                                UserChat(chat_tg_id=message.chat.id, user_tg_id=message.from_user.id,
                                         isAdmin=True))
                    if restriction_period == 0:
                        await message.reply(str_forever)
                    else:
                        await message.reply(str_temporary.format(
                            username=username,
                            time=restriction_end_date.strftime("%d.%m.%Y %H:%M")
                        ))
            case Mode.ban.name:
                logger.debug("Mode: {%s}", Mode.ban.name)
                ban_period = config.tg_bot.ban_period
                await bot.ban_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    until_date=ban_period,
                )
                maybe_username = message.from_user.username
                username = '@' + maybe_username if maybe_username else (
                        message.from_user.first_name or "")
                str_forever = f"""<i>{username} забанен навсегда</i>"""
                str_temporary = "<i>{username} забанен </i>"
                ban_end_date = message.date + timedelta(seconds=ban_period)
                if ban_period == 0:
                    await message.reply(str_forever, parse_mode="HTML")
                else:
                    await message.reply(str_temporary.format(
                        username=username,
                    ), parse_mode="HTML")
        await db.user.rating_reset(user_id=message.from_user.id, chat_id=message.chat.id)
    else:
        new_rating = rating + 1
        await message.answer(text=f'Вы получили предупреждение {new_rating}/{limit}', parse_mode='HTML')
        await db.user.rating_increment(user_id=message.from_user.id, chat_id=message.chat.id)


async def check_is_admin(message: types.Message, db: Database) -> bool:
    user_id = message.from_user.id
    chat_id = message.chat.id
    isAdmin = await db.user.is_admin(user_id=user_id, chat_id=chat_id)

    # logger.debug(f"User with id:{user_id} is Admin for chat with chat_id:{chat_id}, result: {isAdmin}")

    return isAdmin
