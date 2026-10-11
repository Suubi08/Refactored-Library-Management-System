
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    isbn: str
    title: str
