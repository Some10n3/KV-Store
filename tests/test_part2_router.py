import json

from app.config import RouterNode
from app.main import create_app
from app.router.client import ForwardResult
from app.router.partitioning import select_node


class FakeRouterClient:
    def __init__(self) -> None:
        self.get_calls: list[tuple[str, str, bytes]] = []
        self.put_calls: list[tuple[str, str, bytes, bytes]] = []
        self.patch_calls: list[tuple[str, str, bytes, bytes]] = []
        self.delete_calls: list[tuple[str, str, bytes]] = []

    def forward_get(self, node: RouterNode, key: str, query_string: bytes) -> ForwardResult:
        self.get_calls.append((node.node_id, key, query_string))
        return ForwardResult(
            status_code=200,
            body=json.dumps({"key": key, "value": {"from": node.node_id}, "version": 1}).encode("utf-8"),
            content_type="application/json",
        )

    def forward_put(self, node: RouterNode, key: str, query_string: bytes, body: bytes) -> ForwardResult:
        self.put_calls.append((node.node_id, key, query_string, body))
        return ForwardResult(status_code=200, body=body, content_type="application/json")

    def forward_patch(self, node: RouterNode, key: str, query_string: bytes, body: bytes) -> ForwardResult:
        self.patch_calls.append((node.node_id, key, query_string, body))
        return ForwardResult(status_code=200, body=body, content_type="application/json")

    def forward_delete(self, node: RouterNode, key: str, query_string: bytes) -> ForwardResult:
        self.delete_calls.append((node.node_id, key, query_string))
        return ForwardResult(
            status_code=200,
            body=json.dumps({"detail": f"Deleted key {key} successfully"}).encode("utf-8"),
            content_type="application/json",
        )

    def list_keys(self, node: RouterNode) -> tuple[str, list[str]]:
        return node.node_id, [f"{node.node_id}:a", f"{node.node_id}:b"]


def _router_nodes() -> list[RouterNode]:
    return [
        RouterNode(node_id="node-a", base_url="http://127.0.0.1:7001"),
        RouterNode(node_id="node-b", base_url="http://127.0.0.1:7002"),
        RouterNode(node_id="node-c", base_url="http://127.0.0.1:7003"),
    ]


def test_partitioning_same_key_always_same_node() -> None:
    nodes = _router_nodes()
    selected_once = select_node("user:42", nodes)
    selected_twice = select_node("user:42", nodes)
    assert selected_once.node_id == selected_twice.node_id


def test_router_forwards_keyed_requests_to_selected_node() -> None:
    nodes = _router_nodes()
    fake_client = FakeRouterClient()
    app = create_app(mode="router", router_nodes=nodes)
    app.config["ROUTER_CLIENT"] = fake_client
    client = app.test_client()

    key = "user:99"
    expected_node = select_node(key, nodes).node_id

    get_response = client.get(f"/kv/{key}?ifVersion=1")
    put_response = client.put(f"/kv/{key}?ifVersion=1", json={"name": "Ari"})
    patch_response = client.patch(f"/kv/{key}?ifVersion=1", json={"rank": "gold"})
    delete_response = client.delete(f"/kv/{key}?ifVersion=1")

    assert get_response.status_code == 200
    assert put_response.status_code == 200
    assert patch_response.status_code == 200
    assert delete_response.status_code == 200

    assert fake_client.get_calls[0][0] == expected_node
    assert fake_client.put_calls[0][0] == expected_node
    assert fake_client.patch_calls[0][0] == expected_node
    assert fake_client.delete_calls[0][0] == expected_node


def test_router_get_kv_aggregates_all_nodes_as_ndjson() -> None:
    app = create_app(mode="router", router_nodes=_router_nodes())
    app.config["ROUTER_CLIENT"] = FakeRouterClient()
    client = app.test_client()

    response = client.get("/kv")

    assert response.status_code == 200
    assert response.mimetype == "application/x-ndjson"

    lines = [line for line in response.get_data(as_text=True).splitlines() if line.strip()]
    parsed = [json.loads(line) for line in lines]

    assert len(parsed) == 6
    assert {"key": "node-a:a", "node": "node-a"} in parsed
    assert {"key": "node-b:b", "node": "node-b"} in parsed
    assert {"key": "node-c:a", "node": "node-c"} in parsed
