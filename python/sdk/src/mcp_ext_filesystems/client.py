"""Client side: typed helpers over a connected `ClientSession`.

    async with Client(server) as client:
        ops = ResourceOperationsClient(client.session)
        stat = await ops.stat("mem://notes/plan.md")
        await ops.update("mem://notes/plan.md", TextResourceContents(uri=..., text="..."), if_match=stat.revision)

Wire errors come back as the typed exceptions in `mcp_ext_filesystems.errors`.
"""

from __future__ import annotations

from typing import Any, TypeVar

from mcp.client.session import ClientSession
from mcp.shared.exceptions import MCPError
from mcp_types import Request, Resource, Result

from mcp_ext_filesystems.errors import from_mcp_error
from mcp_ext_filesystems.wire import (
    EXTENSION_ID,
    CreateParams,
    CreateRequest,
    CreateResult,
    DeleteParams,
    DeleteRequest,
    DeleteResult,
    ReadDirectoryParams,
    ReadDirectoryRequest,
    ReadDirectoryResult,
    ResourceContents,
    StatParams,
    StatRequest,
    StatResult,
    UpdateParams,
    UpdateRequest,
    UpdateResult,
)

ResultT = TypeVar("ResultT", bound=Result)


class ResourceOperationsClient:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    def supported(self) -> bool:
        """Whether the server advertised the extension."""
        return self._settings() is not None

    async def stat(self, uri: str) -> StatResult:
        return await self._send(StatRequest(params=StatParams(uri=uri)), StatResult)

    async def create(self, uri: str, contents: ResourceContents) -> CreateResult:
        return await self._send(CreateRequest(params=CreateParams(uri=uri, contents=contents)), CreateResult)

    async def update(self, uri: str, contents: ResourceContents, *, if_match: str) -> UpdateResult:
        params = UpdateParams(uri=uri, contents=contents, if_match=if_match)
        return await self._send(UpdateRequest(params=params), UpdateResult)

    async def delete(self, uri: str, *, if_match: str | None = None) -> DeleteResult:
        return await self._send(DeleteRequest(params=DeleteParams(uri=uri, if_match=if_match)), DeleteResult)

    async def read_directory(self, uri: str) -> list[Resource]:
        """Call `resources/directory/read`, following `nextCursor` to the end."""
        if not (self._settings() or {}).get("directoryRead"):
            raise RuntimeError(f"server does not advertise {EXTENSION_ID!r} with directoryRead")
        resources: list[Resource] = []
        cursor: str | None = None
        while True:
            request = ReadDirectoryRequest(params=ReadDirectoryParams(uri=uri, cursor=cursor))
            page = await self._send(request, ReadDirectoryResult)
            resources.extend(page.resources)
            if page.next_cursor is None:
                return resources
            cursor = page.next_cursor

    def _settings(self) -> dict[str, object] | None:
        capabilities = self._session.server_capabilities
        extensions = capabilities.extensions if capabilities else None
        return (extensions or {}).get(EXTENSION_ID)

    async def _send(self, request: Request[Any, Any], result_type: type[ResultT]) -> ResultT:
        if not self.supported():
            raise RuntimeError(f"server does not advertise {EXTENSION_ID!r}")
        try:
            return await self._session.send_request(request, result_type)
        except MCPError as error:
            raise from_mcp_error(error) from None
