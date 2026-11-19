"""A minimal NBT reader: enough to check a structure template.

Only what a 1.21.1/26.3 structure template needs: a named root compound
(gzip-compressed or not) and the payload types NBT defines. Values come back as
Python objects:

    TAG_Byte/Short/Int/Long   -> int
    TAG_Float/Double          -> float
    TAG_String                -> str
    TAG_List                  -> list (empty list -> [])
    TAG_Compound              -> dict
    TAG_Byte_Array            -> bytes
    TAG_Int_Array             -> list[int]
    TAG_Long_Array            -> list[int]

The reader is used by the port's static verification only; the game reads the
templates it needs.
"""
from __future__ import annotations

import gzip
import struct

(END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND,
 INT_ARRAY, LONG_ARRAY) = range(13)


class NbtError(ValueError):
    """A tag the reader does not understand, or a truncated payload."""


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.at = 0

    def take(self, n: int) -> bytes:
        end = self.at + n
        if end > len(self.data):
            raise NbtError(f"truncated payload: wanted {n} bytes at {self.at}")
        out = self.data[self.at:end]
        self.at = end
        return out

    def unpack(self, fmt: str):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.take(size))[0]

    def string(self) -> str:
        return self.take(self.unpack(">H")).decode("utf-8", "replace")

    def payload(self, kind: int):
        if kind == BYTE:
            return self.unpack(">b")
        if kind == SHORT:
            return self.unpack(">h")
        if kind == INT:
            return self.unpack(">i")
        if kind == LONG:
            return self.unpack(">q")
        if kind == FLOAT:
            return self.unpack(">f")
        if kind == DOUBLE:
            return self.unpack(">d")
        if kind == BYTE_ARRAY:
            return self.take(self.unpack(">i"))
        if kind == STRING:
            return self.string()
        if kind == LIST:
            item = self.unpack(">b")
            count = self.unpack(">i")
            if count <= 0:
                return []
            return [self.payload(item) for _ in range(count)]
        if kind == COMPOUND:
            out = {}
            while True:
                tag = self.unpack(">b")
                if tag == 0:
                    return out
                name = self.string()
                out[name] = self.payload(tag)
        if kind == INT_ARRAY:
            count = self.unpack(">i")
            return list(struct.unpack(f">{count}i", self.take(4 * count)))
        if kind == LONG_ARRAY:
            count = self.unpack(">i")
            return list(struct.unpack(f">{count}q", self.take(8 * count)))
        raise NbtError(f"unknown tag type {kind}")


def read(data: bytes):
    """The root compound of an NBT payload (gzip is detected and unwrapped)."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    reader = _Reader(data)
    tag = reader.unpack(">b")
    if tag != COMPOUND:
        raise NbtError(f"root tag is {tag}, not a compound")
    reader.string()  # root name
    return reader.payload(COMPOUND)
