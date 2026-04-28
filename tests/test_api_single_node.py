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


def test_put_with_lowercase_ifversion_success() -> None:
    _store.set("gamma_lower", KVRecord(key="gamma_lower", value={"v": 1}, version=2))

    client = app.test_client()
    response = client.put("/kv/gamma_lower?ifversion=2", json={"v": 2})

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


def test_patch_replaces_on_object_to_array() -> None:
    _store.set("array_replace_key", KVRecord(key="array_replace_key", value={"old": "object"}, version=1))

    client = app.test_client()
    response = client.patch("/kv/array_replace_key", json=[1, 2, 3])

    assert response.status_code == 200
    data = response.get_json()
    assert data["value"] == [1, 2, 3]
    assert data["version"] == 2


def test_patch_with_ifversion_success() -> None:
    _store.set("patch_version", KVRecord(key="patch_version", value={"x": 10}, version=3))

    client = app.test_client()
    response = client.patch("/kv/patch_version?ifVersion=3", json={"y": 20})

    assert response.status_code == 200
    data = response.get_json()
    assert data["value"] == {"x": 10, "y": 20}
    assert data["version"] == 4


def test_put_invalid_json_body_returns_400() -> None:
    client = app.test_client()
    response = client.put(
        "/kv/invalid-json-put",
        data='{"broken":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json() == {"detail": "Invalid JSON body"}


def test_patch_invalid_json_body_returns_400() -> None:
    client = app.test_client()
    response = client.patch(
        "/kv/invalid-json-patch",
        data='{"broken":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json() == {"detail": "Invalid JSON body"}


# DELETE tests

def test_delete_existing_key_returns_204_and_removes_key() -> None:
    _store.set("delete_me", KVRecord(key="delete_me", value={"x": 1}, version=2))

    client = app.test_client()
    delete_response = client.delete("/kv/delete_me")
    get_response = client.get("/kv/delete_me")

    assert delete_response.status_code == 200
    assert delete_response.get_json() == {"detail": "Deleted key delete_me successfully"}
    assert get_response.status_code == 404


def test_delete_missing_key_returns_404() -> None:
    client = app.test_client()
    response = client.delete("/kv/missing-delete")

    assert response.status_code == 404
    assert response.get_json() == {"detail": "Key not found: missing-delete"}


def test_delete_with_ifversion_success() -> None:
    _store.set("delete_version", KVRecord(key="delete_version", value={"x": 1}, version=5))

    client = app.test_client()
    response = client.delete("/kv/delete_version?ifVersion=5")

    assert response.status_code == 200
    assert response.get_json() == {"detail": "Deleted key delete_version successfully"}
    assert _store.get("delete_version") is None


def test_delete_with_ifversion_conflict_returns_409() -> None:
    _store.set("delete_conflict", KVRecord(key="delete_conflict", value={"x": 1}, version=3))

    client = app.test_client()
    response = client.delete("/kv/delete_conflict?ifVersion=2")

    assert response.status_code == 409
    assert response.get_json() == {"detail": "Version conflict"}


def test_delete_invalid_ifversion_returns_400() -> None:
    _store.set("delete_invalid_ifversion", KVRecord(key="delete_invalid_ifversion", value={"x": 1}, version=1))

    client = app.test_client()
    response = client.delete("/kv/delete_invalid_ifversion?ifVersion=not-an-int")

    assert response.status_code == 400
    assert response.get_json() == {"detail": "Invalid ifVersion: must be an integer"}
