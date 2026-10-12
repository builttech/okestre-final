"""Shared, bounded wire contract. Never send absolute local paths."""
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VERSION = 1
MAX_FILE = 1024 * 1024
MAX_MESSAGE = 8 * MAX_FILE
READS = {"list_files", "read_file", "search_files", "list_requirements", "read_requirement", "list_tasks", "git_status", "git_diff"}
WRITES = {"write_file", "patch_file", "create_task", "update_task", "execute_command", "stop_command"}
OPERATIONS = READS | WRITES


class BridgeError(ValueError):
    """Only fixed error codes may cross the bridge or reach logs."""


class RootInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    name: str = Field(min_length=1, max_length=100)
    writable: bool = False


class Call(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal[1] = VERSION
    type: Literal["call"] = "call"
    request_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    root_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    operation: str = Field(max_length=50)
    arguments: dict
    can_write: bool = False
    # Accepted for compatibility with older servers, but never used to expire work.
    deadline: float | None = None


def encode(message):
    raw = json.dumps(message, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if len(raw.encode("utf-8")) > MAX_MESSAGE:
        raise BridgeError("message_too_large")
    return raw


def decode(raw):
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_MESSAGE:
        raise BridgeError("invalid_message")
    value = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(BridgeError("invalid_message")))
    if not isinstance(value, dict):
        raise BridgeError("invalid_message")
    return value
