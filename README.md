# KV Store take-home assignment

## Part 1 (Single Node)

### Scope in this part

- HTTP API for `GET /kv/{key}`, `PUT /kv/{key}`, and `PATCH /kv/{key}`
- In-memory storage only (no database)
- Per-key concurrency control with optimistic version checks
- End-to-end tests for API behavior, conflicts, and concurrent increments

## API behavior

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

## Concurrency model

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

## Part 2

Part 2 scales out with multiple node processes and one router process.

- **Node mode**: runs existing Part 1 behavior and stores node-local in-memory data.
- **Router mode**: stateless process that determines key ownership via hash partitioning and coordinates requests.
- **Partitioning rule**: `node_index = hash(key) % N`, where `N` is number of configured nodes.
- **Guarantee preservation**: all operations for one key map to one node, so per-key atomicity and versioning remain node-local.
- **Tradeoff**: modulo hashing is simple but remaps many keys when node count changes; consistent hashing is a production roadmap item.

### Runtime modes

Start node processes:

```bash
python -m app.main --mode node --port 7001 --node-id node-a
python -m app.main --mode node --port 7002 --node-id node-b
python -m app.main --mode node --port 7003 --node-id node-c
```

Start router process:

```bash
python -m app.main --mode router --port 7000 --nodes http://127.0.0.1:7001,http://127.0.0.1:7002,http://127.0.0.1:7003
```

#### Router and node interaction contracts

- Keyed operations (`GET/PUT/PATCH /kv/<key>`):
  - Router selects owner node using partitioning.
  - Router forwards method, query string, and JSON body to selected node.
  - Router returns node status/body transparently.
- Global key listing (`GET /kv` on router):
  - Router calls each node local key endpoint.
  - Router merges key ownership into NDJSON lines: `{"key":"...","node":"node-id"}`.
- Node local key endpoint (`GET /kv` in node mode):
  - Returns node-local key snapshot payload: `{"node":"node-id","keys":[...]}`.

### File responsibilities for Part 2

- `app/main.py`: startup mode parsing and mode-specific app wiring.
- `app/config.py`: router node configuration parsing and normalization.
- `app/api/routes.py`: node-mode KV behavior plus local key listing endpoint.
- `app/router/partitioning.py`: deterministic node selection utility.
- `app/router/client.py`: router-to-node HTTP forwarding and key-list fan-out client.
- `app/router/routes.py`: router endpoint surface (`/kv/<key>` proxy and `/kv` NDJSON aggregation).

### Part 2 API behavior

- Router mode supports:
  - `GET /kv/<key>` -> forwards to owning node.
  - `PUT /kv/<key>` -> forwards to owning node.
  - `PATCH /kv/<key>` -> forwards to owning node.
  - `GET /kv` -> aggregates all node key lists and returns NDJSON.
- Node mode supports:
  - Existing Part 1 endpoints unchanged.
  - `GET /kv` local listing for router aggregation only.

### Part 2 testing scope

- Deterministic partitioning:
  - same key always maps to same node.
- Router forwarding correctness:
  - `GET/PUT/PATCH` for the same key all route to the same selected node.
- Multi-node key listing aggregation:
  - `GET /kv` returns combined NDJSON across all nodes.

## Part 3 - Roadmap: persistence + replication

Current system behavior is fully in-memory.

This keeps implementation simple and fast for the assignment, but it creates two major production risks:

- Process restart causes total data loss.
- Single node failure makes that partition unavailable.

To make this system production-ready, these are the proposed priorities.

### 1) Write-ahead logging (WAL) for durability

Before applying any successful `PUT` or `PATCH`, the node first appends the operation to a persistent write-ahead log on disk.

Flow:

`Client write request -> append operation to WAL -> flush to disk -> apply update to in-memory store -> return success`

Example log entry:

```json
{
  "operation": "PUT",
  "key": "user:42",
  "value": {"name": "Alice"},
  "version": 5,
  "timestamp": "..."
}
```

If a node crashes after the WAL write but before memory update completes, the process can recover by replaying the WAL during startup and rebuilding in-memory state.

Benefits:

- Durability across restarts.
- Crash recovery.
- Predictable recovery flow.

Tradeoffs:

- Slower writes due to disk flush.
- WAL compaction/snapshot strategy needed over time.

### 2) Leader-follower replication for availability

Each partition uses one leader node and one or more follower replicas.

Example:

- Shard A
  - Leader: node-a
  - Followers: node-a-1, node-a-2

Write flow:

`Client -> Router -> Leader node -> Followers replicate write`

Read flow:

- Strict consistency: read from leader only.
- Higher availability: optionally allow follower reads.

If the leader fails, a follower can be promoted to leader to restore availability.

Benefits:

- High availability.
- Failover support.
- Reduced single-node risk.

Tradeoffs:

- Replication lag.
- Leader election complexity.
- Consistency vs latency decisions.

### 3) Consistency tradeoff

Main design decision:

Should writes wait for replica acknowledgments?

Option A - Strong consistency:

- Leader waits for follower confirmation before returning success.
- Pros:
  - Safer writes.
  - Lower risk of acknowledged data loss.
- Cons:
  - Slower writes.
  - Higher latency.

Option B - Eventual consistency:

- Leader returns success immediately and followers catch up asynchronously.
- Pros:
  - Faster writes.
  - Better latency.
- Cons:
  - Stale reads possible.
  - Small risk during failover.

For this system, strong consistency is the first target, then latency optimization later if needed.

### Rough implementation order

- Phase 1: Write-ahead log (durability)
- Phase 2: Periodic snapshots + WAL compaction
- Phase 3: Leader-follower replication
- Phase 4: Follower promotion and failover
- Phase 5: Consistent hashing for easier node scaling

