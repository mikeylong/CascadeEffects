# Caption Overlay Manifest Template

## Caption Overlay Manifest

- `episode_id`:
- `short_id`:
- `stage`: `video final`
- `short_audio_package_path`:
- `expected_voice_profile_id`:
- `audio_disposition`: `keep`
- `brand_motif_status`: `present|variant|waived|missing`
- `motif_family`:
- `motif_text`:
- `ending_cadence_read`: `pass|tighten|reject`
- `caption_model`: `script_locked_canonical_text_timing_from_asr_v1`
- `caption_text_source_path`:
- `caption_text_source_policy`: `script_locked_canonical_text_only`
- `caption_timing_source_path`:
- `caption_timing_source_policy`: `asr_whisperx_timing_only`
- `caption_text_matches_script_read`: `pass|tighten|reject`
- `caption_asr_text_not_used_read`: `pass|tighten|reject`
- `transcript_sha256`: # audio package transcript provenance only
- `caption_style_preset`: `minimal_surreal_editorial_v1`
- `caption_placement`: `lower-center|lower-left`
- `caption_timing_path`:
- `captioned_final_path`:
- `manual_timing_adjustments_path`:

## Style Defaults

- `preset`: `minimal_surreal_editorial_v1 | era_1940s_newsreel_ivory_v1`
- `contrast`: `high`
- `typeface`: `Avenir Next bold sans, or Futura Condensed ExtraBold for era_1940s_newsreel_ivory_v1`
- `font_color`: `minimal-surreal saturated semantic accent; default #FFD54A amber; 1940s archival default #F2E8C8 ivory`
- `stroke_or_backing`: `soft charcoal/sepia edge and shadow; no hard black TV-caption box`
- `font_size_1080x1920_px`: `78-88`
- `max_text_width_1080x1920_px`: `860`
- `timing_mode`: `phrase-level`
- `segment_duration_seconds`: `1.2-2.4 target`
- `line_count`: `1-2`
- `placement`: `mobile-safe lower third`
- `default_placement`: `lower-center`
- `allowed_placement_override`: `lower-left when lower-center covers the mechanism, faces, key anomaly, or crucial motion`
- `animation`: `restrained editorial fade`
- `visual_style_family`: `source_preserving_documentary_v1`
- `legacy_fallback_preset`: `documentary_lower_third_v1`
- `must_not_cover`: `mechanism|faces|key anomaly|crucial motion`
- `forbidden_style`: `karaoke word-by-word|emoji|bouncing|meme styling|poster graphics|unmotivated all-caps`

## Caption Segments

### `segment_id`

- `start_seconds`:
- `end_seconds`:
- `text`:
- `emphasis_words`:
- `placement_override`:
- `timing_adjustment_note`:

## QA

- `caption_legibility_checked`: `true|false`
- `caption_safe_zone_checked`: `true|false`
- `mechanism_not_occluded`: `true|false`
- `generated_visual_text_leakage_reviewed_separately`: `true|false`
- `closing_motif_caption_preserved`: `true|false`
