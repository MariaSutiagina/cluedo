import asyncio
import logging
from typing import Optional, List

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



class ExitState(BotState):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        self.linked_message_name = 'EXIT'
        self.context: Optional[message.MessageContext] = None
        self._prepare_context()

    def _prepare_context(self) -> None:
        self.context: message.ExitContext = message.ExitContext(self.bot)


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
        else:
            return self


# class DashboardState(object):
#     def __init__(self, bot: Bot) -> None:
#         self.bot = bot

#         self.previous_state: Optional[State] = None
#         self.next_state: Optional[str] = State.QUIZ.name
#         self.default_state: Optional[str] = State.DASHBOARD.name
#         self.finish_state: Optional[str] = State.WAITING.name

#         self.outcoming_message = 'welcome_menu'
#         self.finish_message = 'finish'

#         self._prepare_context()

#     def _prepare_context(self) -> None:
#         self.context: message.DashboardContext = message.DashboardContext(
#             self.bot)

#     async def _next_state_handler(self, user: models.User, task: str) -> None:
#         logging.info('The user [chat_id:%d] has moved to state %s', user.chat_id, self.next_state)
#         user.state = self.next_state
#         user.substate = None
#         user.solving_mode = False
#         user.current_task = task
#         await user.async_save()

#     async def _finish_state_handler(self, user: models.User) -> None:
#         logging.info('The user [chat_id:%d] has moved to state %s', user.chat_id, self.finish_state)
#         user.state = self.finish_state
#         user.substate = None
#         user.solving_mode = False
#         user.current_task = None
#         await user.async_save()

#     async def incoming_handler(self, user: models.User, text: str, message_id: int) -> None:
#         result: Optional[str] = await self.context.run_incoming(user, text, message_id)
#         if result is not None:
#             await self._next_state_handler(user, result)

#     async def outcoming_handler(self, user: models.User, not_done_tasks: Optional[List[str]] = None) -> None:
#         message: str = self.outcoming_message
#         if not_done_tasks is None:
#             not_done_tasks: List[str] = await self._get_not_done_tasks(user)

#         if len(not_done_tasks) == 0:
#             await self._finish_state_handler(user)
#             message = self.finish_message
#         await self.context.run_outcoming(user, message, not_done_tasks)

#     def _check_corectness(self, text: str, not_done_tasks: List[str]) -> str:
#         return True if text in not_done_tasks else False

#     async def _get_not_done_tasks(self, user: models.User) -> List[str]:
#         all_tasks: List[models.FreeAnswerQuiz] = models.FreeAnswerQuiz.get_quiz_all()
#         return models.User.get_not_done_tasks(user, all_tasks)

#     async def handler(self, user: models.User, text: str, message_id: int, init: bool = False) -> None:
#         not_done_tasks: List[str] = await self._get_not_done_tasks(user)
#         if init or not self._check_corectness(text, not_done_tasks):
#             await self.outcoming_handler(user, not_done_tasks)
#         else:
#             await self.incoming_handler(user, text, message_id)


# class QuizState(object):
#     def __init__(self, bot: Bot, user: models.User) -> None:
#         self.bot = bot

#         self.previous_state: Optional[State] = State.DASHBOARD.name

#         self.task_name: str = user.current_task

#         self.context: Optional[message.QuizContext] = None

#     async def _get_quiz(self, name: str) -> models.FreeAnswerQuiz:
#         return models.FreeAnswerQuiz.get_quiz_by_name(name)

#     async def set_context(self) -> None:
#         quiz: models.FreeAnswerQuiz = await self._get_quiz(self.task_name)
#         self.context = message.QuizContext(self.bot, quiz)

#     async def _back_to_menu(self, user: models.User) -> None:
#         user.state = self.previous_state
#         user.solving_mode = False
#         user.current_task = None
#         await user.async_save()

#     async def run_oucoming(self, user: models.User) -> None:
#         await self.context.run_oucoming(user, 'question')
#         user.solving_mode = True
#         await user.async_save()
#         return None

#     async def right_answer_handler(self, user: models.User) -> None:
#         logging.info('The user [chat_id:%d] solve task: %s', user.chat_id, user.current_task)
#         solved_task: str = user.current_task
#         models.User.add_solved_task(user, solved_task)
#         await self._back_to_menu(user)

#     async def run_incoming(self, user: models.User, test: str) -> Optional[bool]:
#         text_type: str = await self.context.run_incoming(user, test)
#         if text_type == 'back':
#             await self._back_to_menu(user)
#             return True
#         elif text_type == 'right_answer':
#             await self.right_answer_handler(user)
#             return True
#         return None

#     async def handler(self, user: models.User, text: str) -> Optional[bool]:
#         if not user.solving_mode:
#             return await self.run_oucoming(user)
#         else:
#             return await self.run_incoming(user, text)


# class WaitingState(object):
#     def __init__(self, bot: Bot, user: models.User) -> None:
#         self.bot = bot

#         self._prepare_context()

#     def _prepare_context(self) -> None:
#         self.context = message.WaitingContext(self.bot)

#     async def handler(self, user: models.User, text: str, message_id: Optional[int]) -> None:
#         await self.context.run_incoming(user, text, message_id)


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
