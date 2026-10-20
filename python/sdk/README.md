# MCP Filesystems Python SDK

Python reference implementation of the experimental MCP Resource operations extension, built on the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) v2. It is meant to plug in through the SDK's extension mechanism (the `Extension` and `MethodBinding` API used by the Apps extension), following [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371), rather than by patching the SDK.

**Status:** Planned. This package is a placeholder until the group has a proposal to implement; see [open questions](../../docs/open-questions.md).

## Development

```bash
uv venv && uv pip install -e . pytest ruff mypy
ruff format --check . && ruff check .
mypy src/mcp_ext_filesystems
pytest
```

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
