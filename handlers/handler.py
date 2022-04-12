import time
import logging

from aiogram import types

from loader import dp, bot, engine

@dp.message_handler()
async def general_message_handler(message: types.Message) -> None:
    try:
        await engine.message_handler(message)
    except Exception:
        logging.exception('Unhandled exception by message: "%s"', message.text)
        logging.warning("Reset user[chat_id:%d] status", message.chat.id)
        await engine.reset_user_by_message(message)
        

@dp.callback_query_handler()
async def process_callback_button1(callback_query: types.CallbackQuery) -> None:
    await engine.callback_handler(callback_query)


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def clean_handler(message: types.Message) -> None:
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
