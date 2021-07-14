import os
from bot import bot, dp, API_TOKEN
from aiogram.utils.executor import start_webhook


WEBHOOK_HOST = os.environ.get('SITE_URL', '')
WEBHOOK_PATH = '/{}'.format(API_TOKEN)
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH


WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.environ.get('PORT', 8080)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
