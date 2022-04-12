from enum import Enum, auto


class State(Enum):
    GREETING: int = auto()
    RULES: int = auto()
    WAITING: int = auto()
    DASHBOARD: int = auto()
    QUIZ: int = auto()
    EXIT: int = auto()
