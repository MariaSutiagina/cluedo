import logging
import ssl
from settings import WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT, WEBHOOK_URL, WEBHOOK_CERT, WEBHOOK_KEY

from aiogram.utils.executor import start_webhook
from aiogram import types

from handlers.handler import bot, dp 

async def on_startup(dp) -> None:
    logging.info('Starting bot...')
    logging.info(f'... at {WEBHOOK_URL}')
    if WEBHOOK_CERT:
        await bot.set_webhook(WEBHOOK_URL, certificate=types.InputFile(WEBHOOK_CERT))
        logging.info('Certificate was uploaded successfully.')
    else:    
        await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp) -> None:
    logging.info('Shutting down...')
    logging.info('Delete webhook...')
    await bot.delete_webhook()
    logging.info('Webhook was deleted.')
    logging.info('The bot was disabled.')


if __name__ == '__main__':
    if WEBHOOK_CERT and WEBHOOK_KEY:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_cert_chain(WEBHOOK_CERT, WEBHOOK_KEY)    
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
            ssl_context=ssl_context
        )
    else:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT
        )
