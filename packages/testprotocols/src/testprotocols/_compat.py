"""Re-export of the standard ``deprecated`` marker for every supported Python."""

import sys

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated

__all__ = ["deprecated"]
