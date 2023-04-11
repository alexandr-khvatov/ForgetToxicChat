from typing import Dict, List, Union

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

from config import config
from db.models.userchat import UserChat


async def fetch_admins(user_repo:UserChat,bot: Bot) -> Dict:


    return result
