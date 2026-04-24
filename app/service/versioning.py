from typing import Optional


def check_expected_version(current_version: int, expected_version: Optional[int]) -> bool:
    if expected_version is None:
        return True
    return current_version == expected_version


def next_version(current_version: int) -> int:
    return current_version + 1
