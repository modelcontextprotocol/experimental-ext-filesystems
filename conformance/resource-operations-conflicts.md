# Scenarios: write conflicts

Implementation-independent checks for the conflict behaviour in the [Resource operations strawman](../docs/proposals/resource-operations.md). A harness runs them against any server that declares `io.modelcontextprotocol/resource-operations`, using one or two client connections.

Conventions:

- `<U>` is a URI the server accepts for writes and that does not exist at the start. The harness gets it from configuration.
- `<R…>` are revisions captured from earlier responses. Revisions are opaque: compare them only for equality, never parse them.
- "Precondition failed" means the error code assigned to precondition failures (provisionally `-32010`).
- Each step lists the request and the checks on its response. A step fails the scenario if any check fails.

## RO-CONFLICT-1: create-if-absent

| # | Connection | Request | Expect |
| :--- | :--- | :--- | :--- |
| 1 | A | `resources/create {uri: <U>, contents: {uri: <U>, text: "a"}}` | Result. `revision` is a non-empty string; save as `<R1>`. `changes` contains `{uri: <U>, effect: "created", revision: <R1>}`. |
| 2 | B | `resources/create {uri: <U>, contents: {uri: <U>, text: "b"}}` | Error. Code is precondition failed. `data.uri` = `<U>`, `data.reason` = `"alreadyExists"`, `data.currentRevision` = `<R1>`. |
| 3 | A | `resources/stat {uri: <U>}` | Result. `revision` = `<R1>`. The second create changed nothing. |

## RO-CONFLICT-2: lost update

The memory-server case from [use cases](../docs/use-cases.md): two sessions read the same revision and both write it back.

| # | Connection | Request | Expect |
| :--- | :--- | :--- | :--- |
| 1 | A | `resources/create {uri: <U>, contents: {uri: <U>, text: "0"}}` | Result. |
| 2 | A | `resources/stat {uri: <U>}` | Result. Save `revision` as `<R1>`. |
| 3 | B | `resources/stat {uri: <U>}` | Result. `revision` = `<R1>`. |
| 4 | A | `resources/update {uri: <U>, contents: {uri: <U>, text: "0A"}, ifMatch: <R1>}` | Result. Save `revision` as `<R2>`; `<R2>` != `<R1>`. `changes` contains `{uri: <U>, effect: "updated", previousRevision: <R1>, revision: <R2>}`. |
| 5 | B | `resources/update {uri: <U>, contents: {uri: <U>, text: "0B"}, ifMatch: <R1>}` | Error. Code is precondition failed. `data.reason` = `"revisionMismatch"`, `data.currentRevision` = `<R2>`. |
| 6 | B | `resources/stat {uri: <U>}` | Result. `revision` = `<R2>`. The rejected write changed nothing. |
| 7 | B | `resources/update {uri: <U>, contents: {uri: <U>, text: "0AB"}, ifMatch: <R2>}` | Result. `changes` contains `previousRevision: <R2>`. |
| 8 | B | `resources/delete {uri: <U>, ifMatch: <R1>}` | Error. Code is precondition failed. `data.reason` = `"revisionMismatch"`. |
| 9 | A | `resources/stat {uri: <U>}` | Result. The resource still exists. |

Optional, if the server reads back what it stores: after step 7, `resources/read {uri: <U>}` returns text `"0AB"`.
