from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.infra.in_memory_store import InMemoryStore
from app.service.kv_service import KVService, VersionConflictError
from app.service.locking import KeyLockManager

# Same concurrency scenario as the pytest test, kept as a runnable demo script
# so the required 3-client / 100-increment proof can be shown live during a demo.


def run_concurrency_proof() -> tuple[int, int]:
    """Run the required 3x100 same-key increment scenario."""
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
    return record.value, record.version


def main() -> int:
    value, version = run_concurrency_proof()

    print(f"Final counter value: {value}")
    print(f"Final version: {version}")

    if value == 300:
        print("Test passed")
        return 0

    print("Test failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
