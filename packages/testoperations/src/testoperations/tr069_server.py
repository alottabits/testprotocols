"""TR-069 server (NBI) operations — CPE online probe with try/except logic.

Receives a resolved ``tr069_server`` template instance and a ``cpe_id`` string
from the caller.  Thin wrappers (GPV, SPV, Reboot) are deleted — step
definitions call the template method directly.
"""

from __future__ import annotations

from testprotocols.tr069_server import Tr069Server

from testoperations._renamed import get_parameter_value


def is_cpe_online(tr069_server: Tr069Server, cpe_id: str) -> bool:
    """Probe whether a CPE is online by attempting a GetParameterValues call.

    Calls ``get_parameter_values`` when the driver has it, else the released ``GPV``.
    Returns True if the ACS can reach the CPE, False otherwise.
    """
    try:
        get_parameter_value(
            tr069_server,
            "InternetGatewayDevice.DeviceInfo.UpTime",
            cpe_id=cpe_id,
        )
        return True
    except Exception:
        return False
