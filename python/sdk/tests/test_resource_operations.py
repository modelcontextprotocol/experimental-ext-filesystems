"""End-to-end tests over the SDK's in-process transport (`Client(server)`)."""

from __future__ import annotations

from typing import Literal

import anyio
import pytest
from mcp.client.client import Client
from mcp.server.mcpserver import MCPServer
from mcp.server.subscriptions import InMemorySubscriptionBus
from mcp.shared.exceptions import MCPError
from mcp.shared.subscriptions import ResourceUpdated
from mcp_types import INVALID_PARAMS, METHOD_NOT_FOUND, Request, RequestParams

from mcp_ext_filesystems import (
    EXTENSION_ID,
    NOT_SUPPORTED,
    PRECONDITION_FAILED,
    REVISION_META_KEY,
    AlreadyExists,
    InMemoryStore,
    InvalidResourceUri,
    OperationNotSupported,
    ResourceNotFound,
    ResourceOperations,
    ResourceOperationsClient,
    RevisionMismatch,
    TextContents,
)
from mcp_ext_filesystems.wire import (
    DIRECTORY_MIME_TYPE,
    DeleteResult,
    ReadDirectoryParams,
    ReadDirectoryRequest,
    ReadDirectoryResult,
    StatParams,
    StatRequest,
    StatResult,
)

pytestmark = pytest.mark.anyio

URI = "mem://notes/plan.md"


def text(body: str) -> TextContents:
    return TextContents(text=body, mime_type="text/markdown")


def make_server(*, directory_read: bool = False, store: InMemoryStore | None = None) -> MCPServer:
    bus = InMemorySubscriptionBus()
    extension = ResourceOperations(store or InMemoryStore(), subscriptions=bus, directory_read=directory_read)
    return MCPServer("notes", subscriptions=bus, extensions=[extension])


async def test_server_advertises_the_extension() -> None:
    async with Client(make_server()) as client:
        assert client.session.server_capabilities.extensions == {EXTENSION_ID: {}}
    async with Client(make_server(directory_read=True)) as client:
        assert client.session.server_capabilities.extensions == {EXTENSION_ID: {"directoryRead": True}}


async def test_methods_are_not_served_on_the_legacy_wire() -> None:
    async with Client(make_server(), mode="legacy") as client:
        assert not ResourceOperationsClient(client.session).supported()
        with pytest.raises(MCPError) as caught:
            await client.session.send_request(StatRequest(params=StatParams(uri=URI)), StatResult)
    assert caught.value.code == METHOD_NOT_FOUND


async def test_create_stat_update_delete() -> None:
    async with Client(make_server()) as client:
        ops = ResourceOperationsClient(client.session)

        created = await ops.create(URI, text("v1"))
        assert created.resource.size == 2
        assert created.resource.annotations is not None and created.resource.annotations.last_modified
        assert [c.effect for c in created.changes] == ["created"]
        assert created.changes[0].revision == created.revision

        stat = await ops.stat(URI)
        assert stat.revision == created.revision
        assert stat.resource.mime_type == "text/markdown"

        updated = await ops.update(URI, text("revision two"), if_match=stat.revision)
        assert updated.revision != stat.revision
        assert updated.resource.size == len("revision two")
        change = updated.changes[0]
        assert (change.effect, change.previous_revision, change.revision) == (
            "updated",
            stat.revision,
            updated.revision,
        )

        deleted = await ops.delete(URI, if_match=updated.revision)
        assert deleted.changes[0].effect == "deleted"
        assert deleted.changes[0].previous_revision == updated.revision
        with pytest.raises(ResourceNotFound):
            await ops.stat(URI)


async def test_create_if_absent_conflict_returns_the_current_revision() -> None:
    async with Client(make_server()) as client:
        ops = ResourceOperationsClient(client.session)
        first = await ops.create(URI, text("mine"))
        with pytest.raises(AlreadyExists) as caught:
            await ops.create(URI, text("theirs"))
    assert caught.value.code == PRECONDITION_FAILED
    assert caught.value.data == {"uri": URI, "reason": "alreadyExists", "currentRevision": first.revision}


async def test_stale_if_match_is_rejected_with_the_current_revision() -> None:
    async with Client(make_server()) as client:
        ops = ResourceOperationsClient(client.session)
        v1 = (await ops.create(URI, text("one"))).revision
        v2 = (await ops.update(URI, text("two"), if_match=v1)).revision
        with pytest.raises(RevisionMismatch) as caught:
            await ops.update(URI, text("stale"), if_match=v1)
        assert (await ops.stat(URI)).revision == v2
    assert caught.value.code == PRECONDITION_FAILED
    assert caught.value.data == {"uri": URI, "reason": "revisionMismatch", "currentRevision": v2}


async def test_delete_with_stale_if_match_keeps_the_resource() -> None:
    async with Client(make_server()) as client:
        ops = ResourceOperationsClient(client.session)
        v1 = (await ops.create(URI, text("one"))).revision
        v2 = (await ops.update(URI, text("two"), if_match=v1)).revision
        with pytest.raises(RevisionMismatch) as caught:
            await ops.delete(URI, if_match=v1)
        assert caught.value.current_revision == v2
        assert (await ops.stat(URI)).revision == v2
        await ops.delete(URI, if_match=v2)
        with pytest.raises(ResourceNotFound):
            await ops.stat(URI)


async def test_not_found_uses_invalid_params_like_resources_read() -> None:
    async with Client(make_server()) as client:
        ops = ResourceOperationsClient(client.session)
        for call in (ops.stat(URI), ops.update(URI, text("x"), if_match="1"), ops.delete(URI, if_match="1")):
            with pytest.raises(ResourceNotFound) as caught:
                await call
            assert caught.value.code == -32602
            assert caught.value.data == {"uri": URI, "reason": "notFound"}


async def test_invalid_uri_and_unsupported_scheme() -> None:
    async with Client(make_server()) as client:
        ops = ResourceOperationsClient(client.session)
        with pytest.raises(InvalidResourceUri):
            await ops.stat("plan.md")
        for call in (
            ops.create("file:///etc/hosts", text("x")),
            ops.update("file:///etc/hosts", text("x"), if_match="1"),
            ops.delete("file:///etc/hosts", if_match="1"),
        ):
            with pytest.raises(OperationNotSupported) as caught:
                await call
            assert caught.value.code == NOT_SUPPORTED


async def test_absolute_uris_without_an_authority_are_valid() -> None:
    """RFC 3986 allows `scheme:path`; a foreign scheme is unsupported by this store, not malformed."""
    async with Client(make_server()) as client:
        with pytest.raises(OperationNotSupported):
            await ResourceOperationsClient(client.session).create("urn:example:plan", text("x"))


class _UriOnly(RequestParams):
    uri: str


class _UriAndContents(RequestParams):
    uri: str
    contents: TextContents


class _UpdateWithoutIfMatch(Request[_UriAndContents, Literal["resources/update"]]):
    method: Literal["resources/update"] = "resources/update"
    params: _UriAndContents


class _DeleteWithoutIfMatch(Request[_UriOnly, Literal["resources/delete"]]):
    method: Literal["resources/delete"] = "resources/delete"
    params: _UriOnly


async def test_update_and_delete_require_if_match() -> None:
    async with Client(make_server()) as client:
        await ResourceOperationsClient(client.session).create(URI, text("one"))
        requests = (
            _UpdateWithoutIfMatch(params=_UriAndContents(uri=URI, contents=text("two"))),
            _DeleteWithoutIfMatch(params=_UriOnly(uri=URI)),
        )
        for request in requests:
            with pytest.raises(MCPError) as caught:
                await client.session.send_request(request, DeleteResult)
            assert caught.value.code == INVALID_PARAMS
        assert (await ResourceOperationsClient(client.session).stat(URI)).resource.size == 3


async def test_update_and_delete_notify_resource_subscribers() -> None:
    server = make_server()
    async with Client(server) as watcher, Client(server) as writer:
        ops = ResourceOperationsClient(writer.session)
        revision = (await ops.create(URI, text("one"))).revision
        async with watcher.listen(resource_subscriptions=[URI]) as subscription:
            revision = (await ops.update(URI, text("two"), if_match=revision)).revision
            with anyio.fail_after(2):
                assert await subscription.__anext__() == ResourceUpdated(uri=URI)
            await ops.delete(URI, if_match=revision)
            with anyio.fail_after(2):
                assert await subscription.__anext__() == ResourceUpdated(uri=URI)


async def test_lost_update_is_rejected() -> None:
    """docs/use-cases.md, Memory servers: two sessions read the same revision and both write it back."""
    server = make_server()
    async with Client(server) as first, Client(server) as second:
        a, b = ResourceOperationsClient(first.session), ResourceOperationsClient(second.session)
        await a.create(URI, text("- fact 0\n"))

        seen_by_a = await a.stat(URI)
        seen_by_b = await b.stat(URI)
        assert seen_by_a.revision == seen_by_b.revision

        written = await a.update(URI, text("- fact 0\n- fact A\n"), if_match=seen_by_a.revision)
        with pytest.raises(RevisionMismatch) as caught:
            await b.update(URI, text("- fact 0\n- fact B\n"), if_match=seen_by_b.revision)
        assert caught.value.current_revision == written.revision

        # The rejected writer re-reads, merges, and retries against the revision it was told about.
        retried = await b.update(URI, text("- fact 0\n- fact A\n- fact B\n"), if_match=caught.value.current_revision)
        assert retried.changes[0].previous_revision == written.revision


async def test_directory_read_reuses_the_skills_method_shape() -> None:
    async with Client(make_server(directory_read=True)) as client:
        ops = ResourceOperationsClient(client.session)
        created = await ops.create(URI, text("plan"))
        await ops.create("mem://notes/archive/old.md", text("old"))

        children = {r.uri: r for r in await ops.read_directory("mem://notes")}
        assert set(children) == {URI, "mem://notes/archive"}
        assert children[URI].meta == {REVISION_META_KEY: created.revision}
        assert children["mem://notes/archive"].mime_type == DIRECTORY_MIME_TYPE
        assert (await ops.stat("mem://notes/archive")).resource.mime_type == DIRECTORY_MIME_TYPE

        with pytest.raises(InvalidResourceUri):
            await ops.read_directory(URI)


async def test_directory_read_pages_with_a_cursor() -> None:
    async with Client(make_server(directory_read=True, store=InMemoryStore(page_size=2))) as client:
        ops = ResourceOperationsClient(client.session)
        uris = [f"mem://notes/{name}.md" for name in "abc"]
        for uri in uris:
            await ops.create(uri, text(uri))

        request = ReadDirectoryRequest(params=ReadDirectoryParams(uri="mem://notes"))
        first = await client.session.send_request(request, ReadDirectoryResult)
        assert [r.uri for r in first.resources] == uris[:2]
        assert first.next_cursor is not None
        request = ReadDirectoryRequest(params=ReadDirectoryParams(uri="mem://notes", cursor=first.next_cursor))
        second = await client.session.send_request(request, ReadDirectoryResult)
        assert [r.uri for r in second.resources] == uris[2:]
        assert second.next_cursor is None

        assert [r.uri for r in await ops.read_directory("mem://notes")] == uris
