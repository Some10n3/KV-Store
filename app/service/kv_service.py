from typing import Optional

from app.models.kv_record import JSONValue, KVRecord
from app.service.locking import KeyLockManager
from app.service.versioning import check_expected_version, next_version
from app.infra.in_memory_store import InMemoryStore


class KeyNotFoundError(Exception):
    pass


class VersionConflictError(Exception):
    pass


class KVService:
    def __init__(self, store: InMemoryStore, locks: KeyLockManager) -> None:
        self._store = store
        self._locks = locks

    def get(self, key: str) -> KVRecord:
        record = self._store.get(key)
        if record is None:
            raise KeyNotFoundError(key)
        return record

    def put(self, key: str, value: JSONValue, if_version: Optional[int] = None) -> KVRecord:
        raise NotImplementedError("Phase 2: implement PUT behavior")

    def patch(self, key: str, delta: JSONValue, if_version: Optional[int] = None) -> KVRecord:
        raise NotImplementedError("Phase 2: implement PATCH behavior")
