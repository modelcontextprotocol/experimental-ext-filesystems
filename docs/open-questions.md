# Open Questions

Questions the group needs to settle for Resource operations. The first three come from the [charter](https://modelcontextprotocol.io/community/working-groups/filesystems); add others by pull request. When a question is settled, record the outcome in the [decision log](decisions.md) and link it here.

| # | Question | Source | Status |
| :--- | :--- | :--- | :--- |
| 1 | Is a transferred file addressed as a Resource URI? The charter keeps writes on Resources rather than a parallel `files/*` family, so the open part is where an upload flow ends and a resource write begins. | Charter, related groups (File Uploads WG) | Open |
| 2 | Which optimistic concurrency control mechanism do writes use, including create-if-absent? | Charter, scope | Open |
| 3 | How do writes interact with `notifications/resources/updated`, `ttlMs`, `cacheScope`, and `lastModified`? | Charter, scope | Open |
| 4 | Which typed errors do Resource operations return? | Proposed | Open |
| 5 | How do the open proposals in this space (SEP-2571, SEP-2532) end up: folded in, superseded, or scoped out? | Charter, success criteria | Open |
| 6 | How do Resource operations relate to the optional directory read in the Skills extension? | Charter, related groups | Open |
