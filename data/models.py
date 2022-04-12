import functools
from typing import List
from django.db import models
from aiogram import types
from botstate import states
from aioutils import sync_to_async


class User(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)
    telegram_id = models.CharField(max_length=255, null=True)
    chat_id = models.IntegerField(null=True)
    state = models.CharField(max_length=255)
    substate = models.IntegerField(null=True)

    # solving_mode = models.BooleanField(default=False)
    # current_task = models.CharField(max_length=255, null=True)
    # solved_task_list = models.CharField(max_length=512, default='')

    @classmethod
    @sync_to_async
    def create(cls, message: types.Message) -> 'User':
        user: 'User' = cls(name=message.from_user.first_name,
                           chat_id=message.chat.id,
                           telegram_id=message.from_user.username,
                           state=states.State.GREETING.name)
        user.save()
        return user

    @staticmethod
    @sync_to_async
    def get_user_by_chat_id(chat_id: int) -> 'User':
        return User.objects.get(chat_id=chat_id)

    @sync_to_async
    def async_save(self) -> None:
        self.save()

    @staticmethod
    def add_solved_task(user: 'User', task_name: str) -> None:
        SEPARATOR: str = '#'
        task_list: List[str] = User.get_task_list(user)
        task_list.append(task_name)
        user.solved_task_list = SEPARATOR.join(task_list)
        user.save()

    @staticmethod
    def check_solve_task(user: 'User', task_name: str) -> bool:
        task_list: List[str] = User.get_task_list(user)
        return True if task_name in task_list else False

    @staticmethod
    def get_not_done_tasks(user: 'User', all_tasks: List['FreeAnswerQuiz']) -> List[str]:
        all_tasks_set = {task.name for task in all_tasks}

        task_list: List[str] = User.get_task_list(user)
        done_tasks = set(task_list)
        not_done_set: set = all_tasks_set - done_tasks
        result: List[str] = []
        for name in not_done_set:
            if '*' not in name or '**' in name:
                continue
            if (name[:-1] in not_done_set):
                result.append(name[:-1])
            else:
                result.append(name)

        for name in not_done_set:
            if '**' not in name:
                continue
            if (name[:-1] not in not_done_set) and (name[:-2] not in not_done_set):
                result.append(name)
        return result

    @staticmethod
    def get_task_list(user: 'User') -> List[str]:
        SEPARATOR: str = '#'
        return user.solved_task_list.split(SEPARATOR)


class Message(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)
    text_content = models.TextField(null=True)
    media_name = models.CharField(max_length=255, null=True)

    group = models.CharField(max_length=255, null=True)
    order = models.IntegerField(null=True)

    actions = models.TextField(null=True)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_message_by_name(name: str) -> 'Messages':
        return Message.objects.get(name=name)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def filter_message_by_group(group: str) -> 'Messages':
        return Message.objects.filter(group=group)


class LinkedMessages(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)

    group = models.CharField(max_length=255, null=True)

    actions = models.TextField(max_length=255, null=True)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_linked_message_by_name(name: str) -> 'LinkedMessages':
        return LinkedMessages.objects.get(name=name)


class FreeAnswerQuiz(models.Model):

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)
    question = models.ForeignKey(
        Message, on_delete=models.SET_NULL, null=True, related_name='question')

    right_answer = models.CharField(max_length=255)

    hint = models.ForeignKey(
        Message, on_delete=models.SET_NULL, null=True, related_name='hint')
    wrong_answer_action = models.ForeignKey(
        Message, on_delete=models.SET_NULL, null=True, related_name='wrong_answer_action')
    right_answer_action = models.ForeignKey(
        Message,  on_delete=models.SET_NULL, null=True, related_name='related_primary_manual_roats')

    next_quiz = models.ForeignKey(
        'FreeAnswerQuiz',  on_delete=models.SET_NULL, null=True, related_name='next_quiz_fk')

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_quiz_by_name(name: str) -> 'FreeAnswerQuiz':
        return FreeAnswerQuiz.objects.get(name=name)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_quiz_all() -> List['FreeAnswerQuiz']:
        return FreeAnswerQuiz.objects.all()

    @staticmethod
    def get_answers_list(quiz: 'FreeAnswerQuiz') -> List[str]:
        SEPARATOR: str = '#'
        return quiz.right_answer.split(SEPARATOR)


class MagicCommand(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)

    command = models.CharField(max_length=255)

    action = models.ForeignKey(
        Message,  on_delete=models.SET_NULL, null=True)

    unixtime = models.IntegerField(null=True)

    @staticmethod
    @sync_to_async
    def get_magic_command_by_name(name: str) -> 'MagicCommand':
        return MagicCommand.objects.get(name=name)
