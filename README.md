# MCP Filesystems (Experimental Extension)

> **Status:** Experimental. This work is for prototyping and feedback only, and is not an accepted or official MCP extension.

This repository holds the working documents and reference implementations for **Resource operations**: a common interface for operating on MCP Resources beyond a single read (`create`, `update`, `delete`, and a metadata read, `stat`), with optimistic concurrency control on writes and a defined interaction with change notification and caching. It is maintained by the Filesystems Working Group, which coordinates with the [File Uploads Working Group](https://modelcontextprotocol.io/community/working-groups/file-uploads) on where an upload flow ends and a resource write begins.

**Charter:** [Filesystems Working Group charter](https://modelcontextprotocol.io/community/working-groups/filesystems): mission, scope, leadership, and active work items.
**Discord:** `#filesystem-wg` on the [MCP Discord](https://modelcontextprotocol.io/community/communication#discord).
**Open work:** [pull requests](https://github.com/modelcontextprotocol/experimental-ext-filesystems/pulls) and [issues](https://github.com/modelcontextprotocol/experimental-ext-filesystems/issues). Proposals, findings, and implementations are welcome.

## Repository Contents

| Document | Description |
| :--- | :--- |
| [Problem Statements](docs/problem-statements.md) | What is missing from Resources today, as six problem statements with a running example |
| [Use Cases](docs/use-cases.md) | Concrete situations Resource operations should serve |
| [Open Questions](docs/open-questions.md) | Questions the group needs to settle, starting with the charter's |
| [Resource operations strawman](docs/proposals/resource-operations.md) | Draft `stat`, `create`, `update`, `delete` with revision-based concurrency, for discussion |
| [Decision Log](docs/decisions.md) | ADR-lite record of the group's decisions, and the vehicle for proposing changes |
| [Related Work](docs/related-work.md) | SEPs, extensions, and discussions this work builds on |
| [Implementations](docs/implementations.md) | Servers, SDKs, and hosts that implement Resource operations |
| [`python/`](python/) | Python reference implementation |
| [`conformance/`](conformance/) | Conformance scenarios for each new method and schema element |

Nothing under `docs/` is part of a specification. A specification will live under `specification/` once the group has accepted text to put there.

## Implementations

| Language | Directory | Package | Status |
| :--- | :--- | :--- | :--- |
| Python | `python/sdk/` | `mcp-ext-filesystems` | Prototype |

The charter's success criteria call for reference implementations in at least two Tier 1 SDKs.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to participate.

## License

Apache License 2.0. See [LICENSE](LICENSE).
