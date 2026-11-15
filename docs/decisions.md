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

**Status:** Proposed. Amended by [2026-11-15 entry](#2026-11-15-merge-create-and-update-into-one-write-method-with-ifmatch-or-ifnonematch).

**Context:** The [charter](https://modelcontextprotocol.io/community/working-groups/filesystems) asks for create, update, delete, and `stat`, typed errors, and optimistic concurrency control on writes including create-if-absent (PS4.1, PS4.3, PS4.5, PS5.1 to PS5.3, PS6.1, and PS6.2 in the [problem statements](problem-statements.md), where PS*n*.*m* is item *m* of Problem Statement *n*; cross-cutting [open questions](open-questions.md) 1 and 3). Options considered for concurrency: no precondition (last writer wins), timestamps (`lastModified`), an opaque server-minted revision compared on write, and that revision optional on update or delete. For listing: a new method, or the `resources/directory/read` method already defined by the Skills extension (SEP-2640).

**Decision:** Use [docs/proposals/resource-operations.md](proposals/resource-operations.md) as the group's starting strawman: an extension `io.modelcontextprotocol/resource-operations` (provisional) with `resources/stat`, `resources/create` (create-if-absent only), `resources/update` and `resources/delete` (both require `ifMatch`); an opaque `revision` as the concurrency token, the term [Problem Statement 5](problem-statements.md#problem-statement-5-optimistic-concurrency-control) uses; a precondition-failed error carrying `currentRevision`; and reuse of `resources/directory/read` unchanged for listing. Search, glob, bulk reads, and ranges are deferred.

**Rationale:** An opaque revision identifier is what HTTP ETags, S3, and GCS already use, survives coarse clocks, and lets each server choose a counter, digest, or backend generation. Required `ifMatch` on update and delete rules out lost updates by omission. Reusing SEP-2640's method avoids two listing methods for the same tree. The change-set vocabulary (entries with `effect`) follows Kryspin Ziemski's working document shared in #filesystem-wg, so later Query and Range work can build on it; that document calls the token `version`, and this draft uses `revision` to match the problem statements. A Python prototype built on the SDK's `Extension`/`MethodBinding` API and conformance scenarios accompany the draft.

**References:**
- [Proposal](proposals/resource-operations.md), [Python prototype](../python/sdk/), [conformance scenarios](../conformance/)
- [SEP-2571](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2571) (closed): `resources/create` and `resources/delete`
- [SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640): Skills extension, `resources/directory/read`
- [SEP-2133](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133), [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371): extensions framework and SDK extension points
- Kryspin Ziemski's working document "MCP Resources as Addressable Domain State", shared in #filesystem-wg

### 2026-11-15: Merge create and update into one write method with ifMatch or ifNoneMatch

**Status:** Proposed

**Context:** The [2026-10-09 entry](#2026-10-09-strawman-for-resource-operations-stat-create-update-delete-with-revision-based-concurrency) split writes into `resources/create` (create-if-absent only) and `resources/update` (requires `ifMatch`); the proposal's open questions listed a single HTTP-style write method as an alternative. Reviewing that pull request, Daniel ([DanielTemesgen](https://github.com/DanielTemesgen)) suggested the single method:

> The create and update split gives the same guarantees as one resources/write that requires exactly one of ifMatch or ifNoneMatch: "*", as with HTTP PUT. I have a preference for fewer methods if possible, but this shouldn't block.
>
> ([review comment on #2](https://github.com/modelcontextprotocol/experimental-ext-filesystems/pull/2#discussion_r4541941540))

Options considered: keep the split, or one `resources/write` with exactly one precondition.

**Decision:** Replace `resources/create` and `resources/update` with `resources/write`, which requires exactly one of `ifMatch: "<revision>"` (replace an existing resource at that revision) or `ifNoneMatch: "*"` (create only if absent). Neither or both is invalid params. Errors, results, and `resources/delete` (requires `ifMatch`) are unchanged: a stale `ifMatch` returns `revisionMismatch`, `ifNoneMatch: "*"` on an existing URI returns `alreadyExists`, both with `currentRevision`.

**Rationale:** Fewer methods for the same guarantees. Every write is still conditional, so a lost update still cannot happen by omission, and there is still no upsert. The two preconditions map one to one to `If-Match` and `If-None-Match: *` on HTTP `PUT` ([RFC 9110, section 13.1](https://www.rfc-editor.org/rfc/rfc9110#section-13.1)), and they match the existing rationale for sharing one error code (HTTP 412 covers both). The cost is a request shape with a mutual-exclusion rule that a schema expresses less directly than two methods do.

**References:**
- [Proposal](proposals/resource-operations.md), [Python prototype](../python/sdk/), [conformance scenarios](../conformance/)
- [#2](https://github.com/modelcontextprotocol/experimental-ext-filesystems/pull/2): the strawman, and the review comment quoted above
