import hashlib

from app.config import RouterNode


def select_node(key: str, nodes: list[RouterNode]) -> RouterNode:
    if not nodes:
        raise ValueError("Router has no configured nodes")

    # Use stable hashing (not Python's process-randomized hash()).
    key_hash = hashlib.sha256(key.encode("utf-8")).digest()
    node_index = int.from_bytes(key_hash[:8], byteorder="big", signed=False) % len(nodes)
    return nodes[node_index]
