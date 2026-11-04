# Related Work

SEPs, extensions, and discussions that Resource operations build on or must stay consistent with. The SEPs named in the charter, with their current status, are tracked in [Related proposals](problem-statements.md#related-proposals) in the problem statements; this file covers the rest. Add entries by pull request; keep each to a line or two.

## Extension framework

- [SEP-2133](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2133) (merged): extensions framework (naming, capability negotiation). Resource operations would ship as an extension under it.
- [SEP-3371](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3371) (open): consistent SDK extension points (extension registration, custom request and notification methods, middleware). The reference implementations here should be built on these extension points rather than on changes to the SDKs.

## Extensions and groups

- [Skills extension](https://github.com/modelcontextprotocol/ext-skills): reads skill files through Resources and defines an optional directory read (`resources/directory/read`). The charter asks this group to coordinate on any Resource operation that affects skills.
- [File Uploads extension](https://github.com/modelcontextprotocol/experimental-ext-file-uploads): continues SEP-2631. The charter asks this group to coordinate on where an upload flow ends and a resource write begins.
- [Interceptors extension](https://github.com/modelcontextprotocol/experimental-ext-interceptors): repository layout this one follows for per-language reference implementations.
