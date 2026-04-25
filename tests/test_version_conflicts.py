import pytest

from app.api.routes import _store
from app.main import app
from app.models.kv_record import KVRecord
from app.service.kv_service import KVService, VersionConflictError
from app.service.locking import KeyLockManager
from app.infra.in_memory_store import InMemoryStore


def test_service_put_ifversion_mismatch_raises_conflict() -> None:
    service = KVService(store=InMemoryStore(), locks=KeyLockManager())
    service.put("k1", {"v": 1})

    with pytest.raises(VersionConflictError):
        service.put("k1", {"v": 2}, if_version=99)


def test_service_patch_ifversion_mismatch_raises_conflict() -> None:
    service = KVService(store=InMemoryStore(), locks=KeyLockManager())
    service.put("k2", {"v": 1})

    with pytest.raises(VersionConflictError):
        service.patch("k2", {"v": 2}, if_version=88)


def test_service_put_ifversion_on_missing_key_raises_conflict() -> None:
    service = KVService(store=InMemoryStore(), locks=KeyLockManager())

    with pytest.raises(VersionConflictError):
        service.put("missing-put", {"v": 1}, if_version=1)


def test_service_patch_ifversion_on_missing_key_raises_conflict() -> None:
    service = KVService(store=InMemoryStore(), locks=KeyLockManager())

    with pytest.raises(VersionConflictError):
        service.patch("missing-patch", {"v": 1}, if_version=1)


def test_api_put_ifversion_mismatch_returns_409() -> None:
    _store.set("api-put", KVRecord(key="api-put", value={"v": 1}, version=2))

    client = app.test_client()
    response = client.put("/kv/api-put?ifVersion=999", json={"v": 2})

    assert response.status_code == 409
    assert "Version conflict" in response.get_json()["detail"]


def test_api_patch_ifversion_mismatch_returns_409() -> None:
    _store.set("api-patch", KVRecord(key="api-patch", value={"v": 1}, version=2))

    client = app.test_client()
    response = client.patch("/kv/api-patch?ifVersion=999", json={"v": 2})

    assert response.status_code == 409
    assert "Version conflict" in response.get_json()["detail"]


def test_api_put_invalid_ifversion_returns_400() -> None:
    client = app.test_client()
    response = client.put("/kv/invalid-put?ifVersion=not-an-int", json={"v": 1})

    assert response.status_code == 400
    assert "Invalid ifVersion" in response.get_json()["detail"]


def test_api_patch_invalid_ifversion_returns_400() -> None:
    client = app.test_client()
    response = client.patch("/kv/invalid-patch?ifVersion=not-an-int", json={"v": 1})

    assert response.status_code == 400
    assert "Invalid ifVersion" in response.get_json()["detail"]
