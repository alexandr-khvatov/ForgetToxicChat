# import logging
# from src.config.config import config
# from aiogram import Bot, types, Dispatcher
#
# API_TOKEN = 'BOT_TOKEN_HERE'
#
# # webhook settings
# WEBHOOK_HOST = 'https://your.domain'
# WEBHOOK_PATH = '/path/to/api'
# WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
#
# # webserver settings
# WEBAPP_HOST = 'localhost'  # or ip
# WEBAPP_PORT = 3055
#
# logging.basicConfig(level=logging.INFO)
#
# bot: Bot = Bot(
#     token=config.tg_bot.token,
#     parse_mode='HTML')
# dp: Dispatcher = Dispatcher()
# await bot.delete_webhook(drop_pending_updates=True)
# await bot.set_webhook()
#
#
# async def on_startup(dp):
#     await bot.set_webhook(WEBHOOK_URL)
#     # insert code here to run it after start
#
#
# async def on_shutdown(dp):
#     logging.warning('Shutting down..')
#
#     # insert code here to run it before shutdown
#
#     # Remove webhook (not acceptable in some cases)
#     await bot.delete_webhook()
#
#     # Close DB connection (if used)
#     await dp.storage.close()
#     await dp.storage.wait_closed()
#
#     logging.warning('Bye!')
#
#
#
# if __name__ == '__main__':
#     start_webhook(
#         dispatcher=dp,
#         webhook_path=WEBHOOK_PATH,
#         on_startup=on_startup,
#         on_shutdown=on_shutdown,
#         skip_updates=True,
#         host=WEBAPP_HOST,
#         port=WEBAPP_PORT,
#     )