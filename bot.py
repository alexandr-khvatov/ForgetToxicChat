import asyncio
import logging

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from before_start import fetch_admins
from src.config.config import config
from src.db.repository.user_repo import UserRepo
from src.handlers.admin import admin_bot_setup_handlers, admin_add_badword_handlers
from src.handlers.admin import admin_chat_manage_cmd_handlers, admin_show_badword_handlers
from src.handlers.moderator import moderator_handlers
from src.handlers.service_events import update_event_admins_handlers, group_join
from src.httpclient.http_client import HttpClient
from src.keyboards.main_menu import set_main_menu
from src.middleware.db_md import DbSessionMiddleware
from src.middleware.http_client import HttpClientMiddleware

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s '
               u'[%(asctime)s] - %(name)s - %(message)s')
    logger.info('Starting bot')
    # Creating DB engine for PostgreSQL
    engine: AsyncEngine = create_async_engine(config.db.build_connection_str(), future=True, echo=True)
    # Creating DB connections pool
    db_pool = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with db_pool() as session:
        ur = UserRepo(session)
    # Define bot, dispatcher and include routers to dispatcher
    bot: Bot = Bot(
        token=config.tg_bot.token,
        parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    await fetch_admins(user_repo=ur, bot=bot)
    # Setting up the main menu of the bot
    await set_main_menu(bot)
    httpClient = HttpClient(base_url=config.tg_bot.toxicity_service_url)
    httpClientMiddleware = HttpClientMiddleware(httpclient=httpClient)

    dbSessionMiddleware = DbSessionMiddleware(db_pool)
    # Register middlewares
    dp.message.outer_middleware(dbSessionMiddleware)
    dp.message.middleware(dbSessionMiddleware)
    dp.message.middleware(httpClientMiddleware)
    dp.edited_message.outer_middleware(dbSessionMiddleware)
    dp.edited_message.middleware(dbSessionMiddleware)
    dp.callback_query.middleware(dbSessionMiddleware)
    dp.chat_member.middleware(dbSessionMiddleware)
    dp.my_chat_member.middleware(dbSessionMiddleware)

    # Register handlers
    dp.include_router(admin_show_badword_handlers.router)
    dp.include_router(admin_add_badword_handlers.router)
    dp.include_router(admin_bot_setup_handlers.router)
    dp.include_router(admin_chat_manage_cmd_handlers.router)
    dp.include_router(group_join.router)
    dp.include_router(update_event_admins_handlers.router)
    dp.include_router(moderator_handlers.router)

    # Start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error('Bot stopped!')
