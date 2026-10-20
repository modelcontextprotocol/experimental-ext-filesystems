"""Python reference implementation of the experimental MCP Resource operations extension."""

from importlib.metadata import version

from mcp_ext_filesystems.client import ResourceOperationsClient
from mcp_ext_filesystems.errors import (
    NOT_SUPPORTED,
    PRECONDITION_FAILED,
    AlreadyExists,
    InvalidResourceUri,
    OperationNotSupported,
    ResourceNotFound,
    ResourceOperationError,
    RevisionMismatch,
)
from mcp_ext_filesystems.server import ResourceOperations
from mcp_ext_filesystems.store import InMemoryStore, ResourceStore, Stat
from mcp_ext_filesystems.wire import EXTENSION_ID, REVISION_META_KEY, ResourceChange

__version__ = version("mcp-ext-filesystems")
