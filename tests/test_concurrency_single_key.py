from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.infra.in_memory_store import InMemoryStore
from app.service.kv_service import KVService, VersionConflictError
from app.service.locking import KeyLockManager


def test_concurrent_increment_same_key_final_value_is_300() -> None:
    store = InMemoryStore()
    locks = KeyLockManager()
    service = KVService(store, locks)

    service.put("counter", 0)

    start_barrier = Barrier(3)

    def increment_worker() -> None:
        start_barrier.wait()
        for _ in range(100):
            while True:
                current = service.get("counter")
                try:
                    service.put("counter", current.value + 1, if_version=current.version)
                    break
                except VersionConflictError:
                    continue

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(increment_worker) for _ in range(3)]
        for future in futures:
            future.result()

    record = service.get("counter")
    assert record.value == 300
    assert record.version == 301
