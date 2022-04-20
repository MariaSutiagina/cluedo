import json
import random as rd
from typing import Dict, List
from cluedo.distances import Distances
from data import models
from cluedo.field import Field
import utils.card_utils as cu

class Player:
    def __init__(self, user: models.User):
        self.cards: List = []
        self.alive = True
        self.auto = False
        self.known_cards: List = []
        self.number = -1
        self.asked = False
        self.user = user
        self.place = None
        self.alias = None

        self.id = user.id
        self.username = user.name
        if self.username is None:
            self.username = ''

    def set_cards(self, cards):
        self.cards = cards[:] 

    def add_known_cards(self, cards):
        self.known_cards = cards[:] 

    def get_cards(self):
        return cu.cards_to_json(self.cards)

    def get_known_cards(self):
        return cu.cards_to_json(self.known_cards)

    def get_cards_info(self):
        return 'Мои карты:' + ', '.join(map(lambda x: f"{x['type']}:{x['name']}", cu.cards_to_info(self.cards)))

    def get_known_cards_info(self):
        return 'Известные мне карты:' + ', '.join(map(lambda x: f"{x['type']}:{x['name']}", cu.cards_to_info(self.known_cards)))

class Game:
    def __init__(self, user: models.User):
        self.user = user
        self.field = Field(user.room)
        self.secret: Dict = None
        self.place_distances: Distances = None
        self.players = None
        self.opencards = None
        # self.messages_content = ""
        
        self.won = False
        self.winner = None
        self.asking = False
        self.accusing = False
        self.asked = False
        self.choose_place = False

        self.turn_number = 0 

    def create(self):
        self.am_open = (0, 0, 0, 0, 0, 0)
        self.secret = {'person': rd.choice(self.field.people), 'weapon': rd.choice(self.field.weapons), 'place': rd.choice(self.field.places)}
        self.place_distances = Distances.new_dist()
        self.cards = self.field.cards()
        rd.shuffle(self.cards)

        self.players: List[Player] = []
        users: List[models.User] = list(models.User.objects.filter(room=self.user.room))
        rd.shuffle(users)
        for p in users:
            self.players.append(Player(p))

        for c in self.secret.values():
            self.cards.remove(c)

        self.alive = len(self.players)
        self.n = len(self.players)
        self.opencards = self.cards[:self.am_open[self.n]]
        aliases = self.field.get_people()[:]
        places = self.field.get_places()[:]
        # self.messages_content = self.add_general_game_info() + \
        #                         self.add_open_cards_info()

        deal_size = (len(self.cards) - self.am_open[self.n]) // self.n
        for player_idx in range(self.n):
            player: Player = self.players[player_idx]
            player.number = player_idx
            deal = self.cards[self.am_open[self.n] + player_idx * deal_size: self.am_open[self.n] + (player_idx + 1) * deal_size]
            player.set_cards(deal)
            player.add_known_cards(deal)

            player.place = rd.choice(places)
            player.alias = rd.choice(aliases)
            aliases.remove(player.alias)
            
        self.started = True
            
            # player.message_content = f'Ваши карты: {player.cards_in_hand()}'
        
    def get_general_game_info(self):
        return "Карты в игре:" + '\n\t' + \
                 "      Подозреваемые:" + ', '.join(map(lambda x: x.name, self.field.get_people())) + '\n\t' + \
                 "      Места:" + ', '.join(map(lambda x: x.name, self.field.get_places()))  + '\n\t' + \
                 "      Орудия:" + ', '.join(map(lambda x: x.name, self.field.get_weapons()))  + '\n'

    def get_open_cards_info(self):
        if self.opencards:
            return "Известные всем карты:" + ', '.join(map(lambda x: x.name, self.opencards))
        else:
            return "Нет известных всем карт"

    def get_secret(self):
        return json.dumps({'person': self.secret['person'].id, 'weapon': self.secret['weapon'].id, 'place': self.secret['place'].id})

    def get_open_cards(self):
        return cu.cards_to_json(self.opencards)

    def get_player(self, user: models.User):
        for p in self.players:
            if p.user == user:
                return p
        return None

    def get_player_by_number(self, number: int):
        for p in self.players:
            if p.number == number:
                return p
        return None

    def get_player_whos_turn(self):
        for p in self.players:
            if p.number == self.turn_number:
                return p
        return None



    def from_model(self, game: models.CluedoGame):
        self.secret = json.loads(game.secret)
        self.place_distances = Distances.get_from_string(game.distances)


