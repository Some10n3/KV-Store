from flask import Blueprint, Response, current_app, request

from app.config import RouterNode
from app.router.client import RouterClient
from app.router.partitioning import select_node

router_blueprint = Blueprint("router", __name__, url_prefix="/kv")


def _get_router_nodes() -> list[RouterNode]:
    nodes: list[RouterNode] = current_app.config.get("ROUTER_NODES", [])
    if not nodes:
        raise ValueError("Router mode requires at least one node")
    return nodes


def _get_router_client() -> RouterClient:
    client: RouterClient | None = current_app.config.get("ROUTER_CLIENT")
    if client is None:
        client = RouterClient()
        current_app.config["ROUTER_CLIENT"] = client
    return client


def _response_from_forwarded(status_code: int, body: bytes, content_type: str) -> Response:
    return Response(body, status=status_code, mimetype=content_type.split(";")[0])


@router_blueprint.get("/<string:key>")
def proxy_get_key(key: str):
    node = select_node(key, _get_router_nodes())
    result = _get_router_client().forward_get(node, key, request.query_string)
    return _response_from_forwarded(result.status_code, result.body, result.content_type)


@router_blueprint.put("/<string:key>")
def proxy_put_key(key: str):
    node = select_node(key, _get_router_nodes())
    result = _get_router_client().forward_put(node, key, request.query_string, request.get_data())
    return _response_from_forwarded(result.status_code, result.body, result.content_type)


@router_blueprint.patch("/<string:key>")
def proxy_patch_key(key: str):
    node = select_node(key, _get_router_nodes())
    result = _get_router_client().forward_patch(node, key, request.query_string, request.get_data())
    return _response_from_forwarded(result.status_code, result.body, result.content_type)


@router_blueprint.get("")
def aggregate_keys():
    nodes = _get_router_nodes()
    client = _get_router_client()

    lines: list[str] = []
    for node in nodes:
        node_id, keys = client.list_keys(node)
        for key in keys:
            lines.append(f'{{"key":"{key}","node":"{node_id}"}}')

    payload = "\n".join(lines)
    if lines:
        payload += "\n"

    return Response(payload, status=200, mimetype="application/x-ndjson")
