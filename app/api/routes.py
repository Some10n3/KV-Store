from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from app.models.kv_record import JSONValue
from app.service.locking import KeyLockManager
from app.service.kv_service import KVService, KeyNotFoundError, VersionConflictError
from app.infra.in_memory_store import InMemoryStore

kv_blueprint = Blueprint("kv", __name__, url_prefix="/kv")

_store = InMemoryStore()
_locks = KeyLockManager()
_service = KVService(_store, _locks)


def _parse_if_version() -> tuple[int | None, tuple[dict[str, str], int] | None]:
    if_version_arg = request.args.get("ifVersion")
    if if_version_arg is None:
        return None, None

    try:
        return int(if_version_arg), None
    except ValueError:
        return None, ({"detail": "Invalid ifVersion: must be an integer"}, 400)


def _parse_json_body() -> tuple[JSONValue | None, tuple[dict[str, str], int] | None]:
    try:
        payload: JSONValue = request.get_json(force=True, silent=False)
    except BadRequest:
        return None, ({"detail": "Invalid JSON body"}, 400)
    return payload, None


@kv_blueprint.errorhandler(BadRequest)
def handle_bad_request(_: BadRequest):
    return jsonify({"detail": "Invalid JSON body"}), 400


@kv_blueprint.errorhandler(KeyNotFoundError)
def handle_key_not_found(error: KeyNotFoundError):
    key = error.args[0] if error.args else "unknown"
    return jsonify({"detail": f"Key not found: {key}"}), 404


@kv_blueprint.get("/<string:key>")
def get_key(key: str):
    record = _service.get(key)
    return jsonify({"key": record.key, "value": record.value, "version": record.version}), 200


@kv_blueprint.put("/<string:key>")
def put_key(key: str):
    value, body_error = _parse_json_body()
    if body_error is not None:
        body, status = body_error
        return jsonify(body), status
    if_version, parse_error = _parse_if_version()
    if parse_error is not None:
        body, status = parse_error
        return jsonify(body), status

    try:
        record = _service.put(key=key, value=value, if_version=if_version)
    except VersionConflictError:
        return jsonify({"detail": "Version conflict"}), 409

    return jsonify({"key": record.key, "value": record.value, "version": record.version}), 200


@kv_blueprint.patch("/<string:key>")
def patch_key(key: str):
    delta, body_error = _parse_json_body()
    if body_error is not None:
        body, status = body_error
        return jsonify(body), status
    if_version, parse_error = _parse_if_version()
    if parse_error is not None:
        body, status = parse_error
        return jsonify(body), status

    try:
        record = _service.patch(key=key, delta=delta, if_version=if_version)
    except VersionConflictError:
        return jsonify({"detail": "Version conflict"}), 409

    return jsonify({"key": record.key, "value": record.value, "version": record.version}), 200
