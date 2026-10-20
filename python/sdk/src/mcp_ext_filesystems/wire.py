"""Wire types for the Resource operations strawman (docs/proposals/resource-operations.md)."""

from __future__ import annotations

from typing import Literal

from mcp_types import (
    BlobResourceContents,
    CacheableResult,
    PaginatedRequestParams,
    PaginatedResult,
    Request,
    RequestParams,
    Resource,
    Result,
    TextResourceContents,
)
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

EXTENSION_ID = "io.modelcontextprotocol/resource-operations"
"""Provisional identifier, advertised under `capabilities.extensions` (SEP-2133)."""

REVISION_META_KEY = "io.modelcontextprotocol/resource-revision"
"""`_meta` key that carries a revision on core shapes this extension may not retype (read contents, list entries)."""

DIRECTORY_MIME_TYPE = "inode/directory"
"""Marks a directory resource, as in SEP-2640."""

METHOD_STAT = "resources/stat"
METHOD_CREATE = "resources/create"
METHOD_UPDATE = "resources/update"
METHOD_DELETE = "resources/delete"
METHOD_READ_DIRECTORY = "resources/directory/read"
"""Defined by SEP-2640 (Skills). Served here unchanged; see the proposal's Listing section."""

ResourceContents = TextResourceContents | BlobResourceContents
Effect = Literal["created", "updated", "deleted"]


class _WireModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ResourceChange(_WireModel):
    """One entry of a change set, in the vocabulary of Kryspin Ziemski's working document."""

    uri: str
    effect: Effect
    previous_revision: str | None = None
    revision: str | None = None


class StatParams(RequestParams):
    uri: str


class StatResult(CacheableResult):
    resource: Resource
    revision: str


class CreateParams(RequestParams):
    uri: str
    contents: ResourceContents


class CreateResult(Result):
    resource: Resource
    revision: str
    changes: list[ResourceChange]


class UpdateParams(RequestParams):
    uri: str
    contents: ResourceContents
    if_match: str


class UpdateResult(Result):
    resource: Resource
    revision: str
    changes: list[ResourceChange]


class DeleteParams(RequestParams):
    uri: str
    if_match: str | None = None


class DeleteResult(Result):
    changes: list[ResourceChange]


class ReadDirectoryParams(PaginatedRequestParams):
    uri: str


class ReadDirectoryResult(PaginatedResult):
    resources: list[Resource]


class StatRequest(Request[StatParams, Literal["resources/stat"]]):
    method: Literal["resources/stat"] = "resources/stat"
    params: StatParams


class CreateRequest(Request[CreateParams, Literal["resources/create"]]):
    method: Literal["resources/create"] = "resources/create"
    params: CreateParams


class UpdateRequest(Request[UpdateParams, Literal["resources/update"]]):
    method: Literal["resources/update"] = "resources/update"
    params: UpdateParams


class DeleteRequest(Request[DeleteParams, Literal["resources/delete"]]):
    method: Literal["resources/delete"] = "resources/delete"
    params: DeleteParams


class ReadDirectoryRequest(Request[ReadDirectoryParams, Literal["resources/directory/read"]]):
    method: Literal["resources/directory/read"] = "resources/directory/read"
    params: ReadDirectoryParams
