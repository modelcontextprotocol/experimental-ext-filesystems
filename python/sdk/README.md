# MCP Filesystems Python SDK

Python reference implementation of the experimental MCP Resource operations extension, built on the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) v2. It is meant to plug in through the SDK's extension mechanism (the `Extension` and `MethodBinding` API used by the Apps extension), following [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371), rather than by patching the SDK.

**Status:** Prototype of the [Resource operations strawman](../../docs/proposals/resource-operations.md). Expect every name and code to change.

It serves `resources/stat`, `resources/create`, `resources/update`, `resources/delete`, and optionally SEP-2640's `resources/directory/read`, on the 2026-07-28 protocol version, through `Extension`/`MethodBinding` only.

## Usage

Server: back the extension with a `ResourceStore` (an in-memory one is included). Pass the same `SubscriptionBus` to the server and the extension so writes reach `subscriptions/listen` subscribers.

```python
from mcp.server.mcpserver import MCPServer
from mcp.server.subscriptions import InMemorySubscriptionBus

from mcp_ext_filesystems import InMemoryStore, ResourceOperations

bus = InMemorySubscriptionBus()
server = MCPServer(
    "notes",
    subscriptions=bus,
    extensions=[ResourceOperations(InMemoryStore(), subscriptions=bus, directory_read=True)],
)
```

Client: wrap a connected session. Errors arrive as typed exceptions.

```python
from mcp import Client
from mcp_types import TextResourceContents

from mcp_ext_filesystems import ResourceOperationsClient, RevisionMismatch

uri = "mem://notes/plan.md"
async with Client(server) as client:
    ops = ResourceOperationsClient(client.session)
    created = await ops.create(uri, TextResourceContents(uri=uri, text="# Plan\n"))
    try:
        await ops.update(uri, TextResourceContents(uri=uri, text="# Plan\n- ship\n"), if_match=created.revision)
    except RevisionMismatch as conflict:
        ...  # someone else wrote first: re-read, merge, retry with conflict.current_revision
```

Store-backed resources are not readable through `resources/read` unless the server registers a resource template for them; see "SDK extension points" in the proposal.

## Development

```bash
uv venv && uv pip install -e . pytest ruff mypy
ruff format --check . && ruff check .
mypy src/mcp_ext_filesystems
pytest
```

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
