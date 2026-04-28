"""Property-based tests using Hypothesis to automatically generate test inputs.

These tests verify KV Store invariants across a wide range of generated inputs,
catching edge cases that manual tests might miss.
"""
import string

from hypothesis import given, strategies as st
from app.api.routes import _store
from app.main import app
from app.models.kv_record import KVRecord


# Define custom strategies for realistic test data
keys_strategy = st.text(alphabet=string.ascii_lowercase + string.digits + "_-:", min_size=1, max_size=32)
values_strategy = st.one_of(
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(max_size=20), st.integers()),
)


class TestPropertyBasedKVStore:
    """Property-based tests that verify KV Store correctness under generated inputs."""

    @given(key=keys_strategy, value=values_strategy)
    def test_set_then_get_returns_same_value(self, key: str, value) -> None:
        """Invariant: after setting a key, getting it returns the same value."""
        _store.clear()
        client = app.test_client()
        
        # Set the key
        put_response = client.put(f"/kv/{key}", json=value)
        assert put_response.status_code == 200
        
        # Get the key
        get_response = client.get(f"/kv/{key}")
        assert get_response.status_code == 200
        assert get_response.get_json()["value"] == value

    @given(key=keys_strategy, value1=values_strategy, value2=values_strategy)
    def test_overwrite_replaces_value(self, key: str, value1, value2) -> None:
        """Invariant: overwriting a key replaces the old value."""
        _store.clear()
        client = app.test_client()
        
        # Set initial value
        client.put(f"/kv/{key}", json=value1)
        
        # Overwrite with new value
        client.put(f"/kv/{key}", json=value2)
        
        # Verify new value is stored
        get_response = client.get(f"/kv/{key}")
        assert get_response.get_json()["value"] == value2

    @given(key=keys_strategy, value=values_strategy)
    def test_version_increments_on_write(self, key: str, value) -> None:
        """Invariant: each write increments the version."""
        _store.clear()
        client = app.test_client()
        
        versions = []
        
        # Write 3 times and collect versions
        for i in range(3):
            response = client.put(f"/kv/{key}", json=value)
            assert response.status_code == 200
            versions.append(response.get_json()["version"])
        
        # Versions should be strictly increasing: 1, 2, 3
        assert versions == [1, 2, 3]

    @given(key=keys_strategy, value=values_strategy)
    def test_delete_removes_key(self, key: str, value) -> None:
        """Invariant: after deletion, key doesn't exist."""
        _store.clear()
        client = app.test_client()
        
        # Set a key
        client.put(f"/kv/{key}", json=value)
        
        # Delete it
        delete_response = client.delete(f"/kv/{key}")
        assert delete_response.status_code == 200
        assert delete_response.get_json() == {"detail": f"Deleted key {key} successfully"}
        
        # Verify it's gone
        get_response = client.get(f"/kv/{key}")
        assert get_response.status_code == 404

    @given(
        key=keys_strategy,
        initial_value=values_strategy,
        delta=st.dictionaries(st.text(max_size=20), st.integers()),
    )
    def test_patch_object_merges_fields(self, key: str, initial_value, delta) -> None:
        """Invariant: PATCH on object merges delta fields into existing object."""
        _store.clear()
        # Only test when both initial and delta are dicts
        if not isinstance(initial_value, dict) or not delta:
            return
        
        client = app.test_client()
        
        # Set initial object
        client.put(f"/kv/{key}", json=initial_value)
        
        # Patch with delta
        patch_response = client.patch(f"/kv/{key}", json=delta)
        assert patch_response.status_code == 200
        
        # Verify merge: all initial fields + delta fields
        result = patch_response.get_json()["value"]
        assert isinstance(result, dict)
        
        # Check that all initial fields are present
        for field, val in initial_value.items():
            assert field in result
        
        # Check that delta fields are present and override
        for field, val in delta.items():
            assert result[field] == val

    @given(key=keys_strategy, value=values_strategy)
    def test_version_conflict_on_mismatch(self, key: str, value) -> None:
        """Invariant: ifVersion mismatch returns 409."""
        _store.clear()
        client = app.test_client()
        
        # Set initial value (version 1)
        client.put(f"/kv/{key}", json=value)
        
        # Try to put with wrong version
        conflict_response = client.put(f"/kv/{key}?ifVersion=99", json={"new": "value"})
        assert conflict_response.status_code == 409
        assert conflict_response.get_json() == {"detail": "Version conflict"}

    @given(
        keys_list=st.lists(keys_strategy, min_size=1, max_size=10, unique=True),
        value=values_strategy,
    )
    def test_multiple_keys_independent(self, keys_list, value) -> None:
        """Invariant: operations on different keys are independent."""
        _store.clear()
        client = app.test_client()
        
        # Set multiple keys with the same value
        for key in keys_list:
            response = client.put(f"/kv/{key}", json=value)
            assert response.status_code == 200
        
        # Delete one key and verify others are unaffected
        deleted_key = keys_list[0]
        client.delete(f"/kv/{deleted_key}")
        
        # Deleted key should be gone
        assert client.get(f"/kv/{deleted_key}").status_code == 404
        
        # Other keys should still exist
        for key in keys_list[1:]:
            response = client.get(f"/kv/{key}")
            assert response.status_code == 200
            assert response.get_json()["value"] == value

    @given(
        key=keys_strategy,
        write_count=st.integers(min_value=1, max_value=20),
    )
    def test_repeated_overwrites_version_stability(self, key: str, write_count: int) -> None:
        """Invariant: version increments correctly after many overwrites."""
        _store.clear()
        client = app.test_client()
        
        for i in range(write_count):
            response = client.put(f"/kv/{key}", json={"attempt": i})
            assert response.status_code == 200
            # Version should equal the number of writes
            assert response.get_json()["version"] == i + 1

    @given(
        key=keys_strategy,
        value=values_strategy,
        delete_version=st.integers(min_value=1, max_value=5),
    )
    def test_delete_with_version_check(self, key: str, value, delete_version: int) -> None:
        """Invariant: DELETE respects ifVersion just like PUT/PATCH."""
        _store.clear()
        client = app.test_client()
        
        # Set key
        put_response = client.put(f"/kv/{key}", json=value)
        actual_version = put_response.get_json()["version"]
        
        # Try delete with specific version
        if delete_version == actual_version:
            # Should succeed
            response = client.delete(f"/kv/{key}?ifVersion={delete_version}")
            assert response.status_code == 200
        else:
            # Should fail with 409
            response = client.delete(f"/kv/{key}?ifVersion={delete_version}")
            assert response.status_code == 409
