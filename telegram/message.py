import os
import json
import logging
import random
from typing import List, Optional, Dict, Union

from aiogram import Bot, types
from django.db.models import Q
import settings
from .keyboard import RoomKeyboard, RoomsKeyboard, SimpleKeyboard #, QuizKeyboard, DashboardKeyboard
from botstate import states
from utils import MediaCache
from data import models
from cluedo.game import Game, Player


class BaseContext(object):
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.media_cache: MediaCache = MediaCache()

    async def update(self, user: models.User, message_payload: Optional[str] = None, message_id: Optional[int] = None):
        pass

    def _get_media(self, message: models.Message) -> Optional[Union[types.InputFile, str]]:
        if message.media_name is None:
            return None

        file_id: str = self.media_cache.find(message.media_name)
        if file_id is not None:
            return file_id
        try:
            path: str = os.path.join(settings.STATIC_ROOT, message.media_name)
            media_file: types.InputFile = types.InputFile(path)
        except:
            logging.error("static file %s not found.", message.media_name)
            return None
        return media_file

    async def send_msg(self, chat_id, message_id, text, keyboard, mode):
        try:
            await self.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=keyboard, parse_mode=mode)
        except:
            await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode=mode)

    async def send_all(self, users, message_id, text, keyboard, mode):
        for u in users:
            await self.send_msg(u.chat_id, u.last_message_id, text, keyboard, mode)


    def _update_media_cache(self, message: models.Message, response) -> None:
        # -1 for get photo with best quality
        file_id: str = response.photo[-1].file_id
        self.media_cache.update(message.media_name, file_id)

    async def send_with_media(self, user: models.User, message: models.Message, reply_markup: types.ReplyKeyboardMarkup) -> None:
        chat_id: int = user.chat_id
        text: str = message.text_content
        media_file: Optional[Union[types.InputFile, str]
                             ] = self._get_media(message)
        if media_file is not None:
            response: types.Message() = await self.bot.send_photo(chat_id=chat_id, photo=media_file, caption=text, reply_markup=reply_markup, parse_mode=types.ParseMode.MARKDOWN)
            self._update_media_cache(message, response)
        else:
            await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=types.ParseMode.MARKDOWN)


class ExitContext(BaseContext):
    def __init__(self, bot: Bot) -> None:
        super().__init__()
        self.bot: Bot = bot

    async def run_incoming(self, user: models.User, payload_data: str, message_id: int) -> Optional[bool]:
        return await self.run_outcoming(user, message_id)

    def get_message(self, substate: int) -> Optional[models.Message]:
        return None

    async def send_message(self, user: models.User, message: models.Message, message_id: Optional[int]) -> None:
        await self._clear_keyboard_and_text(user, message_id)

    async def _clear_keyboard_and_text(self, user: models.User, message_id: int) -> None:
        await self.send_msg(user.chat_id, message_id, 'Bye!', None, None)


class MessageContext(BaseContext):
    def __init__(self, bot: Bot, linked_message: models.LinkedMessages) -> None:
        super().__init__()
        self.bot: Bot = bot
        self.linked_message: models.LinkedMessages = linked_message
        self.user: Optional[models.User] = None

        self.message_list: Optional[List[models.Message]] = None

    async def init_context(self) -> None:
        message_group: str = self.linked_message.group
        self.message_list = list(models.Message.filter_message_by_group(message_group))
        self.message_list.sort(key=lambda x: x.order)

    def get_message(self, substate: int) -> Optional[models.Message]:
        if substate >= len(self.message_list):
            return None
        return self.message_list[substate]

    async def send_message(self, user: models.User, message: models.Message, message_id: Optional[int]) -> None:
        text: str = message.text_content
        keyboard, mode = SimpleKeyboard.get_markup(message)
        await self.send_msg(user.chat_id, message_id, text, keyboard, mode)

class RoomsContext(MessageContext):
    async def send_message(self, user: models.User, message: models.Message, message_id: Optional[int]) -> None:
        text: str = message.text_content
        keyboard, mode = RoomsKeyboard.get_markup(message)
        await self.send_msg(user.chat_id, message_id, text, keyboard, mode)

class RoomContext(MessageContext):

    def _get_users(self, user):
        users = list(models.User.objects.filter(room=user.room))
        if users:
            return ', '.join(list(map(lambda x: x.name, users)) + [user.name, ])
        else:
            return user.name

    async def send_message(self, user: models.User, message: models.Message, message_id: Optional[int]) -> None:
        users = list(models.User.objects.filter(Q(room=user.room) & ~Q(name=user.name)))
        text: str = f"Комната: {user.room.name}" + '\n'+ \
                    f"В комнате: {self._get_users(user)}" + '\n' + \
                    f"{message.text_content}"

        keyboard, mode = RoomKeyboard.get_markup(message, user.room)
        await self.send_msg(user.chat_id, message_id, text, keyboard, mode)
        for u in users:
            await self.send_msg(u.chat_id, u.last_message_id, text, keyboard, mode)

class GameWaitingContext(MessageContext):

    def _get_users(self, user):
        users = list(models.User.objects.filter(room=user.room))
        if users:
            return ', '.join(map(lambda x: x.name, users))
        else:
            return user.name

    async def send_message(self, user: models.User, message: models.Message, message_id: Optional[int]) -> None:
        users = list(await models.User.get_all_players_are_not_ready(user))
        users_text = ', '.join(map(lambda x: x.name, users))
        text: str = f"Комната: {user.room.name}" + '\n' + \
                    f"В комнате: {self._get_users(user)}" + '\n' + \
                    f"Ожидаем: {users_text}" + '\n' + \
                    f"{message.text_content}"

        keyboard, mode = SimpleKeyboard.get_markup(message)
        await self.send_msg(user.chat_id, message_id, text, keyboard, mode)
        # for u in users:
        #     await self.send_msg(u.chat_id, u.last_message_id, text, keyboard, mode)

class GameContext(MessageContext):
    def __init__(self, bot: Bot, linked_message: models.LinkedMessages) -> None:
        super().__init__(bot, linked_message)
        self.game: Game = None

    def _get_users_in_room(self, users):
        if users:
            return ', '.join(map(lambda x: x.name, users))
        else:
            return random.choice(['пусто', 'пустота', 'никогошеньки', 'нет игроков'])

    async def send_message(self, user: models.User, message: models.Message, message_id: Optional[int]) -> None:
        users = list(models.User.objects.filter(Q(room=user.room) & ~Q(name=user.name)))
        text: str = f"Комната: {user.room.name}" + '\n' + \
                    f"В комнате: {self._get_users_in_room([*users, user])}" + '\n' + \
                    f"{self.game.get_general_game_info()}" + '\n' + \
                    f"{self.game.get_open_cards_info()}" + '\n'
        
        player_turn: Player = self.game.get_player_whos_turn()
        turn_message = f'ХОД ИГРОКА {player_turn.alias.name} ({player_turn.user.name})'+'\n'+f'ЖДЕМ ХОДА {player_turn.alias.name} ({player_turn.user.name})'

        keyboard, mode = SimpleKeyboard.get_markup(message)
        for u in users:
            player: Player = self.game.get_player(u)
            msg_text: str = text + \
                player.get_cards_info() + '\n\n' + \
                player.get_known_cards_info() + '\n\n' + \
                f"ТЫ: {player.alias.name} ({player.user.name})" + '\n' + \
                turn_message
            await self.send_msg(u.chat_id, u.last_message_id, msg_text, keyboard, mode)

        player: Player = self.game.get_player(user)
        msg_text: str = text + \
            player.get_cards_info() + '\n\n' + \
            player.get_known_cards_info() + '\n\n' + \
            f"ТЫ: {player.alias.name} ({player.user.name})" + '\n' + \
            turn_message
        await self.send_msg(user.chat_id, message_id, msg_text, keyboard, mode)

    async def persist_game(self, user: models.User):
        cluedo_game = await models.CluedoGame.create(
            user.room, 
            self.game.winner,
            self.game.get_secret(), 
            self.game.place_distances,
            self.game.get_open_cards(),
            True,
            self.game.alive,
            self.game.won,
            self.game.asking,
            self.game.accusing,
            self.game.asked,
            self.game.choose_place,
            self.game.turn_number
            )

        for p in self.game.players:
            await models.CluedoPlayer.create(
                user,
                cluedo_game, 
                p.number,
                p.place,
                p.alias,
                p.alive,
                p.get_cards(),
                p.get_known_cards()
            )

        user.room.game = cluedo_game
        await user.room.async_save()
        
    async def update(self, user: models.User, message_payload: Optional[str] = None, message_id: Optional[int] = None):
        cluedo_game: models.CluedoGame = user.room.game
        if cluedo_game is None:
            self.game = Game(user)
            self.game.create()
            await self.persist_game(user)
        else:
            self.game = Game(user)
            self.game.from_model(cluedo_game)
        
        

# class QuizContext(BaseContext):
#     def __init__(self, bot: Bot, primary_quiz: models.FreeAnswerQuiz) -> None:
#         super().__init__()
#         self.bot: Bot = bot
#         self.current_quiz: models.FreeAnswerQuiz = primary_quiz
#         self.user: Optional[models.User] = None

#     async def _send_message(self, user: models.User, message: models.Message) -> None:
#         keyboard: types.InlineKeyboardMarkup = QuizKeyboard.get_markup(
#             self.current_quiz)
#         await self.send_with_media(user, message, keyboard)

#     def _get_question(self, quiz: models.FreeAnswerQuiz) -> models.Message:
#         return quiz.question

#     def _get_hint(self, quiz: models.FreeAnswerQuiz) -> models.Message:
#         return quiz.hint

#     def _get_right_answer(self, quiz: models.FreeAnswerQuiz) -> models.Message:
#         return quiz.right_answer_action

#     def _get_wrong_answer(self, quiz: models.FreeAnswerQuiz) -> models.Message:
#         return quiz.wrong_answer_action

#     async def run_oucoming(self, user: models.User, text_type: str) -> str:
#         if text_type == 'question':
#             message: models.Message = self._get_question(self.current_quiz)
#         elif text_type == 'hint':
#             message: models.Message = self._get_hint(self.current_quiz)
#         elif text_type == 'right_answer':
#             message: models.Message = self._get_right_answer(self.current_quiz)
#         elif text_type == 'wrong_answer':
#             message: models.Message = self._get_wrong_answer(self.current_quiz)
#         elif text_type == 'back':
#             return text_type
#         else:
#             raise Exception('Unknown text_type')

#         await self._send_message(user, message)
#         return text_type

#     def _check_right_answer(self, text: str) -> bool:
#         right_answer: List[str] = models.FreeAnswerQuiz.get_answers_list(
#             self.current_quiz)
#         text = text.strip().lower()
#         right_answer = [text.strip().lower() for text in right_answer]
#         return True if text in right_answer else False

#     async def run_incoming(self, user: models.User, text: str, firts_time: bool = False) -> str:
#         text_type: Optional[str] = None

#         if firts_time:
#             text_type = 'question'
#         elif text == QuizKeyboard.hint_text:
#             text_type = 'hint'
#         elif text == QuizKeyboard.menu_text:
#             text_type = 'back'
#         elif self._check_right_answer(text):
#             text_type = 'right_answer'
#         else:
#             text_type = 'wrong_answer'
#         return await self.run_oucoming(user, text_type)


# class DashboardContext(BaseContext):
#     def __init__(self, bot: Bot) -> None:
#         super().__init__()
#         self.bot: Bot = bot
#         self.user: Optional[models.User] = None

#     def _format_text(self, text: str) -> str:
#         return text.strip()

#     async def run_incoming(self, user: models.User, text: str, message_id: int) -> Optional[str]:
#         return self._format_text(text)

#     async def _get_message(self, name: str) -> models.Message:
#         return models.Message.get_message_by_name(name)

#     async def _send_message(self, user: models.User, message: models.Message, not_done_tasks: List[str]) -> None:
#         keyboard: types.ReplyKeyboardMarkup = DashboardKeyboard.get_markup(
#             not_done_tasks)
#         await self.send_with_media(user, message, keyboard)

#     async def run_outcoming(self, user: models.User, message_name: str, not_done_tasks: List[str]) -> None:
#         message: models.Message = await self._get_message(message_name)
#         await self._send_message(user, message, not_done_tasks)


# class WaitingContext(BaseContext):
#     def __init__(self, bot: Bot) -> None:
#         super().__init__()
#         self.bot: Bot = bot
#         self.magic_command = 'magic_command'

#     async def _incorrect_text_handler(self, user: models.User, message_id: int) -> None:
#         await self.bot.delete_message(chat_id=user.chat_id, message_id=message_id)

#     async def _check_correctness(self, user: models.User, text: str) -> bool:
#         magic_command: models.MagicCommand = await models.MagicCommand.get_magic_command_by_name(self.magic_command)

#         if text.strip() != magic_command.command.strip():
#             return False
        
#         message: models.Message = magic_command.action
#         await self.send_with_media(user, message, None)

#         return True

#     async def run_incoming(self, user: models.User, text: str, message_id: int) -> None:
#         result: bool = await self._check_correctness(user, text)
#         if not result:
#             await self._incorrect_text_handler(user, message_id)
