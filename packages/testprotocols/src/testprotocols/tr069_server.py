"""TR-069 ACS server template.

Defines the abstract contract for TR-069 ACS (Auto Configuration Server)
operations, including all standard CWMP RPC methods and ACS-side state
(inventory, per-CPE connection status, Inform timing).

"CPE" follows TR-069 §2: any CWMP-managed device — gateway, set-top box,
VoIP ATA, femtocell, IoT endpoint — not specifically a residential
gateway.

Each CWMP RPC is a typed member named after the RPC in snake case
(``get_parameter_values`` for GetParameterValues, …), taking and returning the
CWMP structures of :mod:`testprotocols.models.cwmp`. FactoryReset is
``factory_reset_cpe``, because ``DeviceLifecycle.factory_reset`` is a different
member. ``cpe_id`` (``None``: the driver's default CPE) and the options are
keyword-only; an option left ``None`` is not sent, so the ACS or the CPE applies
its own default.

The released members ``GPV``, ``SPV``, ``GPA``, ``SPA``, ``FactoryReset``,
``Reboot``, ``AddObject``, ``DelObject``, ``GPN``, ``ScheduleInform``,
``GetRPCMethods`` and ``Download`` are deprecated names of the typed members. A
migrated driver warns with ``warn_renamed(old, new)`` and keeps the old member's
released output: released drivers return different dict shapes for the same RPC,
so no conversion from the typed result reproduces each of them. Their ``dict`` and
``Any`` annotations are released signatures kept until removal (a released
driver declares narrower ``dict`` types, and ``dict`` is invariant).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from testprotocols.models.cwmp import (
    AddObjectResult,
    CwmpFileType,
    CwmpStatus,
    DownloadResult,
    ParameterAttribute,
    ParameterInfo,
    ParameterValue,
)
from testprotocols.models.tr069 import CpeConnectionStatus


@runtime_checkable
class Tr069Server(Protocol):
    """Abstract contract for TR-069 ACS operations."""

    # --- CWMP RPCs, typed -------------------------------------------------------------

    def get_parameter_values(
        self,
        names: Sequence[str],
        *,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[ParameterValue]:
        """GetParameterValues: the values of the parameters *names*.

        A name ending in ``.`` (a partial path) asks for every parameter below it.
        *names* is a sequence of names: a bare ``str`` is not one, and the driver raises
        ``TypeError`` for it. *timeout* bounds the RPC in seconds (``None``: the driver's
        default). A value whose type the CPE reports as no built-in type, or not at all, is
        ``CwmpType.OTHER`` with its text (``ParameterValue.from_text`` builds it).
        """
        ...

    def set_parameter_values(
        self,
        values: Sequence[ParameterValue],
        *,
        parameter_key: str | None = None,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> CwmpStatus:
        """SetParameterValues: set every value in *values* in one RPC; return its status.

        *parameter_key* is the CWMP ParameterKey (at most 32 characters) the CPE stores
        on success; ``None`` lets the ACS choose it.
        """
        ...

    def get_parameter_attributes(
        self,
        names: Sequence[str],
        *,
        cpe_id: str | None = None,
    ) -> list[ParameterAttribute]:
        """GetParameterAttributes: the notification and access list of *names* (a bare
        ``str`` is not a sequence of names: the driver raises ``TypeError``)."""
        ...

    def set_parameter_attributes(
        self,
        attributes: Sequence[ParameterAttribute],
        *,
        change_notification: bool = True,
        change_access_list: bool = False,
        cpe_id: str | None = None,
    ) -> None:
        """SetParameterAttributes: apply *attributes* in one RPC.

        *change_notification* and *change_access_list* are the CWMP NotificationChange
        and AccessListChange flags, the same for every attribute: an attribute part whose
        flag is false is left as it is on the CPE.
        """
        ...

    def factory_reset_cpe(self, *, cpe_id: str | None = None) -> None:
        """FactoryReset: ask the CPE to reset to its factory defaults."""
        ...

    def reboot(self, command_key: str | None = None, *, cpe_id: str | None = None) -> None:
        """Reboot: ask the CPE to reboot.

        *command_key* is the CWMP CommandKey the CPE reports back with its ``M Reboot``
        Inform event; ``None`` lets the ACS choose it.
        """
        ...

    def add_object(
        self,
        object_name: str,
        *,
        parameter_key: str | None = None,
        cpe_id: str | None = None,
    ) -> AddObjectResult:
        """AddObject: create an instance of the multi-instance object *object_name*
        (a path ending in ``.``); return its instance number and the status."""
        ...

    def delete_object(
        self,
        object_name: str,
        *,
        parameter_key: str | None = None,
        cpe_id: str | None = None,
    ) -> CwmpStatus:
        """DeleteObject: delete the object instance *object_name* (a path ending in
        ``.``); return the status."""
        ...

    def get_parameter_names(
        self,
        path: str,
        next_level: bool,
        *,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[ParameterInfo]:
        """GetParameterNames: the parameters and objects at or below *path*.

        With *next_level* only the direct children of the partial path *path* are
        returned; otherwise the whole subtree.
        """
        ...

    def schedule_inform(
        self,
        delay_seconds: int = 20,
        *,
        command_key: str | None = None,
        cpe_id: str | None = None,
    ) -> None:
        """ScheduleInform: ask the CPE to start a session (an Inform with the
        ``M ScheduleInform`` event) *delay_seconds* from now; ``0`` asks for one at once.

        *command_key* is the CWMP CommandKey of that event; ``None`` lets the ACS choose
        it.
        """
        ...

    def get_rpc_methods(self, *, cpe_id: str | None = None) -> list[str]:
        """GetRPCMethods: the names of the RPC methods the CPE supports."""
        ...

    def download(
        self,
        url: str,
        file_type: CwmpFileType = CwmpFileType.FIRMWARE_UPGRADE_IMAGE,
        *,
        target_file_name: str | None = None,
        file_size: int | None = None,
        username: str | None = None,
        password: str | None = None,
        command_key: str | None = None,
        delay_seconds: int = 10,
        success_url: str | None = None,
        failure_url: str | None = None,
        cpe_id: str | None = None,
    ) -> DownloadResult:
        """Download: ask the CPE to fetch the file at *url* and apply it.

        A ``None`` argument is not sent: no target file name, no announced size (bytes),
        no credentials, no success or failure URL, and a CommandKey the ACS chooses.
        The CPE starts *delay_seconds* after the RPC.
        """
        ...

    # --- CWMP RPCs, deprecated names --------------------------------------------------

    def GPV(
        self,
        param: str | list[str],
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`get_parameter_values`.

        GetParameterValues. The driver warns with
        ``warn_renamed("GPV", "get_parameter_values")`` and keeps its released output.
        """
        ...

    def SPV(
        self,
        param_value: dict[str, Any] | list[dict[str, Any]],  # released signature kept
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> int:
        """Deprecated name of :meth:`set_parameter_values`.

        SetParameterValues. The driver warns with
        ``warn_renamed("SPV", "set_parameter_values")`` and keeps its released output.
        """
        ...

    def GPA(
        self,
        param: str,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`get_parameter_attributes`.

        GetParameterAttributes. The driver warns with
        ``warn_renamed("GPA", "get_parameter_attributes")`` and keeps its released output.
        """
        ...

    def SPA(
        self,
        param: list[dict[str, Any]] | dict[str, Any],  # released signature kept
        notification_param: bool = True,
        access_param: bool = False,
        access_list: list[Any] | None = None,  # released signature kept
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`set_parameter_attributes`.

        SetParameterAttributes. The driver warns with
        ``warn_renamed("SPA", "set_parameter_attributes")`` and keeps its released output.
        """
        ...

    def FactoryReset(
        self,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`factory_reset_cpe`.

        FactoryReset. The driver warns with
        ``warn_renamed("FactoryReset", "factory_reset_cpe")`` and keeps its released output.
        """
        ...

    def Reboot(
        self,
        CommandKey: str = "reboot",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`reboot`.

        Reboot. The driver warns with ``warn_renamed("Reboot", "reboot")`` and keeps its
        released output.
        """
        ...

    def AddObject(
        self,
        param: str,
        param_key: str = "",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`add_object`.

        AddObject. The driver warns with ``warn_renamed("AddObject", "add_object")`` and
        keeps its released output. Announced: *param_key* ``""`` means "not given"
        (``None`` on the successor).
        """
        ...

    def DelObject(
        self,
        param: str,
        param_key: str = "",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`delete_object`.

        DeleteObject. The driver warns with ``warn_renamed("DelObject", "delete_object")``
        and keeps its released output. Announced: *param_key* ``""`` means "not given"
        (``None`` on the successor).
        """
        ...

    def GPN(
        self,
        param: str,
        next_level: bool,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`get_parameter_names`.

        GetParameterNames. The driver warns with
        ``warn_renamed("GPN", "get_parameter_names")`` and keeps its released output.
        """
        ...

    def ScheduleInform(
        self,
        CommandKey: str = "Test",
        DelaySeconds: int = 20,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`schedule_inform`.

        ScheduleInform. The driver warns with
        ``warn_renamed("ScheduleInform", "schedule_inform")`` and keeps its released
        output.
        """
        ...

    def GetRPCMethods(
        self,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`get_rpc_methods`.

        GetRPCMethods. The driver warns with
        ``warn_renamed("GetRPCMethods", "get_rpc_methods")`` and keeps its released output.
        """
        ...

    def Download(
        self,
        url: str,
        filetype: str = "1 Firmware Upgrade Image",
        targetfilename: str = "",
        filesize: int = 200,
        username: str = "",
        password: str = "",
        commandkey: str = "",
        delayseconds: int = 10,
        successurl: str = "",
        failureurl: str = "",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:  # released signature kept
        """Deprecated name of :meth:`download`.

        Download. The driver warns with ``warn_renamed("Download", "download")`` and keeps
        its released output. *filetype* is a ``CwmpFileType`` value. Announced: the ``""``
        defaults (*targetfilename*, *username*, *password*, *commandkey*, *successurl*,
        *failureurl*) mean "not given" (``None`` on the successor).
        """
        ...

    # --- ACS-side state ---------------------------------------------------------------

    def provision_cpe_via_tr069(
        self,
        tr069provision_api_list: list[dict[str, list[dict[str, str]]]],
        cpe_id: str,
    ) -> None:
        """Provision a CPE by executing a sequence of TR-069 API calls."""
        ...

    def list_cpes(
        self,
        criteria: dict[str, str] | None = None,
    ) -> list[str]:
        """Return CPE IDs known to the ACS, optionally filtered by criteria."""
        ...

    def delete_cpe_record(self, cpe_id: str) -> bool:
        """Delete the CPE record from the ACS inventory. Return True on success."""
        ...

    def get_cpe_connection_status(self, cpe_id: str) -> CpeConnectionStatus:
        """Return the ACS-side view of the CPE's connection state and cached metadata."""
        ...
