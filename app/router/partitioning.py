from app.config import RouterNode


def select_node(key: str, nodes: list[RouterNode]) -> RouterNode:
    if not nodes:
        raise ValueError("Router has no configured nodes")

    node_index = hash(key) % len(nodes)
    return nodes[node_index]
