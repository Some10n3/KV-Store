from dataclasses import dataclass
from typing import Union

JSONValue = Union[
    dict,
    list,
    str,
    int,
    float,
    bool,
    None
]

@dataclass
class KVRecord:
    key: str
    value: JSONValue
    version: int