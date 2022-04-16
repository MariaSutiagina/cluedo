import asyncio
import json
import logging
from typing import Optional, List
from django.db.models import Q

from .states import State

from data import models
from telegram import message
from aiogram import Bot, types

class BotState(object):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.linked_message_name = 'NOMESSAGE'

        self.context: Optional[message.MessageContext] = None

    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        raise NotImplementedError()

    """
    обработчик события в данном состоянии
    """
    async def handler(self, user: models.User, message_payload: Optional[int] = None, message_id: Optional[int] = None, outcoming_flag: bool = False) -> Optional[bool]:
        return await self.send_and_save(user, message_payload, message_id)

    """
    посылает пользователю телеграм сообщение, которое определяется текущим состоянием 
    и сохраняет состояние пользователя в БД
    """
    async def send_and_save(self, user: models.User, message_payload, message_id: Optional[int] = None) -> Optional[bool]:
        user_substate: int = self.get_user_current_substate(user)
        message: models.Message = self.context.get_message(user_substate)
        await self.context.send_message(user, message, message_id)
        await user.async_save()
        return None

    def get_user_current_substate(self, user: models.User) -> str:
        if user.substate == None:
            user.substate = 0
        return user.substate

    def get_message(self, substate: int) -> Optional[models.Message]:
        if substate >= len(self.message_list):
            return None
        return self.message_list[substate]

    async def get_linked_message(self) -> models.LinkedMessages:
        return models.LinkedMessages.get_linked_message_by_name(self.linked_message_name)

    async def get_rooms(self) -> 'CluedoRooms':
        return models.CluedoRoom.get_all_rooms()



class ExitState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'EXIT'
        self.context: Optional[message.MessageContext] = None
        self._prepare_context()

    def _prepare_context(self) -> None:
        self.context: message.ExitContext = message.ExitContext(self.bot)

class RoomsState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'ROOMS'
        self.context: Optional[message.MessageContext] = None

    async def set_context(self) -> None:
        linked_message: models.LinkedMessages = await self.get_linked_message()
        self.context = message.RoomsContext(self.bot, linked_message)
        await self.context.init_context()    

    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        if message_payload ==  'next':
            user.substate += 1
            return self
        elif message_payload == 'prev':
            user.substate = user.substate - 1 if user.substate > 0 else 0
            return self
        elif message_payload == 'home':
            user.substate = 0
            return self
        elif message_payload == 'to_rules':
            user.state = 'RULES'
            user.substate = 0
            state = RulesState(self.bot)
            await state.set_context()
            return state
        elif message_payload == 'to_greeting':
            user.state = 'GREETING'
            user.substate = 0
            state = GreetingState(self.bot)
            await state.set_context()
            return state
        else:
            try:
                room = json.loads(message_payload)
                if room.get('room', 0) > 0:
                    user.state = 'ROOM'
                    user.substate = 0
                    user.room = models.CluedoRoom.get_room_by_id(room['room'])
                    state = RoomState(self.bot)
                    await state.set_context()
                    return state
                else:
                    raise ValueError
            except ValueError as e:
                return self


class RoomState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'ROOM'
        self.context: Optional[message.MessageContext] = None

    async def set_context(self) -> None:
        linked_message: models.LinkedMessages = await self.get_linked_message()
        self.context = message.RoomContext(self.bot, linked_message)
        await self.context.init_context()    


    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        if message_payload == 'to_rooms':
            user.state = 'ROOMS'
            user.substate = 0
            user.room = None
            state = RoomsState(self.bot)
            await state.set_context()
            return state
        else:
            try:
                room = json.loads(message_payload)
                if room.get('room', 0) > 0:
                    users = await models.User.get_all_players_are_not_ready(user)
                    if len(users) > 0:
                        user.state = 'GAME_WAITING'
                        user.substate = 0
                        state = GameWaitingState(self.bot)
                    else:
                        user.state = 'GAME'
                        user.substate = 0
                        state = GameState(self.bot)
                    await state.set_context()
                    return state
                else:
                    raise ValueError
            except ValueError as e:
                return self

class GameWaitingState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'GAME_WAITING'
        self.context: Optional[message.MessageContext] = None

    async def set_context(self) -> None:
        linked_message: models.LinkedMessages = await self.get_linked_message()
        self.context = message.GameWaitingContext(self.bot, linked_message)
        await self.context.init_context()    

    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        if message_payload == 'to_room':
            user.state = 'ROOM'
            user.substate = 0
            state = RoomState(self.bot)
            await state.set_context()
            return state
        elif message_payload == 'to_game':
            user.state = 'GAME'
            user.substate = 0
            state = GameState(self.bot)
            await state.set_context()
            return state
        else:
            return self

class GameState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'GAME'
        self.context: Optional[message.MessageContext] = None

    async def set_context(self) -> None:
        linked_message: models.LinkedMessages = await self.get_linked_message()
        self.context = message.GameContext(self.bot, linked_message)
        await self.context.init_context()    

    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        if message_payload == 'to_room':
            user.state = 'ROOM'
            user.substate = 0
            state = RoomState(self.bot)
            await state.set_context()
            return state
        else:
            return self


class RulesState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'RULES'
        self.context: Optional[message.MessageContext] = None

    async def set_context(self) -> None:
        linked_message: models.LinkedMessages = await self.get_linked_message()
        self.context = message.MessageContext(self.bot, linked_message)
        await self.context.init_context()    

    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        if message_payload ==  'next':
            user.substate += 1
            return self
        elif message_payload == 'prev':
            user.substate = user.substate - 1 if user.substate > 0 else 0
            return self
        elif message_payload == 'home':
            user.substate = 0
            return self
        elif message_payload == 'to_exit':
            user.state = '-'
            user.substate = 0
            return ExitState(self.bot)
        elif message_payload == 'to_greeting':
            user.state = 'GREETING'
            user.substate = 0
            state = GreetingState(self.bot)
            await state.set_context()
            return state
        elif message_payload == 'to_rooms':
            user.state = 'ROOMS'
            user.substate = 0
            state = RoomsState(self.bot)
            await state.set_context()
            return state
        else:
            return self

class GreetingState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.linked_message_name = 'GREETING'
        self.context: Optional[message.MessageContext] = None

    async def set_context(self) -> None:
        linked_message: models.LinkedMessages = await self.get_linked_message()
        self.context = message.MessageContext(self.bot, linked_message)
        await self.context.init_context()
    

    """
    возвращает новое состояние объекта в зависимости от текущего 
    """
    async def update_state(self, user: models.User, message_payload, message_id):
        if message_payload ==  'next':
            user.substate += 1
            return self
        elif message_payload == 'prev':
            user.substate = user.substate - 1 if user.substate > 0 else 0
            return self
        elif message_payload == 'home':
            user.substate = 0
            return self
        elif message_payload == 'to_exit':
            user.state = '-'
            user.substate = 0
            return ExitState(self.bot)
        elif message_payload == 'to_rules':
            user.state = 'RULES'
            user.substate = 0
            state = RulesState(self.bot)
            await state.set_context()
            return state
        elif message_payload == 'to_rooms':
            user.state = 'ROOMS'
            user.substate = 0
            state = RoomsState(self.bot)
            await state.set_context()
            return state
        else:
            return self


class Machine(object):
    def __init__(self, bot: Bot, loop: asyncio.AbstractEventLoop) -> None:
        self.bot: Bot = bot
        self.event_loop: asyncio.AbstractEventLoop = loop

    async def _create_new_user(self, tg_message: types.Message) -> None:
        user: models.User = await models.User.create(tg_message)
        return user

    async def _get_user_by_message(self, tg_message: types.Message) -> Optional[models.User]:
        chat_id: int = tg_message.chat.id
        user_object: models.User = None
        try:
            user_object = await models.User.get_user_by_chat_id(chat_id)
        except models.User.DoesNotExist:
            user_object = await self._create_new_user(tg_message)
        return user_object

    async def _get_current_state(self, user: models.User) -> BotState:
        state: BotState = None
        if user.state == State.GREETING.name:
            state = GreetingState(self.bot)
            await state.set_context()
        elif user.state == State.EXIT.name:
            state = ExitState(self.bot)
        elif user.state == State.RULES.name:
            state = RulesState(self.bot)
            await state.set_context()
        elif user.state == State.ROOMS.name:
            state = RoomsState(self.bot)
            await state.set_context()
        elif user.state == State.ROOM.name:
            state = RoomState(self.bot)
            await state.set_context()
        elif user.state == State.GAME_WAITING.name:
            state = GameWaitingState(self.bot)
            await state.set_context()
        elif user.state == State.GAME.name:
            state = GameState(self.bot)
            await state.set_context()
        else:
            state = GreetingState(self.bot)
            await state.set_context()
        
        return state


    async def message_handler(self, tg_message: types.Message) -> None:
        user: models.User = await self._get_user_by_message(tg_message)
        state: BotState = await self._get_current_state(user)
        new_state: BotState = await state.update_state(user, tg_message.text, tg_message.message_id)
        await new_state.handler(user, tg_message.text, tg_message.message_id, outcoming_flag=False)

    async def callback_handler(self, callback_query: types.CallbackQuery) -> None:
        user: models.User = await self._get_user_by_message(callback_query.message)
        state: BotState = await self._get_current_state(user)
        new_state: BotState = await state.update_state(user, str(callback_query.data), callback_query.message.message_id)
        await new_state.handler(user, str(callback_query.data), callback_query.message.message_id, outcoming_flag=False)

    async def reset_user_by_message(self, tg_message: types.Message) -> None:
         user_object: models.User = await self._get_user_by_message(tg_message)
         user_object.state = 'GREETING'
         user_object.substate = None
         user_object.solving_mode = False
         user_object.substate = None
         user_object.current_task = None

         await user_object.async_save()
