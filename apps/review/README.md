# Inbox Cascade Effects

Standalone reviewer app for Cascade Effects orchestration.

## Launch

- `./bin/ce-inbox review-server`
- `./bin/ce-inbox review-server --reload`
- `./bin/ce-inbox review-inbox --json`
- `./bin/ce-inbox review-action <episode_id> <gate_type> [item_id] --decision approve|reject|unapprove`

## Config

`config/inbox.toml` points at the local Agents checkout:

```toml
agents_root = "/Users/mike/Agents_CascadeEffects"
```

Inbox reads and writes orchestration state directly from that Agents repo.
