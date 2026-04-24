from flask import Blueprint, jsonify, request

from app.models.kv_record import JSONValue
from app.service.locking import KeyLockManager
from app.service.kv_service import KVService, KeyNotFoundError, VersionConflictError
from app.infra.in_memory_store import InMemoryStore

kv_blueprint = Blueprint("kv", __name__, url_prefix="/kv")

_store = InMemoryStore()
_locks = KeyLockManager()
_service = KVService(_store, _locks)


@kv_blueprint.get("/<string:key>")
def get_key(key: str):
    try:
        record = _service.get(key)
    except KeyNotFoundError:
        return jsonify({"detail": f"Key not found: {key}"}), 404

    return jsonify({"key": record.key, "value": record.value, "version": record.version}), 200


@kv_blueprint.put("/<string:key>")
def put_key(key: str):
    value: JSONValue = request.get_json(force=True, silent=False)
    if_version_arg = request.args.get("ifVersion")
    if_version = int(if_version_arg) if if_version_arg is not None else None

    try:
        record = _service.put(key=key, value=value, if_version=if_version)
    except VersionConflictError:
        return jsonify({"detail": "Version conflict"}), 409

    return jsonify({"key": record.key, "value": record.value, "version": record.version}), 200


@kv_blueprint.patch("/<string:key>")
def patch_key(key: str):
    delta: JSONValue = request.get_json(force=True, silent=False)
    if_version_arg = request.args.get("ifVersion")
    if_version = int(if_version_arg) if if_version_arg is not None else None

    try:
        record = _service.patch(key=key, delta=delta, if_version=if_version)
    except VersionConflictError:
        return jsonify({"detail": "Version conflict"}), 409

    return jsonify({"key": record.key, "value": record.value, "version": record.version}), 200
