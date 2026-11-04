## What to reference as a source

Nothing in this repository is a specification yet. The [Filesystems Working Group charter](https://modelcontextprotocol.io/community/working-groups/filesystems) defines the scope. The `docs/` folder holds open questions, the decision log, related work, and the implementations list. Treat it as context, not as normative text.

Do not describe a proposal in this repository as an accepted or official part of MCP. Until accepted text lands under `specification/`, everything here is experimental.

## Proposing changes

Changes are proposed as pull requests. A change to the group's direction is a dated entry in [`docs/decisions.md`](docs/decisions.md) with `**Status:** Proposed`, in the ADR-lite format used in that file (Status / Context / Decision / Rationale / References). When a decision supersedes or amends an earlier one, add a forward pointer to the earlier entry's `**Status:**` line rather than rewriting it.

## Code

The Python reference implementation lives in `python/sdk/`. Run `ruff format --check .`, `ruff check .`, `mypy src/mcp_ext_filesystems`, and `pytest` from that directory before opening a pull request.

## AI disclosure

Pull requests and issues must disclose AI assistance, per the MCP [AI contribution policy](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/AI_POLICY.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for participation, meetings, and decision-making.
