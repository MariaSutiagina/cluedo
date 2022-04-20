import json
from typing import Dict, List, Union
from data.models import CluedoPerson, CluedoPlace, CluedoWeapon

def cards_to_json(cards: List[Union[CluedoPerson, CluedoPlace, CluedoWeapon]]) -> Dict:
    r = []
    for card in cards:
        if type(card) is CluedoPerson:
            r.append({'type': 'person', 'id': card.id})
        elif type(card) is CluedoPlace:
            r.append({'type': 'place', 'id': card.id})
        elif type(card) is CluedoWeapon:
            r.append({'type': 'weapon', 'id': card.id})
        else:
            raise NotImplementedError()
    
    return json.dumps(r)

def cards_to_info(cards: List[Union[CluedoPerson, CluedoPlace, CluedoWeapon]]) -> Dict:
    r = []
    for card in cards:
        if type(card) is CluedoPerson:
            r.append({'type': 'подозреваемый', 'name': card.name})
        elif type(card) is CluedoPlace:
            r.append({'type': 'место', 'name': card.name})
        elif type(card) is CluedoWeapon:
            r.append({'type': 'орудие', 'name': card.name})
        else:
            raise NotImplementedError()
    
    return r
