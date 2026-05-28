# Staged Symlink Cutover

Do not perform cutover until `bin/ce doctor`, web lint/build, and known production validators pass.

1. Confirm all old repos are clean and pushed.
2. Create a dated local archive directory outside the production monorepo.
3. Move each previous root folder named in `ops/migration/source-repos.json` into the archive.
4. Create compatibility symlinks from each old root path to its new monorepo path.
5. Run `bin/ce doctor` and the adapted production validators.
6. Keep symlinks until active scripts and agents no longer require legacy absolute paths.

This runbook is intentionally not automated because the cutover mutates long-lived root paths.
