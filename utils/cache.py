
from typing import Dict, Optional


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):

        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class MediaCache(metaclass=SingletonMeta):
    def __init__(self):
        self._cache: Dict[str, str] = {}

    def find(self, key: str) -> Optional[str]:
        return self._cache[key] if key in self._cache else None

    def update(self, key: str, value: str) -> None:
        if key not in self._cache:
            self._cache[key] = value
