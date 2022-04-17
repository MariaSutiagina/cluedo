from data import models

class Field:
    def __init__(self, room: models.CluedoRoom):
        self.people = models.CluedoPerson.get_room_people(room)
        self.weapons = models.CluedoWeapon.get_room_weapons(room)
        self.places = models.CluedoPlace.get_room_places(room)

    def get_people(self):
        return list(self.people)
        
    def get_weapons(self):
        return list(self.weapons)
    
    def get_places(self):
        return list(self.places)

    def cards(self):
        return list(self.people) + list(self.weapons) + list(self.places)

