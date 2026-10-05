"""SD-WAN failover scenario operations — cross-domain composites.

Receives resolved ``netem`` and ``router`` template instances from the caller.
These combine netem impairment injection with router path monitoring to
measure failover convergence behaviour. Operations are assertion-free —
callers interpret the returned measurements against scenario-specific
thresholds.
"""

from __future__ import annotations

import time

from testprotocols.models.impairment import Blackout
from testprotocols.netem_controller import NetemController
from testprotocols.router import Router

from testoperations._renamed import inject


def measure_failover_convergence(
    netem_controller: NetemController,
    router: Router,
    impaired_wan: str,
    timeout_ms: int = 3000,
) -> float:
    """Inject a blackout on *netem_controller* and measure how long it takes for
    *router* to switch away from *impaired_wan*.

    Returns elapsed milliseconds until the active WAN interface changes. The blackout is
    ``inject_event(Blackout(), timeout_ms)``; a driver without ``inject_event`` gets the
    released ``inject_transient("blackout", timeout_ms)``.
    """
    inject(netem_controller, Blackout(), timeout_ms, {})

    start = time.monotonic()
    while True:
        active = router.get_active_wan_interface()
        if active != impaired_wan:
            break
        time.sleep(0.05)

    elapsed_ms = (time.monotonic() - start) * 1000.0
    return elapsed_ms
