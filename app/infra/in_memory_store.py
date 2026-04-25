from typing import Optional

from app.models.kv_record import KVRecord


class InMemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, KVRecord] = {}

    def get(self, key: str) -> Optional[KVRecord]:
        return self._data.get(key)

    def set(self, key: str, record: KVRecord) -> None:
        self._data[key] = record

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def clear(self) -> None:
        self._data.clear()
