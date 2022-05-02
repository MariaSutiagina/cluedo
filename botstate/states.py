from enum import Enum, auto


class State(Enum):
    GREETING: int = auto()
    RULES: int = auto()
    ROOMS: int = auto()
    ROOM: int = auto()
    GAME: int = auto()
    GAME_WAITING: int = auto()
    THROW_DICE: int = auto()
    SELECT_PLACE: int = auto()
    NEW_PLACE: int = auto()
    ACCUSE_PERSON: int = auto()
    ACCUSE_WEAPON: int = auto()
    CONFIRM_ACCUSE: int = auto()
    CHECK_SUSPICTION: int = auto()
    CHECK_ACCUSE: int = auto()
    GAME_FINISHED: int = auto()
    
    EXIT: int = auto()
