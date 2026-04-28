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
        lock = self._locks.get_lock(key)
        with lock:
            existing = self._store.get(key)
            
            if existing is not None:
                if not check_expected_version(existing.version, if_version):
                    raise VersionConflictError(f"Version mismatch: expected {if_version}, got {existing.version}")
                new_version = next_version(existing.version)
            else:
                if if_version is not None:
                    raise VersionConflictError(f"Version mismatch: key does not exist")
                new_version = 1
            
            record = KVRecord(key=key, value=value, version=new_version)
            self._store.set(key, record)
            return record

    def patch(self, key: str, delta: JSONValue, if_version: Optional[int] = None) -> KVRecord:
        lock = self._locks.get_lock(key)
        with lock:
            existing = self._store.get(key)
            
            if existing is not None:
                if not check_expected_version(existing.version, if_version):
                    raise VersionConflictError(f"Version mismatch: expected {if_version}, got {existing.version}")
                new_version = next_version(existing.version)
                
                # Shallow merge: both value and delta must be dicts
                if isinstance(existing.value, dict) and isinstance(delta, dict):
                    merged_value = {**existing.value, **delta}
                else:
                    # Full replace for any other type combination
                    merged_value = delta
            else:
                if if_version is not None:
                    raise VersionConflictError(f"Version mismatch: key does not exist")
                new_version = 1
                merged_value = delta
            
            record = KVRecord(key=key, value=merged_value, version=new_version)
            self._store.set(key, record)
            return record

    def delete(self, key: str, if_version: Optional[int] = None) -> None:
        lock = self._locks.get_lock(key)
        with lock:
            existing = self._store.get(key)
            if existing is None:
                raise KeyNotFoundError(key)

            if not check_expected_version(existing.version, if_version):
                raise VersionConflictError(f"Version mismatch: expected {if_version}, got {existing.version}")

            self._store.delete(key)
