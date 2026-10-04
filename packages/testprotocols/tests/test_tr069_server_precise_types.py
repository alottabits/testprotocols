"""Tr069Server: typed RPC members over the CWMP structures; the dict RPCs are deprecated names."""

from __future__ import annotations

import ast
import inspect
import typing
import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any, override

import pytest
import testprotocols.tr069_server as tr069_server_module
from _helpers import protocol_attrs
from testprotocols.deprecation import warn_renamed
from testprotocols.models import (
    AddObjectResult,
    CpeConnectionStatus,
    CwmpFileType,
    CwmpNotification,
    CwmpStatus,
    CwmpType,
    DownloadResult,
    ParameterAttribute,
    ParameterInfo,
    ParameterValue,
)
from testprotocols.tr069_server import Tr069Server

_RELEASED_RPCS = {
    "GPV": "get_parameter_values",
    "SPV": "set_parameter_values",
    "GPA": "get_parameter_attributes",
    "SPA": "set_parameter_attributes",
    "FactoryReset": "factory_reset_cpe",
    "Reboot": "reboot",
    "AddObject": "add_object",
    "DelObject": "delete_object",
    "GPN": "get_parameter_names",
    "ScheduleInform": "schedule_inform",
    "GetRPCMethods": "get_rpc_methods",
    "Download": "download",
}


class _OldAcs:
    """A driver written against the released contract (dict RPCs only)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def _record(self, name: str, *args: object, **kwargs: object) -> list[dict[str, Any]]:
        self.calls.append((name, args, kwargs))
        return []

    def GPV(
        self, param: str | list[str], timeout: int | None = None, cpe_id: str | None = None
    ) -> list[dict[str, Any]]:
        self.calls.append(("GPV", (param,), {"timeout": timeout, "cpe_id": cpe_id}))
        names = [param] if isinstance(param, str) else param
        return [{"key": n, "value": "SN42", "type": "xsd:string"} for n in names]

    def SPV(
        self,
        param_value: dict[str, Any] | list[dict[str, Any]],
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> int:
        return 0

    def GPA(self, param: str, cpe_id: str | None = None) -> list[dict[str, Any]]:
        return self._record("GPA", param)

    def SPA(
        self,
        param: list[dict[str, Any]] | dict[str, Any],
        notification_param: bool = True,
        access_param: bool = False,
        access_list: list[Any] | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._record("SPA", param)

    def FactoryReset(self, cpe_id: str | None = None) -> list[dict[str, Any]]:
        return self._record("FactoryReset")

    def Reboot(
        self,
        CommandKey: str = "reboot",
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._record("Reboot", CommandKey)

    def AddObject(
        self, param: str, param_key: str = "", cpe_id: str | None = None
    ) -> list[dict[str, Any]]:
        return self._record("AddObject", param)

    def DelObject(
        self, param: str, param_key: str = "", cpe_id: str | None = None
    ) -> list[dict[str, Any]]:
        return self._record("DelObject", param)

    def GPN(
        self,
        param: str,
        next_level: bool,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._record("GPN", param)

    def ScheduleInform(
        self,
        CommandKey: str = "Test",
        DelaySeconds: int = 20,
        cpe_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._record("ScheduleInform", CommandKey, DelaySeconds)

    def GetRPCMethods(self, cpe_id: str | None = None) -> list[dict[str, Any]]:
        return self._record("GetRPCMethods")

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
        return self._record("Download", url, filetype)

    def provision_cpe_via_tr069(
        self, tr069provision_api_list: list[dict[str, list[dict[str, str]]]], cpe_id: str
    ) -> None: ...

    def list_cpes(self, criteria: dict[str, str] | None = None) -> list[str]:
        return []

    def delete_cpe_record(self, cpe_id: str) -> bool:
        return True

    def get_cpe_connection_status(self, cpe_id: str) -> CpeConnectionStatus:
        return CpeConnectionStatus(online=True)


class _TypedAcs(_OldAcs):
    """A migrated driver: the typed members, and the old names warning and kept."""

    @override
    def GPV(
        self, param: str | list[str], timeout: int | None = None, cpe_id: str | None = None
    ) -> list[dict[str, Any]]:
        warn_renamed("GPV", "get_parameter_values")
        return super().GPV(param, timeout, cpe_id)

    def get_parameter_values(
        self, names: Sequence[str], *, timeout: int | None = None, cpe_id: str | None = None
    ) -> list[ParameterValue]:
        self.calls.append(("get_parameter_values", (list(names),), {"cpe_id": cpe_id}))
        return [ParameterValue(n, 42, CwmpType.UNSIGNED_INT) for n in names]

    def set_parameter_values(
        self,
        values: Sequence[ParameterValue],
        *,
        parameter_key: str | None = None,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> CwmpStatus:
        return CwmpStatus.APPLIED

    def get_parameter_attributes(
        self, names: Sequence[str], *, cpe_id: str | None = None
    ) -> list[ParameterAttribute]:
        return [ParameterAttribute(n, CwmpNotification.OFF) for n in names]

    def set_parameter_attributes(
        self,
        attributes: Sequence[ParameterAttribute],
        *,
        change_notification: bool = True,
        change_access_list: bool = False,
        cpe_id: str | None = None,
    ) -> None: ...

    def factory_reset_cpe(self, *, cpe_id: str | None = None) -> None: ...

    def reboot(self, command_key: str | None = None, *, cpe_id: str | None = None) -> None: ...

    def add_object(
        self, object_name: str, *, parameter_key: str | None = None, cpe_id: str | None = None
    ) -> AddObjectResult:
        return AddObjectResult(1, CwmpStatus.APPLIED)

    def delete_object(
        self, object_name: str, *, parameter_key: str | None = None, cpe_id: str | None = None
    ) -> CwmpStatus:
        return CwmpStatus.APPLIED

    def get_parameter_names(
        self,
        path: str,
        next_level: bool,
        *,
        timeout: int | None = None,
        cpe_id: str | None = None,
    ) -> list[ParameterInfo]:
        return [ParameterInfo(path + "UpTime", False)]

    def schedule_inform(
        self,
        delay_seconds: int = 20,
        *,
        command_key: str | None = None,
        cpe_id: str | None = None,
    ) -> None: ...

    def get_rpc_methods(self, *, cpe_id: str | None = None) -> list[str]:
        return ["GetRPCMethods", "GetParameterValues"]

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
        return DownloadResult(CwmpStatus.NOT_YET_APPLIED)


def test_the_typed_members_are_protocol_members() -> None:
    members = protocol_attrs(Tr069Server)
    assert set(_RELEASED_RPCS) <= members
    assert set(_RELEASED_RPCS.values()) <= members


def test_a_migrated_driver_conforms_and_an_old_driver_no_longer_does() -> None:
    assert isinstance(_TypedAcs(), Tr069Server)
    assert not isinstance(_OldAcs(), Tr069Server)
    acs: Tr069Server = _TypedAcs()
    assert acs.get_parameter_values(["Device.DeviceInfo.UpTime"]) == [
        ParameterValue("Device.DeviceInfo.UpTime", 42, CwmpType.UNSIGNED_INT)
    ]


def _hints(name: str) -> dict[str, object]:
    return typing.get_type_hints(getattr(Tr069Server, name), dict(vars(tr069_server_module)))


def test_typed_member_signatures() -> None:
    expected: dict[str, dict[str, object]] = {
        "get_parameter_values": {
            "names": Sequence[str],
            "timeout": int | None,
            "cpe_id": str | None,
            "return": list[ParameterValue],
        },
        "set_parameter_values": {
            "values": Sequence[ParameterValue],
            "parameter_key": str | None,
            "return": CwmpStatus,
        },
        "get_parameter_attributes": {"names": Sequence[str], "return": list[ParameterAttribute]},
        "set_parameter_attributes": {
            "attributes": Sequence[ParameterAttribute],
            "change_notification": bool,
            "change_access_list": bool,
            "return": type(None),
        },
        "factory_reset_cpe": {"cpe_id": str | None, "return": type(None)},
        "reboot": {"command_key": str | None, "return": type(None)},
        "add_object": {"object_name": str, "parameter_key": str | None, "return": AddObjectResult},
        "delete_object": {"object_name": str, "parameter_key": str | None, "return": CwmpStatus},
        "get_parameter_names": {"path": str, "next_level": bool, "return": list[ParameterInfo]},
        "schedule_inform": {"delay_seconds": int, "command_key": str | None, "return": type(None)},
        "get_rpc_methods": {"return": list[str]},
        "download": {
            "url": str,
            "file_type": CwmpFileType,
            "target_file_name": str | None,
            "file_size": int | None,
            "username": str | None,
            "password": str | None,
            "command_key": str | None,
            "delay_seconds": int,
            "success_url": str | None,
            "failure_url": str | None,
            "return": DownloadResult,
        },
    }
    for name, want in expected.items():
        hints = _hints(name)
        for param, annotation in want.items():
            assert hints[param] == annotation, (name, param)


# Every typed member's parameters, by kind: the leading (positional-or-keyword) ones, and the
# keyword-only options with their defaults. ``None`` means "not given" (O46).
_TYPED_PARAMETERS: dict[str, tuple[list[str], dict[str, object]]] = {
    "get_parameter_values": (["names"], {"timeout": None, "cpe_id": None}),
    "set_parameter_values": (
        ["values"],
        {"parameter_key": None, "timeout": None, "cpe_id": None},
    ),
    "get_parameter_attributes": (["names"], {"cpe_id": None}),
    "set_parameter_attributes": (
        ["attributes"],
        {"change_notification": True, "change_access_list": False, "cpe_id": None},
    ),
    "factory_reset_cpe": ([], {"cpe_id": None}),
    "reboot": (["command_key"], {"cpe_id": None}),
    "add_object": (["object_name"], {"parameter_key": None, "cpe_id": None}),
    "delete_object": (["object_name"], {"parameter_key": None, "cpe_id": None}),
    "get_parameter_names": (["path", "next_level"], {"timeout": None, "cpe_id": None}),
    "schedule_inform": (["delay_seconds"], {"command_key": None, "cpe_id": None}),
    "get_rpc_methods": ([], {"cpe_id": None}),
    "download": (
        ["url", "file_type"],
        {
            "target_file_name": None,
            "file_size": None,
            "username": None,
            "password": None,
            "command_key": None,
            "delay_seconds": 10,
            "success_url": None,
            "failure_url": None,
            "cpe_id": None,
        },
    ),
}


def test_typed_members_take_every_option_by_keyword_only() -> None:
    assert set(_TYPED_PARAMETERS) == set(_RELEASED_RPCS.values())
    for name, (leading, options) in _TYPED_PARAMETERS.items():
        params = list(inspect.signature(getattr(Tr069Server, name)).parameters.values())[1:]
        positional = [p.name for p in params if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD]
        keyword = {p.name: p.default for p in params if p.kind is inspect.Parameter.KEYWORD_ONLY}
        assert positional == leading, name
        assert keyword == options, name
        assert len(params) == len(leading) + len(options), name
    defaults = inspect.signature(Tr069Server.download).parameters
    assert defaults["file_type"].default is CwmpFileType.FIRMWARE_UPGRADE_IMAGE
    assert inspect.signature(Tr069Server.reboot).parameters["command_key"].default is None
    assert inspect.signature(Tr069Server.schedule_inform).parameters["delay_seconds"].default == 20


def test_old_names_are_documented_as_deprecated_names_of_the_typed_members() -> None:
    for old, new in _RELEASED_RPCS.items():
        doc = inspect.getdoc(getattr(Tr069Server, old)) or ""
        assert doc.startswith(f"Deprecated name of :meth:`{new}`"), old
        assert f'warn_renamed("{old}", "{new}")' in doc, old


# The 16 released members exactly as on the last release (``inspect.signature`` text).
_RELEASED_SIGNATURES = {
    "GPV": "(self, param: 'str | list[str]', timeout: 'int | None' = None, cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "SPV": "(self, param_value: 'dict[str, Any] | list[dict[str, Any]]', timeout: 'int | None' = None, cpe_id: 'str | None' = None) -> 'int'",  # noqa: E501
    "GPA": "(self, param: 'str', cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",
    "SPA": "(self, param: 'list[dict[str, Any]] | dict[str, Any]', notification_param: 'bool' = True, access_param: 'bool' = False, access_list: 'list[Any] | None' = None, cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "FactoryReset": "(self, cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",
    "Reboot": "(self, CommandKey: 'str' = 'reboot', cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "AddObject": "(self, param: 'str', param_key: 'str' = '', cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "DelObject": "(self, param: 'str', param_key: 'str' = '', cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "GPN": "(self, param: 'str', next_level: 'bool', timeout: 'int | None' = None, cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "ScheduleInform": "(self, CommandKey: 'str' = 'Test', DelaySeconds: 'int' = 20, cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "GetRPCMethods": "(self, cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",
    "Download": "(self, url: 'str', filetype: 'str' = '1 Firmware Upgrade Image', targetfilename: 'str' = '', filesize: 'int' = 200, username: 'str' = '', password: 'str' = '', commandkey: 'str' = '', delayseconds: 'int' = 10, successurl: 'str' = '', failureurl: 'str' = '', cpe_id: 'str | None' = None) -> 'list[dict[str, Any]]'",  # noqa: E501
    "provision_cpe_via_tr069": "(self, tr069provision_api_list: 'list[dict[str, list[dict[str, str]]]]', cpe_id: 'str') -> 'None'",  # noqa: E501
    "list_cpes": "(self, criteria: 'dict[str, str] | None' = None) -> 'list[str]'",
    "delete_cpe_record": "(self, cpe_id: 'str') -> 'bool'",
    "get_cpe_connection_status": "(self, cpe_id: 'str') -> 'CpeConnectionStatus'",
}


def test_released_signatures_are_kept() -> None:
    # A released implementer (boardfarm's ACS template) declares dict[str, str | int | bool];
    # dict is invariant, so the released annotations stay exactly as they were.
    for name, released in _RELEASED_SIGNATURES.items():
        assert str(inspect.signature(getattr(Tr069Server, name))) == released, name


def test_every_any_line_is_marked_released_signature_kept() -> None:
    source = Path(tr069_server_module.__file__).read_text()
    lines = source.splitlines()
    any_lines = {
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Name) and node.id == "Any"
    }
    assert len(any_lines) == 14  # the released annotations
    for lineno in any_lines:
        assert lines[lineno - 1].endswith("# released signature kept"), lines[lineno - 1]


def test_a_migrated_drivers_old_name_warns() -> None:
    with pytest.warns(DeprecationWarning, match="GPV is deprecated; use get_parameter_values"):
        out = _TypedAcs().GPV("Device.DeviceInfo.SerialNumber")
    assert out == [{"key": "Device.DeviceInfo.SerialNumber", "value": "SN42", "type": "xsd:string"}]


def test_an_old_driver_calls_without_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _OldAcs().GPV(["a.b"])[0]["key"] == "a.b"
