import json
from typing import Dict, List, Union, Tuple, Optional
from aiogram import Bot, Dispatcher, executor, types
from cluedo.game import Game, Player

from data import models


class SimpleKeyboard(object):

    @staticmethod
    def get_markup_dict(message: models.Message) -> Dict:
        def _parse_key(x):
            kk = x.split(':')
            return {'row':int(kk[0][1:]), 'col': int(kk[1][1:]), 'key':x}

        markup =  json.loads(message.actions)
        markup_rows = {}
        if markup is not None:
            markup_keys = map(lambda x: _parse_key(x), markup.keys())
            for k in sorted(list(markup_keys), key = lambda x: (x['row'], x['col'])):
                rn = k['row']
                r = markup_rows.get(rn, None)
                if r is None:
                    markup_rows[rn] = []
                markup_rows[rn].append(types.InlineKeyboardButton(markup[k['key']]['name'], callback_data=markup[k['key']]['action']))

        return markup_rows

    @staticmethod
    def get_markup(message: models.Message) -> types.InlineKeyboardMarkup:

        keyboard_markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup(
            row_width=3)

        markup_rows = SimpleKeyboard.get_markup_dict(message)

        for r in range(len(markup_rows)):
            keyboard_markup.row(*markup_rows[r])

        return keyboard_markup, types.ParseMode.MARKDOWN

class RoomsKeyboard(object):

    @staticmethod
    def get_markup(message: models.Message) -> types.InlineKeyboardMarkup:
        keyboard_markup, _ = SimpleKeyboard.get_markup(message)
        rooms = models.CluedoRoom.get_all_rooms()
        markup_rows = {}
        for idx, room in enumerate(rooms):
            r = markup_rows.get(idx, None)
            if r is None:
                markup_rows[idx] = []
            markup_rows[idx].append(types.InlineKeyboardButton(f'Комната: {room.name}', callback_data=f'{{"room": {room.id}}}'))

        for r in range(len(markup_rows)):
            keyboard_markup.row(*markup_rows[r])

        return keyboard_markup, types.ParseMode.HTML

class RoomKeyboard(object):

    @staticmethod
    def get_markup(message: models.Message, room) -> types.InlineKeyboardMarkup:
        keyboard_markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup(
            row_width=3)
        
        markup_rows = {0:[], 1:[]}
        markup_rows[0].append(types.InlineKeyboardButton('СТАРТ', callback_data=f'{{"room": {room.id}}}'))
        markup_rows[1].append(types.InlineKeyboardButton('выйти из комнаты', callback_data='to_rooms'))

        for r in range(len(markup_rows)):
            keyboard_markup.row(*markup_rows[r])

        return keyboard_markup, types.ParseMode.HTML

class PlayerTurnKeyboard(object):

    @staticmethod
    def get_markup(message: models.Message, player: Player, player_turn: Player, game: Game) -> types.InlineKeyboardMarkup:
        keyboard_markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup(
            row_width=3)
         
        markup_rows = SimpleKeyboard.get_markup_dict(message)
        markup_row = []
        if player == player_turn:
            if player.user.state == 'GAME':
                markup_row.append(types.InlineKeyboardButton('Бросить кости', callback_data='throw_dice'))
                keyboard_markup.row(*markup_row)
            elif player.user.state == 'THROW_DICE':
                markup_row.append(types.InlineKeyboardButton('К выбору локации', callback_data='select_place'))
                keyboard_markup.row(*markup_row)
            elif player.user.state == 'SELECT_PLACE':
                for place in player.accessible_places:
                    markup_row = []
                    markup_row.append(types.InlineKeyboardButton(place.name, callback_data=f'{{"new_location": {place.id}}}'))
                    keyboard_markup.row(*markup_row)
            elif player.user.state == 'ACCUSE_PERSON':
                for person in filter(lambda x: type(x) is models.CluedoPerson, player.cards):
                    markup_row = []
                    markup_row.append(types.InlineKeyboardButton(person.name, callback_data=f'{{"accused_person": {person.id}}}'))
                    keyboard_markup.row(*markup_row)
            elif player.user.state == 'ACCUSE_WEAPON':
                for weapon in filter(lambda x: type(x) is models.CluedoWeapon, player.cards):
                    markup_row = []
                    markup_row.append(types.InlineKeyboardButton(weapon.name, callback_data=f'{{"accused_weapon": {weapon.id}}}'))
                    keyboard_markup.row(*markup_row)
            elif player.user.state == 'CONFIRM_ACCUSE':
                    markup_row = []
                    markup_row.append(types.InlineKeyboardButton('Высказать подозрение', callback_data=f'{{"suspiction": {{"place":{game.accused_place.id}}}, {{"person": {game.accused_person.id}}}, {{"weapon": {game.accused_weapon.id}}} }}'))
                    markup_row.append(types.InlineKeyboardButton('Выдвинуть обвинение', callback_data=f'{{"accuse": {{"place":{game.accused_place.id}}}, {{"person": {game.accused_person.id}}}, {{"weapon": {game.accused_weapon.id}}} }}'))
                    keyboard_markup.row(*markup_row)
            

        for r in range(len(markup_rows)):
            keyboard_markup.row(*markup_rows[r])
        
        return keyboard_markup, types.ParseMode.HTML


# class QuizKeyboard(object):
#     hint_text: str = "Подсказка"
#     menu_text: str = "В меню"

#     @staticmethod
#     def get_markup(quiz: models.FreeAnswerQuiz) -> types.ReplyKeyboardMarkup:
#         keyboard: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(
#             resize_keyboard=True)
#         if quiz.hint is not None:
#             keyboard.add(types.KeyboardButton(text=QuizKeyboard.hint_text))
#         keyboard.add(types.KeyboardButton(text=QuizKeyboard.menu_text))
#         return keyboard


# class DashboardKeyboard(object):
#     COLUMN_NUM_SEPARATOR: int = 3

#     @staticmethod
#     def get_markup(tasks_name: List[str]) -> Union[types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove]:
#         if len(tasks_name) == 0:
#             return types.ReplyKeyboardRemove()
#         keyboard: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(
#             resize_keyboard=True)

#         buttons: List[types.KeyboardButton] = []

#         tasks_name.sort()
#         for i in range(1, len(tasks_name) + 1):
#             buttons.append(types.KeyboardButton(tasks_name[i-1]))
#             if i % DashboardKeyboard.COLUMN_NUM_SEPARATOR == 0 or i == len(tasks_name):
#                 keyboard.add(*buttons)
#                 buttons = []

#         return keyboard
