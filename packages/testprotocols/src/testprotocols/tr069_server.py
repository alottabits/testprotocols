"""TR-069 ACS server template.

Defines the abstract contract for TR-069 ACS (Auto Configuration Server)
operations, including all standard CWMP RPC methods.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tr069Server(Protocol):
    """Abstract contract for TR-069 ACS operations."""

    def GPV(
        self,
        param: str | list[str],
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """GetParameterValues RPC."""
        ...

    def SPV(
        self,
        param_value: dict[str, Any] | list[dict[str, Any]],
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> int:
        """SetParameterValues RPC."""
        ...

    def GPA(
        self,
        param: str,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """GetParameterAttributes RPC."""
        ...

    def SPA(
        self,
        param: list[dict[str, Any]] | dict[str, Any],
        notification_param: bool = True,
        access_param: bool = False,
        access_list: list[Any] | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """SetParameterAttributes RPC."""
        ...

    def FactoryReset(self, cpe_id: str | None = None) -> list[dict[str, Any]]:
        """FactoryReset RPC."""
        ...

    def Reboot(
        self,
        CommandKey: str = "reboot",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reboot RPC."""
        ...

    def AddObject(
        self,
        param: str,
        param_key: str = "",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """AddObject RPC."""
        ...

    def DelObject(
        self,
        param: str,
        param_key: str = "",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """DeleteObject RPC."""
        ...

    def GPN(
        self,
        param: str,
        next_level: bool,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """GetParameterNames RPC."""
        ...

    def ScheduleInform(
        self,
        CommandKey: str = "Test",
        DelaySeconds: int = 20,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """ScheduleInform RPC."""
        ...

    def GetRPCMethods(self, cpe_id: str | None = None) -> list[dict[str, Any]]:
        """GetRPCMethods RPC."""
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
    ) -> list[dict[str, Any]]:
        """Download RPC."""
        ...

    def provision_cpe_via_tr069(
        self,
        tr069provision_api_list: list[dict[str, list[dict[str, str]]]],
        cpe_id: str,
    ) -> None:
        """Provision a CPE by executing a sequence of TR-069 API calls."""
        ...
