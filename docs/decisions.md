# Decision Log

This document records significant decisions made by the Filesystems Working Group about Resource operations, using an ADR-lite (Architecture Decision Record) format. It serves as a transparent, auditable trace of the group's reasoning over time.

For background on the ADR format, see [adr.github.io](https://adr.github.io/).

No decisions have been accepted yet. The first one the charter calls for is listed in [open-questions.md](open-questions.md).

## Entry format

Add new entries below this section, oldest first. A pull request that adds an entry with `**Status:** Proposed` is a proposal.

```markdown
### YYYY-MM-DD: Short statement of the decision

**Status:** Proposed | Accepted | Superseded by [YYYY-MM-DD entry](#anchor)

**Context:** What prompted the decision, and the options considered.

**Decision:** What the group decided.

**Rationale:** Why this option over the alternatives.

**References:**
- Links to meeting notes, issues, pull requests, or Discord threads
```

---

### 2026-10-09: Strawman for Resource operations: stat, create, update, delete with revision-based concurrency

**Status:** Proposed

**Context:** The [charter](https://modelcontextprotocol.io/community/working-groups/filesystems) asks for create, update, delete, and `stat`, typed errors, and optimistic concurrency control on writes including create-if-absent ([open questions](open-questions.md) 2 to 6). Options considered for concurrency: no precondition (last writer wins), timestamps (`lastModified`), and an opaque server-minted revision compared on write. For listing: a new method, or the `resources/directory/read` method already defined by the Skills extension (SEP-2640).

**Decision:** Use [docs/proposals/resource-operations.md](proposals/resource-operations.md) as the group's starting strawman: an extension `io.modelcontextprotocol/resource-operations` (provisional) with `resources/stat`, `resources/create` (create-if-absent only), `resources/update` (requires `ifMatch`), and `resources/delete` (optional `ifMatch`); an opaque `revision` as the concurrency token, the term [Problem Statement 5](problem-statements.md#problem-statement-5-optimistic-concurrency-control) uses; a precondition-failed error carrying `currentRevision`; and reuse of `resources/directory/read` unchanged for listing. Search, glob, bulk reads, and ranges are deferred.

**Rationale:** An opaque revision identifier is what HTTP ETags, S3, and GCS already use, survives coarse clocks, and lets each server choose a counter, digest, or backend generation. Required `ifMatch` on update rules out lost updates by omission. Reusing SEP-2640's method avoids two listing methods for the same tree. The change-set vocabulary (entries with `effect`) follows Kryspin Ziemski's working document shared in #filesystem-wg, so later Query and Range work can build on it; that document calls the token `version`, and this draft uses `revision` to match the problem statements. A Python prototype built on the SDK's `Extension`/`MethodBinding` API and conformance scenarios accompany the draft.

**References:**
- [Proposal](proposals/resource-operations.md), [Python prototype](../python/sdk/), [conformance scenarios](../conformance/)
- [SEP-2571](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2571) (closed): `resources/create` and `resources/delete`
- [SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640): Skills extension, `resources/directory/read`
- [SEP-2133](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133), [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371): extensions framework and SDK extension points
- Kryspin Ziemski's working document "MCP Resources as Addressable Domain State", shared in #filesystem-wg
