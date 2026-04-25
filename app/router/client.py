from app.config import RouterNode


class RouterClient:
    """HTTP client contract for router<->node interactions.

    Step 1 provides only structure and contracts. HTTP forwarding is implemented later.
    """

    def forward_get(self, node: RouterNode, key: str, query_string: bytes):
        raise NotImplementedError

    def forward_put(self, node: RouterNode, key: str, query_string: bytes, body: bytes):
        raise NotImplementedError

    def forward_patch(self, node: RouterNode, key: str, query_string: bytes, body: bytes):
        raise NotImplementedError

    def list_keys(self, node: RouterNode):
        raise NotImplementedError
