"""Server side: the Resource operations extension, registered through the SDK's `Extension`/`MethodBinding` API.

    store = InMemoryStore()
    bus = InMemorySubscriptionBus()
    server = MCPServer("notes", subscriptions=bus, extensions=[ResourceOperations(store, subscriptions=bus)])

Pass the same `SubscriptionBus` to `MCPServer` and to the extension so writes reach `subscriptions/listen`
streams. Extension handlers receive no handle on the server's bus; see "SDK extension points" in the proposal.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

from mcp.server.context import HandlerResult, ServerRequestContext
from mcp.server.extension import Extension, MethodBinding
from mcp.server.subscriptions import ResourcesListChanged, ResourceUpdated, SubscriptionBus
from mcp_types.version import MODERN_PROTOCOL_VERSIONS

from mcp_ext_filesystems.errors import InvalidResourceUri
from mcp_ext_filesystems.store import ResourceStore
from mcp_ext_filesystems.wire import (
    EXTENSION_ID,
    METHOD_CREATE,
    METHOD_DELETE,
    METHOD_READ_DIRECTORY,
    METHOD_STAT,
    METHOD_UPDATE,
    CreateParams,
    CreateResult,
    DeleteParams,
    DeleteResult,
    ReadDirectoryParams,
    ReadDirectoryResult,
    ResourceChange,
    StatParams,
    StatResult,
    UpdateParams,
    UpdateResult,
)

# `capabilities.extensions` only exists on the 2026-07-28 wire, so the methods are served there only.
_VERSIONS = frozenset(MODERN_PROTOCOL_VERSIONS)


class ResourceOperations(Extension):
    """Serve `resources/stat`, `create`, `update`, `delete`, and optionally `resources/directory/read`.

    `directory_read=True` binds SEP-2640's `resources/directory/read` and advertises `directoryRead`. Leave it
    off on a server that also runs the Skills extension with directory reads: the SDK lets one extension bind a
    method, and binding it twice fails at construction.
    """

    identifier = EXTENSION_ID

    def __init__(
        self,
        store: ResourceStore,
        *,
        subscriptions: SubscriptionBus | None = None,
        directory_read: bool = False,
    ) -> None:
        self._store = store
        self._bus = subscriptions
        self._directory_read = directory_read

    def settings(self) -> dict[str, Any]:
        return {"directoryRead": True} if self._directory_read else {}

    def methods(self) -> Sequence[MethodBinding]:
        bindings = [
            MethodBinding(METHOD_STAT, StatParams, self._stat, _VERSIONS),
            MethodBinding(METHOD_CREATE, CreateParams, self._create, _VERSIONS),
            MethodBinding(METHOD_UPDATE, UpdateParams, self._update, _VERSIONS),
            MethodBinding(METHOD_DELETE, DeleteParams, self._delete, _VERSIONS),
        ]
        if self._directory_read:
            bindings.append(MethodBinding(METHOD_READ_DIRECTORY, ReadDirectoryParams, self._read_directory, _VERSIONS))
        return bindings

    async def _stat(self, ctx: ServerRequestContext[Any, Any], params: StatParams) -> HandlerResult:
        _check_uri(params.uri)
        stat = await self._store.stat(params.uri)
        return StatResult(resource=stat.resource, revision=stat.revision)

    async def _create(self, ctx: ServerRequestContext[Any, Any], params: CreateParams) -> HandlerResult:
        _check_uri(params.uri)
        stat = await self._store.create(params.uri, params.contents)
        await self._publish(ResourcesListChanged())
        change = ResourceChange(uri=params.uri, effect="created", revision=stat.revision)
        return CreateResult(resource=stat.resource, revision=stat.revision, changes=[change])

    async def _update(self, ctx: ServerRequestContext[Any, Any], params: UpdateParams) -> HandlerResult:
        _check_uri(params.uri)
        previous, stat = await self._store.update(params.uri, params.contents, params.if_match)
        await self._publish(ResourceUpdated(uri=params.uri))
        change = ResourceChange(uri=params.uri, effect="updated", previous_revision=previous, revision=stat.revision)
        return UpdateResult(resource=stat.resource, revision=stat.revision, changes=[change])

    async def _delete(self, ctx: ServerRequestContext[Any, Any], params: DeleteParams) -> HandlerResult:
        _check_uri(params.uri)
        previous = await self._store.delete(params.uri, params.if_match)
        await self._publish(ResourceUpdated(uri=params.uri))
        await self._publish(ResourcesListChanged())
        return DeleteResult(changes=[ResourceChange(uri=params.uri, effect="deleted", previous_revision=previous)])

    async def _read_directory(self, ctx: ServerRequestContext[Any, Any], params: ReadDirectoryParams) -> HandlerResult:
        _check_uri(params.uri)
        resources, next_cursor = await self._store.read_directory(params.uri, params.cursor)
        return ReadDirectoryResult(resources=resources, next_cursor=next_cursor)

    async def _publish(self, event: ResourceUpdated | ResourcesListChanged) -> None:
        if self._bus is not None:
            await self._bus.publish(event)


# RFC 3986 absolute URI: scheme ":" hier-part, so `urn:` and other URIs without an authority are accepted.
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _check_uri(uri: str) -> None:
    parts = urlsplit(uri)
    if not _SCHEME.match(uri):
        raise InvalidResourceUri(uri, "not an absolute URI")
    if parts.fragment or uri.endswith("/"):
        raise InvalidResourceUri(uri, "fragments and trailing slashes are not allowed")
    if any(segment in (".", "..") for segment in parts.path.split("/")):
        raise InvalidResourceUri(uri, "dot segments are not allowed")
