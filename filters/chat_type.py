import logging

from aiogram.filters import BaseFilter
from aiogram.types import Message

logger = logging.getLogger(__name__)


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: str | list):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            logger.debug(f"Chat type is:{message.chat.type}, allowed chat types: {self.chat_type}")
            return message.chat.type in self.chat_type
