# Resource operations: strawman

**Status:** Draft strawman for discussion. Not accepted by the Filesystems Working Group, not part of any specification.

**Decision log entry:** [2026-10-09](../decisions.md#2026-10-09-strawman-for-resource-operations-stat-create-update-delete-with-revision-based-concurrency)  
**Prototype:** [`python/sdk/`](../../python/sdk/) · **Conformance scenarios:** [`conformance/`](../../conformance/)

## Motivation

Resources can be listed and read, but not created, updated, deleted, or inspected without reading the content ([Problem Statement 4](../problem-statements.md#problem-statement-4-writes-metadata-and-typed-errors)). Servers that need writes expose them as tools with ad hoc names, arguments, and errors, and nothing stops two writers from overwriting each other ([Problem Statement 5](../problem-statements.md#problem-statement-5-optimistic-concurrency-control); [use cases](../use-cases.md): shared state written by several agents, memory servers).

This strawman covers the smallest slice of the charter's scope that fixes the write path: a metadata read (`resources/stat`), `resources/create` with create-if-absent semantics, `resources/update` conditional on a revision, `resources/delete` with an optional revision check, typed errors, and how these interact with existing cache and notification fields. Listing reuses `resources/directory/read` from SEP-2640. Search, glob, bulk reads, and ranges are deferred.

Vocabulary follows Kryspin Ziemski's working document shared in #filesystem-wg ("MCP Resources as Addressable Domain State"), which proposes Create, Read, Update, Delete, Query, and Range (CRUDQR) over Resources and a change-set entry `{uri, effect, previousVersion?, version?}`. This draft covers C, U, D, plus `stat`, and uses the change-set entry in write results. It calls the concurrency token a `revision`, the term [Problem Statement 5](../problem-statements.md#problem-statement-5-optimistic-concurrency-control) uses, so the entry here is `{uri, effect, previousRevision?, revision?}`. Query and Range are deferred.

## Extension identifier and capability negotiation

Identifier (provisional): `io.modelcontextprotocol/resource-operations`.

A server that supports the extension declares it under `capabilities.extensions` ([SEP-2133](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133)) and also declares the `resources` capability:

```json
{
  "capabilities": {
    "resources": {},
    "extensions": {
      "io.modelcontextprotocol/resource-operations": { "directoryRead": true }
    }
  }
}
```

| Setting | Type | Default | Meaning |
| :--- | :--- | :--- | :--- |
| `directoryRead` | boolean | `false` | The server serves `resources/directory/read` as defined by SEP-2640. |

Declaring the extension commits the server to serving all four methods below. A server that cannot perform an operation on a given URI returns `notSupported` for that URI. Clients MUST NOT call these methods on a server that did not declare the extension. No new methods are added to core, and no existing method changes type: per the core-maintainer meeting on 2026-10-07, extensions may add methods but must not change the types of existing ones.

## Revisions

A `revision` is the opaque revision identifier that [Problem Statement 5](../problem-statements.md#problem-statement-5-optimistic-concurrency-control) asks for: a string minted by the server for the current state of one resource, compared byte-for-byte like a strong HTTP `ETag`.

- Clients compare revisions only for exact string equality. Revisions have no order.
- A revision MUST change whenever the content or `mimeType` of the resource changes. A revision MUST NOT be reused for a different state of the same URI, including after a delete and re-create. A digest over the content and `mimeType` is a valid revision.
- Revisions are scoped to one server and one URI.
- Returned by `resources/stat`, `resources/create`, and `resources/update`. Core shapes that this extension may not retype carry it in `_meta` under `io.modelcontextprotocol/resource-revision`: entries in a `resources/directory/read` result (`Resource._meta`), and, when the server can provide it, each item of a `resources/read` result (`contents[]._meta`). The `_meta` key name is provisional.
- A directory resource's revision SHOULD change when its set of direct children changes.

## Methods

Content in `create` and `update` uses the core `TextResourceContents` or `BlobResourceContents` shape, the same one `resources/read` returns. `contents.uri` MUST equal `uri`. Content travels inline; moving large content is the File Uploads Working Group's job.

### `resources/stat`

Returns metadata and the current revision without the content. The result is a core `Resource` plus `revision`, and carries the SEP-2549 cache fields like other cacheable results.

```json
{ "method": "resources/stat", "params": { "uri": "mem://notes/plan.md" } }
```
```json
{
  "resource": {
    "uri": "mem://notes/plan.md", "name": "plan.md", "mimeType": "text/markdown", "size": 7,
    "annotations": { "lastModified": "2026-10-09T14:02:11Z" }
  },
  "revision": "17",
  "ttlMs": 0,
  "cacheScope": "private"
}
```

A directory resource stats with `mimeType: "inode/directory"`, as in SEP-2640.

### `resources/create`

Creates the resource at `uri` only if nothing exists there (create-if-absent). If the URI is taken, the server returns `alreadyExists` with the current revision and changes nothing. There is no upsert: a client that wants to overwrite reads the revision from the error and calls `resources/update`.

```json
{
  "method": "resources/create",
  "params": {
    "uri": "mem://notes/plan.md",
    "contents": { "uri": "mem://notes/plan.md", "mimeType": "text/markdown", "text": "# Plan\n" }
  }
}
```
```json
{
  "resource": { "uri": "mem://notes/plan.md", "name": "plan.md", "mimeType": "text/markdown", "size": 7 },
  "revision": "17",
  "changes": [{ "uri": "mem://notes/plan.md", "effect": "created", "revision": "17" }]
}
```

The client chooses the URI. SEP-2571 instead had the server assign the URI; that variant is an open question below.

### `resources/update`

Replaces the content of an existing resource, only if its current revision equals `ifMatch`. `ifMatch` is required, so every update is conditional and a lost update cannot happen by omission. The result reports the previous and new revisions.

```json
{
  "method": "resources/update",
  "params": {
    "uri": "mem://notes/plan.md",
    "contents": { "uri": "mem://notes/plan.md", "mimeType": "text/markdown", "text": "# Plan\n- ship\n" },
    "ifMatch": "17"
  }
}
```
```json
{
  "resource": { "uri": "mem://notes/plan.md", "name": "plan.md", "mimeType": "text/markdown", "size": 14 },
  "revision": "18",
  "changes": [{ "uri": "mem://notes/plan.md", "effect": "updated", "previousRevision": "17", "revision": "18" }]
}
```

Update is full replacement. Partial updates (patch, append, range writes) are deferred.

### `resources/delete`

Deletes the resource. With `ifMatch`, only if the current revision matches. Deleting a directory resource is out of scope for this draft (`notSupported`).

```json
{ "method": "resources/delete", "params": { "uri": "mem://notes/plan.md", "ifMatch": "18" } }
```
```json
{ "changes": [{ "uri": "mem://notes/plan.md", "effect": "deleted", "previousRevision": "18" }] }
```

### Change sets

Each write result carries `changes`, a list of change-set entries in the vocabulary of Kryspin's document. It MUST contain an entry for the target URI and MAY contain entries for other resources the operation affected. This draft uses only `created`, `updated`, and `deleted`; `invalidated` and `affected` are left to a later draft. `revision` duplicates the target entry's `revision` for convenience; whether to keep both is open.

### Concurrency

The server MUST compare the revision and apply the write as one atomic step. A check followed by a separate write reintroduces the lost update this mechanism exists to prevent.

The lost-update case from [use cases](../use-cases.md) plays out as follows. Two sessions stat `plan.md` at revision `17`. Session A updates with `ifMatch: "17"` and gets revision `18`. Session B updates with `ifMatch: "17"` and gets `revisionMismatch` with `currentRevision: "18"`. B re-reads, merges, and retries with `ifMatch: "18"`.

### Listing: reuse `resources/directory/read`

The Skills extension ([SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640), Final) already defines `resources/directory/read`: request `{uri, cursor?}`, result `{resources: Resource[], nextCursor?}` listing direct children, with subdirectories as `inode/directory` resources and `-32602` for a missing or non-directory URI. SEP-2640 states that the method is not skill-specific and that a server MAY support it on any directory resource under any scheme.

This draft reuses that method unchanged and adds no listing method of its own. The only addition is a way to advertise it without the Skills extension: SEP-2640 gates the method behind `directoryRead` under `io.modelcontextprotocol/skills`, and declaring that extension commits a server to `skills/list` and `skills/get`, which a plain file server cannot honor. So this extension carries its own `directoryRead` setting with the same meaning. A client may call the method if either extension declares `directoryRead: true`. Entries carry their revision in `_meta` (see Revisions), which also gives SEP-2640 hosts the snapshot token that SEP-2640 notes it lacks.

The cleaner long-term shape is probably for one definition to live in one place (this extension, or core) with Skills referencing it. That is for the Skills Over MCP WG and this WG to agree on ([open question 6](../open-questions.md)).

### Deferred

- **Search and glob (Query).** The query language and glob semantics over URIs (as opposed to paths) are unsettled; Kryspin's document lists the query language as open. Better to land the write path first than to block it on a query design.
- **Recursive traversal.** Clients descend with repeated `resources/directory/read` calls. A recursive variant needs limits and pagination rules that are easier to set once listing is settled.
- **Bulk reads.** Their size limits and failure modes depend on the File Uploads Working Group's transfer design.
- **Range.** Partial reads and writes need range coordinates (bytes, lines, records) and overlap with `resources/stream` (SEP-2532), which the charter assigns to content transfer.

## Errors

| Condition | Code | `data.reason` | Other `data` |
| :--- | :--- | :--- | :--- |
| Resource does not exist | `-32602` Invalid params | `notFound` | `uri` |
| URI malformed, `contents.uri` mismatch, or not a directory (`resources/directory/read`) | `-32602` Invalid params | `invalidUri` | `uri` |
| `ifMatch` does not match | `-32010` (provisional) | `revisionMismatch` | `uri`, `currentRevision` |
| `resources/create` on an existing URI | `-32010` (provisional) | `alreadyExists` | `uri`, `currentRevision` |
| Operation not supported for this URI (read-only scheme, directory, ancestor is a file) | `-32011` (provisional) | `notSupported` | `uri` |
| Extension not declared, or wrong protocol version | `-32601` Method not found | | |

Not found reuses `-32602` because core `resources/read` (2026-07-28) and SEP-2640's `resources/directory/read` already use it for unknown resources; `data.reason` lets a client tell it apart from other invalid params without a new code. Revision mismatch and already-exists share one code because both mean "your precondition about the current state was wrong" (HTTP 412 covers `If-Match` and `If-None-Match: *` alike) and both carry the current revision for recovery.

The two new codes are placeholders in the implementation-defined band. The 2026-07-28 allocation policy reserves `-32020..-32099` for spec-defined codes allocated in sequence, `-32000` and `-32001` are used by the Python SDK internally, and `-32002` is retired. Where extension error codes should come from is an open question.

## Interactions

**`notifications/resources/updated`.** After a successful update or delete, the server SHOULD send `notifications/resources/updated` for the URI to clients subscribed to it (through `subscriptions/listen` with `resourceSubscriptions` on 2026-07-28, or `resources/subscribe` on earlier versions). After a create or delete, it SHOULD send `notifications/resources/list_changed` if it declared `listChanged`. The writer may receive its own notification; it can compare its result's `revision` with a fresh `stat`. Open: whether the notification should carry the change-set entry in `_meta` so subscribers can skip the `stat`.

**`lastModified`.** Servers that track modification time MUST set `annotations.lastModified` on the `Resource` returned by `stat` and by writes, and update it on every write. It is informational only and MUST NOT be used as a precondition: timestamps have coarse resolution and clocks skew, so two writes can share one.

**`ttlMs`.** `resources/stat` results carry `ttlMs` as a freshness hint for metadata, as SEP-2549 defines for other results. A cached revision is only ever a guess: the conditional write is the check, and a stale revision fails safely with `revisionMismatch`. A client SHOULD discard cached reads and stats of a URI after its own successful write to it or an updated notification for it. Write results are not cacheable.

**`cacheScope`.** `resources/stat` defaults to `"private"`. A revision reveals that and when a resource changed, so a server whose resources differ per user MUST NOT mark `stat` results `"public"`. Open: whether `"public"` should be allowed at all for `stat`.

## SDK extension points

The Python prototype is built only on the MCP Python SDK's public `Extension` and `MethodBinding` API (`mcp>=2,<3`, tested on 2.3.0), per [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371), without patching the SDK. It works, with these gaps, offered as feedback for SEP-3371:

1. **Extension method handlers cannot publish change events.** A `MethodBinding` handler receives a `ServerRequestContext`, which has no handle on the server's `SubscriptionBus`; only the `MCPServer`-level `Context` has `notify_resource_updated`. On 2026-07-28 connections, `session.send_resource_updated` is dropped by design (change notifications travel only on `subscriptions/listen` streams). The prototype works around this by having the server author pass the same bus to both `MCPServer(subscriptions=bus)` and the extension. A bus or notify API on the handler context would remove that wiring.
2. **Events carry no metadata.** `ResourceUpdated` holds only `uri`, so the `_meta` of `notifications/resources/updated` cannot carry a revision or change-set entry through the bus, even though the wire notification allows `_meta`.
3. **Extensions cannot contribute to `resources/read`.** `MethodBinding` rejects spec methods (correctly, given the 2026-10-07 rule), `ResourceBinding` takes only static resources, resource templates take one static `meta` per template, and an `Extension` cannot contribute middleware. So the extension can neither make store-backed resources readable through `resources/read` nor stamp a per-read revision into `contents[]._meta`; the server author has to register a template. A per-read hook for `_meta`, or letting an extension contribute a resource provider, would close this.
4. **One method, two extensions.** `MCPServer` raises if two extensions bind the same method. A server running both Skills (with `read_directory`) and this extension must bind `resources/directory/read` in exactly one of them; the prototype makes it opt-in (`directory_read=True`) for that reason. Shared methods across extensions need an ownership rule.
5. **Legacy wire.** `capabilities.extensions` exists only on 2026-07-28 in this SDK, and `MCPServer` does not serve `resources/subscribe`, which an extension cannot bind. The prototype therefore serves its methods on 2026-07-28 only.

## Open questions

Numbers refer to [open-questions.md](../open-questions.md); "new" marks questions this draft raises.

- **#1** Files as Resource URIs: not addressed (see below). This draft assumes `resources/*` and would be renamed if the group chooses a `files/*` family.
- **#2** Concurrency: this draft proposes an opaque `revision`, required `ifMatch` on update, optional on delete, and create-if-absent as the only create. Alternatives: optional `ifMatch` on update (unconditional overwrite allowed); HTTP-style `ifNoneMatch: "*"` on a single write method instead of separate create and update.
- **#3** Interactions: proposed above. Open: change-set entry in notification `_meta`; `cacheScope: "public"` for `stat`; whether `resources/read` SHOULD or MUST carry the revision in `_meta`, and the key name.
- **#4** Typed errors: proposed above. Open: where extension error codes are allocated; whether `notFound` deserves its own code despite core's `-32602`.
- **#5** One SEP or several: this draft suggests one SEP for `stat` and writes, with listing settled jointly with Skills, and Query and Range in a later SEP.
- **#6** Skills directory read: reuse as-is with a second `directoryRead` flag. Open: whether the definition moves here or to core.
- **New** Server-assigned URIs (SEP-2571 style, create in a collection) alongside client-chosen URIs.
- **New** Whether a server can declare `stat` without writes (a read-only setting) instead of answering `notSupported` per URI.
- **New** The extension identifier and `_meta` key names, and whether experimental builds should use a different prefix.
- **New** Whether `revision` and `changes` both belong in write results.

## Not addressed

- **Content transfer.** Content travels inline. Out-of-band transfer, digests, size limits, and streaming belong to the File Uploads Working Group; `create` and `update` will need a way to reference transferred content once that exists.
- **File inputs.** Marking tool or elicitation inputs as files belongs to the File Uploads Working Group. Nothing here depends on it.
- **Whether files are Resource URIs.** The charter's cross-cutting decision ([open question 1](../open-questions.md)). This draft operates on Resource URIs because that is what exists today; it takes no position on the decision.
- **Authorization.** Who may write what is out of the charter's scope beyond stating that the existing MCP authorization specification applies.
