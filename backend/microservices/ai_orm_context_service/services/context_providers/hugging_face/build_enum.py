from typing import List, Type
from enum import Enum


def build_enum(enum_name: str, enum_vals: List[str]) -> Type[Enum]:
    return Enum(enum_name, {v: v for v in enum_vals})
