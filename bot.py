import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

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

    # await fetch_admins(user_repo=ur, bot=bot)  РАСКОММЕНТИРОВАТЬ

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

    # try:
    #     await bot.delete_webhook(drop_pending_updates=True)
    #     await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    # finally:
    #     await bot.session.close()

    try:
        if not config.tg_bot.webhook_domain:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        else:
            # Suppress aiohttp access log completely
            aiohttp_logger = logging.getLogger("aiohttp.access")
            aiohttp_logger.setLevel(logging.CRITICAL)

            # Setting webhook
            await bot.set_webhook(
                url=config.tg_bot.webhook_domain + config.tg_bot.webhook_path,
                # certificate=open(config.tg_bot.ssl, 'r'),
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types()

            )

            logger.info(f"Path to CERT {config.tg_bot.ssl}",)

            # f = open('etc-ssl/hello.txt', 'r')
            f = open(config.tg_bot.ssl, 'r')
            logger.info(*f)
            info = await bot.get_webhook_info()
            logger.info(info)

            # Creating an aiohttp application
            app = web.Application()
            SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=config.tg_bot.webhook_path)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host=config.tg_bot.app_host, port=config.tg_bot.app_port)
            await site.start()

            # Running it forever
            await asyncio.Event().wait()
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error('Bot stopped!')
