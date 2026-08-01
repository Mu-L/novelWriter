"""
novelWriter - TOML Config Parser
================================

This file is a part of novelWriter
Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""  # noqa

from __future__ import annotations

import logging
import tomllib

from enum import Enum
from pathlib import Path
from typing import TypeVar

from PyQt6.QtGui import QFont

from novelwriter.common import checkBool, checkFloat, checkInt, checkPath, checkString

logger = logging.getLogger(__name__)

_T_Enum = TypeVar("_T_Enum", bound=Enum)

T_ConfValue = str | int | float | bool | Path | list[str] | list[int] | Enum | QFont
T_ConfEntry = dict[str, T_ConfValue]
T_ConfData = dict[str, T_ConfEntry]


class NTomlParser:
    """Core: Toml Config Parser.

    This is a wrapper around the standard tomllib module, and assumes a
    two level section and key/value structure. It has type safe getters
    for all the supported types.
    """

    def __init__(self) -> None:
        self._data: T_ConfData = {}

    def read(self, path: Path) -> None:
        """Read and parse TOML data from a file."""
        with open(path, mode="r", encoding="utf-8") as fileObj:
            data = tomllib.loads(fileObj.read())

        self._data = {}
        for section, values in data.items():
            if not isinstance(values, dict):
                logger.error("Invalid config section '%s', expected key/value pairs", section)
                continue
            self._data[section] = values

    def write(self, path: Path, data: T_ConfData) -> None:
        """Write a dict of sections to a file in TOML format."""
        with open(path, mode="w", encoding="utf-8") as fileObj:
            for section, values in data.items():
                if not isinstance(values, dict):
                    logger.error("Invalid config section '%s', expected key/value pairs", section)
                    continue
                fileObj.write(f"[{section}]\n")
                for key, value in values.items():
                    fileObj.write(f"{key} = {self._dump(value)}\n")
                fileObj.write("\n")

    def getStr(self, section: str, option: str, default: str) -> str:
        """Read string value."""
        return checkString(self._value(section, option), default)

    def getInt(self, section: str, option: str, default: int) -> int:
        """Read integer value."""
        return checkInt(self._value(section, option), default)

    def getFloat(self, section: str, option: str, default: float) -> float:
        """Read float value."""
        return checkFloat(self._value(section, option), default)

    def getBool(self, section: str, option: str, default: bool) -> bool:
        """Read boolean value."""
        return checkBool(self._value(section, option), default)

    def getPath(self, section: str, option: str, default: Path) -> Path:
        """Read a Path value."""
        return checkPath(self._value(section, option), default)

    def getStrList(self, section: str, option: str, default: list[str]) -> list[str]:
        """Read string list, keeping the length of the default."""
        result = default.copy() if isinstance(default, list) else []
        data = self._value(section, option)
        if isinstance(data, list):
            for i in range(min(len(data), len(result))):
                result[i] = str(data[i])
        return result

    def getIntList(self, section: str, option: str, default: list[int]) -> list[int]:
        """Read integer list, keeping the length of the default."""
        result = default.copy() if isinstance(default, list) else []
        data = self._value(section, option)
        if isinstance(data, list):
            for i in range(min(len(data), len(result))):
                result[i] = checkInt(data[i], result[i])
        return result

    def getEnum(self, section: str, option: str, default: _T_Enum) -> _T_Enum:
        """Read enum value."""
        data = self._value(section, option)
        if isinstance(data, str):
            return type(default).__members__.get(data.upper(), default)
        return default

    ##
    # Internal Functions
    ##

    def _value(self, section: str, option: str) -> T_ConfValue | None:
        """Look up a raw value, or None if the section or option is unset."""
        return self._data.get(section, {}).get(option)

    @staticmethod
    def _dump(value: T_ConfValue) -> str:
        """Format a value as a TOML literal."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return "[" + ", ".join(NTomlParser._dump(v) for v in value) + "]"
        elif isinstance(value, Enum):
            return f'"{value.name}"'
        elif isinstance(value, QFont):
            return f'"{value.toString()}"'
        return NTomlParser._dumpStr(str(value))

    @staticmethod
    def _dumpStr(value: str) -> str:
        """Format a string as a quoted TOML basic string."""
        escaped = (
            value
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\t", "\\t")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )
        return f'"{escaped}"'
