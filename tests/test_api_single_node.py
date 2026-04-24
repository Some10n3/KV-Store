from app.api.routes import _store
from app.main import app
from app.models.kv_record import KVRecord


# GET tests

def test_get_missing_key_returns_404() -> None:
    client = app.test_client()
    response = client.get("/kv/missing")
    assert response.status_code == 404


def test_get_existing_key_returns_record() -> None:
    _store.set("alpha", KVRecord(key="alpha", value={"count": 1}, version=2))

    client = app.test_client()
    response = client.get("/kv/alpha")

    assert response.status_code == 200
    assert response.get_json() == {"key": "alpha", "value": {"count": 1}, "version": 2}


# PUT tests

def test_put_new_key_creates_with_version_1() -> None:
    client = app.test_client()
    response = client.put("/kv/newkey", json={"data": "value"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["key"] == "newkey"
    assert data["value"] == {"data": "value"}
    assert data["version"] == 1


def test_put_existing_key_increments_version() -> None:
    _store.set("beta", KVRecord(key="beta", value={"old": "data"}, version=3))

    client = app.test_client()
    response = client.put("/kv/beta", json={"new": "data"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["key"] == "beta"
    assert data["value"] == {"new": "data"}
    assert data["version"] == 4


def test_put_with_ifversion_success() -> None:
    _store.set("gamma", KVRecord(key="gamma", value={"v": 1}, version=2))

    client = app.test_client()
    response = client.put("/kv/gamma?ifVersion=2", json={"v": 2})

    assert response.status_code == 200
    data = response.get_json()
    assert data["version"] == 3


# PATCH tests

def test_patch_on_nonexistent_key_creates_with_version_1() -> None:
    client = app.test_client()
    response = client.patch("/kv/newpatch", json={"field": "value"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["key"] == "newpatch"
    assert data["value"] == {"field": "value"}
    assert data["version"] == 1


def test_patch_shallow_merge_object_to_object() -> None:
    _store.set("merge_key", KVRecord(key="merge_key", value={"a": 1, "b": 2}, version=1))

    client = app.test_client()
    response = client.patch("/kv/merge_key", json={"b": 3, "c": 4})

    assert response.status_code == 200
    data = response.get_json()
    assert data["value"] == {"a": 1, "b": 3, "c": 4}
    assert data["version"] == 2


def test_patch_replaces_on_object_to_scalar() -> None:
    _store.set("obj_key", KVRecord(key="obj_key", value={"old": "object"}, version=1))

    client = app.test_client()
    response = client.patch("/kv/obj_key", json="string_value")

    assert response.status_code == 200
    data = response.get_json()
    assert data["value"] == "string_value"
    assert data["version"] == 2


def test_patch_replaces_on_scalar_to_object() -> None:
    _store.set("scalar_key", KVRecord(key="scalar_key", value="old_string", version=1))

    client = app.test_client()
    response = client.patch("/kv/scalar_key", json={"new": "object"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["value"] == {"new": "object"}
    assert data["version"] == 2


def test_patch_with_ifversion_success() -> None:
    _store.set("patch_version", KVRecord(key="patch_version", value={"x": 10}, version=3))

    client = app.test_client()
    response = client.patch("/kv/patch_version?ifVersion=3", json={"y": 20})

    assert response.status_code == 200
    data = response.get_json()
    assert data["value"] == {"x": 10, "y": 20}
    assert data["version"] == 4
