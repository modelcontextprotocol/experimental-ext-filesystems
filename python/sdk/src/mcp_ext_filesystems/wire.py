"""Wire types for the Resource operations strawman (docs/proposals/resource-operations.md)."""

from __future__ import annotations

from typing import Any, Literal

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
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

EXTENSION_ID = "io.modelcontextprotocol/resource-operations"
"""Provisional identifier, advertised under `capabilities.extensions` (SEP-2133)."""

REVISION_META_KEY = "io.modelcontextprotocol/resource-revision"
"""`_meta` key that carries a revision on core shapes this extension may not retype (read contents, list entries)."""

DIRECTORY_MIME_TYPE = "inode/directory"
"""Marks a directory resource, as in SEP-2640."""

METHOD_STAT = "resources/stat"
METHOD_WRITE = "resources/write"
METHOD_DELETE = "resources/delete"
METHOD_READ_DIRECTORY = "resources/directory/read"
"""Defined by SEP-2640 (Skills). Served here unchanged; see the proposal's Listing section."""

ResourceContents = TextResourceContents | BlobResourceContents
Effect = Literal["created", "updated", "deleted"]


class _WireModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TextContents(_WireModel):
    """Write payload: core `TextResourceContents` without `uri`. The method's `uri` names the target."""

    mime_type: str | None = None
    text: str
    meta: dict[str, Any] | None = Field(alias="_meta", default=None)


class BlobContents(_WireModel):
    """Write payload: core `BlobResourceContents` without `uri`. The method's `uri` names the target."""

    mime_type: str | None = None
    blob: str
    meta: dict[str, Any] | None = Field(alias="_meta", default=None)


WriteContents = TextContents | BlobContents


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


class WriteParams(RequestParams):
    """Exactly one precondition, as with HTTP PUT: `ifMatch` updates that revision, `ifNoneMatch: "*"` creates."""

    uri: str
    contents: WriteContents
    if_match: str | None = None
    if_none_match: Literal["*"] | None = None

    @model_validator(mode="after")
    def _exactly_one_precondition(self) -> WriteParams:
        if (self.if_match is None) == (self.if_none_match is None):
            raise ValueError('exactly one of ifMatch or ifNoneMatch: "*" is required')
        return self


class WriteResult(Result):
    resource: Resource
    revision: str
    changes: list[ResourceChange]


class DeleteParams(RequestParams):
    uri: str
    if_match: str


class DeleteResult(Result):
    changes: list[ResourceChange]


class ReadDirectoryParams(PaginatedRequestParams):
    uri: str


class ReadDirectoryResult(PaginatedResult):
    resources: list[Resource]


class StatRequest(Request[StatParams, Literal["resources/stat"]]):
    method: Literal["resources/stat"] = "resources/stat"
    params: StatParams


class WriteRequest(Request[WriteParams, Literal["resources/write"]]):
    method: Literal["resources/write"] = "resources/write"
    params: WriteParams


class DeleteRequest(Request[DeleteParams, Literal["resources/delete"]]):
    method: Literal["resources/delete"] = "resources/delete"
    params: DeleteParams


class ReadDirectoryRequest(Request[ReadDirectoryParams, Literal["resources/directory/read"]]):
    method: Literal["resources/directory/read"] = "resources/directory/read"
    params: ReadDirectoryParams
