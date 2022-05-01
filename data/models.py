import functools
from typing import List
from unicodedata import name
from django.db import models
from django.db.models import Q
from aiogram import types
from botstate import states
from aioutils import sync_to_async

class CluedoGame(models.Model):
    id = models.AutoField(primary_key=True)

    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Начало игры')
    finished_at = models.DateTimeField(verbose_name='Окончание игры', null=True)

    distances = models.TextField(max_length=1023, blank=True, null=True, verbose_name='Расстояния между помещениями')
    secret = models.TextField(max_length=1023, null=True, blank=True, verbose_name='Загадка игры (кто, место, орудие) в формате {"person": id, "place": id, "weapon": id}')
    open_cards = models.TextField(max_length=1023, null=True, blank=True, verbose_name='Открытые в процессе игры карты в формате {"<type>": id}, где type = person, place, weapon')
    alive = models.IntegerField(default=-1, verbose_name='осталось игроков')
    started = models.BooleanField(default=False, verbose_name='игра началась')
    won = models.BooleanField(default=False, verbose_name=' Победа в игре')
    turn_number = models.IntegerField(default=-1, verbose_name='')
    winner = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Победитель')

    accuse_place = models.ForeignKey('CluedoPlace', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Подозрение на место преступления')
    accuse_person = models.ForeignKey('CluedoPerson', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Подозрение на преступника')
    accuse_weapon = models.ForeignKey('CluedoWeapon', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Подозрение на орудие')


    @classmethod
    @sync_to_async
    def create(cls, old_game: 'CluedoGame'=None, room: 'CluedoRoom'=None, winner: 'User'=None, 
            secret: str = '', distances: str = '', open_cards:str='', started:bool=False, alive:int=0, won:bool=True,
            turn_number:int=0,
            accused_place: 'CluedoPlace' = None, accused_person: 'CluedoPerson'=None, accused_weapon: 'CluedoWeapon'=None) -> 'CluedoGame':
        if old_game is not None:
            game: 'CluedoGame' = old_game
        else:
            game: 'CluedoGame' = cls()
        game.room = room
        game.winner = winner
        game.secret = secret
        game.open_cards = open_cards
        game.distances = distances
        game.started = started
        game.alive = alive
        game.won = won
        game.turn_number = turn_number
        game.accuse_place = accused_place
        game.accuse_person = accused_person
        game.accuse_weapon = accused_weapon

        game.save()
        return game
    
    @sync_to_async
    def async_save(self) -> None:
        self.save()

class CluedoPlayer(models.Model):
    id = models.AutoField(primary_key=True)

    alive = models.BooleanField(default=True, verbose_name='игрок жив')
    number = models.IntegerField(default=-1, verbose_name='номер игрока в порядке хода')
    dice_throw_result = models.IntegerField(default=-1, verbose_name='результат броска кубика')
    known_cards = models.TextField(max_length=1023, null=True, blank=True, verbose_name='Известные игроку карты')
    cards = models.TextField(max_length=1023, null=True, blank=True, verbose_name='карты игрока')

    user = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь, который является игроком')
    game = models.ForeignKey(CluedoGame, on_delete=models.CASCADE, blank=True, null=True, verbose_name='ссылка на игру')

    place = models.ForeignKey('CluedoPlace', on_delete=models.CASCADE, blank=True, null=True, verbose_name='место, в котором находится игрок')
    alias = models.ForeignKey('CluedoPerson', on_delete=models.CASCADE, blank=True, null=True, verbose_name='игровой псевдоним игрока')

    @classmethod
    @sync_to_async
    def create(cls, old_player: 'CluedoPlayer'=None, user: 'User'=None, game: CluedoGame=-1, number:int=-1, dice_throw_result:int=None, place: 'CluedoPlace'=None, alias: 'CluedoPerson'=None, alive:bool = True, 
                    cards: str='', known_cards: str=''):
        if old_player is not None:
            player = old_player
        else:
            player: 'CluedoPlayer' = cls()
            player.user = user
        player.game = game
        player.number = number
        player.dice_throw_result = dice_throw_result
        player.place = place
        player.alias = alias
        player.alive = alive
        player.cards = cards
        player.known_cards = known_cards

        player.save()
        return player
    
    @sync_to_async
    def async_save(self) -> None:
        self.save()


class CluedoRoom(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64, verbose_name='Название комнаты')
    game = models.OneToOneField(CluedoGame, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Игра в комнате')
    
    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_all_rooms() -> 'CluedoRooms':
        return CluedoRoom.objects.all()

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_room_by_id(id) -> 'CluedoRoom':
        return CluedoRoom.objects.get(id=id)

    @sync_to_async
    def async_save(self) -> None:
        self.save()


    def __str__(self):
        return self.name


class CluedoPerson(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Имя персонажа')
    room=models.ForeignKey(CluedoRoom, on_delete=models.CASCADE,  verbose_name='Комната')

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_room_people(room: CluedoRoom) -> 'CluedoPeople':
        return CluedoPerson.objects.filter(room=room).order_by('id')

    def get_name_str(self):
        return 'подозреваемый:' + self.name

    def __str__(self):
        return self.name


class CluedoPlace(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Место преступления')
    room=models.ForeignKey(CluedoRoom, on_delete=models.CASCADE,  verbose_name='Комната')

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_room_places(room: CluedoRoom) -> 'CluedoPlaces':
        return CluedoPlace.objects.filter(room=room).order_by('id')

    def get_name_str(self):
        return 'место:' + self.name
        
    def __str__(self):
        return self.name

class CluedoWeapon(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=64,  verbose_name='Орудие убийства')
    room=models.ForeignKey(CluedoRoom, on_delete=models.CASCADE,  verbose_name='Комната')

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_room_weapons(room: CluedoRoom) -> 'CluedoWeapons':
        return CluedoWeapon.objects.filter(room=room).order_by('id')

    def get_name_str(self):
        return 'орудие:' + self.name
        
    def __str__(self):
        return self.name

class User(models.Model):
    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255, verbose_name='Имя пользователя')
    telegram_id = models.CharField(max_length=255, null=True, verbose_name='id пользователя в Telegram')
    chat_id = models.IntegerField(null=True, verbose_name='Чат')
    last_message_id = models.CharField(max_length=64, blank=True, null=True, verbose_name='ID последнего сообщения пользователя в Telegram')
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

