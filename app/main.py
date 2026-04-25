import argparse

from flask import Flask

from app.api.routes import kv_blueprint
from app.config import RouterNode, parse_router_nodes
from app.router.routes import router_blueprint


def create_app(
    mode: str = "node",
    node_id: str | None = None,
    router_nodes: list[RouterNode] | None = None,
) -> Flask:
    app = Flask(__name__)
    if mode == "node":
        app.config["MODE"] = "node"
        app.config["NODE_ID"] = node_id or "node"
        app.register_blueprint(kv_blueprint)
    elif mode == "router":
        app.config["MODE"] = "router"
        app.config["ROUTER_NODES"] = router_nodes or []
        app.register_blueprint(router_blueprint)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return app


app = create_app()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KV Store runtime")
    parser.add_argument("--mode", choices=("node", "router"), default="node")
    parser.add_argument("--port", type=int, default=7000)
    parser.add_argument("--node-id", default="node")
    parser.add_argument(
        "--nodes",
        default="",
        help="Comma-separated node base URLs for router mode.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    nodes = parse_router_nodes(args.nodes) if args.mode == "router" else None
    app = create_app(mode=args.mode, node_id=args.node_id, router_nodes=nodes)
    app.run(host="127.0.0.1", port=args.port)
