"""WiFi / WifiBss template.

Defines the abstract contract for per-SSID / per-VAP configuration on a
WiFi-capable device: lifecycle, security, MAC ACL authorization,
broadcast suppression, VLAN binding, max-clients, DTIM, and captive-portal
admin.

A BSS is identified by a stable logical *name* the test supplies at
creation time (matching the RadiusClient.add_server pattern). The SSID
broadcast string can change later via set_ssid without affecting the
identity of the BSS in the contract.

802.1X / Enterprise security references RADIUS servers by *name* — the
referenced server must be registered via the RadiusClient template
composed on the same device. Drivers whose device does not compose
RadiusClient cannot satisfy EAP modes — they raise on those
*security_mode* values.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import WifiAcl, WifiBssConfig


@runtime_checkable
class WifiBss(Protocol):
    """Abstract contract for per-SSID / per-VAP WiFi configuration."""

    # --- Lifecycle ---

    def create_bss(
        self,
        name: str,
        band: str,
        ssid: str,
        security_mode: str,
        *,
        passphrase: str | None = None,
        radius_server_name: str | None = None,
        mfp: str = "optional",
        vlan_id: int | None = None,
        max_clients: int | None = None,
        broadcast_enabled: bool = True,
        dtim_period: int = 2,
    ) -> None:
        """Create a new BSS on *band*, identified by *name*.

        *security_mode* is one of: ``"Open"``, ``"OWE"``, ``"WPA2-PSK"``,
        ``"WPA2-EAP"``, ``"WPA3-SAE"``, ``"WPA3-EAP"``,
        ``"WPA2-WPA3-PSK-Mixed"``, ``"WPA2-WPA3-EAP-Mixed"``.

        *mfp* is one of ``"off"``, ``"optional"``, ``"required"``.

        Required arguments per security_mode:
        - PSK / SAE / mixed-PSK modes: *passphrase* required
        - EAP / mixed-EAP modes: *radius_server_name* required, must
          reference a server registered via RadiusClient on this device
        - Open / OWE: neither required

        Raises ValueError on a duplicate *name* or on missing
        mode-required arguments.
        """
        ...

    def delete_bss(self, name: str) -> None:
        """Delete the BSS identified by *name*. Raises KeyError if absent."""
        ...

    def list_bss(self) -> list[WifiBssConfig]:
        """Return all BSS configurations on the device (without secrets)."""
        ...

    def get_bss_config(self, name: str) -> WifiBssConfig:
        """Return the full configuration of the BSS identified by *name* (without secret).

        Raises KeyError if absent.
        """
        ...

    # --- Admin state ---

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable the BSS without deleting it.

        The radio stays up (DFS continues, neighbour scanning continues);
        only the BSS stops broadcasting and accepting clients.
        """
        ...

    # --- SSID broadcast ---

    def set_ssid(self, name: str, ssid: str) -> None:
        """Change the broadcast SSID string of the BSS identified by *name*.

        Does not change the logical *name* (which remains the contract handle).
        """
        ...

    def set_broadcast_enabled(self, name: str, enabled: bool) -> None:
        """Suppress or restore SSID broadcast in beacons (hidden SSID)."""
        ...

    # --- Security ---

    def set_security(
        self,
        name: str,
        mode: str,
        *,
        passphrase: str | None = None,
        radius_server_name: str | None = None,
        mfp: str = "optional",
    ) -> None:
        """Reconfigure the security of an existing BSS.

        Same value space and required-argument rules as ``create_bss``.
        Reconfiguration disconnects currently associated clients on most
        drivers; tests should expect re-association.
        """
        ...

    # --- MAC ACL — per-BSS authorization scheme ---

    def set_acl_mode(self, name: str, mode: str) -> None:
        """Set the per-BSS MAC ACL mode.

        *mode* is one of:
        - ``"disabled"`` — no MAC filtering; the BSS's ACL list is ignored
        - ``"allow"`` — allow-list (whitelist); only MACs in the ACL may associate
        - ``"deny"`` — deny-list (blacklist); MACs in the ACL are blocked

        Raises KeyError if *name* is not registered.
        """
        ...

    def add_acl_entry(self, name: str, mac: str) -> None:
        """Add *mac* to the BSS's ACL list. No-op if already present.

        Effective filtering depends on the current ACL mode.
        Raises KeyError if *name* is not registered.
        """
        ...

    def remove_acl_entry(self, name: str, mac: str) -> None:
        """Remove *mac* from the BSS's ACL list. No-op if absent.

        Raises KeyError if *name* is not registered.
        """
        ...

    def clear_acl(self, name: str) -> None:
        """Remove all entries from the BSS's ACL list. Mode is unchanged.

        Raises KeyError if *name* is not registered.
        """
        ...

    def get_acl(self, name: str) -> WifiAcl:
        """Return the BSS's MAC ACL state (mode + entries).

        Raises KeyError if *name* is not registered.
        """
        ...

    # --- VLAN binding ---

    def set_vlan(self, name: str, vlan_id: int | None) -> None:
        """Bind the BSS to *vlan_id*, or pass None to remove the binding (untagged)."""
        ...

    # --- Capacity / timing ---

    def set_max_clients(self, name: str, max_clients: int | None) -> None:
        """Cap concurrent associations at *max_clients*, or pass None to remove the cap."""
        ...

    def set_dtim_period(self, name: str, period: int) -> None:
        """Set the DTIM period (number of beacons between DTIM transmissions). Typical: 1-5."""
        ...

    # --- Captive portal (minimal on-AP surface) ---

    def set_captive_portal(
        self,
        name: str,
        enabled: bool,
        redirect_url: str | None = None,
    ) -> None:
        """Enable or disable the per-BSS captive portal.

        When enabled, *redirect_url* is the splash page clients are
        redirected to. Voucher / local-account / splash-HTML upload are
        out of scope here — they belong to WifiController.
        """
        ...
