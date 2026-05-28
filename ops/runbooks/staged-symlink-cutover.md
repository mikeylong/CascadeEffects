# Staged Symlink Cutover

Do not perform cutover until `bin/ce doctor`, web lint/build, and known production validators pass.

1. Confirm all old repos are clean and pushed.
2. Create a dated local archive directory, for example `/Users/mike/CascadeEffects_LocalArchive/2026-05-28_pre_monorepo_roots/`.
3. Move old `/Users/mike/*_CascadeEffects` roots into the archive.
4. Create compatibility symlinks from each old root path to its new monorepo path.
5. Run `bin/ce doctor` and the adapted production validators.
6. Keep symlinks until active scripts and agents no longer require legacy absolute paths.

This runbook is intentionally not automated because the cutover mutates long-lived root paths.
