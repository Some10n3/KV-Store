from typing import TypedDict

from app.models.kv_record import JSONValue


class KVResponse(TypedDict):
    key: str
    value: JSONValue
    version: int


class ErrorResponse(TypedDict):
    detail: str
