"""WiFi / WifiMesh template.

Defines the abstract contract for WiFi mesh participation: role
inspection, mesh enable/disable, topology read, backhaul-link
control (band / channel), agent onboarding (configurator and enrollee
sides), agent removal, and cross-mesh client steering.

Composed onto any device that participates in or will participate in a
wireless mesh. A pre-onboarding device (about to be added as an agent)
composes WifiMesh with its role reading "uncommissioned"; after
onboarding via the controller's add_agent, role becomes "agent".

Vendor uniformity for mesh is low — enterprise stacks use proprietary
multi-AP protocols; EasyMesh R1/R2/R3 lives in prpl, OneWiFi (RDK-B),
OpenWrt prplMesh, and select carrier-grade SKUs. Each driver translates
the uniform contract here to its underlying vendor RPCs (EasyMesh M1/M2,
proprietary controller add-agent calls, vendor-specific steering APIs).
Drivers without support for specific operations raise NotImplementedError.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from testprotocols.models.wifi import WifiMeshStatus, WifiMeshTopology


@runtime_checkable
class WifiMesh(Protocol):
    """Abstract contract for WiFi mesh participation."""

    # --- Admin state ---

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this device's participation in the mesh.

        When disabled, the device retains its role configuration but stops
        forwarding mesh frames and stops responding to mesh control messages.
        """
        ...

    # --- Status and topology ---

    def get_mesh_status(self) -> WifiMeshStatus:
        """Return this device's local mesh status.

        Includes role, enabled state, parent, hop count, and backhaul link.
        Lightweight read — does not query other agents.
        """
        ...

    def get_topology(self) -> WifiMeshTopology:
        """Return the full mesh topology as known to this device.

        Heavier read — for a controller, returns the full list of known
        agents with their parents and roles. For an agent, returns the
        agent's local view (typically just its parent and any peers it
        directly observes).
        """
        ...

    # --- Backhaul control (agent-side) ---

    def set_backhaul_band(self, band: str | None) -> None:
        """Force the backhaul radio to *band* (e.g. ``"5GHz"``), or pass None to
        release the constraint.

        Releasing returns the device to whatever band-selection policy
        the mesh controller / driver default uses. Drivers without
        backhaul-band override (typical of controller-only nodes that
        have no uplink) raise NotImplementedError.
        """
        ...

    def set_backhaul_channel(self, channel: int | None) -> None:
        """Force the backhaul radio to *channel*, or pass None to release the constraint.

        Drivers without backhaul-channel override raise NotImplementedError.
        Raises ValueError if *channel* is not supported on the current
        backhaul band.
        """
        ...

    # --- Agent management (typically controller-side) ---

    def add_agent(
        self,
        agent_mac: str,
        *,
        dpp_uri: str | None = None,
        psk: str | None = None,
        wps_pin: str | None = None,
        wps_pbc: bool = False,
        timeout: float = 60.0,
    ) -> None:
        """Onboard a new agent identified by *agent_mac* into the mesh.

        Exactly one onboarding credential must be passed:
        - *dpp_uri* — the agent's Device Provisioning Protocol URI
        - *psk* — pre-shared key the agent is preconfigured with
        - *wps_pin* — WPS PIN displayed on or assigned to the agent
        - *wps_pbc=True* — WPS Push-Button onboarding (controller starts PBC window)

        Blocks until the agent has joined the mesh (M1/M2 exchange complete
        and the agent appears in get_topology) or *timeout* seconds elapse.

        Raises ValueError if zero or multiple credentials are passed.
        Raises TimeoutError if onboarding does not complete within *timeout*.
        Drivers that do not support an onboarding method raise
        NotImplementedError when that credential is passed.
        """
        ...

    def remove_agent(self, agent_mac: str) -> None:
        """Remove the agent identified by *agent_mac* from the mesh.

        The agent is told to leave (mesh-leave message in EasyMesh, vendor
        equivalent otherwise), and is removed from the controller's
        topology.

        Raises KeyError if no agent with that MAC is currently in the mesh.
        """
        ...

    # --- DPP enrollee (typically agent-side, before onboarding) ---

    def get_dpp_uri(self) -> str:
        """Return this device's DPP bootstrap URI for use by a configurator.

        The URI encodes the device's DPP public key and supported channels
        (e.g. ``DPP:C:81/1;K:MDkw...;;``). Tests fetch it from the new agent,
        then pass it to the controller's ``add_agent(dpp_uri=...)``.

        Drivers without DPP enrollee support raise NotImplementedError.
        """
        ...

    def start_dpp_enrollee(self, timeout: float = 120.0) -> None:
        """Put the device into DPP-enrollee listening mode.

        Returns immediately. The device listens for DPP authentication
        from a configurator for *timeout* seconds (standard DPP window
        is 120s); after that, the listener closes whether or not
        onboarding completed.

        Drivers without DPP enrollee support raise NotImplementedError.
        Drivers where the enrollee listener is always-on (no explicit
        trigger needed) implement this as a no-op.
        """
        ...

    # --- WPS / PSK enrollee (agent-side) ---

    def trigger_wps_enrollee(
        self,
        *,
        pin: str | None = None,
        window_seconds: float = 120.0,
    ) -> None:
        """Put the device into WPS enrollee mode for mesh-agent onboarding.

        Returns immediately. The device listens for WPS handshake from a
        controller for *window_seconds* (standard WPS window is 120s).

        When *pin* is None, the device opens a WPS-PBC window — a
        controller in PBC mode within the same window completes the join.
        When *pin* is provided, the device opens a WPS-PIN window expecting
        a controller to present that PIN.

        *pin* is 4 or 8 digits per WPS spec, as ``str`` (preserves leading zeros).
        Drivers raise ValueError on malformed PINs.

        Drivers without WPS enrollee support raise NotImplementedError.
        """
        ...

    def set_mesh_psk_for_enrollment(self, psk: str | None) -> None:
        """Configure (or clear) the pre-shared key this device presents when joining a mesh.

        Used for PSK-based mesh enrollment, where an agent is preconfigured
        with the mesh PSK and the controller accepts agents presenting that
        PSK. Pass None to clear a previously-set PSK.

        Drivers without PSK-based mesh enrollment raise NotImplementedError.
        Read-side intentionally omitted: PSK is write-only across the contract.
        """
        ...

    # --- Cross-mesh client steering (typically controller-side) ---

    def steer_client(
        self,
        client_mac: str,
        target_agent_mac: str,
        *,
        disassoc_imminent: bool = False,
    ) -> None:
        """Steer the associated client *client_mac* toward agent *target_agent_mac*.

        The controller looks up which agent the client is currently on,
        sends an 802.11v BSS Transition Management Request from that agent
        suggesting the target, and (when *disassoc_imminent* is True) sets
        the disassoc-imminent bit so the client must roam or be disassociated.

        Fire-and-forget: returns once the BTM Request has been sent. Tests
        verify the outcome by polling ``WifiStations.get_station(client_mac).bss_name``
        on the target agent (or reading the controller's topology / association
        events).

        Raises KeyError if the client is not currently associated to any agent
        in the mesh, or if *target_agent_mac* is not a known agent.
        """
        ...
