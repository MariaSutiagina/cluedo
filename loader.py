from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from settings import API_TOKEN

from django.core.wsgi import get_wsgi_application  # Джанговские штуки, чтоб использовать ORM
_django_app = get_wsgi_application()  # Джанговские штуки, чтоб использовать ORM

from botstate import machine


bot: Bot = Bot(token=API_TOKEN)

dp: Dispatcher = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

engine: machine.Machine = machine.Machine(bot, None)