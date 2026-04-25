from flask import Blueprint, current_app, jsonify

from app.config import RouterNode
from app.router.partitioning import select_node

router_blueprint = Blueprint("router", __name__, url_prefix="/kv")


def _get_router_nodes() -> list[RouterNode]:
    nodes: list[RouterNode] = current_app.config.get("ROUTER_NODES", [])
    if not nodes:
        raise ValueError("Router mode requires at least one node")
    return nodes


@router_blueprint.get("/<string:key>")
def proxy_get_key(key: str):
    _ = select_node(key, _get_router_nodes())
    return jsonify({"detail": "Router forwarding is not implemented yet"}), 501


@router_blueprint.put("/<string:key>")
def proxy_put_key(key: str):
    _ = select_node(key, _get_router_nodes())
    return jsonify({"detail": "Router forwarding is not implemented yet"}), 501


@router_blueprint.patch("/<string:key>")
def proxy_patch_key(key: str):
    _ = select_node(key, _get_router_nodes())
    return jsonify({"detail": "Router forwarding is not implemented yet"}), 501


@router_blueprint.get("")
def aggregate_keys():
    _ = _get_router_nodes()
    return jsonify({"detail": "Router key aggregation is not implemented yet"}), 501
