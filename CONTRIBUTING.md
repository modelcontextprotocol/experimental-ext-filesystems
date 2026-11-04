# Contributing

## How to Participate

The Filesystems Working Group welcomes contributions from anyone interested in operating on MCP Resources beyond a single read. You can participate by:

- Joining the discussion in `#filesystem-wg` on the MCP Discord (info on joining the server [here](https://modelcontextprotocol.io/community/communication#discord))
- Opening pull requests with concrete proposals, so the group can comment on specifics
- Sharing findings from your own implementations as [GitHub issues](https://github.com/modelcontextprotocol/experimental-ext-filesystems/issues)
- Adding servers, SDKs, and hosts to [docs/implementations.md](docs/implementations.md)

## Communication Channels

| Channel | Purpose | Response Expectation |
| :--- | :--- | :--- |
| Discord `#filesystem-wg` | Quick questions, coordination, async discussion | Best effort |
| This repository | Proposals, decision log, reference implementations, conformance scenarios | Reviewed by the WG |

## Meetings

Working Session cadence is defined in the [charter](https://modelcontextprotocol.io/community/working-groups/filesystems). Meeting requirements (advance notice, agendas, and notes) follow MCP [group governance](https://modelcontextprotocol.io/community/working-interest-groups#meeting-requirements).

## Decision-Making

Scope and per-decision-type authority are defined in the charter. The decision progression (lazy consensus, then formal vote, then escalation) follows MCP [group governance](https://modelcontextprotocol.io/community/working-interest-groups#decision-making-process).

## Contribution Guidelines

### Proposals

A proposal is a pull request. For a change to the group's direction, add a dated entry to [docs/decisions.md](docs/decisions.md) with `**Status:** Proposed`, in the ADR-lite format defined there. A proposal can also carry prototype code under `python/` or scenarios under `conformance/` that show it working.

### Decision Log

Record significant decisions in [docs/decisions.md](docs/decisions.md) after the meeting where they were made, or once consensus is reached asynchronously. A decision is worth logging when it:

- Chooses one approach over alternatives
- Sets or changes the group's scope
- Establishes a convention or coordination mechanism

When a decision supersedes or amends an earlier one, add a forward pointer to the earlier entry's `**Status:**` line rather than rewriting it.

### Sharing Implementation Findings

When reporting a finding:

- Include enough detail for others to reproduce or evaluate it
- Note which clients and servers were tested, and the specification revision
- Be explicit about what worked, what didn't, and what remains untested
- Write "Not documented" for missing details instead of inferring them

### Community Input

When quoting community discussion, attribute it by name and GitHub handle, link to the source where possible, and use blockquotes to separate it from editorial text.

### AI Contributions

Follow the MCP [AI contribution policy](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/AI_POLICY.md): disclose any AI assistance in the pull request or issue, along with the extent of it.

## License

By contributing, you agree that your contributions are licensed under the Apache License 2.0.
