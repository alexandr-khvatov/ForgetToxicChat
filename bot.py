import asyncio
import logging

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config.config import config
from handlers import admin_handlers, moderator_handlers, update_event_admins_handlers, admin_bot_setup_handlers, \
    admin_add_badword_handlers
from keyboards.main_menu import set_main_menu
from middleware.db import DbSessionMiddleware

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s '
               u'[%(asctime)s] - %(name)s - %(message)s')
    logger.info('Starting bot')

    # Creating DB engine for PostgreSQL
    engine = create_async_engine(config.db.build_connection_str(), future=True, echo=True)

    # Creating DB connections pool
    db_pool = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Define bot, dispatcher and include routers to dispatcher
    bot: Bot = Bot(
        token=config.tg_bot.token,
        parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    # Setting up the main menu of the bot
    await set_main_menu(bot)

    # Register middlewares
    dp.message.outer_middleware(DbSessionMiddleware(db_pool))
    dp.message.middleware(DbSessionMiddleware(db_pool))
    dp.callback_query.middleware(DbSessionMiddleware(db_pool))
    dp.chat_member.middleware(DbSessionMiddleware(db_pool))

    # Register handlers
    dp.include_router(admin_add_badword_handlers.router)
    dp.include_router(admin_bot_setup_handlers.router)
    dp.include_router(admin_handlers.router)
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
