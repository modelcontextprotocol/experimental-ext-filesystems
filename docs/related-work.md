# Related Work

SEPs, extensions, and discussions that Resource operations build on or must stay consistent with. Add entries by pull request; keep each to a line or two.

## SEPs named in the charter

| SEP | Status | Relevance |
| :--- | :--- | :--- |
| [SEP-2571](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2571) | Closed 2026-09-22 | Proposed `resources/create` and `resources/delete`. The charter names taking it up with its author as the group's first work item. |
| [SEP-2631](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2631) | Draft | File objects and out-of-band transfer. The [File Uploads Working Group](https://modelcontextprotocol.io/community/working-groups/file-uploads) plans to supersede it with a new SEP. |
| [SEP-2532](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2532) | Open | `resources/stream`. To be reconciled with the transfer work. |
| [SEP-2356](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2356) | Closed 2026-06-26 | File input model, closed in favour of SEP-2631. |

## Extension framework

- [SEP-2133](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133) (merged): extensions framework (naming, capability negotiation). Resource operations would ship as an extension under it.
- [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371) (open): consistent SDK extension points (extension registration, custom request and notification methods, middleware). The reference implementations here should be built on these extension points rather than on changes to the SDKs.

## Extensions and groups

- [Skills extension](https://github.com/modelcontextprotocol/ext-skills): reads skill files through Resources and defines an optional directory read (`resources/directory/read`). The charter asks this group to coordinate on any Resource operation that affects skills.
- [Interceptors extension](https://github.com/modelcontextprotocol/experimental-ext-interceptors): repository layout this one follows for per-language reference implementations.
