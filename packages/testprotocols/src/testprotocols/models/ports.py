"""Layer-4 port ranges: the typed form of the released port text.

The released ACL records carried ports as text (``"any"``, ``"80"``, ``"80-90"``,
``"22,80-90"``). :class:`PortRange` is the typed form; a record holds a tuple of them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override


@dataclass(frozen=True)
class PortRange:
    """An inclusive L4 port range; a single port has ``first == last``.

    ``1 <= first <= last <= 65535``.
    """

    first: int
    last: int

    @classmethod
    def single(cls, port: int) -> PortRange:
        """The range holding exactly *port*."""
        return cls(port, port)

    @override
    def __str__(self) -> str:
        return str(self.first) if self.first == self.last else f"{self.first}-{self.last}"
