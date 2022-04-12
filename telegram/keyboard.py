import json
from typing import List, Union, Tuple, Optional
from aiogram import Bot, Dispatcher, executor, types

from data import models


class SimpleKeyboard(object):

    @staticmethod
    def get_markup(message: models.Message) -> types.InlineKeyboardMarkup:
        def _parse_key(x):
            kk = x.split(':')
            return {'row':int(kk[0][1:]), 'col': int(kk[1][1:]), 'key':x}

        keyboard_markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup(
            row_width=3)

        markup =  json.loads(message.actions)
        if markup is not None:
            markup_rows = {}
            markup_keys = map(lambda x: _parse_key(x), markup.keys())
            for k in sorted(list(markup_keys), key = lambda x: (x['row'], x['col'])):
                rn = k['row']
                r = markup_rows.get(rn, None)
                if r is None:
                    markup_rows[rn] = []
                markup_rows[rn].append(types.InlineKeyboardButton(markup[k['key']]['name'], callback_data=markup[k['key']]['action']))

        for r in range(len(markup_rows)):
            keyboard_markup.row(*markup_rows[r])

        return keyboard_markup


class QuizKeyboard(object):
    hint_text: str = "Подсказка"
    menu_text: str = "В меню"

    @staticmethod
    def get_markup(quiz: models.FreeAnswerQuiz) -> types.ReplyKeyboardMarkup:
        keyboard: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(
            resize_keyboard=True)
        if quiz.hint is not None:
            keyboard.add(types.KeyboardButton(text=QuizKeyboard.hint_text))
        keyboard.add(types.KeyboardButton(text=QuizKeyboard.menu_text))
        return keyboard


class DashboardKeyboard(object):
    COLUMN_NUM_SEPARATOR: int = 3

    @staticmethod
    def get_markup(tasks_name: List[str]) -> Union[types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove]:
        if len(tasks_name) == 0:
            return types.ReplyKeyboardRemove()
        keyboard: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(
            resize_keyboard=True)

        buttons: List[types.KeyboardButton] = []

        tasks_name.sort()
        for i in range(1, len(tasks_name) + 1):
            buttons.append(types.KeyboardButton(tasks_name[i-1]))
            if i % DashboardKeyboard.COLUMN_NUM_SEPARATOR == 0 or i == len(tasks_name):
                keyboard.add(*buttons)
                buttons = []

        return keyboard
