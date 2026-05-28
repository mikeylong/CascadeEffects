# Cascade Effects Review App

Human gate review surface for the Cascade Effects production monorepo.

## Launch

- `/Users/mike/CascadeEffects/bin/ce review-server`
- `/Users/mike/CascadeEffects/bin/ce review-server --reload`
- `/Users/mike/CascadeEffects/bin/ce review-list --json`
- `/Users/mike/CascadeEffects/bin/ce review-approve <episode_id> <gate_type> [item_id]`
- `/Users/mike/CascadeEffects/bin/ce review-reject <episode_id> <gate_type> [item_id]`

## Config

`config/inbox.toml` points at the active production tooling and registry packages:

```toml
production_tools_root = "/Users/mike/CascadeEffects/packages/production-tools"
production_registry_root = "/Users/mike/CascadeEffects/packages/production-registry"
```

Review commands read and write production state through the monorepo packages. The `inbox_app`
module name is retained only as implementation detail from the migration.
