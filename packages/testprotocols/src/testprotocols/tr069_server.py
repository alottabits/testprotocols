"""TR-069 ACS server template.

Defines the abstract contract for TR-069 ACS (Auto Configuration Server)
operations, including all standard CWMP RPC methods.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Tr069Server(Protocol):
    """Abstract contract for TR-069 ACS operations."""

    def GPV(
        self,
        param: str | list[str],
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict]:
        """GetParameterValues RPC."""
        ...

    def SPV(
        self,
        param_value: dict | list[dict],
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> int:
        """SetParameterValues RPC."""
        ...

    def GPA(
        self,
        param: str,
        cpe_id: str | None = None,
    ) -> list[dict]:
        """GetParameterAttributes RPC."""
        ...

    def SPA(
        self,
        param: list[dict] | dict,
        notification_param: bool = True,
        access_param: bool = False,
        access_list: list | None = None,
        cpe_id: str | None = None,
    ) -> list[dict]:
        """SetParameterAttributes RPC."""
        ...

    def FactoryReset(self, cpe_id: str | None = None) -> list[dict]:
        """FactoryReset RPC."""
        ...

    def Reboot(
        self,
        CommandKey: str = "reboot",
        cpe_id: str | None = None,
    ) -> list[dict]:
        """Reboot RPC."""
        ...

    def AddObject(
        self,
        param: str,
        param_key: str = "",
        cpe_id: str | None = None,
    ) -> list[dict]:
        """AddObject RPC."""
        ...

    def DelObject(
        self,
        param: str,
        param_key: str = "",
        cpe_id: str | None = None,
    ) -> list[dict]:
        """DeleteObject RPC."""
        ...

    def GPN(
        self,
        param: str,
        next_level: bool,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict]:
        """GetParameterNames RPC."""
        ...

    def ScheduleInform(
        self,
        CommandKey: str = "Test",
        DelaySeconds: int = 20,
        cpe_id: str | None = None,
    ) -> list[dict]:
        """ScheduleInform RPC."""
        ...

    def GetRPCMethods(self, cpe_id: str | None = None) -> list[dict]:
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
    ) -> list[dict]:
        """Download RPC."""
        ...

    def provision_cpe_via_tr069(
        self,
        tr069provision_api_list: list[dict[str, list[dict[str, str]]]],
        cpe_id: str,
    ) -> None:
        """Provision a CPE by executing a sequence of TR-069 API calls."""
        ...
