"""The standard ``deprecated`` marker on every supported Python, with no runtime dependency.

Type checkers resolve ``typing_extensions.deprecated`` from their bundled stubs (typeshed),
so they report every use of a marked member on every supported Python. At run time Python
3.13 and later supply ``warnings.deprecated``. On Python 3.12 an identity marker stands in:
it takes the same arguments and returns the decorated object unchanged. Every marker in this
package passes ``category=None``, under which the standard marker does not warn either, so
the two behave the same at run time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import deprecated
else:
    try:
        from warnings import deprecated
    except ImportError:  # Python 3.12

        class deprecated:
            """Identity stand-in for ``warnings.deprecated`` (Python 3.12)."""

            def __init__(self, message, /, *, category=DeprecationWarning, stacklevel=1):
                if not isinstance(message, str):
                    raise TypeError(
                        "Expected an object of type str for 'message', "
                        f"not {type(message).__name__!r}"
                    )
                self.message = message
                self.category = category
                self.stacklevel = stacklevel

            def __call__(self, arg, /):
                return arg


__all__ = ["deprecated"]
