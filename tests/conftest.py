import pytest

from app.api.routes import _store


@pytest.fixture(autouse=True)
def clear_store_between_tests() -> None:
    _store.clear()
