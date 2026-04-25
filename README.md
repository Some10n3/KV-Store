# KV Store

Part 1 (Single Node) for a Backend Engineering take-home assignment.

## Scope in this part

- HTTP API for `GET /kv/{key}`, `PUT /kv/{key}`, and `PATCH /kv/{key}`
- In-memory storage only (no database)
- Per-key concurrency control with optimistic version checks
- End-to-end tests for API behavior, conflicts, and concurrent increments

## API behavior (Part 1)

- `GET /kv/{key}`: returns `{ key, value, version }` or `404` when missing.
- `PUT /kv/{key}`: full replacement of value.
	- If `ifVersion` is provided and does not match current version, returns `409`.
	- New keys are created with `version = 1` when `ifVersion` is not provided.
	- Existing keys increment version on success.
	- Request body must be valid JSON (object/array/scalar); malformed JSON returns `400`.
- `PATCH /kv/{key}`: applies delta.
	- If key is missing and `ifVersion` is not provided, creates key with `version = 1`.
	- If both current value and delta are JSON objects, does shallow merge of top-level fields.
	- Otherwise, replaces full value (for example, object -> array or object -> scalar).
	- If `ifVersion` is provided and version mismatches, returns `409`.
	- Request body must be valid JSON (object/array/scalar); malformed JSON returns `400`.

## Concurrency model (Part 1)

- **Pessimistic locking per key**:
	- A lock is acquired for the target key before write operations (`PUT`, `PATCH`).
	- Operations on the same key are serialized in a critical section.
	- Different keys can proceed in parallel (lock granularity is per key, not global).
- **Optimistic concurrency control using versions**:
	- Clients can send `ifVersion` as a compare-and-set guard.
	- Mismatched versions fail with `409` to prevent lost updates.
- **Race-condition proof**:
	- Test runs 3 concurrent clients with 100 increments each on one key.
	- Final value is exactly 300, demonstrating no torn writes and no lost updates.

Deadlock risk is minimized because each operation acquires at most one key lock.

## Assumptions and tradeoffs

- Data is stored in memory only; process restart loses all keys/values.
- No durability guarantees are provided in Part 1 (no WAL, snapshots, or persistence layer).
- No high availability or redundancy is implemented in Part 1; this is a single-process node.
- Versioning keeps only the current per-key version (no version history).
- Per-key locking is used for writes (`PUT`, `PATCH`) so same-key updates serialize while different keys can proceed concurrently.

## Error contract

- `404 Not Found`: key does not exist on `GET /kv/{key}`.
  - Example: `{"detail":"Key not found: user:42"}`
- `409 Conflict`: optimistic lock check failed (`ifVersion` mismatch) on `PUT` or `PATCH`.
  - Example: `{"detail":"Version conflict"}`
- `400 Bad Request`: invalid `ifVersion` value (must be integer) on `PUT` or `PATCH`.
  - Example: `{"detail":"Invalid ifVersion: must be an integer"}`
- `400 Bad Request`: malformed JSON body on `PUT` or `PATCH`.
  - Example: `{"detail":"Invalid JSON body"}`

## Tech stack

- Python
- Flask
- In-memory storage only
- Pytest

## Project layout

```
app/
	api/
		routes.py
		schemas.py
	service/
		locking.py
		kv_service.py
		versioning.py
	infra/
		in_memory_store.py
	models/
		kv_record.py
	main.py
tests/
	test_api_single_node.py
	test_concurrency_single_key.py
	test_version_conflicts.py
requirements.txt
pyproject.toml
```

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API:

```bash
flask --app app.main run --debug
```

4. Run tests:

```bash
pytest
```

## Current test coverage

- API correctness for GET/PUT/PATCH paths
- Dedicated version-conflict scenarios for PUT and PATCH
- Input validation scenarios (invalid `ifVersion`, malformed JSON body)
- PATCH replace behavior when delta is non-object (including object -> array/scalar)
- Concurrency correctness on same-key increments

