# Conformance

Conformance scenarios for each new Resource operation method and schema element, as the charter requires. Scenarios should run against any implementation, not only the ones in this repository, so that independent servers exercising the write path can be checked against a common client.

| Scenarios | Covers |
| :--- | :--- |
| [resource-operations-conflicts.md](resource-operations-conflicts.md) | Create-if-absent and stale `ifMatch` from the [Resource operations strawman](../docs/proposals/resource-operations.md) |

Scenarios are written as request and expectation tables for now. A runnable harness can come once the methods settle.
