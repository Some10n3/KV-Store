from dataclasses import dataclass
import json
from urllib import parse, request

from app.config import RouterNode


@dataclass
class ForwardResult:
    status_code: int
    body: bytes
    content_type: str


class RouterClient:
    """HTTP client for router<->node interactions.

    Preserves status codes and response body from nodes.
    """

    @staticmethod
    def _build_url(node: RouterNode, path: str, query_string: bytes) -> str:
        query = query_string.decode("utf-8") if query_string else ""
        if query:
            return f"{node.base_url}{path}?{query}"
        return f"{node.base_url}{path}"

    def _request(self, *, method: str, url: str, body: bytes | None = None) -> ForwardResult:
        req = request.Request(url=url, method=method, data=body)
        if body is not None:
            req.add_header("Content-Type", "application/json")

        try:
            with request.urlopen(req) as response:
                payload = response.read()
                content_type = response.headers.get("Content-Type", "application/json")
                return ForwardResult(
                    status_code=response.status,
                    body=payload,
                    content_type=content_type,
                )
        except request.HTTPError as exc:
            payload = exc.read()
            content_type = exc.headers.get("Content-Type", "application/json")
            return ForwardResult(
                status_code=exc.code,
                body=payload,
                content_type=content_type,
            )

    def forward_get(self, node: RouterNode, key: str, query_string: bytes) -> ForwardResult:
        url = self._build_url(node, f"/kv/{parse.quote(key, safe='')}", query_string)
        return self._request(method="GET", url=url)

    def forward_put(
        self,
        node: RouterNode,
        key: str,
        query_string: bytes,
        body: bytes,
    ) -> ForwardResult:
        url = self._build_url(node, f"/kv/{parse.quote(key, safe='')}", query_string)
        return self._request(method="PUT", url=url, body=body)

    def forward_patch(
        self,
        node: RouterNode,
        key: str,
        query_string: bytes,
        body: bytes,
    ) -> ForwardResult:
        url = self._build_url(node, f"/kv/{parse.quote(key, safe='')}", query_string)
        return self._request(method="PATCH", url=url, body=body)

    def list_keys(self, node: RouterNode) -> tuple[str, list[str]]:
        url = self._build_url(node, "/kv", b"")
        result = self._request(method="GET", url=url)
        if result.status_code != 200:
            raise ValueError(f"Failed to list keys from {node.base_url}: {result.status_code}")

        body_json = json.loads(result.body.decode("utf-8"))
        node_id = str(body_json.get("node", node.node_id))
        keys = body_json.get("keys", [])
        if not isinstance(keys, list):
            raise ValueError(f"Invalid key list payload from {node.base_url}")

        return node_id, [str(key) for key in keys]
