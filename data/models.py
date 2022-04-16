import functools
from typing import List
from django.db import models
from django.db.models import Q
from aiogram import types
from botstate import states
from aioutils import sync_to_async


class CluedoRoom(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Название комнаты')

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_all_rooms() -> 'CluedoRooms':
        return CluedoRoom.objects.all()

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_room_by_id(id) -> 'CluedoRoom':
        return CluedoRoom.objects.get(id=id)

    def __str__(self):
        return self.name


class CluedoPerson(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Имя персонажа')
    room=models.ForeignKey(CluedoRoom, on_delete=models.CASCADE,  verbose_name='Комната')
    def __str__(self):
        return self.name

class CluedoPlace(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Место преступления')
    room=models.ForeignKey(CluedoRoom, on_delete=models.CASCADE,  verbose_name='Комната')
    def __str__(self):
        return self.name

class CluedoWeapon(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Орудие убийства')
    room=models.ForeignKey(CluedoRoom, on_delete=models.CASCADE,  verbose_name='Комната')
    def __str__(self):
        return self.name

class User(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, verbose_name='Имя пользователя')
    telegram_id = models.CharField(max_length=255, null=True, verbose_name='id пользователя в Telegram')
    chat_id = models.IntegerField(null=True, verbose_name='Чат')
    state = models.CharField(max_length=255, verbose_name='Статус')
    substate = models.IntegerField(null=True, verbose_name='Подстатус')
    room = models.ForeignKey(CluedoRoom, blank=True, null=True, on_delete=models.SET_NULL, verbose_name='Комната')

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

    @staticmethod
    @sync_to_async
    def get_all_players_are_not_ready(user) :
        return User.objects.filter(Q(room=user.room) & ~Q(state='GAME_WAITING') & ~Q(id=user.id))

    @sync_to_async
    def async_save(self) -> None:
        self.save()

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
        return Message.objects.filter(group=group).order_by('id')


class LinkedMessages(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)

    group = models.CharField(max_length=255, null=True)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_linked_message_by_name(name: str) -> 'LinkedMessages':
        return LinkedMessages.objects.get(name=name)

