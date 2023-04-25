import asyncio
import datetime
import logging
from datetime import timedelta

from aiogram import Router, Bot, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiohttp import ServerDisconnectedError

from config.config import config
from db.models.chat import Chat
from db.models.chat_mode_restriction import Mode
from db.models.userchat import UserChat
from db.repository.chat_repo import ChatRepo
from db.repository.user_repo import UserRepo
from filters.chat_type import ChatTypeFilter
from filters.is_admin import IsChatAdmin
from httpclient.http_client import HttpClient

router: Router = Router()

logger = logging.getLogger(__name__)


@router.message(ChatTypeFilter(chat_type=["group", "supergroup"]), F.text, ~IsChatAdmin())
async def process_moderator(message: Message, httpclient: HttpClient, chat_repo: ChatRepo, user_repo: UserRepo,
                            bot: Bot):
    await _process_moderator(message, httpclient, chat_repo, user_repo, bot)


@router.edited_message(ChatTypeFilter(chat_type=["group", "supergroup"]), F.text, ~IsChatAdmin())
async def process_moderator(message: Message, httpclient: HttpClient, chat_repo: ChatRepo, user_repo: UserRepo,
                            bot: Bot):
    await _process_moderator(message, httpclient, chat_repo, user_repo, bot)


async def _process_moderator(message: Message, httpclient: HttpClient, chat_repo: ChatRepo, user_repo: UserRepo,
                             bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_settings: Chat = await chat_repo.find_chat_settings(chat_id=chat_id)
    user: UserChat = await user_repo.find_user(user_id=user_id, chat_id=chat_id)

    start_time = datetime.datetime.now()
    msg_sentiment = await check_toxicity(httpclient, message)
    end_time = datetime.datetime.now()
    latency = (end_time - start_time).total_seconds() * 1000

    if msg_sentiment['sentiment'] == 1:
        await handle_toxicity(
            message=message,
            user=user,
            chat_settings=chat_settings,
            user_repo=user_repo,
            bot=bot)

    # send debug message
    msg = f'''
        <b>
        probs: {list(map(lambda x: format(x, '.2f'), msg_sentiment['probabilities']))}\n
        label: {msg_sentiment['sentiment']}
        latency: {latency:.3f} ms
        </b>
        '''
    del_msg = await message.answer(text=msg, parse_mode='HTML')
    # send debug message

    # clear debug message
    await asyncio.sleep(5)
    await del_msg.delete()


async def check_toxicity(httpclient, message):
    try:
        result = await httpclient.post(url='/predict', json={'text': message.text})
    except ServerDisconnectedError as ex:
        result = await httpclient.post(url='/predict', json={'text': message.text})
    return result


async def handle_toxicity(message: Message, user: UserChat, chat_settings: Chat, user_repo: UserRepo, bot: Bot):
    mode = chat_settings.mode
    if mode == Mode.remove.name:
        await message.delete()
        return

    limit = chat_settings.num_warnings
    rating = user.num_warnings

    if not (rating < limit):
        match mode:
            case Mode.mute.name:
                logger.debug("Mode: {%s}", Mode.mute.name)
                restriction_period = chat_settings.mute_time
                restriction_end_date = message.date + timedelta(seconds=restriction_period)

                maybe_username = message.from_user.username
                username = '@' + maybe_username if maybe_username else (
                        message.from_user.first_name or "")

                str_forever = f"""<i>{username}  переведён в режим «только чтение» навсегда </i>"""
                str_temporary = "<i>{username} переведён в режим «только чтение» до {time} (время серверное)</i>"
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
                        await user_repo.add(
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
                str_temporary = "<i>{username} забанен до {time} (время серверное)</i>"
                ban_end_date = message.date + timedelta(seconds=ban_period)
                if ban_period == 0:
                    await message.reply(str_forever, parse_mode="HTML")
                else:
                    await message.reply(str_temporary.format(
                        username=username,
                        time=ban_end_date.strftime("%d.%m.%Y %H:%M")
                    ), parse_mode="HTML")
        await user_repo.rating_reset(user_id=message.from_user.id, chat_id=message.chat.id)
    else:
        new_rating = rating + 1
        await message.answer(text=f'Вы получили предупреждение {new_rating}/{limit}', parse_mode='HTML')
        await user_repo.rating_increment(user_id=message.from_user.id, chat_id=message.chat.id)
