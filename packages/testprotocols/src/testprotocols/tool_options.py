"""Typed options for the command-line tools behind host capabilities (shape 4p).

A host capability's tool member (``curl``, ``http_get``, ``nmap``) released a free option
string that the driver pasted into the tool's command line. Each now also takes the typed
keyword-only parameters that callers were seen to pass; the string stays through the
deprecation period. A member no caller was seen to pass options to (``ping``, ``traceroute``,
``dns_lookup``, ``ps_options``) gets no typed parameter: its string is deprecated with no
successor, and :func:`settle_option_string` still gives the warning.

The protocol only declares the parameters. A driver builds the tool's argument vector
from them with the renderers below, and settles the two spellings with
:func:`settle_option_string`::

    def http_get(self, url, timeout=20, options="", *, insecure=False):
        legacy = settle_option_string(
            options, what="http_get(options)", typed={"insecure": insecure}
        )
        extra = shlex.split(options) if legacy else http_get_options(insecure=insecure)
        ...

A driver that does not know the typed parameters (it predates them) keeps working for
every caller that passes only the string.
"""

from __future__ import annotations

import shlex
import warnings
from collections.abc import Mapping
from typing import cast


def settle_option_string(
    option_string: str | None,
    *,
    what: str,
    typed: Mapping[str, object],
    default: str = "",
) -> bool:
    """Decide which spelling a call used; return ``True`` when it is the option string.

    *option_string* is the deprecated free string, *typed* maps each typed parameter's name
    to the value the caller gave (``None`` and ``False`` mean "not given"), and *default*
    is the string's released default (``""``; ``"-A"`` for ``ps_options``), which counts
    as not given.

    - String not given: returns ``False``; the typed parameters apply.
    - String given and no typed parameter set: warns (``DeprecationWarning``, pointing at
      the driver's caller) and returns ``True``; the driver passes the string to the tool
      exactly as before.
    - Both given: raises ``ValueError`` naming the typed parameters, before any warning.
    """
    if option_string is None or option_string == default:
        return False
    if not isinstance(cast(object, option_string), str):  # callers are not all type-checked
        raise TypeError(f"{what}: takes a str, not {option_string!r}")
    given = [name for name, value in typed.items() if value is not None and bool(value)]
    if given:
        raise ValueError(
            f"{what}: pass either the option string {option_string!r} or the typed "
            f"parameters, not both (typed given: {', '.join(given)})"
        )
    warnings.warn(
        f"{what}: the option string is deprecated; pass the typed parameters"
        if typed
        else f"{what}: the option string is deprecated and has no typed replacement",
        DeprecationWarning,
        stacklevel=3,
    )
    return True


def option_text(argv: list[str]) -> str:
    """*argv* as the option string a pre-typed driver would receive (shell-quoted)."""
    return shlex.join(argv)


def http_get_options(
    *, no_proxy: bool = False, insecure: bool = False, follow_redirects: bool = False
) -> list[str]:
    """``curl``'s ``--noproxy '*'``, ``-k`` (skip certificate checks) and ``-L`` (follow
    redirects)."""
    argv: list[str] = []
    if no_proxy:
        argv += ["--noproxy", "*"]
    if insecure:
        argv.append("-k")
    if follow_redirects:
        argv.append("-L")
    return argv


def nmap_options(*, fast: bool = False) -> list[str]:
    """``nmap``'s ``-F`` (scan fewer ports than the default set)."""
    return ["-F"] if fast else []
