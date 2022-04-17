import json
import random as rd
from typing import Dict
from cluedo.distances import Distances
from data import models
from cluedo.field import Field

class Game:
    def __init__(self, room: models.CluedoGame):
        self.field = Field(room)
        self.secret: Dict = None
        self.place_distances: Distances = None

    def create(self):
        self.secret = {'person': rd.choice(self.field.people).id, 'weapon': rd.choice(self.field.weapons).id, 'place': rd.choice(self.field.places).id}
        self.place_distances = Distances.new_dist()

    def from_model(self, game: models.CluedoGame):
        self.secret = json.loads(game.secret)
        self.place_distances = Distances.get_from_string(game.distances)


