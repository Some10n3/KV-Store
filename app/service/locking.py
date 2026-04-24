from collections import defaultdict
from threading import Lock


class KeyLockManager:
    def __init__(self) -> None:
        self._master_lock = Lock()
        self._locks: dict[str, Lock] = defaultdict(Lock)

    def get_lock(self, key: str) -> Lock:
        self._master_lock.acquire()
        try:
            return self._locks[key]
        finally:
            self._master_lock.release()
