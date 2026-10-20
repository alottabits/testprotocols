"""Administrator credential — the gateway's local management accounts.

The password of a local account is a lever: its confirming observation is a
new management session authenticating with the credential, which the test
opens (a second driver instance), never the driver after its own write. When
the account is the driver's own login, the driver's open session continues
and every later connection needs the new credential, which the test supplies;
the driver does not update its own configuration.

In scope: set an account's password, list the accounts.

Out of scope: a server registry for remote authentication (see
``radius_client``), the remote-management credentials (see ``tr069_client``).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AdminCredential(Protocol):
    """Abstract contract for the gateway's local administrator credential."""

    def set_password(self, account: str, password: str) -> None:
        """Set the password of the local *account*.

        A lever: confirmed by a new management session the test opens with the credential.
        The driver's own session continues and its configuration is not updated;
        ``list_accounts`` is the read that finds the account. Raises ``KeyError`` if no local
        account named *account* exists.
        """
        ...

    def list_accounts(self) -> list[str]:
        """Return the names of the local management accounts."""
        ...
