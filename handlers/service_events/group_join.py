from aiogram import types, Router, F, Bot
from aiogram.dispatcher.event.bases import SkipHandler

from config.config import config

router = Router()


@router.message(F.new_chat_members, lambda x: config.tg_bot.remove_joins is True)
async def on_user_join(message: types.Message, bot: Bot):
    # for chat_member in message.new_chat_members:
    #     if chat_member.id == bot.id:
    #         await bot.get_chat_administrators(chat_id=message.chat.id)
    # # print(message.new_chat_members)
    # # print(message)
    raise SkipHandler


@router.message(F.left_chat_member, lambda x: config.tg_bot.remove_joins is True)
async def on_user_left(message: types.Message):
    raise SkipHandler
