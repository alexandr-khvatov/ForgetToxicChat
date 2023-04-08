from aiogram.filters import BaseFilter
from aiogram.types import ChatMemberUpdated

"""
Note: Currently these filters don't check for group ownership transfer
Consider this a #TODO
"""


class AdminAdded(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.new_chat_member.status in ("creator", "administrator")


class AdminRemoved(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.old_chat_member.status in ("creator", "administrator") \
               and event.new_chat_member.status not in ("creator", "administrator")


class InvitedRemoved(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.old_chat_member.status in ("creator", "administrator") \
               and event.new_chat_member.status not in ("creator", "administrator")
