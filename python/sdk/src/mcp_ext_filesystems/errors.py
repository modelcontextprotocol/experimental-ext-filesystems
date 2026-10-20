"""Typed errors for Resource operations.

Not found and invalid URI reuse `-32602` (Invalid params), the code core `resources/read` and SEP-2640's
`resources/directory/read` use for unknown resources. Precondition failures and unsupported operations need
codes of their own; the values below are provisional placeholders in the implementation-defined band
(-32000..-32019), pending allocation. Every error carries `data.uri` and `data.reason`.
"""

from __future__ import annotations

from typing import Any

from mcp.shared.exceptions import MCPError
from mcp_types import INVALID_PARAMS

PRECONDITION_FAILED = -32010
"""Provisional: `ifMatch` did not match, or `resources/create` found the URI taken. `data.currentRevision` is set."""

NOT_SUPPORTED = -32011
"""Provisional: the server does not support this operation on this URI."""


class ResourceOperationError(MCPError):
    """Base class. `reason` is the machine-readable discriminator sent as `data.reason`."""

    code_value: int = INVALID_PARAMS
    reason: str = ""

    def __init__(self, uri: str, message: str, *, current_revision: str | None = None) -> None:
        data: dict[str, Any] = {"uri": uri, "reason": self.reason}
        if current_revision is not None:
            data["currentRevision"] = current_revision
        super().__init__(code=self.code_value, message=message, data=data)
        self.uri = uri
        self.current_revision = current_revision


class ResourceNotFound(ResourceOperationError):
    reason = "notFound"

    def __init__(self, uri: str) -> None:
        super().__init__(uri, f"Resource not found: {uri}")


class InvalidResourceUri(ResourceOperationError):
    reason = "invalidUri"

    def __init__(self, uri: str, detail: str = "not a valid resource URI") -> None:
        super().__init__(uri, f"Invalid resource URI {uri!r}: {detail}")


class RevisionMismatch(ResourceOperationError):
    code_value = PRECONDITION_FAILED
    reason = "revisionMismatch"

    def __init__(self, uri: str, current_revision: str) -> None:
        super().__init__(
            uri, f"ifMatch does not match the current revision of {uri}", current_revision=current_revision
        )


class AlreadyExists(ResourceOperationError):
    code_value = PRECONDITION_FAILED
    reason = "alreadyExists"

    def __init__(self, uri: str, current_revision: str) -> None:
        super().__init__(uri, f"Resource already exists: {uri}", current_revision=current_revision)


class OperationNotSupported(ResourceOperationError):
    code_value = NOT_SUPPORTED
    reason = "notSupported"

    def __init__(self, uri: str, detail: str = "operation not supported for this URI") -> None:
        super().__init__(uri, f"{detail}: {uri}")


def from_mcp_error(error: MCPError) -> MCPError:
    """Map a wire error back to its typed exception; return `error` unchanged if it is not one of ours."""
    data = error.data if isinstance(error.data, dict) else {}
    uri, reason, current = data.get("uri"), data.get("reason"), data.get("currentRevision")
    if not isinstance(uri, str):
        return error
    if error.code == INVALID_PARAMS and reason == "notFound":
        return ResourceNotFound(uri)
    if error.code == INVALID_PARAMS and reason == "invalidUri":
        return InvalidResourceUri(uri)
    if error.code == PRECONDITION_FAILED and isinstance(current, str):
        if reason == "revisionMismatch":
            return RevisionMismatch(uri, current)
        if reason == "alreadyExists":
            return AlreadyExists(uri, current)
    if error.code == NOT_SUPPORTED:
        return OperationNotSupported(uri)
    return error
