from dataclasses import dataclass


@dataclass(frozen=True)
class RouterNode:
    node_id: str
    base_url: str


def parse_router_nodes(nodes_arg: str) -> list[RouterNode]:
    if not nodes_arg.strip():
        return []

    nodes: list[RouterNode] = []
    for index, raw_url in enumerate(nodes_arg.split(",")):
        base_url = raw_url.strip().rstrip("/")
        if not base_url:
            continue
        nodes.append(RouterNode(node_id=f"node-{index}", base_url=base_url))

    return nodes
