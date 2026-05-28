# Therac Midjourney Resources

Use this folder as the single entry point when loading the Therac package into Midjourney:

- `shot_list.md` gives the overall package guidance.
- `lookrefs/` contains the optional global style references.
- `shot_refs/cover/` contains the cover prompt doc and its reference images.
- `shot_refs/beats/beat_01` through `shot_refs/beats/beat_05` contain each beat's prompt doc and reference images.
- Approved Midjourney finals should be dropped in `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/midjourney/therac_short_minimal_surreal_v1/selects/`.

Recommended loading order:

1. Open `shot_list.md`.
2. Review `lookrefs/` for the current style direction.
3. For each shot, open the matching `prompt.txt` in `shot_refs/cover/` or `shot_refs/beats/` and upload only that shot's listed `references/` files.
4. After approval, place final Midjourney stills in the package-level `selects/` folder using the required filenames.

Important:

- `lookrefs/` are optional style guidance, not replacements for per-shot references.
- The shot-specific `references/` folders remain the source of truth for upload order.
- The package-level `selects/` folder should contain only approved final stills, not drafts or local Comfy outputs.
