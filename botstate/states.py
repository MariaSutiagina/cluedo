from enum import Enum, auto


class State(Enum):
    GREETING: int = auto()
    RULES: int = auto()
    ROOMS: int = auto()
    ROOM: int = auto()
    GAME: int = auto()
    GAME_WAITING: int = auto()
    # DASHBOARD: int = auto()
    # QUIZ: int = auto()
    EXIT: int = auto()
