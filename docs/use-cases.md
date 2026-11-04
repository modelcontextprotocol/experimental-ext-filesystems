# Use Cases

Concrete situations Resource operations should serve. Add yours by pull request: describe who the client and server are, what they need to do, and what they do today instead.

## Shared state written by several agents

The charter names multi-agent and job orchestration systems as the motivating consumers of a shared write path. The [running example](problem-statements.md#running-example) in the problem statements walks through this case.

## Memory servers

A memory server stores facts as files that an agent reads and rewrites. Today a write is a tool call that replaces the file, so two sessions updating the same memory lose one update without either noticing. A conditional write (update only if the revision is still the one I read) and create-if-absent would make that safe, and `notifications/resources/updated` would tell other sessions to re-read.

## Servers that ask for base64 content in prose

Some servers ask the model to pass file content as base64 inside a tool argument, described in the tool's text. The charter calls for a migration guide away from this pattern, which depends on a real write path existing first.

## Navigating large Resource trees

A client working in a large repository or document store needs to list one directory, glob for matching paths, or read metadata (`stat`) without reading every Resource, then read only what it needs. See Problem Statements [1](problem-statements.md#problem-statement-1-scoped-listing-and-directory-traversal), [2](problem-statements.md#problem-statement-2-server-side-search-and-glob-matching) and [3](problem-statements.md#problem-statement-3-bulk-and-partial-reads).
