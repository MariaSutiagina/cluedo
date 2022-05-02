import json
import logging
import random as rd
from typing import Dict, List, Union
from cluedo.distances import Distances
from data import models
from cluedo.field import Field
import utils.card_utils as cu
from utils.consts import MAX_EDGES_ON_DICE

class Player:
    def __init__(self, user: models.User):
        self.cards: List = []
        self.alive = True
        self.auto = False
        self.known_cards: List = []
        self.number = -1
        self.dice_throw_result = -1
        self.accessible_places = []
        self.asked = False
        self.user = user
        self.place = None
        self.alias = None
        self.game = None
        self.player = None

        self.id = user.id
        self.username = user.name

        if self.username is None:
            self.username = ''


    def populate_accessible_places(self, places: List[models.CluedoPlace], distances: Distances):
        self.accessible_places = []
        index1 = places.index(self.place)
        for place in places:
            index2 = places.index(place)
            if distances.get_dist(index1, index2) <= self.dice_throw_result:
                self.accessible_places.append(place)



    def throw_dice(self):
        if self.dice_throw_result < 0:
            self.dice_throw_result = rd.randrange(1, MAX_EDGES_ON_DICE + 1) + rd.randrange(1, MAX_EDGES_ON_DICE + 1)

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

    def update_known_cards(self, reflute_players):
        if self.user.state == 'CHECK_SUSPICTION' or self.user.state == 'GAME':
            if reflute_players:
                for pp in reflute_players:
                    self.known_cards.append(pp[1])


class Game:
    def __init__(self, user: models.User):
        self.am_open = (0, 0, 0, 0, 0, 0)
        self.user = user
        self.field: Field = Field(user.room)
        self.secret: Dict = None
        self.place_distances: Distances = None
        self.players: List[Player] = []
        self.opencards = None
        
        self.won = False
        self.winner = None

        self.accused_place = None
        self.accused_person = None
        self.accused_weapon = None

        self.turn_number = 0 
        self.reflute_players = None

    def create(self):
        self.secret = {'person': rd.choice(self.field.people), 'weapon': rd.choice(self.field.weapons), 'place': rd.choice(self.field.places)}
        self.place_distances = Distances.new_dist()
        self.cards = self.field.cards()
        rd.shuffle(self.cards)

        logging.info(f'game create for user: {self.user.name}:{self.user.id}')
        users: List[models.User] = list(models.User.objects.filter(room=self.user.room))
        rd.shuffle(users)
        for p in users:
            if p.id == self.user.id:
                pp = Player(self.user)
            else:
                pp = Player(p)
            self.players.append(pp)
            logging.info(f'player create: user:{pp.user.id} for game {self.user.id}')

        for c in self.secret.values():
            self.cards.remove(c)

        self.alive = len(self.players)
        self.n = len(self.players)
        self.turn_number = rd.randint(0,self.n-1)
        self.opencards = self.cards[:self.am_open[self.n]]
        aliases = self.field.get_people()[:]
        places = self.field.get_places()[:]

        deal_size = (len(self.cards) - self.am_open[self.n]) // self.n
        for player_idx in range(self.n):
            player: Player = self.players[player_idx]
            player.number = player_idx
            player.dice_throw_result = -1
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
            if p.user.id == user.id:
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


    def parse_secret(self, secret: str) -> Dict:
        d = json.loads(secret)

        person = models.CluedoPerson.objects.filter(id=d['person']).first()
        place = models.CluedoPlace.objects.filter(id=d['place']).first()
        weapon=models.CluedoWeapon.objects.filter(id=d['weapon']).first()

        d['person'] = person
        d['place'] = place
        d['weapon'] = weapon

        self.secret = d

        for c in self.secret.values():
            cc = list(filter(lambda x: (x.name == c.name), self.cards))[0]
            self.cards.remove(cc)


    def parse_opencards(self, cards: str) -> List[Union[models.CluedoPerson, models.CluedoPlace, models.CluedoWeapon]]:
        self.opencards = cu.json_to_cards(json.loads(cards))

    def parse_cards(self, player: Player, cards: str) -> List[Union[models.CluedoPerson, models.CluedoPlace, models.CluedoWeapon]]:
        player.cards = cu.json_to_cards(json.loads(cards))

    def parse_known_cards(self, player: Player, cards: str) -> List[Union[models.CluedoPerson, models.CluedoPlace, models.CluedoWeapon]]:
        player.known_cards = cu.json_to_cards(json.loads(cards))

    def parse_players(self, game: models.CluedoGame):
        plist = models.CluedoPlayer.objects.filter(game=game)
        for pp in plist:
            p = pp
            if p.user.id == self.user.id:
                p.user = self.user
            player = Player(p.user)
            player.player = pp
            logging.info(f'player load: user:{pp.user.id} in game {self.user.id}')
            player.alive = p.alive
            player.number = p.number
            player.game = game
            player.place = p.place
            player.alias = p.alias
            player.dice_throw_result = p.dice_throw_result
            player.populate_accessible_places(self.field.get_places(), self.place_distances)
            self.parse_cards(player, p.cards)
            self.parse_known_cards(player, p.known_cards)


            self.players.append(player)
        
    def from_model(self, game: models.CluedoGame):
        self.cards = self.field.cards()
        rd.shuffle(self.cards)

        self.place_distances = Distances.get_from_string(game.distances)
        logging.info(f'game load for user: {self.user.name}:{self.user.id}')
        self.parse_players(game)
        self.parse_secret(game.secret)
        self.parse_opencards(game.open_cards)
        self.alive = game.alive
        self.started = game.started
        self.won = game.won
        self.turn_number = game.turn_number
        self.winner = game.winner
        self.n = len(self.players)

        self.accused_person = game.accuse_person
        self.accused_place = game.accuse_place
        self.accused_weapon = game.accuse_weapon

    def get_next_player(self):
        next_turn = (self.turn_number + 1) % self.n
        for p in self.players:
            if p.number == next_turn:
                return p
        return None

    async def next_turn(self):
        self.turn_number = (self.turn_number + 1) % self.n
        p = self.get_player_whos_turn()
        p.dice_throw_result = -1

    async def update_after_send(self, user: models.User):
        if self.user.state == 'CHECK_SUSPICTION':
            await self.next_turn()

    

    def update_state(self, **kwargs):
        if self.user.state == 'THROW_DICE':
            player: Player = self.get_player_whos_turn()
            player.throw_dice()
            player.populate_accessible_places(self.field.get_places(), self.place_distances)
        elif self.user.state == 'ACCUSE_PERSON':
            player: Player = self.get_player_whos_turn()
            if kwargs.get('accused_location', -1) >= 0:
                player.place = models.CluedoPlace.objects.filter(id=kwargs['accused_location']).first()
                self.accused_place = player.place
        elif self.user.state == 'ACCUSE_WEAPON':
            player: Player = self.get_player_whos_turn()
            if kwargs.get('accused_person', -1) >= 0:
                self.accused_person = models.CluedoPerson.objects.filter(id=kwargs['accused_person']).first()
        elif self.user.state == 'CONFIRM_ACCUSE':
            player: Player = self.get_player_whos_turn()
            if kwargs.get('accused_weapon', -1) >= 0:
                self.accused_weapon = models.CluedoWeapon.objects.filter(id=kwargs['accused_weapon']).first()
        elif self.user.state == 'CHECK_SUSPICTION':
            player: Player = self.get_player_whos_turn()
            if kwargs.get('suspiction', None) is not None:
                player.place = models.CluedoPlace.objects.filter(id=kwargs['suspiction']['place']).first()
                self.accused_place = player.place
                self.accused_person = models.CluedoPerson.objects.filter(id=kwargs['suspiction']['person']).first()
                self.accused_weapon = models.CluedoWeapon.objects.filter(id=kwargs['suspiction']['weapon']).first()
                self.check_suspiction(player)
        elif self.user.state == 'CHECK_ACCUSE':
            player: Player = self.get_player_whos_turn()
            if kwargs.get('suspiction', None) is not None:
                # self.accused_weapon = models.CluedoWeapon.objects.filter(id=kwargs['accused_weapon']).first()
                pass

    def check_suspiction(self, player) -> List[Player]:
        lfc_place = lambda x: type(x) is models.CluedoPlace and self.accused_place.id == x.id
        lfc_person = lambda x: type(x) is models.CluedoPerson and self.accused_person.id == x.id
        lfc_weapon = lambda x: type(x) is models.CluedoWeapon and self.accused_weapon.id == x.id
        lf_place = lambda y: next(filter(lfc_place, y.cards), None) is not None
        lf_person = lambda y: next(filter(lfc_person, y.cards), None) is not None
        lf_weapon = lambda y: next(filter(lfc_weapon, y.cards), None) is not None
        players = list(filter(lambda z: (z != player) and (lf_place(z) or lf_person(z) or lf_weapon(z)), self.players))
        self.reflute_players = []
        for pp in players:
            self.reflute_players.extend(map(lambda x: (pp, x), filter(lfc_place, pp.cards)))
            self.reflute_players.extend(map(lambda x: (pp, x), filter(lfc_person, pp.cards)))
            self.reflute_players.extend(map(lambda x: (pp, x), filter(lfc_weapon, pp.cards)))
            
        return self.reflute_players
