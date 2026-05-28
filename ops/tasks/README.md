# Task Queue

Use `bin/ce claim-task <task-id> --owner <agent>` before changing active production state.

Root task records live in `tasks.jsonl`; episode-local task queues live beside the episode in `episodes/<season>/<episode>/tasks.jsonl`.

Locks live in `ops/locks/*.lock.json` and should be released with `bin/ce release-task <task-id>`.
