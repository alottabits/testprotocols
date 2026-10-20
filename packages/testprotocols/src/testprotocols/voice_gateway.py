"""Voice gateway — the gateway's own SIP accounts and analogue lines (the ``voice`` tier).

A residential gateway with voice registers its own SIP accounts with the
operator's registrar and serves analogue telephones on its FXS ports. This
capability is the gateway's side of that: its accounts, their registration
state and its lines. The test-bed ``sip_phone`` and ``sip_server`` are the far
ends and stay what they are.

In scope: the SIP accounts (write, remove, list), the registration state per
account, the FXS lines.

Out of scope: the test-bed phone and registrar (see ``sip_phone``,
``sip_server``), the other management protocols (see ``tr069_client``,
``usp_agent``), call control on the gateway.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.voice import FxsLine, SipAccount, SipRegistration


@runtime_checkable
class VoiceGateway(Protocol):
    """Abstract contract for the gateway's own SIP accounts and analogue lines."""

    def set_sip_account(self, account: SipAccount) -> None:
        """Write the SIP *account* under its ``name``; paired read ``list_sip_accounts``.

        ``SipAccount.password`` is required on a write and ``None`` on every read: the written
        value is confirmed by ``get_sip_registration`` showing
        ``SipRegistrationState.REGISTERED``.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found account list where the family commits atomically,
        otherwise the steps applied before the rejection.
        """
        ...

    def remove_sip_account(self, name: str) -> None:
        """Remove the SIP account *name*; paired read ``list_sip_accounts``.

        Raises ``KeyError`` if no account named *name* exists.

        A write rejected at any step raises naming the step; the driver puts nothing back. The
        state is then the as-found account list where the family commits atomically, otherwise
        the steps applied before the rejection.
        """
        ...

    def list_sip_accounts(self) -> list[SipAccount]:
        """Return every SIP account, every ``password`` ``None``."""
        ...

    def get_sip_registration(self, name: str) -> SipRegistration:
        """Return the registration state of the account *name*.

        Raises ``KeyError`` if no account named *name* exists.
        """
        ...

    def list_fxs_lines(self) -> list[FxsLine]:
        """Return the analogue lines; ``hook_state`` is ``None`` where the family publishes
        the port but not its state."""
        ...
