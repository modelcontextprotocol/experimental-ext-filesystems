"""Pluggable storage behind the extension, plus an in-memory implementation for tests and demos."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from typing import Protocol

from mcp_types import Annotations, BlobResourceContents, Resource

from mcp_ext_filesystems.errors import (
    AlreadyExists,
    InvalidResourceUri,
    OperationNotSupported,
    ResourceNotFound,
    RevisionMismatch,
)
from mcp_ext_filesystems.wire import DIRECTORY_MIME_TYPE, REVISION_META_KEY, ResourceContents


@dataclass(frozen=True)
class Stat:
    """A resource's metadata and its current revision."""

    resource: Resource
    revision: str


class ResourceStore(Protocol):
    """Backend for the extension.

    Each write MUST compare the revision and apply the change atomically: the extension does not hold a lock
    between a check and a write, so a store that checks then writes in two steps reintroduces lost updates.
    Methods raise the typed errors in `mcp_ext_filesystems.errors`.
    """

    async def stat(self, uri: str) -> Stat:
        """Raise `ResourceNotFound` if `uri` does not exist."""
        ...

    async def create(self, uri: str, contents: ResourceContents) -> Stat:
        """Create `uri` only if it does not exist; raise `AlreadyExists` with the current revision otherwise."""
        ...

    async def update(self, uri: str, contents: ResourceContents, if_match: str) -> tuple[str, Stat]:
        """Replace `uri` only if its revision equals `if_match`. Return the previous revision and the new stat."""
        ...

    async def delete(self, uri: str, if_match: str | None) -> str:
        """Delete `uri`, conditionally if `if_match` is set. Return the deleted revision."""
        ...

    async def read_directory(self, uri: str) -> list[Resource]:
        """Return the direct children of directory `uri`."""
        ...


@dataclass(frozen=True)
class _Entry:
    contents: ResourceContents
    revision: str
    last_modified: str


class InMemoryStore:
    """A flat map from URI to contents. Directories are implicit: a URI is a directory if it has descendants.

    Revisions come from one counter shared by every URI, so a deleted and re-created resource never repeats a
    revision. Writes contain no `await`, which makes each compare-and-write atomic on a single event loop.
    """

    def __init__(self, scheme: str = "mem") -> None:
        self._scheme = scheme
        self._entries: dict[str, _Entry] = {}
        self._revisions = count(1)

    async def stat(self, uri: str) -> Stat:
        return self._stat(uri)

    def _stat(self, uri: str) -> Stat:
        entry = self._entries.get(uri)
        if entry is not None:
            return Stat(_describe(uri, entry), entry.revision)
        children = self._children(uri)
        if not children:
            raise ResourceNotFound(uri)
        # A directory's revision changes whenever the set of its direct children or any child's revision changes.
        digest = hashlib.sha256(repr(sorted((c.uri, (c.meta or {}).get(REVISION_META_KEY)) for c in children)).encode())
        return Stat(_directory(uri), "d-" + digest.hexdigest()[:16])

    async def create(self, uri: str, contents: ResourceContents) -> Stat:
        self._check_writable(uri)
        if uri in self._entries or self._children(uri):
            raise AlreadyExists(uri, self._stat(uri).revision)
        entry = self._write(uri, contents)
        return Stat(_describe(uri, entry), entry.revision)

    async def update(self, uri: str, contents: ResourceContents, if_match: str) -> tuple[str, Stat]:
        current = self._file(uri)
        if current.revision != if_match:
            raise RevisionMismatch(uri, current.revision)
        entry = self._write(uri, contents)
        return current.revision, Stat(_describe(uri, entry), entry.revision)

    async def delete(self, uri: str, if_match: str | None) -> str:
        current = self._file(uri)
        if if_match is not None and current.revision != if_match:
            raise RevisionMismatch(uri, current.revision)
        del self._entries[uri]
        return current.revision

    async def read_directory(self, uri: str) -> list[Resource]:
        if uri in self._entries:
            raise InvalidResourceUri(uri, "not a directory resource")
        children = self._children(uri)
        if not children:
            raise ResourceNotFound(uri)
        return children

    def _file(self, uri: str) -> _Entry:
        entry = self._entries.get(uri)
        if entry is None:
            if self._children(uri):
                raise OperationNotSupported(uri, "directories cannot be updated or deleted")
            raise ResourceNotFound(uri)
        return entry

    def _check_writable(self, uri: str) -> None:
        root = f"{self._scheme}://"
        if not uri.startswith(root):
            raise OperationNotSupported(uri, f"this store only holds {root} resources")
        segments = uri.removeprefix(root).split("/")
        if any(root + "/".join(segments[:i]) in self._entries for i in range(1, len(segments))):
            raise OperationNotSupported(uri, "an ancestor is a file, not a directory")

    def _write(self, uri: str, contents: ResourceContents) -> _Entry:
        stamp = datetime.now(timezone.utc).isoformat()
        entry = _Entry(contents.model_copy(update={"uri": uri}), str(next(self._revisions)), stamp)
        self._entries[uri] = entry
        return entry

    def _children(self, uri: str) -> list[Resource]:
        prefix = uri + "/"
        files: dict[str, Resource] = {}
        directories: set[str] = set()
        for key, entry in self._entries.items():
            if not key.startswith(prefix):
                continue
            head, _, rest = key[len(prefix) :].partition("/")
            if rest:
                directories.add(prefix + head)
            else:
                files[key] = _describe(key, entry)
        return [*files.values(), *(_directory(d) for d in sorted(directories))]


def _describe(uri: str, entry: _Entry) -> Resource:
    contents = entry.contents
    if isinstance(contents, BlobResourceContents):
        size = len(base64.b64decode(contents.blob))
    else:
        size = len(contents.text.encode())
    return Resource(
        uri=uri,
        name=uri.rsplit("/", 1)[-1],
        mime_type=contents.mime_type,
        size=size,
        annotations=Annotations(last_modified=entry.last_modified),
        _meta={REVISION_META_KEY: entry.revision},
    )


def _directory(uri: str) -> Resource:
    return Resource(uri=uri, name=uri.rsplit("/", 1)[-1], mime_type=DIRECTORY_MIME_TYPE)
