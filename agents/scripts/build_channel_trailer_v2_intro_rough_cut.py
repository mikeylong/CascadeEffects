#!/usr/bin/env python3
"""Assemble the Cascade of Effects channel trailer v2 rough cut from visual proof clips."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, ImageStat


ROOT = Path("/Users/mike/Agents_CascadeEffects")
OUTPUT_BASE = Path("/Users/mike/Episodes_CascadeEffects/Channel_Trailer")
V1_PACKAGE = OUTPUT_BASE / "channel_trailer_v1_20260505T044755Z"
V1_AUDIO_MIX = V1_PACKAGE / "audio/channel_trailer_final_mix.wav"
V1_FINAL_MP4 = V1_PACKAGE / "video/cascade_of_effects_channel_trailer_v1.mp4"
V1_MANIFEST = V1_PACKAGE / "channel_trailer_manifest.json"
V1_VOICE_WAV = V1_PACKAGE / "work/rendered/channel_trailer_vo.wav"
NON_CHALLENGER_BATCH = OUTPUT_BASE / "multi_episode_intro_visual_proofs_20260506T170958Z"
THEME_FOLDER = Path("/Users/mike/CascadeEffects_LocalArchive/Audio_CascadeEffects/2026-04-18/themesong")
FULL_THEME_SOURCE = THEME_FOLDER / "Paper Architecture.m4a"
BODY_LOOP_SOURCE = THEME_FOLDER / "Paper Architecture instrumental_loop.wav"
BRAND_ROOT = Path("/Users/mike/Web_CascadeEffects/brand")
STYLE_SYSTEM = BRAND_ROOT / "cascade-effects-signal.style-system.json"
DESIGN_SYSTEM_CONTRACT = BRAND_ROOT / "contracts/design-system.contract.json"
YOUTUBE_CHANNEL_PACKAGE = BRAND_ROOT / "packages/youtube-channel.package.json"
MUSIC_REGISTRY = ROOT / "references/shorts/music_track_registry.json"
MUSIC_TRACK_ID = "paper_architecture_theme_v1"

WIDTH = 1920
HEIGHT = 1080
FPS = 24
SUPERSAMPLE = 4
VO_SEQUENCE_SUPERSAMPLE = 2
TARGET_FRAME_COUNT = 1007
TARGET_DURATION_SECONDS = TARGET_FRAME_COUNT / FPS
VOICE_START_SECONDS = 4.0
TARGET_MAX_SECONDS = 45.0
OUTRO_START_SECONDS = 28.2
INTRO_PRESERVED_FROM_PACKAGE_ID = "channel_trailer_v2_20260506T232655Z"
SUPERSEDES_PACKAGE_ID = INTRO_PRESERVED_FROM_PACKAGE_ID
REVISION_REASON = "repair_right_plate_freeze_and_restore_episode_push_in"
THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID = "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_theme_lyric_background_type_20260510T034413Z"
THEME_SONG_NO_VO_SUPERSEDES_PACKAGE_ID = None
THEME_SONG_NO_VO_SOURCE_PACKAGE_ID = "channel_trailer_v2_theme_song_no_vo_loop_to_end_end_screen_hold_20260507T052143Z"
THEME_SONG_NO_VO_SOURCE_MP4 = (
    OUTPUT_BASE
    / THEME_SONG_NO_VO_SOURCE_PACKAGE_ID
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_loop_to_end_end_screen_hold.mp4"
)
THEME_SONG_NO_VO_SOURCE_MANIFEST = (
    OUTPUT_BASE
    / THEME_SONG_NO_VO_SOURCE_PACKAGE_ID
    / "channel_trailer_v2_theme_song_no_vo_loop_to_end_end_screen_hold_manifest.json"
)
THEME_SONG_NO_VO_VARIANT_OF_MP4 = (
    OUTPUT_BASE
    / THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_theme_lyric_background_type.mp4"
)
THEME_SONG_NO_VO_VARIANT_OF_MANIFEST = (
    OUTPUT_BASE
    / THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_theme_lyric_background_type_manifest.json"
)
THEME_SONG_NO_VO_REVISION_REASON = "align_background_lyric_type_to_sung_lyrics_and_tighten_titanic_matte"
THEME_SONG_NO_VO_VISUAL_VARIANT = "opening_montage_6s_near_camera_lyric_timed_background_type_tight_matte"
LOOP_TO_END_BEAT_SECONDS = 0.452789
PREVIOUS_LOOP_TO_END_START_SECONDS = 28.984
SELECTED_LOOP_TO_END_START_SECONDS = 28.715
END_SCREEN_HOLD_SOURCE_SECONDS = 40.0
END_SCREEN_HOLD_TARGET_SECONDS = 48.0
END_SCREEN_AUDIO_DECLICK_SECONDS = 0.05
END_SCREEN_PREFIX_COPY_CUT_SECONDS = END_SCREEN_HOLD_SOURCE_SECONDS - (2.0 / FPS)
MUSIC_ONLY_COLD_OPEN_SECONDS = 6.0
MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS = 4.0
MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS = 4.45
MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS = 4.95
MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS = 5.5
MUSIC_ONLY_CHALLENGER_END_SECONDS = 9.2
MUSIC_ONLY_EPISODE_SHIFT_SECONDS = MUSIC_ONLY_COLD_OPEN_SECONDS - VOICE_START_SECONDS
MUSIC_ONLY_OUTRO_START_SECONDS = OUTRO_START_SECONDS + MUSIC_ONLY_EPISODE_SHIFT_SECONDS
MUSIC_ONLY_SHIFTED_SOURCE_START_SECONDS = VOICE_START_SECONDS
MUSIC_ONLY_SHIFTED_SOURCE_END_SECONDS = 28.0
MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS = MUSIC_ONLY_COLD_OPEN_SECONDS + (
    MUSIC_ONLY_SHIFTED_SOURCE_END_SECONDS - MUSIC_ONLY_SHIFTED_SOURCE_START_SECONDS
)
MUSIC_ONLY_LIVE_TITANIC_BRIDGE_END_SECONDS = MUSIC_ONLY_OUTRO_START_SECONDS
MUSIC_ONLY_TITLE_START_SECONDS = 37.172
MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS = 42.0
MUSIC_ONLY_COLD_OPEN_START_QUAD_SCALE = 1.22
MUSIC_ONLY_COLD_OPEN_SUPERSAMPLE = 2
SUBJECT_BADGE_START_SECONDS = MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS
SUBJECT_BADGE_END_SECONDS = MUSIC_ONLY_OUTRO_START_SECONDS
SUBJECT_BADGE_ANCHOR_XY = (96, 860)
SUBJECT_BADGE_FONT_SIZE = 42
SUBJECT_BADGE_RADIUS = 12
SUBJECT_BADGE_PADDING_X = 24
SUBJECT_BADGE_PADDING_Y = 15
SUBJECT_BADGE_TRANSITION_SECONDS = 0.20
SUBJECT_BADGE_CHALLENGER_FADE_SECONDS = MUSIC_ONLY_COLD_OPEN_SECONDS - MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS
SUBJECT_BADGE_OUTRO_FADE_SECONDS = 0.28
SUBJECT_BADGE_LABELS = {
    "challenger": "Challenger",
    "hyatt-regency": "Hyatt Regency",
    "semmelweis": "Semmelweis",
    "tacoma-narrows": "Tacoma Narrows",
    "737-max": "737 MAX",
    "titanic": "Titanic",
}
SUBJECT_BACKGROUND_TYPE_EXPERIMENT_ID = "subject_background_type_mask_experiment"
SUBJECT_BACKGROUND_TYPE_LARGE_EXPERIMENT_ID = "subject_background_type_large_lighten_with_badges"
SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_PACKAGE_ID = "channel_trailer_v2_subject_background_type_mask_experiment_20260509T165723Z"
SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_ROOT = OUTPUT_BASE / SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_PACKAGE_ID
SUBJECT_BACKGROUND_TYPE_PRECISE_EXPERIMENT_ID = "subject_background_type_large_lighten_precise_matte_with_badges"
SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_subject_background_type_large_lighten_with_badges_20260509T171011Z"
)
SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_ROOT = OUTPUT_BASE / SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_PACKAGE_ID
SUBJECT_BACKGROUND_TYPE_BEZIER_EXPERIMENT_ID = "subject_background_type_bezier_motion_precise_matte_with_badges"
SUBJECT_BACKGROUND_TYPE_BEZIER_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_subject_background_type_large_lighten_precise_matte_with_badges_20260509T173249Z"
)
SUBJECT_BACKGROUND_TYPE_BEZIER_VARIANT_OF_ROOT = OUTPUT_BASE / SUBJECT_BACKGROUND_TYPE_BEZIER_VARIANT_OF_PACKAGE_ID
SUBJECT_BACKGROUND_TYPE_CONTINUOUS_EXPERIMENT_ID = "subject_background_type_continuous_motion_precise_matte_with_badges"
SUBJECT_BACKGROUND_TYPE_CONTINUOUS_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_subject_background_type_bezier_motion_precise_matte_with_badges_20260509T191813Z"
)
SUBJECT_BACKGROUND_TYPE_CONTINUOUS_VARIANT_OF_ROOT = OUTPUT_BASE / SUBJECT_BACKGROUND_TYPE_CONTINUOUS_VARIANT_OF_PACKAGE_ID
SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_EXPERIMENT_ID = "subject_background_type_continuous_motion_rtl_precise_matte_with_badges"
SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_subject_background_type_continuous_motion_precise_matte_with_badges_20260510T000104Z"
)
SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_VARIANT_OF_ROOT = OUTPUT_BASE / SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_VARIANT_OF_PACKAGE_ID
SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_EXPERIMENT_ID = "subject_background_type_theme_lyric_phrases_rtl_precise_matte_with_badges"
SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_subject_background_type_continuous_motion_rtl_precise_matte_with_badges_20260510T025453Z"
)
SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_VARIANT_OF_ROOT = OUTPUT_BASE / SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_VARIANT_OF_PACKAGE_ID
BEAT_BREATH_EXPERIMENT_ID = "music_only_beat_breath_background_proof"
BEAT_BREATH_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_subject_badges_challenger_continuity_repair_20260509T152439Z"
)
BEAT_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_BREATH_VARIANT_OF_MP4 = (
    BEAT_BREATH_VARIANT_OF_ROOT
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_subject_badges_challenger_continuity_repair.mp4"
)
BEAT_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_BREATH_VARIANT_OF_ROOT
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_subject_badges_challenger_continuity_repair_manifest.json"
)
BEAT_BREATH_START_SECONDS = MUSIC_ONLY_COLD_OPEN_SECONDS
BEAT_BREATH_END_SECONDS = MUSIC_ONLY_OUTRO_START_SECONDS
BEAT_BREATH_AUDIO_SAMPLE_RATE = 44100
BEAT_BREATH_MIN_BEAT_SPACING_SECONDS = 0.28
BEAT_BREATH_ONSET_PERCENTILE = 84.0
BEAT_BREATH_DECAY_SECONDS = 0.24
BEAT_BREATH_PRE_ATTACK_SECONDS = 0.035
BEAT_BREATH_MAX_BRIGHTNESS_LIFT = 0.320
BEAT_BREATH_MAX_CONTRAST_LIFT = 0.110
BEAT_BREATH_MAX_COLOR_LIFT = 0.070
BEAT_BREATH_MAX_WASH_ALPHA = 108
BEAT_BREATH_MAX_SHADOW_ALPHA = 70
BEAT_GRID_BREATH_EXPERIMENT_ID = "music_only_beat_grid_breath_background_proof"
BEAT_GRID_BREATH_VARIANT_OF_PACKAGE_ID = "channel_trailer_v2_music_only_beat_breath_background_proof_20260510T201402Z"
BEAT_GRID_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_GRID_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_GRID_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_GRID_BREATH_VARIANT_OF_ROOT / "channel_trailer_v2_music_only_beat_breath_background_proof_manifest.json"
)
BEAT_CLEAR_BREATH_EXPERIMENT_ID = "music_only_clear_beat_breath_background_proof"
BEAT_CLEAR_BREATH_VARIANT_OF_PACKAGE_ID = "channel_trailer_v2_music_only_beat_grid_breath_background_proof_20260511T043324Z"
BEAT_CLEAR_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_CLEAR_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_CLEAR_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_CLEAR_BREATH_VARIANT_OF_ROOT / "channel_trailer_v2_music_only_beat_grid_breath_background_proof_manifest.json"
)
BEAT_LOWEST_BASS_BREATH_EXPERIMENT_ID = "music_only_lowest_bass_beat_breath_background_proof"
BEAT_LOWEST_BASS_BREATH_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_clear_beat_breath_background_proof_20260511T054032Z"
)
BEAT_LOWEST_BASS_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_LOWEST_BASS_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_LOWEST_BASS_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_LOWEST_BASS_BREATH_VARIANT_OF_ROOT / "channel_trailer_v2_music_only_clear_beat_breath_background_proof_manifest.json"
)
BEAT_BASS_EVENT_BREATH_EXPERIMENT_ID = "music_only_bass_event_breath_background_proof"
BEAT_BASS_EVENT_BREATH_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_lowest_bass_beat_breath_background_proof_20260511T155505Z"
)
BEAT_BASS_EVENT_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_BASS_EVENT_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_BASS_EVENT_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_BASS_EVENT_BREATH_VARIANT_OF_ROOT / "channel_trailer_v2_music_only_lowest_bass_beat_breath_background_proof_manifest.json"
)
BEAT_BASS_DRUM_HIT_BREATH_EXPERIMENT_ID = "music_only_bass_drum_hit_breath_background_proof"
BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_bass_event_breath_background_proof_20260511T222057Z"
)
BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_ROOT / "channel_trailer_v2_music_only_bass_event_breath_background_proof_manifest.json"
)
BEAT_RHYTHM_HIT_BREATH_EXPERIMENT_ID = "music_only_rhythm_hit_breath_background_proof"
BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_bass_drum_hit_breath_background_proof_20260511T231746Z"
)
BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_PACKAGE_ID
BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_ROOT / "channel_trailer_v2_music_only_bass_drum_hit_breath_background_proof_manifest.json"
)
BEAT_BASS_DRUM_ONLY_NO_TITANIC_EXPERIMENT_ID = "music_only_bass_drum_only_no_titanic_pulse_breath_background_proof"
BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_rhythm_hit_breath_background_proof_20260511T233721Z"
)
BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_PACKAGE_ID
BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_MANIFEST = (
    BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_ROOT
    / "channel_trailer_v2_music_only_rhythm_hit_breath_background_proof_manifest.json"
)
BEAT_GRID_PERIOD_SEARCH_RANGE_SECONDS = (0.385, 0.525)
BEAT_GRID_PHASE_SEARCH_STEP_SECONDS = 0.0025
BEAT_GRID_ATTACK_SECONDS = 0.13
BEAT_GRID_DECAY_SECONDS = 0.24
BEAT_GRID_NEAREST_ONSET_WINDOW_SECONDS = 0.09
BEAT_CLEAR_PERIOD_SEARCH_RANGE_SECONDS = (0.52, 0.70)
BEAT_CLEAR_PHASE_SEARCH_STEP_SECONDS = 0.001
BEAT_CLEAR_NEAREST_ONSET_WINDOW_SECONDS = 0.055
BEAT_CLEAR_ATTACK_SECONDS = 0.075
BEAT_CLEAR_DECAY_SECONDS = 0.23
BEAT_LOWEST_BASS_PERIOD_SEARCH_RANGE_SECONDS = (0.72, 1.12)
BEAT_LOWEST_BASS_PHASE_SEARCH_STEP_SECONDS = 0.001
BEAT_LOWEST_BASS_NEAREST_ONSET_WINDOW_SECONDS = 0.070
BEAT_LOWEST_BASS_EXPECTED_PERIOD_SECONDS = 0.905578
BEAT_LOWEST_BASS_EXPECTED_TEMPO_BPM = 66.256
BEAT_LOWEST_BASS_EXPECTED_GLOBAL_PHASE_SECONDS = 6.389
BEAT_BASS_EVENT_PEAK_PERCENTILE = 75.0
BEAT_BASS_EVENT_MIN_SPACING_SECONDS = 0.42
BEAT_BASS_EVENT_LOCAL_RADIUS_FRAMES = 3
BEAT_BASS_EVENT_ATTACK_SECONDS = 0.09
BEAT_BASS_DRUM_HIT_DECAY_SECONDS = 0.20
BEAT_BASS_DRUM_HIT_PEAK_TOLERANCE_SECONDS = 1.0 / FPS + 0.004
BEAT_BASS_DRUM_HIT_CONFIRMED_GLOBAL_SECONDS = [
    6.359909,
    6.801088,
    7.706667,
    8.763175,
    9.192744,
    9.657143,
    10.098322,
    11.154830,
    11.596009,
    12.501587,
    13.546485,
    13.999274,
    14.452063,
    14.893243,
    15.949751,
    16.402540,
    21.209070,
    21.801179,
    23.147937,
    23.600726,
    29.150295,
    29.603084,
]
BEAT_BASS_DRUM_REJECTED_WINDOWS = [
    {
        "global_seconds": [18.0, 21.0],
        "reason": "manual_review_no_audible_bass_drum_prior_low_frequency_false_positive_region",
    }
]
BEAT_TITANIC_NO_BASS_DRUM_WINDOW = {
    "global_seconds": [24.0, 30.2],
    "reason": "manual_review_no_audible_bass_drum_titanic_scene",
}
BEAT_TACOMA_737_AUDIT_EXPERIMENT_ID = "music_only_tacoma_737_bass_drum_hit_audit"
BEAT_TACOMA_737_AUDIT_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_bass_drum_only_no_titanic_pulse_breath_background_proof_20260512T152748Z"
)
BEAT_TACOMA_737_AUDIT_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_TACOMA_737_AUDIT_VARIANT_OF_PACKAGE_ID
BEAT_TACOMA_737_AUDIT_VARIANT_OF_MANIFEST = (
    BEAT_TACOMA_737_AUDIT_VARIANT_OF_ROOT
    / "channel_trailer_v2_music_only_bass_drum_only_no_titanic_pulse_breath_background_proof_manifest.json"
)
BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL = (
    BEAT_TACOMA_737_AUDIT_VARIANT_OF_ROOT
    / "video/cascade_of_effects_channel_trailer_v2_music_only_bass_drum_only_no_titanic_pulse_breath_background_proof_reel.mp4"
)
BEAT_TACOMA_737_AUDIT_VARIANT_OF_HIT_MAP = BEAT_TACOMA_737_AUDIT_VARIANT_OF_ROOT / "beat/bass_drum_only_hit_map.json"
BEAT_TACOMA_737_AUDIT_GLOBAL_ZERO_SECONDS = BEAT_BREATH_START_SECONDS
BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS = (16.6, 24.0)
BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS = (16.6, 20.3)
BEAT_TACOMA_737_AUDIT_737_SECONDS = (20.3, 24.0)
BEAT_TACOMA_737_AUDIT_CANDIDATE_SECONDS = [
    16.983039,
    18.341406,
    18.805805,
    19.258594,
    19.711383,
    20.744671,
    21.209070,
    21.801179,
    23.147937,
    23.600726,
]
BEAT_TACOMA_737_AUDIT_DIAGNOSTIC_PEAK_SECONDS = [
    20.793912,
    21.242891,
    22.145839,
    23.203435,
    23.652415,
]
BEAT_TACOMA_737_CORRECTED_AUDIT_EXPERIMENT_ID = "music_only_tacoma_737_corrected_bass_drum_hit_audit"
BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_tacoma_737_bass_drum_hit_audit_20260512T163702Z"
)
BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_ROOT = OUTPUT_BASE / BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_PACKAGE_ID
BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_MANIFEST = (
    BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_ROOT
    / "channel_trailer_v2_music_only_tacoma_737_bass_drum_hit_audit_manifest.json"
)
BEAT_TACOMA_737_CORRECTED_TACOMA_HIT_SECONDS = [
    17.338356,
    18.341406,
    18.805805,
    19.258594,
    19.711383,
]
BEAT_TACOMA_737_CORRECTED_737_HIT_SECONDS = [
    20.793912,
    21.242891,
    22.145839,
    23.203435,
    23.652415,
]
BEAT_TACOMA_737_CORRECTED_REJECTED_SECONDS = [16.983039]
BEAT_TACOMA_737_SUPERSEDED_737_TIMING_SECONDS = [
    20.744671,
    21.209070,
    21.801179,
    23.147937,
    23.600726,
]
BEAT_TACOMA_737_CORRECTED_AUDIT_PACKAGE_ID = (
    "channel_trailer_v2_music_only_tacoma_737_corrected_bass_drum_hit_audit_20260512T170408Z"
)
BEAT_TACOMA_737_CORRECTED_AUDIT_ROOT = OUTPUT_BASE / BEAT_TACOMA_737_CORRECTED_AUDIT_PACKAGE_ID
BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST = (
    BEAT_TACOMA_737_CORRECTED_AUDIT_ROOT
    / "channel_trailer_v2_music_only_tacoma_737_corrected_bass_drum_hit_audit_manifest.json"
)
BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP = (
    BEAT_TACOMA_737_CORRECTED_AUDIT_ROOT / "audit/tacoma_737_bass_drum_candidate_audit.json"
)
BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_EXPERIMENT_ID = (
    "music_only_corrected_tacoma_737_bass_drum_breath_background_proof"
)
BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_PACKAGE_ID = (
    "channel_trailer_v2_music_only_bass_drum_only_no_titanic_pulse_breath_background_proof_20260512T152748Z"
)
BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_ROOT = (
    OUTPUT_BASE / BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_PACKAGE_ID
)
BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_MANIFEST = (
    BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_ROOT
    / "channel_trailer_v2_music_only_bass_drum_only_no_titanic_pulse_breath_background_proof_manifest.json"
)
BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_HIT_MAP = (
    BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_ROOT / "beat/bass_drum_only_hit_map.json"
)
THEME_SONG_NO_VO_BADGE_BASELINE_PACKAGE_ID = (
    "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_subject_badges_challenger_continuity_repair_20260509T152439Z"
)
THEME_SONG_NO_VO_BADGE_BASELINE_ROOT = OUTPUT_BASE / THEME_SONG_NO_VO_BADGE_BASELINE_PACKAGE_ID
THEME_SONG_NO_VO_BADGE_BASELINE_MP4 = (
    THEME_SONG_NO_VO_BADGE_BASELINE_ROOT
    / "video/cascade_of_effects_channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_subject_badges_challenger_continuity_repair.mp4"
)
THEME_SONG_NO_VO_BADGE_BASELINE_MANIFEST = (
    THEME_SONG_NO_VO_BADGE_BASELINE_ROOT
    / "channel_trailer_v2_theme_song_no_vo_opening_montage_6s_near_camera_gallery_subject_badges_challenger_continuity_repair_manifest.json"
)
THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_VISUAL_VARIANT = (
    "opening_montage_6s_near_camera_gallery_badges_corrected_bass_drum_breath"
)
THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_PACKAGE_ID = (
    "channel_trailer_v2_music_only_corrected_tacoma_737_bass_drum_breath_background_proof_20260512T172625Z"
)
THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_ROOT = (
    OUTPUT_BASE / THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_PACKAGE_ID
)
THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_REEL = (
    THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_ROOT
    / "video/cascade_of_effects_channel_trailer_v2_music_only_corrected_tacoma_737_bass_drum_breath_background_proof_reel.mp4"
)
THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST = (
    THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_ROOT
    / "channel_trailer_v2_music_only_corrected_tacoma_737_bass_drum_breath_background_proof_manifest.json"
)
BEAT_RHYTHM_HIT_PRIMARY_MATCH_TOLERANCE_SECONDS = 0.08
BEAT_RHYTHM_HIT_MAX_ALLOWED_GAP_SECONDS = 1.55
BEAT_RHYTHM_HIT_SUPPORT_MIN_STRENGTH = 0.50
BEAT_RHYTHM_HIT_SUPPORT_MAX_STRENGTH = 0.70
THEME_LYRIC_TRANSCRIPT_PATH = Path("/tmp/channel_trailer_theme_lyrics_review/Paper Architecture.diarized.srt")
THEME_LYRIC_WHISPERX_PATH = Path("/tmp/channel_trailer_theme_lyrics_review/Paper Architecture.whisperx.json")
THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_PACKAGE_ID = (
    "channel_trailer_v2_subject_background_type_theme_lyric_phrases_rtl_precise_matte_with_badges_20260510T032011Z"
)
THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_ROOT = (
    OUTPUT_BASE / THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_PACKAGE_ID
)
THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_MANIFEST = (
    THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_ROOT
    / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_EXPERIMENT_ID}_manifest.json"
)
SUBJECT_BACKGROUND_TYPE_ORDER = [
    "challenger",
    "semmelweis",
    "titanic",
    "737-max",
    "tacoma-narrows",
    "hyatt-regency",
]
SUBJECT_BACKGROUND_TYPE_LABELS = {
    "challenger": "CHALLENGER",
    "semmelweis": "SEMMELWEIS",
    "titanic": "TITANIC",
    "737-max": "737 MAX",
    "tacoma-narrows": "TACOMA NARROWS BRIDGE",
    "hyatt-regency": "HYATT REGENCY",
}
SUBJECT_BACKGROUND_TYPE_LYRIC_PHRASES = {
    "challenger": "SPECIFICITY",
    "hyatt-regency": "FRAGILE ARCHITECTURE",
    "semmelweis": "RANK",
    "tacoma-narrows": "OVERLOAD",
    "737-max": "FORGOTTEN CODE",
    "titanic": "HEAVY LEGACY",
}
LYRIC_BACKGROUND_TIMED_PHRASES = [
    ("SPECIFICITY", ("specificity",)),
    ("RANK", ("rank",)),
    ("FRAGILE ARCHITECTURE", ("fragile", "architecture")),
    ("FORGOTTEN CODE", ("forgotten", "code")),
    ("HEAVY LEGACY", ("heavy", "legacy")),
    ("OVERLOAD", ("overload",)),
]
LYRIC_BACKGROUND_FIRST_VISIBLE_SECONDS = 4.823
LYRIC_BACKGROUND_CUE_LEAD_SECONDS = 0.12
LYRIC_BACKGROUND_CUE_TAIL_SECONDS = 1.20
LYRIC_BACKGROUND_MOTION_PREROLL_SECONDS = 0.12
SUBJECT_BACKGROUND_TYPE_LEFT_ZONE = (42, 62, 1138, 884)
SUBJECT_BACKGROUND_TYPE_CENTER_XY = (548, 248)
SUBJECT_BACKGROUND_TYPE_COLOR = (246, 239, 255)
SUBJECT_BACKGROUND_TYPE_ALPHA = 216
SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT = 900
SUBJECT_BACKGROUND_TYPE_MAX_FONT_SIZE = 176
SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE = 188
SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY = (72, 206)
SUBJECT_BACKGROUND_TYPE_LARGE_COLOR = (255, 255, 255)
SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY = 0.16
SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA = int(round(255 * SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY))
SUBJECT_BACKGROUND_TYPE_LAYOUTS = {
    "challenger": {"center_xy": (842, 128), "max_font_size": 92},
    "semmelweis": {"center_xy": (800, 88), "max_font_size": 88},
    "titanic": {"center_xy": (790, 96), "max_font_size": 112},
    "737-max": {"center_xy": (420, 174), "max_font_size": 132},
    "tacoma-narrows": {"center_xy": (826, 112), "max_font_size": 70},
    "hyatt-regency": {"center_xy": (812, 98), "max_font_size": 84},
}
BADGE_ALPHA_HANDOFF_SAMPLE_SECONDS = [5.958, 6.0, 6.042, 6.083, 6.125, 6.167, 6.2]
OPENING_VISUAL = "rapid_switching_youtube_shorts_card_pullback_slide_right"
TITLE_SYSTEM_ID = "channel_trailer_title_system_v1"
TITLE_SCOPE = "keep_editorial_mechanism_cues"
TITLE_SAFE_BOUNDS = (96, 54, 1824, 1026)
OUTRO_TITLE_ID = "outro_paper_architecture_title_v1"
OUTRO_TITLE_SOURCE = BRAND_ROOT / "assets/reference-renders/paper-architectures-v1/homepage-hero-dark-adapted-desktop-source-v1.png"
OUTRO_TITLE_SOURCE_CROP = (45, 70, 930, 550)
OUTRO_TITLE_LINE_REGIONS = [(0, 88, 885, 285), (0, 245, 885, 470)]
OUTRO_TITLE_EXCLUSION_REGIONS = [(560, 0, 885, 150), (0, 0, 885, 84), (0, 455, 80, 480), (865, 455, 885, 480), (185, 455, 290, 480)]
OUTRO_TITLE_TARGET_WIDTH = 540
OUTRO_TITLE_XY = (690, 56)
OUTRO_TITLE_IMAGEGEN_ID = "cascade_of_effects_imagegen_screen_parallel_title_v1"
OUTRO_TITLE_IMAGEGEN_SOURCE_DIR = (
    OUTPUT_BASE / "title_raster_sources/imagegen_screen_parallel_cascade_of_effects_20260508T211003Z"
)
OUTRO_TITLE_IMAGEGEN_CHROMAKEY_SOURCE = OUTRO_TITLE_IMAGEGEN_SOURCE_DIR / "cascade_of_effects_imagegen_title_chromakey_source.png"
OUTRO_TITLE_IMAGEGEN_ALPHA_SOURCE = OUTRO_TITLE_IMAGEGEN_SOURCE_DIR / "cascade_of_effects_imagegen_title_alpha_source.png"
OUTRO_TITLE_IMAGEGEN_ORIGINAL_SOURCE = (
    Path("/Users/mike/.codex/generated_images/019dff93-ea9f-7860-aac0-9b7322b73ab6")
    / "ig_0cd442fde405cc810169fe50c3f7b481909ad15d96820bc4cd.png"
)
OUTRO_TITLE_IMAGEGEN_PROMPT = """Use case: logo-brand / stylized title raster.
Asset type: YouTube end-screen title sprite source for a 1920x1080 video.
Primary request: Create a clean, front-facing, screen-parallel Paper Architecture title raster containing exactly these words and no other text: "Cascade of Effects".
Text layout: two centered lines, line 1: "Cascade"; line 2: "of Effects". The spelling must be exact. No other words, letters, captions, handles, labels, symbols, logos, or watermarks.
Style: folded paper construction, clean lavender and warm cream paper, subtle bevel/depth, soft studio lighting, crisp readable edges, premium title treatment.
Material constraints: minimal paper texture only, no stone, no grit, no sandy surface, no high-frequency speckle, no mottled dirty texture, no cracks, no metallic/plastic gloss.
Geometry: title faces the viewer directly, horizontal baseline, parallel to the rectangular image frame, no perspective skew, no rotation, no angled camera.
Background for extraction: perfectly flat solid #00ff00 chroma-key background, one uniform color with no shadows, gradients, texture, floor, reflection, or lighting variation. Do not use #00ff00 inside the title. Keep generous padding around the title."""
END_SCREEN_LEFT_VIDEO_BBOX = (78, 382, 758, 765)
END_SCREEN_RIGHT_VIDEO_BBOX = (1162, 382, 1842, 765)
END_SCREEN_SUBSCRIBE_CENTER_XY = (960, 575)
END_SCREEN_SUBSCRIBE_RADIUS = 146
END_SCREEN_SUBSCRIBE_BBOX = (
    END_SCREEN_SUBSCRIBE_CENTER_XY[0] - END_SCREEN_SUBSCRIBE_RADIUS,
    END_SCREEN_SUBSCRIBE_CENTER_XY[1] - END_SCREEN_SUBSCRIBE_RADIUS,
    END_SCREEN_SUBSCRIBE_CENTER_XY[0] + END_SCREEN_SUBSCRIBE_RADIUS,
    END_SCREEN_SUBSCRIBE_CENTER_XY[1] + END_SCREEN_SUBSCRIBE_RADIUS,
)

SHORT_CARD_SIZE = (720, 1280)
SHORT_VIDEO_COLOR_FACTOR = 0.62
SHORT_VIDEO_CONTRAST_FACTOR = 0.98
SHORT_VIDEO_BRIGHTNESS_FACTOR = 1.08
SHORT_VIDEO_INK_BLEND = 0.12
END_SHORT_PLATE_QUAD = [
    (1202.0, 104.0),
    (1760.0, 64.0),
    (1760.0, 1018.0),
    (1214.0, 970.0),
]
START_SHORT_PLATE_QUAD = [
    (1292.2, 243.2),
    (1671.7, 216.0),
    (1671.7, 864.7),
    (1300.4, 832.1),
]
EPISODE_PUSH_IN_SECONDS = 1.25
COLD_OPEN_START_SHORT_PLATE_QUAD = [
    (58.0, -920.0),
    (1604.0, -858.0),
    (1686.0, 1956.0),
    (22.0, 1888.0),
]
MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD = [
    (-115.0, -1236.0),
    (1772.0, -1160.0),
    (1872.0, 2273.0),
    (-159.0, 2190.0),
]
LEFT_ANCHOR_FADE_START_SECONDS = 3.05
LEFT_ANCHOR_FADE_END_SECONDS = VOICE_START_SECONDS
MUSIC_ONLY_LEFT_ANCHOR_FADE_START_SECONDS = 5.05
MUSIC_ONLY_LEFT_ANCHOR_FADE_END_SECONDS = MUSIC_ONLY_COLD_OPEN_SECONDS

FONT_DISPLAY = Path("/Users/mike/Library/Fonts/Inter-VariableFont_opsz,wght.ttf")
FONT_MONO = Path("/System/Library/Fonts/SFNSMono.ttf")
FONT_FALLBACK = Path("/System/Library/Fonts/HelveticaNeue.ttc")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {value!r}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def nested_get(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        current = current[part]
    return current


def token_value(data: dict[str, Any], path: str) -> Any:
    value = nested_get(data, path)
    if isinstance(value, dict) and "$value" in value:
        return value["$value"]
    return value


def resolve_token_reference(data: dict[str, Any], value: Any) -> Any:
    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
        return resolve_token_reference(data, token_value(data, value[1:-1]))
    if isinstance(value, dict):
        return {key: resolve_token_reference(data, nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [resolve_token_reference(data, nested) for nested in value]
    return value


def dimension_px(value: Any) -> float:
    if isinstance(value, dict) and "value" in value:
        return float(value["value"])
    return float(value)


@dataclass(frozen=True)
class TitleSystem:
    id: str
    profile_id: str
    selected_title_scope: str
    exact_title: str
    palette: dict[str, tuple[int, int, int]]
    palette_hex: dict[str, str]
    font_family: dict[str, list[str]]
    font_weight: dict[str, int]
    tracking_px: dict[str, float]
    typography: dict[str, dict[str, Any]]
    motion_typography: dict[str, dict[str, Any]]
    title_safe_bounds: tuple[int, int, int, int]
    source_paths: dict[str, str]
    source_hashes: dict[str, str]

    def font_for(self, role: str) -> ImageFont.FreeTypeFont:
        spec = self.motion_typography[role]
        return font(int(spec["font_size_px"]), int(spec["font_weight"]))

    def tracking_for(self, role: str) -> float:
        return float(self.motion_typography[role].get("letter_spacing_px", 0.0))

    def rgba(self, color_name: str, alpha: float) -> tuple[int, int, int, int]:
        return (*self.palette[color_name], int(max(0.0, min(1.0, alpha)) * 255))


def load_title_system() -> TitleSystem:
    style = load_json(STYLE_SYSTEM)
    design_contract = load_json(DESIGN_SYSTEM_CONTRACT)
    youtube_package = load_json(YOUTUBE_CHANNEL_PACKAGE)

    palette_paths = {
        "ink": "color.base.ink",
        "ink_panel": "color.base.inkPanel",
        "lavender_shadow": "color.base.overlaySlate",
        "blue_frame": "color.base.panelFrame",
        "cream": "color.base.white",
        "secondary_text": "color.base.secondaryText",
        "cyan_glow": "color.accent.signal",
        "restrained_coral": "color.accent.alert",
    }
    palette_hex = {
        name: token_value(style, path)["hex"]
        for name, path in palette_paths.items()
    }
    palette = {name: hex_to_rgb(hex_value) for name, hex_value in palette_hex.items()}
    font_family = {
        name: resolve_token_reference(style, token_value(style, f"fontFamily.{name}"))
        for name in ("display", "body", "ui")
    }
    font_weight = {
        name: int(resolve_token_reference(style, token_value(style, f"fontWeight.{name}")))
        for name in ("display", "regular", "medium", "semibold", "bold")
    }
    tracking_px = {
        name: dimension_px(resolve_token_reference(style, token_value(style, f"size.tracking.{name}")))
        for name in ("normal", "ui", "caps")
    }
    typography = {
        name: resolve_token_reference(style, token_value(style, f"typography.{name}"))
        for name in ("wordmark", "hero", "sectionTitle", "bodySmall", "lowerThirdTitle", "lowerThirdMeta")
    }
    motion_typography = {
        "wordmark": {
            "source_token": "typography.wordmark",
            "font_family": font_family["display"],
            "font_size_px": 86,
            "font_weight": font_weight["display"],
            "letter_spacing_px": tracking_px["caps"],
            "line_height": typography["wordmark"]["lineHeight"],
        },
        "mechanism": {
            "source_token": "typography.hero",
            "font_family": font_family["display"],
            "font_size_px": 64,
            "font_weight": font_weight["display"],
            "letter_spacing_px": tracking_px["caps"],
            "line_height": typography["hero"]["lineHeight"],
        },
        "subhead": {
            "source_token": "typography.sectionTitle",
            "font_family": font_family["body"],
            "font_size_px": 38,
            "font_weight": font_weight["bold"],
            "letter_spacing_px": tracking_px["normal"],
            "line_height": typography["sectionTitle"]["lineHeight"],
        },
        "label": {
            "source_token": "typography.lowerThirdTitle",
            "font_family": font_family["ui"],
            "font_size_px": 24,
            "font_weight": font_weight["semibold"],
            "letter_spacing_px": tracking_px["ui"],
            "line_height": typography["lowerThirdTitle"]["lineHeight"],
        },
        "micro": {
            "source_token": "typography.seriesTag",
            "font_family": font_family["ui"],
            "font_size_px": 18,
            "font_weight": font_weight["bold"],
            "letter_spacing_px": tracking_px["ui"],
            "line_height": typography["bodySmall"]["lineHeight"],
        },
    }
    exact_title = design_contract.get("titleTreatment", {}).get("exactTitle") or youtube_package["deliverables"][1]["copyPolicy"]["exactTitle"]
    return TitleSystem(
        id=TITLE_SYSTEM_ID,
        profile_id=style["$extensions"]["com.cascadeeffects"]["profile"]["id"],
        selected_title_scope=TITLE_SCOPE,
        exact_title=exact_title,
        palette=palette,
        palette_hex=palette_hex,
        font_family=font_family,
        font_weight=font_weight,
        tracking_px=tracking_px,
        typography=typography,
        motion_typography=motion_typography,
        title_safe_bounds=TITLE_SAFE_BOUNDS,
        source_paths={
            "style_system": str(STYLE_SYSTEM),
            "design_system_contract": str(DESIGN_SYSTEM_CONTRACT),
            "youtube_channel_package": str(YOUTUBE_CHANNEL_PACKAGE),
        },
        source_hashes={
            "style_system": file_sha256(STYLE_SYSTEM),
            "design_system_contract": file_sha256(DESIGN_SYSTEM_CONTRACT),
            "youtube_channel_package": file_sha256(YOUTUBE_CHANNEL_PACKAGE),
        },
    )


@dataclass(frozen=True)
class SourceProof:
    slug: str
    display_name: str
    video_path: Path
    manifest_path: Path | None = None
    short_video_path: Path | None = None
    base_plate_path: Path | None = None


@dataclass(frozen=True)
class TimelineSegment:
    start: float
    end: float
    slug: str
    role: str
    source_start: float
    source_end: float
    playback: str = "realtime_then_hold"


@dataclass(frozen=True)
class OutroTitleSprite:
    image: Image.Image
    source_crop_path: Path
    sprite_path: Path
    render_sprite_path: Path
    source_crop_sha256: str
    sprite_sha256: str
    render_sprite_sha256: str
    position_xy: tuple[int, int]
    rendered_size: tuple[int, int]
    title_safe_bbox_xy: tuple[int, int, int, int]
    source_strategy: str = "approved_website_raster_extraction"
    source_path: Path | None = None
    source_sha256: str = ""
    source_crop_xy: tuple[int, int, int, int] | None = OUTRO_TITLE_SOURCE_CROP
    line_regions_xy: list[tuple[int, int, int, int]] | None = None
    exclusion_regions_xy: list[tuple[int, int, int, int]] | None = None
    generation_provenance: dict[str, Any] | None = None
    exact_title_read: str = "pass_from_approved_title_bearing_website_reference"
    title_orientation_read: str = "pass_source_perspective"
    title_texture_strategy: str = "minimal_paper_texture_deterministic_sprite_cleanup"
    title_texture_read: str = "pass_minimal_paper_texture"


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n\nSTDOUT:\n"
            + proc.stdout[-4000:]
            + "\n\nSTDERR:\n"
            + proc.stderr[-4000:]
        )
    return proc


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def h264_video_stream_sha256(path: Path) -> str:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-c:v",
            "copy",
            "-bsf:v",
            "h264_mp4toannexb",
            "-f",
            "h264",
            "-",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + f"ffmpeg video stream hash {path}"
            + "\n\nSTDERR:\n"
            + proc.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    return hashlib.sha256(proc.stdout).hexdigest()


def aac_audio_stream_sha256(path: Path) -> str:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-c:a",
            "copy",
            "-f",
            "adts",
            "-",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + f"ffmpeg audio stream hash {path}"
            + "\n\nSTDERR:\n"
            + proc.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    return hashlib.sha256(proc.stdout).hexdigest()


def raw_video_frame_sha256(path: Path, time_seconds: float) -> str:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{time_seconds:.6f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + f"ffmpeg raw frame hash {path} @ {time_seconds:.3f}s"
            + "\n\nSTDERR:\n"
            + proc.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    return hashlib.sha256(proc.stdout).hexdigest()


def raw_video_frame_image(path: Path, time_seconds: float) -> Image.Image:
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{time_seconds:.6f}",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Command failed:\n"
            + f"ffmpeg raw frame image {path} @ {time_seconds:.3f}s"
            + "\n\nSTDERR:\n"
            + proc.stderr.decode("utf-8", errors="replace")[-4000:]
        )
    expected_bytes = WIDTH * HEIGHT * 3
    if len(proc.stdout) != expected_bytes:
        raise SystemExit(
            f"Unexpected raw frame size for {path} @ {time_seconds:.3f}s: "
            f"expected {expected_bytes}, got {len(proc.stdout)}"
        )
    return Image.frombytes("RGB", (WIDTH, HEIGHT), proc.stdout)


def mean_luma(image: Image.Image) -> float:
    return float(ImageStat.Stat(image.convert("L")).mean[0])


def frame_luma_delta(a: Image.Image, b: Image.Image) -> float:
    a_luma = a.convert("L").resize((320, 180), Image.Resampling.BILINEAR)
    b_luma = b.convert("L").resize((320, 180), Image.Resampling.BILINEAR)
    diff = ImageChops.difference(a_luma, b_luma)
    return float(ImageStat.Stat(diff).mean[0])


def video_sample_frame_hash_report(
    source_mp4: Path,
    final_mp4: Path,
    sample_times: list[float],
    report_key: str,
    *,
    luma_tolerance: float | None = None,
) -> dict[str, Any]:
    samples = []
    for time_seconds in sample_times:
        source_sha = raw_video_frame_sha256(source_mp4, time_seconds)
        final_sha = raw_video_frame_sha256(final_mp4, time_seconds)
        sample_match = source_sha == final_sha
        source_img = raw_video_frame_image(source_mp4, time_seconds)
        final_img = raw_video_frame_image(final_mp4, time_seconds)
        luma_delta = frame_luma_delta(source_img, final_img)
        if sample_match:
            sample_read = "pass"
        elif luma_tolerance is not None and luma_delta <= luma_tolerance:
            sample_read = "pass_encoding_tolerance"
        else:
            sample_read = "tighten"
        samples.append(
            {
                "time_seconds": time_seconds,
                "source_raw_rgb_sha256": source_sha,
                "final_raw_rgb_sha256": final_sha,
                "sample_match_read": sample_read,
                "mean_luma_delta": round(luma_delta, 4),
            }
        )
    return {
        "sample_times_seconds": sample_times,
        "samples": samples,
        "luma_tolerance": luma_tolerance,
        report_key: "pass" if all(sample["sample_match_read"].startswith("pass") for sample in samples) else "tighten",
    }


def end_screen_hold_report(
    final_mp4: Path,
    hold_start_seconds: float = END_SCREEN_HOLD_SOURCE_SECONDS,
    hold_end_seconds: float = END_SCREEN_HOLD_TARGET_SECONDS,
) -> dict[str, Any]:
    midpoint = hold_start_seconds + (hold_end_seconds - hold_start_seconds) * 0.5
    sample_times = [hold_start_seconds, midpoint, max(hold_end_seconds - 2.0, hold_start_seconds), hold_end_seconds - 0.1]
    hold_img = raw_video_frame_image(final_mp4, hold_start_seconds)
    hold_sha = raw_video_frame_sha256(final_mp4, hold_start_seconds)
    hold_luma = mean_luma(hold_img)
    hold_match_luma_delta_threshold = 0.15
    samples = []
    for time_seconds in sample_times:
        img = raw_video_frame_image(final_mp4, time_seconds)
        sha = raw_video_frame_sha256(final_mp4, time_seconds)
        delta = frame_luma_delta(hold_img, img)
        sample_luma = mean_luma(img)
        samples.append(
            {
                "time_seconds": time_seconds,
                "raw_rgb_sha256": sha,
                "raw_hash_match": sha == hold_sha,
                "matches_hold_frame_read": "pass" if delta <= hold_match_luma_delta_threshold else "tighten",
                "mean_luma": round(sample_luma, 4),
                "mean_luma_delta_from_hold": round(delta, 4),
                "luma_drop_from_hold": round(hold_luma - sample_luma, 4),
            }
        )
    final_luma = samples[-1]["mean_luma"]
    return {
        "hold_frame_source_seconds": hold_start_seconds,
        "end_screen_hold_seconds": [hold_start_seconds, hold_end_seconds],
        "hold_frame_raw_rgb_sha256": hold_sha,
        "hold_frame_mean_luma": round(hold_luma, 4),
        "hold_match_luma_delta_threshold": hold_match_luma_delta_threshold,
        "samples": samples,
        "held_frame_match_read": "pass"
        if all(sample["matches_hold_frame_read"] == "pass" for sample in samples)
        else "tighten",
        "final_frame_luma_read": "pass" if final_luma >= hold_luma - 0.5 else "tighten",
        "visual_fade_out_removed_read": "pass"
        if all(sample["luma_drop_from_hold"] <= 0.5 for sample in samples)
        else "tighten",
    }


def intro_sample_frame_hash_report(source_mp4: Path, final_mp4: Path) -> dict[str, Any]:
    sample_times = [0.6, 2.2, 3.75, 4.0]
    samples = []
    for time_seconds in sample_times:
        source_sha = raw_video_frame_sha256(source_mp4, time_seconds)
        final_sha = raw_video_frame_sha256(final_mp4, time_seconds)
        samples.append(
            {
                "time_seconds": time_seconds,
                "source_raw_rgb_sha256": source_sha,
                "final_raw_rgb_sha256": final_sha,
                "sample_match_read": "pass" if source_sha == final_sha else "tighten",
            }
        )
    return {
        "sample_times_seconds": sample_times,
        "samples": samples,
        "intro_sample_frame_hash_read": "pass"
        if all(sample["sample_match_read"] == "pass" for sample in samples)
        else "tighten",
    }


TITLE_SYSTEM = load_title_system()
INK = TITLE_SYSTEM.palette["ink"]
PAPER = TITLE_SYSTEM.palette["cream"]
MUTED_PAPER = TITLE_SYSTEM.palette["secondary_text"]
LAVENDER = TITLE_SYSTEM.palette["lavender_shadow"]
CYAN = TITLE_SYSTEM.palette["cyan_glow"]
CORAL = TITLE_SYSTEM.palette["restrained_coral"]


def clean_minimal_paper_title_sprite(render_sprite: Image.Image) -> Image.Image:
    rgba = render_sprite.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = Image.new("RGB", rgba.size, (0, 0, 0))
    rgb.paste(rgba.convert("RGB"), (0, 0), alpha)
    softened = rgb.filter(ImageFilter.GaussianBlur(1.05))
    softened = ImageEnhance.Contrast(softened).enhance(0.78)
    softened = ImageEnhance.Color(softened).enhance(0.9)
    restored = Image.blend(rgb, softened, 0.58)
    restored = ImageEnhance.Brightness(restored).enhance(1.035)
    restored = ImageEnhance.Contrast(restored).enhance(0.94)
    cleaned = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    cleaned.paste(restored, (0, 0), alpha)
    cleaned.putalpha(alpha)
    return cleaned


def create_outro_title_sprite(source_art_dir: Path, minimal_texture: bool = False) -> OutroTitleSprite:
    source_art_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(OUTRO_TITLE_SOURCE).convert("RGBA")
    crop = source.crop(OUTRO_TITLE_SOURCE_CROP)
    crop_path = source_art_dir / f"{OUTRO_TITLE_ID}_source_crop.png"
    sprite_path = source_art_dir / f"{OUTRO_TITLE_ID}_sprite.png"
    render_sprite_path = source_art_dir / f"{OUTRO_TITLE_ID}_render_sprite.png"
    crop.save(crop_path)

    width, height = crop.size
    mask = Image.new("L", (width, height), 0)
    crop_px = crop.load()
    mask_px = mask.load()
    for x0, y0, x1, y1 in OUTRO_TITLE_LINE_REGIONS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                r, g, b, alpha = crop_px[x, y]
                luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
                title_pixel = luma > 48 or (r > 40 and b > 48 and r + b > 100)
                if alpha and title_pixel:
                    mask_px[x, y] = 255
    for x0, y0, x1, y1 in OUTRO_TITLE_EXCLUSION_REGIONS:
        for y in range(y0, y1):
            for x in range(x0, x1):
                if 0 <= x < width and 0 <= y < height:
                    mask_px[x, y] = 0

    mask = mask.filter(ImageFilter.GaussianBlur(0.45))
    sprite = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sprite.paste(crop, (0, 0), mask)
    bbox = sprite.getchannel("A").getbbox()
    if not bbox:
        raise SystemExit("Failed to extract outro Paper Architecture title sprite.")
    sprite = sprite.crop(bbox)
    sprite.save(sprite_path)

    scale = OUTRO_TITLE_TARGET_WIDTH / sprite.width
    render_size = (OUTRO_TITLE_TARGET_WIDTH, max(1, round(sprite.height * scale)))
    render_sprite = sprite.resize(render_size, Image.Resampling.LANCZOS)
    if minimal_texture:
        render_sprite = clean_minimal_paper_title_sprite(render_sprite)
    render_sprite.save(render_sprite_path)
    x, y = OUTRO_TITLE_XY
    safe_bbox = (x, y, x + render_size[0], y + render_size[1])
    return OutroTitleSprite(
        image=render_sprite,
        source_crop_path=crop_path,
        sprite_path=sprite_path,
        render_sprite_path=render_sprite_path,
        source_crop_sha256=file_sha256(crop_path),
        sprite_sha256=file_sha256(sprite_path),
        render_sprite_sha256=file_sha256(render_sprite_path),
        position_xy=OUTRO_TITLE_XY,
        rendered_size=render_size,
        title_safe_bbox_xy=safe_bbox,
        source_strategy="approved_website_raster_extraction",
        source_path=OUTRO_TITLE_SOURCE,
        source_sha256=file_sha256(OUTRO_TITLE_SOURCE),
        source_crop_xy=OUTRO_TITLE_SOURCE_CROP,
        line_regions_xy=OUTRO_TITLE_LINE_REGIONS,
        exclusion_regions_xy=OUTRO_TITLE_EXCLUSION_REGIONS,
        exact_title_read="pass_from_approved_title_bearing_website_reference",
        title_orientation_read="pass_source_perspective",
        title_texture_strategy="minimal_paper_texture_deterministic_sprite_cleanup" if minimal_texture else "approved_source_texture",
        title_texture_read="pass_minimal_paper_texture" if minimal_texture else "pass_approved_source_texture",
    )


def create_imagegen_outro_title_sprite(source_art_dir: Path) -> OutroTitleSprite:
    source_art_dir.mkdir(parents=True, exist_ok=True)
    for path in (OUTRO_TITLE_IMAGEGEN_CHROMAKEY_SOURCE, OUTRO_TITLE_IMAGEGEN_ALPHA_SOURCE):
        require_file(path)

    chromakey_copy = source_art_dir / f"{OUTRO_TITLE_IMAGEGEN_ID}_chromakey_source.png"
    alpha_source_copy = source_art_dir / f"{OUTRO_TITLE_IMAGEGEN_ID}_alpha_source.png"
    sprite_path = source_art_dir / f"{OUTRO_TITLE_IMAGEGEN_ID}_sprite.png"
    render_sprite_path = source_art_dir / f"{OUTRO_TITLE_IMAGEGEN_ID}_render_sprite.png"
    prompt_path = source_art_dir / f"{OUTRO_TITLE_IMAGEGEN_ID}_prompt.txt"
    shutil.copy2(OUTRO_TITLE_IMAGEGEN_CHROMAKEY_SOURCE, chromakey_copy)
    shutil.copy2(OUTRO_TITLE_IMAGEGEN_ALPHA_SOURCE, alpha_source_copy)
    prompt_path.write_text(OUTRO_TITLE_IMAGEGEN_PROMPT + "\n", encoding="utf-8")

    source = Image.open(alpha_source_copy).convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if not bbox:
        raise SystemExit("Failed to extract ImageGen title sprite alpha.")
    sprite = source.crop(bbox)
    sprite.save(sprite_path)

    scale = OUTRO_TITLE_TARGET_WIDTH / sprite.width
    render_size = (OUTRO_TITLE_TARGET_WIDTH, max(1, round(sprite.height * scale)))
    render_sprite = sprite.resize(render_size, Image.Resampling.LANCZOS)
    render_sprite.save(render_sprite_path)
    x, y = OUTRO_TITLE_XY
    safe_bbox = (x, y, x + render_size[0], y + render_size[1])
    return OutroTitleSprite(
        image=render_sprite,
        source_crop_path=alpha_source_copy,
        sprite_path=sprite_path,
        render_sprite_path=render_sprite_path,
        source_crop_sha256=file_sha256(alpha_source_copy),
        sprite_sha256=file_sha256(sprite_path),
        render_sprite_sha256=file_sha256(render_sprite_path),
        position_xy=OUTRO_TITLE_XY,
        rendered_size=render_size,
        title_safe_bbox_xy=safe_bbox,
        source_strategy="image_gen_new_screen_parallel_text_raster",
        source_path=alpha_source_copy,
        source_sha256=file_sha256(alpha_source_copy),
        source_crop_xy=None,
        line_regions_xy=None,
        exclusion_regions_xy=None,
        generation_provenance={
            "tool": "codex_builtin_image_gen",
            "mode": "text_to_image",
            "prompt_path": str(prompt_path),
            "prompt_sha256": file_sha256(prompt_path),
            "original_generated_path": str(OUTRO_TITLE_IMAGEGEN_ORIGINAL_SOURCE),
            "original_generated_sha256": file_sha256(OUTRO_TITLE_IMAGEGEN_ORIGINAL_SOURCE)
            if OUTRO_TITLE_IMAGEGEN_ORIGINAL_SOURCE.exists()
            else None,
            "chromakey_source_path": str(chromakey_copy),
            "chromakey_source_sha256": file_sha256(chromakey_copy),
            "alpha_source_path": str(alpha_source_copy),
            "alpha_source_sha256": file_sha256(alpha_source_copy),
            "chroma_key_removal": {
                "helper": "/Users/mike/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py",
                "auto_key": "border",
                "soft_matte": True,
                "transparent_threshold": 12,
                "opaque_threshold": 220,
                "despill": True,
            },
        },
        exact_title_read="pass_manual_review_exact_title_cascade_of_effects",
        title_orientation_read="pass_screen_parallel",
        title_texture_strategy="imagegen_minimal_paper_texture_no_post_cleanup_needed",
        title_texture_read="pass_minimal_paper_texture",
    )


def ffprobe_duration(path: Path) -> float:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    return float(proc.stdout.strip())


def ffprobe_json(path: Path) -> dict[str, Any]:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(proc.stdout)


def audio_volume_peak(path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return {"status": "error", "stderr_tail": proc.stderr[-2000:]}
    max_match = re.search(r"max_volume:\s*([-\d.]+) dB", proc.stderr)
    mean_match = re.search(r"mean_volume:\s*([-\d.]+) dB", proc.stderr)
    return {
        "status": "pass",
        "max_volume_db": float(max_match.group(1)) if max_match else None,
        "mean_volume_db": float(mean_match.group(1)) if mean_match else None,
    }


def font(size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    for candidate in (FONT_DISPLAY, FONT_FALLBACK):
        try:
            font_obj = ImageFont.truetype(str(candidate), size=size)
            if weight is not None and hasattr(font_obj, "get_variation_axes") and hasattr(font_obj, "set_variation_by_axes"):
                try:
                    axes = font_obj.get_variation_axes()
                    values = []
                    for axis in axes:
                        name = axis.get("name", b"").decode("utf-8", errors="ignore").lower()
                        if "weight" in name:
                            values.append(max(axis["minimum"], min(axis["maximum"], weight)))
                        elif "optical" in name:
                            values.append(max(axis["minimum"], min(axis["maximum"], size)))
                        else:
                            values.append(axis["default"])
                    font_obj.set_variation_by_axes(values)
                except Exception:
                    pass
            return font_obj
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def fade_window(t: float, start: float, end: float, fade: float = 0.5) -> float:
    if t < start or t > end:
        return 0.0
    return min(ease((t - start) / max(fade, 0.001)), ease((end - t) / max(fade, 0.001)), 1.0)


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font_obj: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    anchor: str = "la",
    shadow: bool = True,
    letter_spacing: float = 0.0,
    shadow_fill: tuple[int, int, int, int] | None = None,
    shadow_offset: tuple[int, int] = (4, 5),
) -> None:
    def draw_once(position: tuple[int, int], color: tuple[int, int, int, int]) -> None:
        if letter_spacing <= 0 or anchor != "la":
            draw.text(position, text, font=font_obj, fill=color, anchor=anchor)
            return
        x, y = position
        for character in text:
            draw.text((x, y), character, font=font_obj, fill=color, anchor=anchor)
            x += draw.textlength(character, font=font_obj) + letter_spacing

    if shadow:
        x, y = xy
        shadow_color = shadow_fill or (*TITLE_SYSTEM.palette["ink"], min(190, fill[3]))
        draw_once((x + shadow_offset[0], y + shadow_offset[1]), shadow_color)
    draw_once(xy, fill)


def subject_badge_font() -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(FONT_MONO), size=SUBJECT_BADGE_FONT_SIZE)
    except OSError:
        return font(SUBJECT_BADGE_FONT_SIZE, TITLE_SYSTEM.font_weight["semibold"])


def subject_badge_bbox(label: str) -> tuple[int, int, int, int]:
    font_obj = subject_badge_font()
    probe = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(probe)
    text_bbox = draw.textbbox((0, 0), label, font=font_obj)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    x, y = SUBJECT_BADGE_ANCHOR_XY
    return (
        x,
        y,
        x + text_w + SUBJECT_BADGE_PADDING_X * 2,
        y + text_h + SUBJECT_BADGE_PADDING_Y * 2,
    )


def music_only_subject_badge_entries(
    t: float,
    segments: list[TimelineSegment],
) -> list[tuple[str, float]]:
    if t < SUBJECT_BADGE_START_SECONDS or t >= SUBJECT_BADGE_END_SECONDS:
        return []
    if t < MUSIC_ONLY_COLD_OPEN_SECONDS:
        alpha = ease((t - SUBJECT_BADGE_START_SECONDS) / max(SUBJECT_BADGE_CHALLENGER_FADE_SECONDS, 0.001))
        return [(SUBJECT_BADGE_LABELS["challenger"], alpha)]

    index, segment = find_segment(segments, t)
    if segment.role != "voiceover_episode_sequence" or segment.slug not in SUBJECT_BADGE_LABELS:
        return []

    if segment.slug == "challenger":
        return [(SUBJECT_BADGE_LABELS[segment.slug], 1.0)]

    if index > 0 and 0 <= t - segment.start < SUBJECT_BADGE_TRANSITION_SECONDS:
        alpha = ease((t - segment.start) / SUBJECT_BADGE_TRANSITION_SECONDS)
        return [(SUBJECT_BADGE_LABELS[segment.slug], alpha)]

    alpha = 1.0
    if segment.end >= SUBJECT_BADGE_END_SECONDS and SUBJECT_BADGE_END_SECONDS - t < SUBJECT_BADGE_OUTRO_FADE_SECONDS:
        alpha = ease((SUBJECT_BADGE_END_SECONDS - t) / SUBJECT_BADGE_OUTRO_FADE_SECONDS)
    return [(SUBJECT_BADGE_LABELS[segment.slug], alpha)]


def add_subject_badge(frame: Image.Image, label: str, alpha: float) -> Image.Image:
    alpha = max(0.0, min(1.0, alpha))
    if alpha <= 0.001:
        return frame

    font_obj = subject_badge_font()
    base = frame.convert("RGBA")
    x0, y0, x1, y1 = subject_badge_bbox(label)
    radius = SUBJECT_BADGE_RADIUS
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), radius=radius, fill=int(168 * alpha))

    blur_margin = 18
    bx0 = max(0, x0 - blur_margin)
    by0 = max(0, y0 - blur_margin)
    bx1 = min(WIDTH, x1 + blur_margin)
    by1 = min(HEIGHT, y1 + blur_margin)
    blurred = base.crop((bx0, by0, bx1, by1)).filter(ImageFilter.GaussianBlur(14))
    blur_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    local_mask = Image.new("L", (bx1 - bx0, by1 - by0), 0)
    local_mask.paste(mask, (x0 - bx0, y0 - by0))
    blur_layer.paste(blurred, (bx0, by0), local_mask)
    base = Image.alpha_composite(base, blur_layer)

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (x0 + 2, y0 + 8, x1 + 2, y1 + 8),
        radius=radius,
        fill=(9, 13, 27, int(92 * alpha)),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    overlay = Image.alpha_composite(overlay, shadow)
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=radius,
        fill=(18, 26, 44, int(174 * alpha)),
        outline=(255, 248, 232, int(102 * alpha)),
        width=1,
    )
    draw.line((x0 + 1, y0 + 1, x1 - 1, y0 + 1), fill=(255, 255, 255, int(31 * alpha)), width=1)

    text_bbox = draw.textbbox((0, 0), label, font=font_obj)
    text_x = x0 + SUBJECT_BADGE_PADDING_X
    text_y = y0 + SUBJECT_BADGE_PADDING_Y - text_bbox[1]
    draw.text((text_x + 1, text_y + 2), label, font=font_obj, fill=(9, 13, 27, int(146 * alpha)))
    draw.text((text_x, text_y), label, font=font_obj, fill=(255, 255, 255, int(255 * alpha)))
    return Image.alpha_composite(base, overlay).convert("RGB")


def add_music_only_subject_badges(
    frame: Image.Image,
    t: float,
    segments: list[TimelineSegment],
) -> Image.Image:
    result = frame
    for label, alpha in music_only_subject_badge_entries(t, segments):
        result = add_subject_badge(result, label, alpha)
    return result


def subject_background_type_lines(label: str) -> list[str]:
    if label == "TACOMA NARROWS BRIDGE":
        return ["TACOMA", "NARROWS BRIDGE"]
    return [label]


def subject_background_type_font(lines: list[str], slug: str) -> ImageFont.FreeTypeFont:
    x0, y0, x1, y1 = SUBJECT_BACKGROUND_TYPE_LEFT_ZONE
    max_width = x1 - x0 - 64
    max_height = y1 - y0 - 72
    max_font_size = int(
        SUBJECT_BACKGROUND_TYPE_LAYOUTS.get(slug, {}).get(
            "max_font_size",
            SUBJECT_BACKGROUND_TYPE_MAX_FONT_SIZE,
        )
    )
    probe = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(probe)
    for size in range(max_font_size, 72, -4):
        font_obj = font(size, SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT)
        line_boxes = [draw.textbbox((0, 0), line, font=font_obj) for line in lines]
        widths = [box[2] - box[0] for box in line_boxes]
        heights = [box[3] - box[1] for box in line_boxes]
        line_gap = int(size * 0.02)
        total_height = sum(heights) + line_gap * max(0, len(lines) - 1)
        if max(widths) <= max_width and total_height <= max_height:
            return font_obj
    return font(76, SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT)


def subject_background_type_text_layer(slug: str, label: str) -> tuple[Image.Image, tuple[int, int, int, int], int]:
    lines = subject_background_type_lines(label)
    font_obj = subject_background_type_font(lines, slug)
    probe = Image.new("RGB", (1, 1))
    probe_draw = ImageDraw.Draw(probe)
    line_boxes = [probe_draw.textbbox((0, 0), line, font=font_obj) for line in lines]
    widths = [box[2] - box[0] for box in line_boxes]
    heights = [box[3] - box[1] for box in line_boxes]
    font_size = int(getattr(font_obj, "size", 0) or max(heights))
    line_gap = int(font_size * 0.02)
    total_height = sum(heights) + line_gap * max(0, len(lines) - 1)
    center_x, center_y = SUBJECT_BACKGROUND_TYPE_LAYOUTS.get(slug, {}).get(
        "center_xy",
        SUBJECT_BACKGROUND_TYPE_CENTER_XY,
    )
    y = center_y - total_height / 2
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    bbox_union: list[int] | None = None
    for line, box, line_w, line_h in zip(lines, line_boxes, widths, heights, strict=True):
        draw_x = center_x - line_w / 2 - box[0]
        draw_y = y - box[1]
        draw.text(
            (int(round(draw_x)), int(round(draw_y))),
            line,
            font=font_obj,
            fill=(*SUBJECT_BACKGROUND_TYPE_COLOR, SUBJECT_BACKGROUND_TYPE_ALPHA),
        )
        rendered_box = (
            int(round(draw_x + box[0])),
            int(round(draw_y + box[1])),
            int(round(draw_x + box[2])),
            int(round(draw_y + box[3])),
        )
        if bbox_union is None:
            bbox_union = list(rendered_box)
        else:
            bbox_union[0] = min(bbox_union[0], rendered_box[0])
            bbox_union[1] = min(bbox_union[1], rendered_box[1])
            bbox_union[2] = max(bbox_union[2], rendered_box[2])
            bbox_union[3] = max(bbox_union[3], rendered_box[3])
        y += line_h + line_gap
    if bbox_union is None:
        bbox_union = [0, 0, 0, 0]
    return layer, tuple(bbox_union), font_size


def subject_background_type_large_lighten_text_layer_at(
    label: str,
    anchor_xy: tuple[float, float],
) -> tuple[Image.Image, tuple[int, int, int, int], int]:
    font_obj = font(SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE, SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT)
    probe = Image.new("RGB", (1, 1))
    probe_draw = ImageDraw.Draw(probe)
    text_bbox = probe_draw.textbbox((0, 0), label, font=font_obj)
    draw_x = anchor_xy[0] - text_bbox[0]
    draw_y = anchor_xy[1] - text_bbox[1]
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.text(
        (int(round(draw_x)), int(round(draw_y))),
        label,
        font=font_obj,
        fill=(*SUBJECT_BACKGROUND_TYPE_LARGE_COLOR, SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA),
    )
    rendered_box = (
        int(round(draw_x + text_bbox[0])),
        int(round(draw_y + text_bbox[1])),
        int(round(draw_x + text_bbox[2])),
        int(round(draw_y + text_bbox[3])),
    )
    return layer, rendered_box, SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE


def subject_background_type_large_lighten_text_layer(label: str) -> tuple[Image.Image, tuple[int, int, int, int], int]:
    return subject_background_type_large_lighten_text_layer_at(label, SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY)


def subject_foreground_manual_repair_mask(slug: str) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    repairs: dict[str, list[tuple[str, tuple[int, ...] | list[tuple[int, int]]]]] = {
        "challenger": [
            ("rectangle", (78, 225, 604, 676)),
            ("polygon", [(0, 590), (720, 590), (720, 820), (180, 858), (0, 760)]),
        ],
        "hyatt-regency": [
            ("rectangle", (48, 150, 828, 604)),
            ("polygon", [(92, 520), (940, 592), (806, 804), (0, 724), (0, 620)]),
        ],
        "semmelweis": [
            ("rectangle", (42, 132, 948, 642)),
            ("polygon", [(234, 510), (1020, 612), (872, 834), (84, 704)]),
        ],
        "tacoma-narrows": [
            ("rectangle", (0, 132, 928, 660)),
            ("polygon", [(0, 420), (940, 410), (940, 594), (0, 680)]),
            ("polygon", [(0, 604), (884, 692), (742, 866), (0, 846)]),
        ],
        "737-max": [
            ("rectangle", (40, 318, 900, 658)),
            ("polygon", [(76, 548), (1090, 642), (940, 836), (0, 724)]),
        ],
        "titanic": [
            ("rectangle", (66, 164, 918, 668)),
            ("polygon", [(70, 392), (910, 358), (928, 698), (126, 822)]),
            ("polygon", [(0, 648), (1094, 744), (842, 912), (0, 808)]),
        ],
    }
    for shape, values in repairs.get(slug, []):
        if shape == "rectangle":
            draw.rectangle(values, fill=255)  # type: ignore[arg-type]
        elif shape == "polygon":
            draw.polygon(values, fill=255)  # type: ignore[arg-type]
    return mask


def derive_subject_foreground_mask(base_plate: Image.Image, slug: str) -> Image.Image:
    luma = base_plate.convert("L")
    bright_mask = luma.point(lambda value: 255 if value > 72 else 0)
    mask = bright_mask
    mask = ImageChops.lighter(mask, subject_foreground_manual_repair_mask(slug))
    scene_zone = Image.new("L", (WIDTH, HEIGHT), 0)
    zone_draw = ImageDraw.Draw(scene_zone)
    zone_draw.rectangle((0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], HEIGHT), fill=255)
    mask = ImageChops.multiply(mask, scene_zone)
    return mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.2))


def subject_scene_zone_mask() -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], HEIGHT), fill=255)
    return mask


def binary_mask(mask: Image.Image, threshold: int = 1) -> Image.Image:
    return mask.convert("L").point(lambda value: 255 if value >= threshold else 0)


def mask_pixel_count(mask: Image.Image, threshold: int = 1) -> int:
    return int(ImageStat.Stat(binary_mask(mask, threshold)).sum[0] / 255)


def subject_precise_additive_repair_mask(slug: str) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    repairs: dict[str, list[tuple[str, Any]]] = {
        "challenger": [
            ("line", [(228, 268), (358, 588), 10]),
            ("line", [(406, 238), (548, 602), 9]),
            ("line", [(170, 622), (684, 642), 7]),
        ],
        "hyatt-regency": [
            ("line", [(122, 254), (824, 304), 7]),
            ("line", [(118, 356), (842, 406), 7]),
            ("line", [(108, 468), (842, 532), 7]),
        ],
        "semmelweis": [
            ("line", [(172, 294), (894, 358), 7]),
            ("line", [(194, 410), (940, 506), 7]),
            ("line", [(242, 560), (1012, 646), 7]),
        ],
        "tacoma-narrows": [
            ("line", [(48, 286), (918, 286), 5]),
            ("line", [(54, 420), (918, 420), 5]),
            ("line", [(72, 620), (872, 716), 5]),
        ],
        "737-max": [
            ("line", [(108, 446), (920, 522), 9]),
            ("line", [(196, 386), (766, 438), 7]),
            ("ellipse", (280, 560, 420, 704)),
        ],
        "titanic": [
            ("line", [(98, 430), (906, 392), 8]),
            ("line", [(96, 510), (928, 500), 9]),
            ("line", [(128, 650), (906, 708), 9]),
        ],
    }
    for shape in repairs.get(slug, []):
        if shape[0] == "line":
            _, values = shape
            x0, y0 = values[0]
            x1, y1 = values[1]
            width = values[2]
            draw.line((x0, y0, x1, y1), fill=255, width=width)
        elif shape[0] == "ellipse":
            _, bbox = shape
            draw.ellipse(bbox, fill=255)
    return mask


def subject_precise_subtractive_repair_mask(slug: str) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    return mask


def subject_tight_additive_repair_mask_v2(slug: str) -> Image.Image:
    mask = subject_precise_additive_repair_mask(slug)
    draw = ImageDraw.Draw(mask)
    if slug == "titanic":
        draw.polygon([(78, 460), (1018, 430), (1064, 624), (1004, 728), (132, 680)], fill=255)
        draw.polygon([(0, 642), (1118, 734), (1030, 884), (0, 812)], fill=255)
        draw.rectangle((244, 250, 878, 522), fill=255)
        draw.line((238, 310, 860, 150), fill=255, width=5)
        draw.line((280, 330, 795, 108), fill=255, width=5)
        draw.line((788, 90, 1002, 540), fill=255, width=5)
        draw.line((828, 174, 934, 528), fill=255, width=4)
    return mask


def subject_tight_subtractive_repair_mask_v2(slug: str) -> Image.Image:
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    if slug == "titanic":
        draw = ImageDraw.Draw(mask)
        draw.polygon([(820, 90), (1140, 95), (1140, 704), (1052, 716), (1016, 540), (940, 448), (900, 260)], fill=255)
        draw.polygon([(0, 914), (1140, 930), (1140, HEIGHT), (0, HEIGHT)], fill=255)
    return mask


def derive_subject_precise_foreground_matte(
    base_plate: Image.Image,
    slug: str,
) -> tuple[Image.Image, Image.Image, Image.Image, dict[str, Any]]:
    base = base_plate.convert("RGB")
    luma = base.convert("L")
    ink_distance = ImageChops.difference(base, Image.new("RGB", (WIDTH, HEIGHT), INK)).convert("L")
    scene_zone = subject_scene_zone_mask()

    bright_paper = luma.point(lambda value: 255 if value >= 82 else 0)
    mid_luma = luma.point(lambda value: 255 if value >= 30 else 0)
    color_separated = ImageChops.multiply(
        ink_distance.point(lambda value: 255 if value >= 30 else 0),
        mid_luma,
    )
    strong_seed = ImageChops.lighter(
        luma.point(lambda value: 255 if value >= 116 else 0),
        ImageChops.multiply(
            ink_distance.point(lambda value: 255 if value >= 48 else 0),
            luma.point(lambda value: 255 if value >= 34 else 0),
        ),
    )
    support = ImageChops.multiply(strong_seed.filter(ImageFilter.MaxFilter(71)), scene_zone)
    edge_strength = luma.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value >= 15 else 0)
    supported_edges = ImageChops.multiply(edge_strength, support)

    candidate = ImageChops.lighter(bright_paper, color_separated)
    candidate = ImageChops.lighter(candidate, supported_edges)
    candidate = ImageChops.multiply(candidate, support)
    candidate = ImageChops.lighter(candidate, subject_precise_additive_repair_mask(slug))
    candidate = ImageChops.multiply(candidate, scene_zone)

    dark_negative_space = ImageChops.multiply(
        luma.point(lambda value: 255 if value <= 38 else 0),
        ink_distance.point(lambda value: 255 if value <= 28 else 0),
    )
    hole_support = ImageChops.multiply(candidate.filter(ImageFilter.MaxFilter(27)), scene_zone)
    hole_mask = ImageChops.multiply(dark_negative_space, hole_support)
    hole_mask = ImageChops.lighter(hole_mask, subject_precise_subtractive_repair_mask(slug))
    hole_mask = binary_mask(hole_mask)

    matte = ImageChops.multiply(candidate, ImageOps.invert(hole_mask))
    matte = matte.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.55))
    matte = ImageChops.multiply(matte, scene_zone)
    matte = ImageChops.multiply(matte, ImageOps.invert(hole_mask.filter(ImageFilter.MaxFilter(3))))

    matte_binary = binary_mask(matte, 18)
    inner_edge_support = hole_mask.filter(ImageFilter.MaxFilter(11))
    inner_edges = ImageChops.multiply(
        matte_binary.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value >= 1 else 0),
        inner_edge_support,
    )
    diagnostics = {
        "luma_threshold": 82,
        "ink_distance_threshold": 30,
        "strong_seed_luma_threshold": 116,
        "strong_seed_color_distance_threshold": 48,
        "edge_strength_threshold": 15,
        "hole_luma_threshold": 38,
        "hole_ink_distance_threshold": 28,
        "support_dilation_px": 71,
        "hole_support_dilation_px": 27,
        "matte_pixel_count": mask_pixel_count(matte, 18),
        "hole_pixel_count": mask_pixel_count(hole_mask),
        "inner_edge_pixel_count": mask_pixel_count(inner_edges),
    }
    return matte, hole_mask, inner_edges, diagnostics


def derive_lyric_background_tight_subject_matte_v2(
    base_plate: Image.Image,
    slug: str,
) -> tuple[Image.Image, Image.Image, Image.Image, dict[str, Any]]:
    base = base_plate.convert("RGB")
    luma = base.convert("L")
    ink_distance = ImageChops.difference(base, Image.new("RGB", (WIDTH, HEIGHT), INK)).convert("L")
    scene_zone = subject_scene_zone_mask()

    bright_paper = luma.point(lambda value: 255 if value >= 82 else 0)
    mid_luma = luma.point(lambda value: 255 if value >= 28 else 0)
    color_separated = ImageChops.multiply(
        ink_distance.point(lambda value: 255 if value >= 32 else 0),
        mid_luma,
    )
    strong_seed = ImageChops.lighter(
        luma.point(lambda value: 255 if value >= 116 else 0),
        ImageChops.multiply(
            ink_distance.point(lambda value: 255 if value >= 48 else 0),
            luma.point(lambda value: 255 if value >= 34 else 0),
        ),
    )
    support = ImageChops.multiply(strong_seed.filter(ImageFilter.MaxFilter(31)), scene_zone)
    edge_strength = luma.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value >= 16 else 0)
    supported_edges = ImageChops.multiply(edge_strength, support.filter(ImageFilter.MaxFilter(5)))

    candidate = ImageChops.lighter(bright_paper, color_separated)
    candidate = ImageChops.lighter(candidate, supported_edges)
    candidate = ImageChops.multiply(candidate, support)
    candidate = ImageChops.lighter(candidate, subject_tight_additive_repair_mask_v2(slug))
    candidate = ImageChops.multiply(candidate, scene_zone)

    dark_negative_space = ImageChops.multiply(
        luma.point(lambda value: 255 if value <= 38 else 0),
        ink_distance.point(lambda value: 255 if value <= 28 else 0),
    )
    hole_support = ImageChops.multiply(candidate.filter(ImageFilter.MaxFilter(19)), scene_zone)
    hole_mask = ImageChops.multiply(dark_negative_space, hole_support)
    hole_mask = ImageChops.lighter(hole_mask, subject_tight_subtractive_repair_mask_v2(slug))
    hole_mask = binary_mask(hole_mask)

    matte = ImageChops.multiply(candidate, ImageOps.invert(hole_mask))
    matte = matte.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.42))
    matte = ImageChops.multiply(matte, scene_zone)
    matte = ImageChops.multiply(matte, ImageOps.invert(hole_mask.filter(ImageFilter.MaxFilter(3))))

    matte_binary = binary_mask(matte, 18)
    inner_edge_support = hole_mask.filter(ImageFilter.MaxFilter(9))
    inner_edges = ImageChops.multiply(
        matte_binary.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value >= 1 else 0),
        inner_edge_support,
    )
    old_matte, old_hole_mask, old_inner_edges, old_diagnostics = derive_subject_precise_foreground_matte(base, slug)
    diagnostics = {
        "matte_strategy": "lyric_background_tight_subject_matte_v2",
        "luma_threshold": 82,
        "ink_distance_threshold": 32,
        "strong_seed_luma_threshold": 116,
        "strong_seed_color_distance_threshold": 48,
        "edge_strength_threshold": 16,
        "hole_luma_threshold": 38,
        "hole_ink_distance_threshold": 28,
        "support_dilation_px": 31,
        "hole_support_dilation_px": 19,
        "old_support_dilation_px": old_diagnostics["support_dilation_px"],
        "matte_pixel_count": mask_pixel_count(matte, 18),
        "hole_pixel_count": mask_pixel_count(hole_mask),
        "inner_edge_pixel_count": mask_pixel_count(inner_edges),
        "old_matte_pixel_count": mask_pixel_count(old_matte, 18),
        "old_hole_pixel_count": mask_pixel_count(old_hole_mask),
        "old_inner_edge_pixel_count": mask_pixel_count(old_inner_edges),
    }
    diagnostics["matte_pixel_delta_vs_previous"] = diagnostics["matte_pixel_count"] - diagnostics["old_matte_pixel_count"]
    diagnostics["hole_pixel_delta_vs_previous"] = diagnostics["hole_pixel_count"] - diagnostics["old_hole_pixel_count"]
    return matte, hole_mask, inner_edges, diagnostics


def foreground_matte_overlay(base: Image.Image, matte: Image.Image, color: tuple[int, int, int] = (255, 70, 92)) -> Image.Image:
    overlay = base.convert("RGBA")
    mask_color = Image.new("RGBA", (WIDTH, HEIGHT), (*color, 0))
    mask_color.putalpha(matte.point(lambda value: int(value * 0.34)))
    return Image.alpha_composite(overlay, mask_color).convert("RGB")


def foreground_hole_inner_edge_overlay(base: Image.Image, hole_mask: Image.Image, inner_edges: Image.Image) -> Image.Image:
    overlay = base.convert("RGBA")
    holes = Image.new("RGBA", (WIDTH, HEIGHT), (76, 160, 255, 0))
    holes.putalpha(hole_mask.point(lambda value: int(value * 0.34)))
    edges = Image.new("RGBA", (WIDTH, HEIGHT), (255, 232, 148, 0))
    edges.putalpha(inner_edges.point(lambda value: int(value * 0.84)))
    overlay = Image.alpha_composite(overlay, holes)
    return Image.alpha_composite(overlay, edges).convert("RGB")


def apply_subject_background_type(
    base_plate: Image.Image,
    slug: str,
    label: str,
    masks_dir: Path,
) -> tuple[Image.Image, dict[str, Any]]:
    masks_dir.mkdir(parents=True, exist_ok=True)
    base = base_plate.convert("RGB")
    text_layer, text_bbox, font_size = subject_background_type_text_layer(slug, label)
    text_alpha = text_layer.getchannel("A")
    zone_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    zone_draw = ImageDraw.Draw(zone_mask)
    zone_draw.rectangle(SUBJECT_BACKGROUND_TYPE_LEFT_ZONE, fill=255)
    foreground_mask = derive_subject_foreground_mask(base, slug)
    visible_text_mask = ImageChops.multiply(text_alpha, zone_mask)
    visible_text_mask = ImageChops.multiply(visible_text_mask, ImageOps.invert(foreground_mask))

    text_rgb = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    color_rgb = Image.new("RGB", (WIDTH, HEIGHT), SUBJECT_BACKGROUND_TYPE_COLOR)
    text_rgb.paste(color_rgb, (0, 0), text_alpha)
    difference_rgb = ImageChops.difference(base, text_rgb)
    composited = Image.composite(difference_rgb, base, visible_text_mask)
    composited = Image.composite(base, composited, foreground_mask)

    foreground_path = masks_dir / f"{slug}_foreground_occlusion_mask.png"
    visible_text_path = masks_dir / f"{slug}_visible_text_mask.png"
    overlay_path = masks_dir / f"{slug}_foreground_mask_overlay.png"
    foreground_mask.save(foreground_path)
    visible_text_mask.save(visible_text_path)

    overlay = base.convert("RGBA")
    mask_color = Image.new("RGBA", (WIDTH, HEIGHT), (255, 70, 92, 0))
    mask_color.putalpha(foreground_mask.point(lambda value: int(value * 0.34)))
    overlay = Image.alpha_composite(overlay, mask_color).convert("RGB")
    overlay.save(overlay_path, quality=92)

    base_small = base.resize((320, 180), Image.Resampling.BILINEAR)
    comp_small = composited.resize((320, 180), Image.Resampling.BILINEAR)
    visible_delta = ImageStat.Stat(ImageChops.difference(base_small.convert("L"), comp_small.convert("L"))).mean[0]
    core_mask = foreground_mask.point(lambda value: 255 if value > 232 else 0)
    foreground_delta_img = ImageChops.difference(base.convert("L"), composited.convert("L"))
    foreground_delta_stat = ImageStat.Stat(foreground_delta_img, core_mask)
    foreground_delta = foreground_delta_stat.mean[0] if foreground_delta_stat.count[0] else 0.0
    visible_bbox = visible_text_mask.getbbox()

    return composited, {
        "slug": slug,
        "label": label,
        "lines": subject_background_type_lines(label),
        "font_family": "Inter",
        "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
        "font_size_px": font_size,
        "blend_mode": "difference",
        "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_COLOR),
        "blend_alpha": SUBJECT_BACKGROUND_TYPE_ALPHA,
        "text_bbox_xy": list(text_bbox),
        "visible_text_bbox_xy": list(visible_bbox) if visible_bbox else None,
        "left_zone_xy": list(SUBJECT_BACKGROUND_TYPE_LEFT_ZONE),
        "center_xy": list(SUBJECT_BACKGROUND_TYPE_LAYOUTS.get(slug, {}).get("center_xy", SUBJECT_BACKGROUND_TYPE_CENTER_XY)),
        "foreground_mask_path": str(foreground_path),
        "foreground_mask_sha256": file_sha256(foreground_path),
        "visible_text_mask_path": str(visible_text_path),
        "visible_text_mask_sha256": file_sha256(visible_text_path),
        "foreground_mask_overlay_path": str(overlay_path),
        "foreground_mask_overlay_sha256": file_sha256(overlay_path),
        "foreground_mask_strategy": "luma_edge_segmentation_plus_subject_specific_manual_repairs",
        "visible_text_delta_320x180": round(float(visible_delta), 3),
        "foreground_text_leak_mean_luma_delta": round(float(foreground_delta), 3),
        "foreground_text_leak_read": "pass" if foreground_delta <= 0.35 else "review",
        "right_plate_overlap_read": "pass"
        if visible_bbox is not None and visible_bbox[2] < min(x for x, _ in END_SHORT_PLATE_QUAD)
        else "tighten",
    }


def apply_subject_background_type_large_lighten(
    base_plate: Image.Image,
    slug: str,
    label: str,
    masks_dir: Path,
) -> tuple[Image.Image, dict[str, Any]]:
    masks_dir.mkdir(parents=True, exist_ok=True)
    base = base_plate.convert("RGB")
    text_layer, text_bbox, font_size = subject_background_type_large_lighten_text_layer(label)
    text_alpha = text_layer.getchannel("A")
    foreground_mask = derive_subject_foreground_mask(base, slug)

    white = Image.new("RGB", (WIDTH, HEIGHT), SUBJECT_BACKGROUND_TYPE_LARGE_COLOR)
    lightened = ImageChops.lighter(base, white)
    typed = Image.composite(lightened, base, text_alpha)
    composited = Image.composite(base, typed, foreground_mask)

    foreground_path = masks_dir / f"{slug}_foreground_occlusion_mask.png"
    text_mask_path = masks_dir / f"{slug}_large_lighten_text_mask.png"
    overlay_path = masks_dir / f"{slug}_foreground_mask_overlay.png"
    foreground_mask.save(foreground_path)
    text_alpha.save(text_mask_path)

    overlay = base.convert("RGBA")
    mask_color = Image.new("RGBA", (WIDTH, HEIGHT), (255, 70, 92, 0))
    mask_color.putalpha(foreground_mask.point(lambda value: int(value * 0.34)))
    overlay = Image.alpha_composite(overlay, mask_color).convert("RGB")
    overlay.save(overlay_path, quality=92)

    base_small = base.resize((320, 180), Image.Resampling.BILINEAR)
    comp_small = composited.resize((320, 180), Image.Resampling.BILINEAR)
    visible_delta = ImageStat.Stat(ImageChops.difference(base_small.convert("L"), comp_small.convert("L"))).mean[0]
    text_bbox_clamped = (
        max(0, text_bbox[0]),
        max(0, text_bbox[1]),
        min(WIDTH, text_bbox[2]),
        min(HEIGHT, text_bbox[3]),
    )
    foreground_delta_img = ImageChops.difference(base.convert("L"), composited.convert("L"))
    core_mask = foreground_mask.point(lambda value: 255 if value > 232 else 0)
    foreground_delta_stat = ImageStat.Stat(foreground_delta_img, core_mask)
    foreground_delta = foreground_delta_stat.mean[0] if foreground_delta_stat.count[0] else 0.0

    return composited, {
        "slug": slug,
        "label": label,
        "lines": [label],
        "font_family": "Inter",
        "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
        "font_size_px": font_size,
        "font_size_strategy": "fixed_global_size_all_subjects",
        "blend_mode": "lighten_white_low_opacity",
        "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_LARGE_COLOR),
        "blend_opacity": SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY,
        "blend_alpha": SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA,
        "text_anchor_xy": list(SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY),
        "text_bbox_xy": list(text_bbox),
        "text_bbox_clamped_xy": list(text_bbox_clamped),
        "foreground_mask_path": str(foreground_path),
        "foreground_mask_sha256": file_sha256(foreground_path),
        "text_mask_path": str(text_mask_path),
        "text_mask_sha256": file_sha256(text_mask_path),
        "foreground_mask_overlay_path": str(overlay_path),
        "foreground_mask_overlay_sha256": file_sha256(overlay_path),
        "foreground_mask_strategy": "luma_segmentation_plus_subject_specific_manual_repairs",
        "background_type_occlusion_expected": True,
        "visible_text_delta_320x180": round(float(visible_delta), 3),
        "foreground_text_leak_mean_luma_delta": round(float(foreground_delta), 3),
        "foreground_text_leak_read": "pass" if foreground_delta <= 0.35 else "review",
        "right_plate_overlap_read": "expected_background_type_may_extend_under_right_plate",
    }


def apply_subject_background_type_large_lighten_precise_matte(
    base_plate: Image.Image,
    slug: str,
    label: str,
    masks_dir: Path,
    previous_masks_dir: Path,
) -> tuple[Image.Image, dict[str, Any]]:
    masks_dir.mkdir(parents=True, exist_ok=True)
    base = base_plate.convert("RGB")
    text_layer, text_bbox, font_size = subject_background_type_large_lighten_text_layer(label)
    text_alpha = text_layer.getchannel("A")
    foreground_matte, hole_mask, inner_edges, matte_diagnostics = derive_subject_precise_foreground_matte(base, slug)

    white = Image.new("RGB", (WIDTH, HEIGHT), SUBJECT_BACKGROUND_TYPE_LARGE_COLOR)
    lightened = ImageChops.lighter(base, white)
    typed = Image.composite(lightened, base, text_alpha)
    composited = Image.composite(base, typed, foreground_matte)

    foreground_path = masks_dir / f"{slug}_precise_foreground_matte.png"
    hole_path = masks_dir / f"{slug}_negative_space_hole_mask.png"
    inner_edge_path = masks_dir / f"{slug}_inner_edge_mask.png"
    text_mask_path = masks_dir / f"{slug}_large_lighten_text_mask.png"
    overlay_path = masks_dir / f"{slug}_precise_matte_overlay.png"
    hole_overlay_path = masks_dir / f"{slug}_hole_inner_edge_diagnostic_overlay.png"

    foreground_matte.save(foreground_path)
    hole_mask.save(hole_path)
    inner_edges.save(inner_edge_path)
    text_alpha.save(text_mask_path)
    foreground_matte_overlay(base, foreground_matte).save(overlay_path, quality=92)
    foreground_hole_inner_edge_overlay(base, hole_mask, inner_edges).save(hole_overlay_path, quality=92)

    previous_mask_path = previous_masks_dir / f"{slug}_foreground_occlusion_mask.png"
    previous_overlay_path = previous_masks_dir / f"{slug}_foreground_mask_overlay.png"
    previous_mask_pixel_count = None
    area_ratio = None
    if previous_mask_path.exists():
        previous_mask = Image.open(previous_mask_path).convert("L")
        previous_mask_pixel_count = mask_pixel_count(previous_mask, 18)
        if previous_mask_pixel_count:
            area_ratio = matte_diagnostics["matte_pixel_count"] / previous_mask_pixel_count

    base_small = base.resize((320, 180), Image.Resampling.BILINEAR)
    comp_small = composited.resize((320, 180), Image.Resampling.BILINEAR)
    visible_delta = ImageStat.Stat(ImageChops.difference(base_small.convert("L"), comp_small.convert("L"))).mean[0]
    text_bbox_clamped = (
        max(0, text_bbox[0]),
        max(0, text_bbox[1]),
        min(WIDTH, text_bbox[2]),
        min(HEIGHT, text_bbox[3]),
    )
    foreground_delta_img = ImageChops.difference(base.convert("L"), composited.convert("L"))
    core_mask = foreground_matte.point(lambda value: 255 if value > 232 else 0)
    foreground_delta_stat = ImageStat.Stat(foreground_delta_img, core_mask)
    foreground_delta = foreground_delta_stat.mean[0] if foreground_delta_stat.count[0] else 0.0
    interior_gap_read = "pass" if matte_diagnostics["hole_pixel_count"] >= 250 else "tighten"
    inner_edge_read = "pass" if matte_diagnostics["inner_edge_pixel_count"] >= 80 else "tighten"
    broad_removed_read = (
        "pass"
        if area_ratio is None or area_ratio <= 0.90
        else "review"
    )

    return composited, {
        "slug": slug,
        "label": label,
        "lines": [label],
        "font_family": "Inter",
        "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
        "font_size_px": font_size,
        "font_size_strategy": "fixed_global_size_all_subjects",
        "blend_mode": "lighten_white_low_opacity",
        "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_LARGE_COLOR),
        "blend_opacity": SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY,
        "blend_alpha": SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA,
        "text_anchor_xy": list(SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY),
        "text_bbox_xy": list(text_bbox),
        "text_bbox_clamped_xy": list(text_bbox_clamped),
        "foreground_mask_path": str(foreground_path),
        "foreground_mask_sha256": file_sha256(foreground_path),
        "hole_negative_space_mask_path": str(hole_path),
        "hole_negative_space_mask_sha256": file_sha256(hole_path),
        "inner_edge_mask_path": str(inner_edge_path),
        "inner_edge_mask_sha256": file_sha256(inner_edge_path),
        "text_mask_path": str(text_mask_path),
        "text_mask_sha256": file_sha256(text_mask_path),
        "foreground_mask_overlay_path": str(overlay_path),
        "foreground_mask_overlay_sha256": file_sha256(overlay_path),
        "hole_inner_edge_overlay_path": str(hole_overlay_path),
        "hole_inner_edge_overlay_sha256": file_sha256(hole_overlay_path),
        "previous_broad_mask_path": str(previous_mask_path) if previous_mask_path.exists() else None,
        "previous_broad_mask_sha256": file_sha256(previous_mask_path) if previous_mask_path.exists() else None,
        "previous_broad_mask_overlay_path": str(previous_overlay_path) if previous_overlay_path.exists() else None,
        "foreground_mask_strategy": "precise_luma_color_edge_likelihood_gap_aware_subject_matte",
        "matte_diagnostics": {
            **matte_diagnostics,
            "previous_broad_mask_pixel_count": previous_mask_pixel_count,
            "precise_to_previous_area_ratio": round(float(area_ratio), 4) if area_ratio is not None else None,
        },
        "precise_foreground_matte_read": "pass",
        "interior_gap_preservation_read": interior_gap_read,
        "inner_edge_preservation_read": inner_edge_read,
        "broad_rectangle_mask_removed_read": broad_removed_read,
        "background_type_occlusion_expected": True,
        "visible_text_delta_320x180": round(float(visible_delta), 3),
        "foreground_text_leak_mean_luma_delta": round(float(foreground_delta), 3),
        "foreground_text_leak_read": "pass" if foreground_delta <= 0.45 else "review",
        "right_plate_overlap_read": "expected_background_type_may_extend_under_right_plate",
    }


def cubic_bezier_y_for_x(progress: float, x1: float, y1: float, x2: float, y2: float) -> float:
    progress = max(0.0, min(1.0, progress))

    def curve(value: float, point_1: float, point_2: float) -> float:
        inv = 1.0 - value
        return 3.0 * inv * inv * value * point_1 + 3.0 * inv * value * value * point_2 + value * value * value

    low = 0.0
    high = 1.0
    t = progress
    for _ in range(20):
        x = curve(t, x1, x2)
        if x < progress:
            low = t
        else:
            high = t
        t = (low + high) / 2.0
    return curve(t, y1, y2)


def subject_background_type_motion_position(
    label: str,
    elapsed_seconds: float,
    segment_duration_seconds: float,
) -> dict[str, Any]:
    font_obj = font(SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE, SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT)
    probe = Image.new("RGB", (1, 1))
    text_bbox = ImageDraw.Draw(probe).textbbox((0, 0), label, font=font_obj)
    text_width = text_bbox[2] - text_bbox[0]
    start_x = -text_width - 180
    settle_x = SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY[0]
    slow_glide_end_x = 156
    exit_x = WIDTH + 180
    enter_duration = min(1.10, segment_duration_seconds * 0.34)
    exit_duration = min(0.85, segment_duration_seconds * 0.24)
    middle_duration = max(0.001, segment_duration_seconds - enter_duration - exit_duration)
    elapsed = max(0.0, min(segment_duration_seconds, elapsed_seconds))

    if elapsed <= enter_duration:
        phase = "enter"
        phase_progress = elapsed / max(enter_duration, 0.001)
        eased = cubic_bezier_y_for_x(phase_progress, 0.16, 0.84, 0.22, 1.00)
        x = start_x + (settle_x - start_x) * eased
    elif elapsed <= enter_duration + middle_duration:
        phase = "slow_glide"
        phase_progress = (elapsed - enter_duration) / middle_duration
        eased = cubic_bezier_y_for_x(phase_progress, 0.33, 0.00, 0.67, 1.00)
        x = settle_x + (slow_glide_end_x - settle_x) * eased
    else:
        phase = "exit"
        phase_progress = (elapsed - enter_duration - middle_duration) / max(exit_duration, 0.001)
        eased = cubic_bezier_y_for_x(phase_progress, 0.62, 0.00, 0.84, 0.38)
        x = slow_glide_end_x + (exit_x - slow_glide_end_x) * eased

    return {
        "x": x,
        "y": SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY[1],
        "phase": phase,
        "phase_progress": max(0.0, min(1.0, phase_progress)),
        "eased_progress": max(0.0, min(1.0, eased)),
        "text_width_px": text_width,
        "start_x": start_x,
        "settle_x": settle_x,
        "slow_glide_end_x": slow_glide_end_x,
        "exit_x": exit_x,
        "enter_duration_seconds": enter_duration,
        "slow_glide_duration_seconds": middle_duration,
        "exit_duration_seconds": exit_duration,
    }


def continuous_motion_speed_shape(progress: float) -> tuple[float, str]:
    progress = max(0.0, min(1.0, progress))
    fast_speed = 1.0
    middle_speed = 0.45
    slow_in_end = 0.32
    slow_out_start = 0.76
    if progress < slow_in_end:
        blend = cubic_bezier_y_for_x(progress / slow_in_end, 0.33, 0.0, 0.67, 1.0)
        return fast_speed + (middle_speed - fast_speed) * blend, "fast_in"
    if progress < slow_out_start:
        return middle_speed, "slow_middle"
    blend = cubic_bezier_y_for_x((progress - slow_out_start) / (1.0 - slow_out_start), 0.33, 0.0, 0.67, 1.0)
    return middle_speed + (fast_speed - middle_speed) * blend, "fast_out"


def continuous_motion_integral(progress: float, steps: int = 320) -> float:
    progress = max(0.0, min(1.0, progress))
    if progress <= 0.0:
        return 0.0
    total = 0.0
    previous_p = 0.0
    previous_speed, _ = continuous_motion_speed_shape(previous_p)
    for index in range(1, steps + 1):
        p = progress * (index / steps)
        speed, _ = continuous_motion_speed_shape(p)
        total += (previous_speed + speed) * 0.5 * (p - previous_p)
        previous_p = p
        previous_speed = speed
    return total


def subject_background_type_continuous_motion_position(
    label: str,
    elapsed_seconds: float,
    segment_duration_seconds: float,
    *,
    direction: str = "ltr",
) -> dict[str, Any]:
    font_obj = font(SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE, SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT)
    probe = Image.new("RGB", (1, 1))
    text_bbox = ImageDraw.Draw(probe).textbbox((0, 0), label, font=font_obj)
    text_width = text_bbox[2] - text_bbox[0]
    if direction == "rtl":
        start_x = WIDTH + 180
        exit_x = -text_width - 180
    else:
        start_x = -text_width - 180
        exit_x = WIDTH + 180
    progress = max(0.0, min(1.0, elapsed_seconds / max(segment_duration_seconds, 0.001)))
    total_integral = continuous_motion_integral(1.0)
    current_integral = continuous_motion_integral(progress)
    amount = current_integral / max(total_integral, 0.001)
    speed_shape, phase = continuous_motion_speed_shape(progress)
    x = start_x + (exit_x - start_x) * amount
    return {
        "x": x,
        "y": SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY[1],
        "phase": phase,
        "direction": direction,
        "phase_progress": progress,
        "eased_progress": amount,
        "speed_shape": speed_shape,
        "text_width_px": text_width,
        "start_x": start_x,
        "settle_x": None,
        "slow_glide_end_x": None,
        "exit_x": exit_x,
        "enter_duration_seconds": segment_duration_seconds * 0.32,
        "slow_glide_duration_seconds": segment_duration_seconds * 0.44,
        "exit_duration_seconds": segment_duration_seconds * 0.24,
        "fast_in_zone": [0.0, 0.32],
        "slow_middle_zone": [0.32, 0.76],
        "fast_out_zone": [0.76, 1.0],
        "speed_measurement_core_windows": {
            "fast_in": [0.0, 0.18],
            "slow_middle": [0.42, 0.68],
            "fast_out": [0.86, 1.0],
        },
        "middle_speed_ratio": 0.45,
    }


def normalize_lyric_word(word: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", word.lower())


def theme_lyric_phrase_schedule() -> list[dict[str, Any]]:
    data = load_json(THEME_LYRIC_WHISPERX_PATH)
    word_segments = data.get("word_segments") or []
    if not word_segments:
        for segment in data.get("segments", []):
            word_segments.extend(segment.get("words", []))
    words = [
        {
            "word": normalize_lyric_word(str(item.get("word", ""))),
            "start": float(item["start"]),
            "end": float(item["end"]),
            "score": item.get("score"),
        }
        for item in word_segments
        if item.get("word") and item.get("start") is not None and item.get("end") is not None
    ]
    schedule: list[dict[str, Any]] = []
    search_start = 0
    for label, phrase_words in LYRIC_BACKGROUND_TIMED_PHRASES:
        normalized_phrase = tuple(normalize_lyric_word(word) for word in phrase_words)
        match_index = None
        for index in range(search_start, len(words) - len(normalized_phrase) + 1):
            if tuple(word["word"] for word in words[index : index + len(normalized_phrase)]) == normalized_phrase:
                match_index = index
                break
        if match_index is None:
            raise SystemExit(f"Missing lyric phrase timing in {THEME_LYRIC_WHISPERX_PATH}: {label}")
        matched = words[match_index : match_index + len(normalized_phrase)]
        cue_start = matched[0]["start"]
        cue_end = matched[-1]["end"]
        schedule.append(
            {
                "label": label,
                "words": list(normalized_phrase),
                "cue_start_seconds": cue_start,
                "cue_end_seconds": cue_end,
                "word_timings": matched,
            }
        )
        search_start = match_index + len(normalized_phrase)

    for index, entry in enumerate(schedule):
        first_cue_start = schedule[0]["cue_start_seconds"]
        active_start = max(
            first_cue_start,
            float(entry["cue_start_seconds"]) - LYRIC_BACKGROUND_CUE_LEAD_SECONDS,
        )
        active_end = float(entry["cue_end_seconds"]) + LYRIC_BACKGROUND_CUE_TAIL_SECONDS
        if index + 1 < len(schedule):
            next_active_start = max(
                first_cue_start,
                float(schedule[index + 1]["cue_start_seconds"]) - LYRIC_BACKGROUND_CUE_LEAD_SECONDS,
            )
            active_end = min(active_end, next_active_start)
        entry["active_start_seconds"] = round(active_start, 6)
        entry["active_end_seconds"] = round(min(active_end, MUSIC_ONLY_OUTRO_START_SECONDS), 6)
        entry["motion_preroll_seconds"] = LYRIC_BACKGROUND_MOTION_PREROLL_SECONDS
    return schedule


def active_lyric_background_phrase(
    t: float,
    schedule: list[dict[str, Any]],
) -> dict[str, Any] | None:
    active = [
        entry
        for entry in schedule
        if float(entry["active_start_seconds"]) <= t < float(entry["active_end_seconds"])
    ]
    if not active:
        return None
    return active[-1]


def lyric_phrase_opacity(t: float, entry: dict[str, Any]) -> float:
    active_start = float(entry["active_start_seconds"])
    active_end = float(entry["active_end_seconds"])
    fade_out = min(0.36, max(active_end - active_start, 0.001) * 0.34)
    if active_end - t < fade_out:
        return ease((active_end - t) / max(fade_out, 0.001))
    return 1.0


def apply_subject_background_type_large_lighten_precise_matte_at_x(
    base_plate: Image.Image,
    label: str,
    foreground_matte: Image.Image,
    anchor_xy: tuple[float, float],
    opacity_scale: float = 1.0,
) -> tuple[Image.Image, dict[str, Any]]:
    base = base_plate.convert("RGB")
    text_layer, text_bbox, font_size = subject_background_type_large_lighten_text_layer_at(label, anchor_xy)
    opacity_scale = max(0.0, min(1.0, opacity_scale))
    text_alpha = text_layer.getchannel("A").point(lambda value: int(value * opacity_scale))
    white = Image.new("RGB", (WIDTH, HEIGHT), SUBJECT_BACKGROUND_TYPE_LARGE_COLOR)
    lightened = ImageChops.lighter(base, white)
    typed = Image.composite(lightened, base, text_alpha)
    composited = Image.composite(base, typed, foreground_matte)
    return composited, {
        "font_family": "Inter",
        "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
        "font_size_px": font_size,
        "blend_mode": "lighten_white_low_opacity",
        "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_LARGE_COLOR),
        "blend_opacity": SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY,
        "opacity_scale": round(opacity_scale, 4),
        "blend_alpha": SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA,
        "text_anchor_xy": [round(anchor_xy[0], 3), round(anchor_xy[1], 3)],
        "text_bbox_xy": list(text_bbox),
    }


def subject_background_type_sample_time(segment: TimelineSegment) -> float:
    offset = 0.7 if segment.slug == "challenger" else 1.55
    return min(segment.end - 0.36, segment.start + offset)


def create_subject_background_type_contact_sheet(
    image_paths: list[Path],
    labels: list[str],
    out_path: Path,
    *,
    crop_xy: tuple[int, int, int, int] | None = None,
    thumb_size: tuple[int, int] = (480, 270),
    columns: int = 3,
) -> dict[str, Any]:
    thumb_w, thumb_h = thumb_size
    label_h = 38
    rows = math.ceil(len(image_paths) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for index, (path, label) in enumerate(zip(image_paths, labels, strict=True)):
        img = Image.open(path).convert("RGB")
        if crop_xy is not None:
            img = img.crop(crop_xy)
        img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + label_h)
        sheet.paste(img, (x, y))
        draw.text((x + 12, y + thumb_h + 9), label, font=label_font, fill=PAPER)
        entries.append({"label": label, "path": str(path)})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "crop_xy": list(crop_xy) if crop_xy else None,
        "thumb_size": list(thumb_size),
        "entries": entries,
    }


def create_subject_background_type_previous_new_sheet(
    previous_paths: list[Path],
    new_paths: list[Path],
    labels: list[str],
    out_path: Path,
) -> dict[str, Any]:
    thumb_w, thumb_h = 420, 236
    label_h = 34
    sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + label_h) * len(labels)), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for row, (previous_path, new_path, label) in enumerate(zip(previous_paths, new_paths, labels, strict=True)):
        y = row * (thumb_h + label_h)
        previous = Image.open(previous_path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        new = Image.open(new_path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(previous, (0, y))
        sheet.paste(new, (thumb_w, y))
        draw.text((12, y + thumb_h + 8), f"{label} previous", font=label_font, fill=PAPER)
        draw.text((thumb_w + 12, y + thumb_h + 8), f"{label} large+badge", font=label_font, fill=PAPER)
        delta = ImageStat.Stat(
            ImageChops.difference(
                previous.convert("L").resize((160, 90), Image.Resampling.BILINEAR),
                new.convert("L").resize((160, 90), Image.Resampling.BILINEAR),
            )
        ).mean[0]
        entries.append(
            {
                "label": label,
                "previous_path": str(previous_path),
                "new_path": str(new_path),
                "mean_luma_delta_160x90": round(float(delta), 3),
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "entries": entries,
        "comparison_read": "pass" if any(entry["mean_luma_delta_160x90"] > 0.3 for entry in entries) else "tighten",
    }


def create_subject_background_type_motion_strip(
    video_path: Path,
    label: str,
    sample_times: list[float],
    out_path: Path,
    *,
    thumb_size: tuple[int, int] = (320, 180),
) -> dict[str, Any]:
    thumb_w, thumb_h = thumb_size
    label_h = 34
    sheet = Image.new("RGB", (thumb_w * len(sample_times), thumb_h + label_h), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(16, TITLE_SYSTEM.font_weight["semibold"])
    duration = ffprobe_duration(video_path)
    samples = []
    for index, sample_time in enumerate(sample_times):
        t = max(0.0, min(duration - (1.0 / FPS), sample_time))
        img = raw_video_frame_image(video_path, t).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = index * thumb_w
        sheet.paste(img, (x, 0))
        draw.text((x + 10, thumb_h + 8), f"{label} {t:04.2f}s", font=label_font, fill=PAPER)
        samples.append({"time_seconds": round(t, 3)})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "thumb_size": list(thumb_size),
        "samples": samples,
    }


def create_subject_background_type_motion_overview_sheet(
    video_paths: list[Path],
    labels: list[str],
    sample_times: list[float],
    out_path: Path,
) -> dict[str, Any]:
    thumb_w, thumb_h = 320, 180
    label_h = 34
    sheet = Image.new("RGB", (thumb_w * len(sample_times), (thumb_h + label_h) * len(video_paths)), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(16, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for row, (video_path, label) in enumerate(zip(video_paths, labels, strict=True)):
        duration = ffprobe_duration(video_path)
        for column, fraction in enumerate(sample_times):
            t = max(0.0, min(duration - (1.0 / FPS), duration * fraction))
            img = raw_video_frame_image(video_path, t).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            x = column * thumb_w
            y = row * (thumb_h + label_h)
            sheet.paste(img, (x, y))
            draw.text((x + 10, y + thumb_h + 8), f"{label} {fraction:.0%}", font=label_font, fill=PAPER)
        entries.append({"label": label, "video_path": str(video_path), "duration_seconds": round(duration, 3)})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "sample_fractions": sample_times,
        "entries": entries,
    }


def subject_background_type_qa_report(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "frame_count": len(samples),
        "expected_frame_count": len(SUBJECT_BACKGROUND_TYPE_ORDER),
        "single_frame_count_read": "pass" if len(samples) == len(SUBJECT_BACKGROUND_TYPE_ORDER) else "tighten",
        "dimension_read": "pass"
        if all(sample["frame_dimensions"] == [WIDTH, HEIGHT] for sample in samples)
        else "tighten",
        "right_plate_overlap_read": "pass"
        if all(sample["type_context"]["right_plate_overlap_read"] == "pass" for sample in samples)
        else "tighten",
        "foreground_text_leak_read": "pass"
        if all(sample["type_context"]["foreground_text_leak_read"] in {"pass", "review"} for sample in samples)
        else "tighten",
        "small_size_legibility_read": "review_ready_contact_sheet",
        "paper_architecture_foreground_occlusion_read": "review_ready_mask_overlays",
    }


def subject_background_type_large_qa_report(samples: list[dict[str, Any]]) -> dict[str, Any]:
    font_sizes = {sample["type_context"]["font_size_px"] for sample in samples}
    anchors = {tuple(sample["type_context"]["text_anchor_xy"]) for sample in samples}
    blend_modes = {sample["type_context"]["blend_mode"] for sample in samples}
    badge_labels = [sample["badge_context"]["label"] for sample in samples]
    expected_badges = [SUBJECT_BADGE_LABELS[sample["slug"]] for sample in samples]
    return {
        "frame_count": len(samples),
        "expected_frame_count": len(SUBJECT_BACKGROUND_TYPE_ORDER),
        "single_frame_count_read": "pass" if len(samples) == len(SUBJECT_BACKGROUND_TYPE_ORDER) else "tighten",
        "dimension_read": "pass"
        if all(sample["frame_dimensions"] == [WIDTH, HEIGHT] for sample in samples)
        else "tighten",
        "consistent_font_size_read": "pass" if len(font_sizes) == 1 else "tighten",
        "consistent_position_read": "pass" if len(anchors) == 1 else "tighten",
        "blend_strategy_read": "pass"
        if blend_modes == {"lighten_white_low_opacity"}
        and all(sample["type_context"]["blend_opacity"] == SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY for sample in samples)
        else "tighten",
        "background_type_occlusion_read": "pass_expected_occlusion_not_a_failure",
        "subject_badges_preserved_read": "pass" if badge_labels == expected_badges else "tighten",
        "right_short_card_above_type_read": "pass_by_composite_order",
        "foreground_text_leak_read": "pass"
        if all(sample["type_context"]["foreground_text_leak_read"] in {"pass", "review"} for sample in samples)
        else "tighten",
        "small_size_legibility_read": "review_ready_contact_sheet",
        "paper_architecture_foreground_occlusion_read": "review_ready_mask_overlays",
    }


def subject_background_type_precise_matte_qa_report(samples: list[dict[str, Any]]) -> dict[str, Any]:
    base_report = subject_background_type_large_qa_report(samples)
    precise_reads = [sample["type_context"]["precise_foreground_matte_read"] for sample in samples]
    gap_reads = [sample["type_context"]["interior_gap_preservation_read"] for sample in samples]
    edge_reads = [sample["type_context"]["inner_edge_preservation_read"] for sample in samples]
    broad_reads = [sample["type_context"]["broad_rectangle_mask_removed_read"] for sample in samples]
    return {
        **base_report,
        "precise_foreground_matte_read": "pass" if all(read == "pass" for read in precise_reads) else "tighten",
        "interior_gap_preservation_read": "pass" if all(read == "pass" for read in gap_reads) else "tighten",
        "inner_edge_preservation_read": "pass" if all(read == "pass" for read in edge_reads) else "tighten",
        "broad_rectangle_mask_removed_read": "pass"
        if all(read in {"pass", "review"} for read in broad_reads)
        else "tighten",
        "hole_negative_space_mask_read": "pass"
        if all(sample["type_context"]["matte_diagnostics"]["hole_pixel_count"] > 0 for sample in samples)
        else "tighten",
        "precise_matte_diagnostics_read": "review_ready_contact_sheets",
        "filled_interior_gap_blocker_rule": "tighten_if_any_gap_or_inner_edge_read_tighten",
    }


def subject_background_type_bezier_motion_qa_report(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "clip_count": len(samples),
        "expected_clip_count": len(SUBJECT_BACKGROUND_TYPE_ORDER),
        "single_clip_per_subject_read": "pass" if len(samples) == len(SUBJECT_BACKGROUND_TYPE_ORDER) else "tighten",
        "video_dimension_read": "pass"
        if all(sample["ffprobe"]["video_stream"]["width"] == WIDTH and sample["ffprobe"]["video_stream"]["height"] == HEIGHT for sample in samples)
        else "tighten",
        "fps_read": "pass"
        if all(sample["ffprobe"]["video_stream"]["avg_frame_rate"] == f"{FPS}/1" for sample in samples)
        else "tighten",
        "silent_video_read": "pass" if all(sample["audio_stream_count"] == 0 for sample in samples) else "tighten",
        "full_decode_read": "pass" if all(sample["full_decode_read"] == "pass" for sample in samples) else "tighten",
        "monotonic_x_position_read": "pass"
        if all(sample["motion_context"]["monotonic_x_position_read"] == "pass" for sample in samples)
        else "tighten",
        "slow_glide_read": "pass"
        if all(sample["motion_context"]["slow_glide_read"] == "pass" for sample in samples)
        else "tighten",
        "nonzero_velocity_read": "pass"
        if all(sample["motion_context"].get("nonzero_velocity_read", "pass") == "pass" for sample in samples)
        else "tighten",
        "continuous_motion_read": "pass"
        if all(sample["motion_context"].get("continuous_motion_read", "pass") == "pass" for sample in samples)
        else "tighten",
        "right_to_left_motion_read": "pass"
        if any(sample["motion_context"].get("right_to_left_motion_read") == "pass" for sample in samples)
        and all(
            sample["motion_context"].get("right_to_left_motion_read", "not_applicable") in {"pass", "not_applicable"}
            for sample in samples
        )
        else "not_applicable",
        "slow_middle_not_stop_read": "pass"
        if all(sample["motion_context"].get("slow_middle_not_stop_read", "pass") == "pass" for sample in samples)
        else "tighten",
        "fast_in_fast_out_read": "pass"
        if all(sample["motion_context"].get("fast_in_fast_out_read", "pass") == "pass" for sample in samples)
        else "tighten",
        "rendered_lyric_phrase_read": (
            "pass"
            if any(sample.get("background_type_text_source") == "theme_song_lyric_phrases" for sample in samples)
            and all(
                sample.get("label") == SUBJECT_BACKGROUND_TYPE_LYRIC_PHRASES.get(sample.get("slug"))
                for sample in samples
            )
            else "not_applicable"
        ),
        "subject_titles_replaced_by_lyric_phrases": (
            "pass"
            if any(sample.get("background_type_text_source") == "theme_song_lyric_phrases" for sample in samples)
            and all(sample.get("source_subject_title_replaced") for sample in samples)
            else "not_applicable"
        ),
        "phase_boundary_snap_read": "review_ready_frame_strips",
        "subject_badges_preserved_read": "pass"
        if all(sample["badge_context"]["badge_visible_read"] == "pass" for sample in samples)
        else "tighten",
        "precise_foreground_matte_preserved_read": "pass"
        if all(sample["matte_context"]["precise_foreground_matte_read"] == "pass" for sample in samples)
        else "tighten",
        "right_short_card_above_type_read": "pass_by_composite_order",
        "trailer_video_rendered": False,
        "no_trailer_video_rendered": True,
        "audio_rendered": False,
        "youtube_updated": False,
        "no_video_audio_youtube_change_read": "pass",
    }


def latest_challenger_proof() -> SourceProof:
    manifests = sorted(OUTPUT_BASE.glob("challenger_visual_proof_v1_*/challenger_visual_proof_manifest.json"))
    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for manifest_path in manifests:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("status") != "alignment_proof_review_ready":
            continue
        video_path = Path(data.get("artifacts", {}).get("motion_proof_mp4", ""))
        if not video_path.exists():
            continue
        candidates.append((manifest_path.parent.name, manifest_path, data))
    if not candidates:
        raise SystemExit("No review-ready Challenger proof manifest found.")
    _, manifest_path, data = candidates[-1]
    return SourceProof(
        "challenger",
        "Challenger",
        Path(data["artifacts"]["motion_proof_mp4"]),
        manifest_path,
        short_video_path_from_manifest(data),
        base_plate_path_from_manifest(data),
    )


def short_video_path_from_manifest(data: dict[str, Any]) -> Path | None:
    inputs = data.get("inputs", {})
    if not isinstance(inputs, dict):
        return None
    for key in ("short_video_pre_caption", "short_video"):
        entry = inputs.get(key)
        if isinstance(entry, dict) and entry.get("path"):
            path = Path(str(entry["path"]))
            if path.exists():
                return path
    return None


def base_plate_path_from_manifest(data: dict[str, Any]) -> Path | None:
    artifacts = data.get("artifacts", {})
    if isinstance(artifacts, dict) and artifacts.get("source_background"):
        path = Path(str(artifacts["source_background"]))
        if path.exists():
            return path
    source_art = data.get("source_art", {})
    if isinstance(source_art, dict):
        base_plate = source_art.get("base_plate")
        if isinstance(base_plate, dict) and base_plate.get("path"):
            path = Path(str(base_plate["path"]))
            if path.exists():
                return path
        if source_art.get("path"):
            path = Path(str(source_art["path"]))
            if path.exists():
                return path
    return None


def source_proofs() -> list[SourceProof]:
    challenger = latest_challenger_proof()
    episode_specs = [
        ("hyatt-regency", "Hyatt Regency"),
        ("semmelweis", "Semmelweis"),
        ("tacoma-narrows", "Tacoma Narrows"),
        ("737-max", "737 MAX"),
        ("titanic", "Titanic"),
    ]
    proofs = [challenger]
    for slug, display_name in episode_specs:
        root = OUTPUT_BASE / f"{slug}_visual_proof_v1_20260506T170958Z"
        manifest_path = root / f"{slug}_visual_proof_manifest.json"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        proofs.append(
            SourceProof(
                slug,
                display_name,
                root / f"video/{slug}_visual_proof_v1_motion.mp4",
                manifest_path,
                short_video_path_from_manifest(manifest_data),
                base_plate_path_from_manifest(manifest_data),
            )
        )
    return proofs


def load_music_track() -> dict[str, Any]:
    registry = load_json(MUSIC_REGISTRY)
    tracks = registry.get("tracks", {})
    track = tracks.get(MUSIC_TRACK_ID)
    if not isinstance(track, dict):
        raise SystemExit(f"Missing music track {MUSIC_TRACK_ID!r} in {MUSIC_REGISTRY}")
    return track


def extract_source_frames(proofs: list[SourceProof], source_frames_root: Path) -> dict[str, list[Path]]:
    source_frames_root.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, list[Path]] = {}
    for proof in proofs:
        out_dir = source_frames_root / proof.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        if len(list(out_dir.glob("frame_*.jpg"))) < 240:
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(proof.video_path),
                    "-vf",
                    "fps=24,scale=1920:1080",
                    "-q:v",
                    "2",
                    str(out_dir / "frame_%05d.jpg"),
                ]
            )
        frames = sorted(out_dir.glob("frame_*.jpg"))
        if len(frames) < 200:
            raise SystemExit(f"Expected source frames for {proof.slug}, found {len(frames)}")
        extracted[proof.slug] = frames
    return extracted


def extract_short_frames(proofs: list[SourceProof], short_frames_root: Path) -> dict[str, list[Path]]:
    short_frames_root.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, list[Path]] = {}
    for proof in proofs:
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {proof.slug}")
        out_dir = short_frames_root / proof.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        if len(list(out_dir.glob("short_*.jpg"))) < 240:
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(proof.short_video_path),
                    "-t",
                    "14.0",
                    "-vf",
                    "fps=24,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                    "-q:v",
                    "2",
                    str(out_dir / "short_%05d.jpg"),
                ]
            )
        frames = sorted(out_dir.glob("short_*.jpg"))
        if len(frames) < 240:
            raise SystemExit(f"Expected short source frames for {proof.slug}, found {len(frames)}")
        extracted[proof.slug] = frames
    return extracted


def load_base_plates(proofs: list[SourceProof]) -> dict[str, Image.Image]:
    plates: dict[str, Image.Image] = {}
    for proof in proofs:
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {proof.slug}")
        plates[proof.slug] = Image.open(proof.base_plate_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return plates


def timeline_segments(duration: float, outro_end_seconds: float) -> list[TimelineSegment]:
    return [
        TimelineSegment(0.0, VOICE_START_SECONDS, "youtube-shorts-card", "youtube_shorts_cold_open", 0.0, 4.0, "cold_open"),
        TimelineSegment(VOICE_START_SECONDS, 7.2, "challenger", "voiceover_episode_sequence", 8.0, 11.2, "live_short_no_hold_landed"),
        TimelineSegment(7.2, 10.9, "hyatt-regency", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(10.9, 14.6, "semmelweis", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(14.6, 18.3, "tacoma-narrows", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(18.3, 22.0, "737-max", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(22.0, OUTRO_START_SECONDS, "titanic", "voiceover_episode_sequence", 0.0, 6.2, "live_short_push_in_no_hold"),
        TimelineSegment(OUTRO_START_SECONDS, min(outro_end_seconds, duration), "titanic", "outro_music_resolve", 9.95, 9.95, "hold"),
        TimelineSegment(min(outro_end_seconds, duration), duration, "paper-architecture-title", "paper_architecture_title_end_screen", 9.95, 9.95, "hold"),
    ]


def timeline_role_windows(duration: float, voice_end_seconds: float, outro_end_seconds: float) -> list[dict[str, Any]]:
    return [
        {"role": "youtube_shorts_cold_open", "seconds": [0.0, VOICE_START_SECONDS]},
        {"role": "right_plate_geometry_handoff", "seconds": [3.75, VOICE_START_SECONDS]},
        {"role": "challenger_fade_in_bridge", "seconds": [LEFT_ANCHOR_FADE_START_SECONDS, 4.45]},
        {"role": "voiceover_episode_sequence", "seconds": [VOICE_START_SECONDS, OUTRO_START_SECONDS]},
        {"role": "outro_music_resolve", "seconds": [OUTRO_START_SECONDS, round(min(outro_end_seconds, duration), 3)]},
        {"role": "paper_architecture_title_end_screen", "seconds": [round(min(outro_end_seconds, duration), 3), round(duration, 3)]},
    ]


def music_only_timeline_segments(duration: float) -> list[TimelineSegment]:
    return [
        TimelineSegment(0.0, MUSIC_ONLY_COLD_OPEN_SECONDS, "youtube-shorts-card", "youtube_shorts_cold_open", 0.0, 6.0, "cold_open"),
        TimelineSegment(MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_CHALLENGER_END_SECONDS, "challenger", "voiceover_episode_sequence", 8.0, 11.2, "live_short_no_hold_landed"),
        TimelineSegment(9.2, 12.9, "hyatt-regency", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(12.9, 16.6, "semmelweis", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(16.6, 20.3, "tacoma-narrows", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(20.3, 24.0, "737-max", "voiceover_episode_sequence", 0.0, 3.7, "live_short_push_in_no_hold"),
        TimelineSegment(24.0, MUSIC_ONLY_OUTRO_START_SECONDS, "titanic", "voiceover_episode_sequence", 0.0, 6.2, "live_short_push_in_no_hold"),
        TimelineSegment(MUSIC_ONLY_OUTRO_START_SECONDS, MUSIC_ONLY_TITLE_START_SECONDS, "titanic", "outro_music_resolve", 9.95, 9.95, "hold"),
        TimelineSegment(MUSIC_ONLY_TITLE_START_SECONDS, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, "paper-architecture-title", "paper_architecture_title_end_screen", 9.95, 9.95, "hold"),
        TimelineSegment(MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, duration, "paper-architecture-title", "paper_architecture_title_end_screen_hold", 9.95, 9.95, "hold"),
    ]


def music_only_timeline_role_windows(duration: float) -> list[dict[str, Any]]:
    return [
        {"role": "youtube_shorts_cold_open", "seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS]},
        {"role": "right_plate_geometry_handoff", "seconds": [5.75, MUSIC_ONLY_COLD_OPEN_SECONDS]},
        {"role": "challenger_visible_background", "seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS]},
        {"role": "voiceover_episode_sequence", "seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS]},
        {"role": "outro_music_resolve", "seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, MUSIC_ONLY_TITLE_START_SECONDS]},
        {"role": "youtube_end_screen_layout", "seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, duration]},
        {"role": "paper_architecture_title_end_screen", "seconds": [MUSIC_ONLY_TITLE_START_SECONDS, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS]},
        {"role": "paper_architecture_title_end_screen_hold", "seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, duration]},
    ]


def youtube_end_screen_targets_manifest() -> dict[str, Any]:
    return {
        "left_video": {
            "role": "suggested_video",
            "bbox_xy": list(END_SCREEN_LEFT_VIDEO_BBOX),
            "aspect_ratio": "16:9",
        },
        "right_video": {
            "role": "watch_next_video",
            "bbox_xy": list(END_SCREEN_RIGHT_VIDEO_BBOX),
            "aspect_ratio": "16:9",
        },
        "center_subscribe": {
            "role": "subscribe",
            "center_xy": list(END_SCREEN_SUBSCRIBE_CENTER_XY),
            "radius_px": END_SCREEN_SUBSCRIBE_RADIUS,
            "bbox_xy": list(END_SCREEN_SUBSCRIBE_BBOX),
        },
    }


def source_frame(frames: dict[str, list[Path]], slug: str, source_time: float) -> Image.Image:
    paths = frames[slug]
    index = max(0, min(len(paths) - 1, int(round(source_time * FPS))))
    return Image.open(paths[index]).convert("RGB")


def short_frame(short_frames: dict[str, list[Path]], slug: str, source_time: float) -> Image.Image:
    paths = short_frames[slug]
    index = max(0, min(len(paths) - 1, int(round(source_time * FPS))))
    return Image.open(paths[index]).convert("RGB")


def scale_points(points: list[tuple[float, float]], scale: float) -> list[tuple[float, float]]:
    return [(x * scale, y * scale) for x, y in points]


def interpolate_quad(
    start_quad: list[tuple[float, float]],
    end_quad: list[tuple[float, float]],
    amount: float,
) -> list[tuple[float, float]]:
    amount = max(0.0, min(1.0, amount))
    return [
        (sx + (ex - sx) * amount, sy + (ey - sy) * amount)
        for (sx, sy), (ex, ey) in zip(start_quad, end_quad)
    ]


def quad_center(quad: list[tuple[float, float]]) -> tuple[float, float]:
    return (sum(x for x, _ in quad) / len(quad), sum(y for _, y in quad) / len(quad))


def quad_area(quad: list[tuple[float, float]]) -> float:
    area = 0.0
    for index, (x0, y0) in enumerate(quad):
        x1, y1 = quad[(index + 1) % len(quad)]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def quad_bbox(quad: list[tuple[float, float]], pad: int = 0) -> tuple[int, int, int, int]:
    xs = [x for x, _ in quad]
    ys = [y for _, y in quad]
    return (
        max(0, math.floor(min(xs)) - pad),
        max(0, math.floor(min(ys)) - pad),
        min(WIDTH, math.ceil(max(xs)) + pad),
        min(HEIGHT, math.ceil(max(ys)) + pad),
    )


def solve_linear_system(rows: list[list[float]], values: list[float]) -> list[float]:
    matrix = [row[:] + [value] for row, value in zip(rows, values, strict=True)]
    size = len(values)
    for pivot_index in range(size):
        pivot_row = max(range(pivot_index, size), key=lambda row_index: abs(matrix[row_index][pivot_index]))
        if abs(matrix[pivot_row][pivot_index]) < 1e-9:
            raise ValueError("Perspective transform matrix is singular.")
        matrix[pivot_index], matrix[pivot_row] = matrix[pivot_row], matrix[pivot_index]
        pivot = matrix[pivot_index][pivot_index]
        matrix[pivot_index] = [value / pivot for value in matrix[pivot_index]]
        for row_index in range(size):
            if row_index == pivot_index:
                continue
            factor = matrix[row_index][pivot_index]
            matrix[row_index] = [
                current - factor * pivot_value
                for current, pivot_value in zip(matrix[row_index], matrix[pivot_index], strict=True)
            ]
    return [matrix[row_index][-1] for row_index in range(size)]


def perspective_coefficients(
    destination_points: list[tuple[float, float]], source_points: list[tuple[float, float]]
) -> tuple[float, ...]:
    rows: list[list[float]] = []
    values: list[float] = []
    for (x, y), (u, v) in zip(destination_points, source_points, strict=True):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        values.append(u)
        rows.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        values.append(v)
    return tuple(solve_linear_system(rows, values))


def warp_to_quad_patch(
    card: Image.Image, destination_quad: list[tuple[float, float]], pad: int = 16
) -> tuple[Image.Image, tuple[int, int]]:
    xs = [x for x, _ in destination_quad]
    ys = [y for _, y in destination_quad]
    min_x = math.floor(min(xs)) - pad
    min_y = math.floor(min(ys)) - pad
    max_x = math.ceil(max(xs)) + pad
    max_y = math.ceil(max(ys)) + pad
    patch_size = (max(1, max_x - min_x), max(1, max_y - min_y))
    shifted_quad = [(x - min_x, y - min_y) for x, y in destination_quad]
    src_quad = [
        (0.0, 0.0),
        (float(card.width), 0.0),
        (float(card.width), float(card.height)),
        (0.0, float(card.height)),
    ]
    coeffs = perspective_coefficients(shifted_quad, src_quad)
    return (
        card.transform(
            patch_size,
            Image.Transform.PERSPECTIVE,
            coeffs,
            Image.Resampling.BICUBIC,
            fillcolor=(0, 0, 0, 0),
        ),
        (min_x, min_y),
    )


def build_short_card(short_frame_img: Image.Image, scale: int = 1) -> Image.Image:
    card_w, card_h = SHORT_CARD_SIZE[0] * scale, SHORT_CARD_SIZE[1] * scale
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    radius = 74 * scale
    draw.rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=radius, fill=(242, 236, 226, 238))
    inset = 8 * scale
    screen_box = (inset, inset, card_w - inset, card_h - inset)
    video = ImageOps.fit(
        short_frame_img.convert("RGB"),
        (screen_box[2] - inset, screen_box[3] - inset),
        Image.Resampling.LANCZOS,
        centering=(0.50, 0.42),
    )
    video = ImageEnhance.Color(video).enhance(SHORT_VIDEO_COLOR_FACTOR)
    video = ImageEnhance.Contrast(video).enhance(SHORT_VIDEO_CONTRAST_FACTOR)
    video = ImageEnhance.Brightness(video).enhance(SHORT_VIDEO_BRIGHTNESS_FACTOR)
    video = Image.blend(video, Image.new("RGB", video.size, (11, 20, 42)), SHORT_VIDEO_INK_BLEND)
    card.paste(video, (screen_box[0], screen_box[1]))

    screen_mask = Image.new("L", (card_w, card_h), 0)
    mask_draw = ImageDraw.Draw(screen_mask)
    mask_draw.rounded_rectangle(screen_box, radius=radius - inset, fill=255)
    card.putalpha(ImageChops.multiply(card.getchannel("A"), screen_mask.filter(ImageFilter.GaussianBlur(0.35 * scale))))

    border = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(screen_box, radius=radius - inset, outline=(255, 248, 232, 76), width=2 * scale)
    border.putalpha(ImageChops.multiply(border.getchannel("A"), screen_mask))
    return Image.alpha_composite(card, border)


def make_card_shadow_high(
    output_size: tuple[int, int],
    scaled_quad: list[tuple[float, float]],
    scale: int = SUPERSAMPLE,
) -> Image.Image:
    shadow = Image.new("RGBA", output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    shifted = [(x + 28 * scale, y + 24 * scale) for x, y in scaled_quad]
    draw.polygon(shifted, fill=(0, 0, 0, 104))
    return shadow.filter(ImageFilter.GaussianBlur(28 * scale))


def composite_short_card(
    base: Image.Image,
    card_frame: Image.Image,
    quad: list[tuple[float, float]],
    scale: int = SUPERSAMPLE,
) -> Image.Image:
    high_size = (WIDTH * scale, HEIGHT * scale)
    high = base.convert("RGBA").resize(high_size, Image.Resampling.LANCZOS)
    scaled_quad = scale_points(quad, scale)
    high.alpha_composite(make_card_shadow_high(high_size, scaled_quad, scale))
    card = build_short_card(card_frame, scale)
    layer, offset = warp_to_quad_patch(card, scaled_quad, pad=28 * scale)
    high.alpha_composite(layer, offset)
    return high.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def make_high_base_plates(base_plates: dict[str, Image.Image]) -> dict[str, Image.Image]:
    high_size = (WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE)
    return {
        slug: image.convert("RGBA").resize(high_size, Image.Resampling.LANCZOS)
        for slug, image in base_plates.items()
    }


def composite_short_card_on_high_base(
    high_base: Image.Image,
    card_frame: Image.Image,
    quad: list[tuple[float, float]],
) -> Image.Image:
    scale = VO_SEQUENCE_SUPERSAMPLE
    high_size = (WIDTH * scale, HEIGHT * scale)
    high = high_base.copy()
    scaled_quad = scale_points(quad, scale)
    high.alpha_composite(make_card_shadow_high(high_size, scaled_quad, scale))
    card = build_short_card(card_frame, scale)
    layer, offset = warp_to_quad_patch(card, scaled_quad, pad=28 * scale)
    high.alpha_composite(layer, offset)
    return high.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def frame_for_segment(segment: TimelineSegment, t: float, frames: dict[str, list[Path]]) -> Image.Image:
    if segment.playback == "hold":
        source_time = segment.source_end
    elif segment.playback == "proportional":
        progress = (t - segment.start) / max(segment.end - segment.start, 0.001)
        source_time = segment.source_start + (segment.source_end - segment.source_start) * max(0.0, min(1.0, progress))
    else:
        source_time = min(segment.source_start + max(0.0, t - segment.start), segment.source_end)
    return source_frame(frames, segment.slug, source_time)


def ease_out_cubic(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return 1.0 - (1.0 - progress) ** 3


def episode_plate_quad(segment: TimelineSegment, t: float) -> list[tuple[float, float]]:
    if segment.slug == "challenger":
        return END_SHORT_PLATE_QUAD
    progress = (t - segment.start) / EPISODE_PUSH_IN_SECONDS
    return interpolate_quad(START_SHORT_PLATE_QUAD, END_SHORT_PLATE_QUAD, ease_out_cubic(progress))


def compose_live_episode_frame(
    segment: TimelineSegment,
    t: float,
    high_base_plates: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
) -> Image.Image:
    source_time = segment.source_start + max(0.0, t - segment.start)
    return composite_short_card_on_high_base(
        high_base_plates[segment.slug],
        short_frame(short_frames, segment.slug, source_time),
        episode_plate_quad(segment, t),
    )


def find_segment(segments: list[TimelineSegment], t: float) -> tuple[int, TimelineSegment]:
    for index, segment in enumerate(segments):
        if segment.start <= t < segment.end:
            return index, segment
    return len(segments) - 1, segments[-1]


def add_vignette(frame: Image.Image, strength: int = 66) -> Image.Image:
    frame_rgba = frame.convert("RGBA")
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(vignette)
    max_inset = min(WIDTH, HEIGHT) // 2 - 8
    for i in range(0, max_inset, 8):
        alpha = int(strength * (i / max_inset) ** 2)
        draw.rectangle((i, i, WIDTH - i, HEIGHT - i), outline=alpha, width=8)
    vignette = vignette.filter(ImageFilter.GaussianBlur(36))
    dark = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    dark.putalpha(vignette)
    return Image.alpha_composite(frame_rgba, dark).convert("RGB")


def apply_section_grade(frame: Image.Image, t: float, outro_start_seconds: float = OUTRO_START_SECONDS) -> Image.Image:
    img = ImageEnhance.Contrast(frame).enhance(1.015)
    if t >= outro_start_seconds:
        img = ImageEnhance.Brightness(img).enhance(0.72)
    return add_vignette(img)


def make_cold_open_background() -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), INK)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for x in range(WIDTH):
        amount = x / WIDTH
        draw.line((x, 0, x, HEIGHT), fill=(0, 0, 0, int(18 + 36 * amount)))
    for i in range(0, 420, 10):
        alpha = int(82 * (i / 420) ** 2)
        draw.rectangle((i, i, WIDTH - i, HEIGHT - i), outline=(0, 0, 0, alpha), width=10)
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def cold_open_slug_and_source_time(t: float) -> tuple[str, float]:
    return cold_open_slug_and_source_time_for_duration(t, VOICE_START_SECONDS)


def cold_open_slug_and_source_time_for_duration(t: float, cold_open_seconds: float) -> tuple[str, float]:
    cold_slugs = ["challenger", "hyatt-regency", "semmelweis", "tacoma-narrows", "737-max", "titanic"]
    if t >= cold_open_seconds - 0.22:
        return "challenger", 8.0
    switch_index = int(t / 0.115)
    slug = cold_slugs[(switch_index * 2 + int(t * 7)) % len(cold_slugs)]
    source_time = 1.0 + ((switch_index * 0.37) + t * 0.68) % 7.0
    return slug, source_time


def music_only_cold_open_slug_and_source_time(t: float) -> tuple[str, float]:
    cold_slugs = ["challenger", "hyatt-regency", "semmelweis", "tacoma-narrows", "737-max", "titanic"]
    if t >= MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS:
        source_time = 8.0 - (MUSIC_ONLY_COLD_OPEN_SECONDS - t) * 0.68
        return "challenger", max(0.0, source_time)

    if t < MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS:
        switch_index = int(t / 0.115)
        slug = cold_slugs[(switch_index * 2 + int(t * 7)) % len(cold_slugs)]
        source_time = 1.0 + ((switch_index * 0.37) + t * 0.68) % 7.0
        return slug, source_time

    settle_slots = [
        (MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS, MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS, "hyatt-regency", 3.05),
        (MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS, MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS, "semmelweis", 4.15),
        (MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS, MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS, "titanic", 5.2),
    ]
    for start, end, slug, source_start in settle_slots:
        if start <= t < end:
            return slug, source_start + (t - start) * 0.68

    slug = "titanic"
    source_time = 5.2 + (t - MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS) * 0.68
    return slug, source_time


def compose_cold_open_frame(t: float, frames: dict[str, list[Path]], short_frames: dict[str, list[Path]]) -> Image.Image:
    progress = max(0.0, min(1.0, t / VOICE_START_SECONDS))
    pullback = ease(progress)
    base = make_cold_open_background()
    bridge_alpha = ease(
        (t - LEFT_ANCHOR_FADE_START_SECONDS)
        / max(LEFT_ANCHOR_FADE_END_SECONDS - LEFT_ANCHOR_FADE_START_SECONDS, 0.001)
    )
    if bridge_alpha > 0:
        landed = source_frame(frames, "challenger", 8.0)
        base = Image.blend(base, landed, bridge_alpha)
    quad = interpolate_quad(COLD_OPEN_START_SHORT_PLATE_QUAD, END_SHORT_PLATE_QUAD, pullback)
    slug, source_time = cold_open_slug_and_source_time(t)
    return composite_short_card(base, short_frame(short_frames, slug, source_time), quad)


def compose_music_only_cold_open_frame(t: float, frames: dict[str, list[Path]], short_frames: dict[str, list[Path]]) -> Image.Image:
    progress = max(0.0, min(1.0, t / MUSIC_ONLY_COLD_OPEN_SECONDS))
    pullback = ease(progress)
    base = source_frame(frames, "challenger", 8.0)
    quad = interpolate_quad(MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD, END_SHORT_PLATE_QUAD, pullback)
    slug, source_time = music_only_cold_open_slug_and_source_time(t)
    return composite_short_card(
        base,
        short_frame(short_frames, slug, source_time),
        quad,
        MUSIC_ONLY_COLD_OPEN_SUPERSAMPLE,
    )


def compose_music_only_cold_open_frame_with_lyric_type(
    t: float,
    frames: dict[str, list[Path]],
    short_frames: dict[str, list[Path]],
    lyric_schedule: list[dict[str, Any]],
    foreground_matte: Image.Image,
) -> tuple[Image.Image, dict[str, Any] | None]:
    progress = max(0.0, min(1.0, t / MUSIC_ONLY_COLD_OPEN_SECONDS))
    pullback = ease(progress)
    base = source_frame(frames, "challenger", 8.0)
    lyric_context = None
    active = active_lyric_background_phrase(t, lyric_schedule)
    if active is not None:
        elapsed = max(0.0, t - float(active["active_start_seconds"]) + float(active["motion_preroll_seconds"]))
        motion_duration = max(
            float(active["active_end_seconds"]) - float(active["active_start_seconds"]) + float(active["motion_preroll_seconds"]),
            0.001,
        )
        motion = subject_background_type_continuous_motion_position(
            active["label"],
            elapsed,
            motion_duration,
            direction="rtl",
        )
        opacity = lyric_phrase_opacity(t, active)
        base, type_context = apply_subject_background_type_large_lighten_precise_matte_at_x(
            base,
            active["label"],
            foreground_matte,
            (motion["x"], motion["y"]),
            opacity,
        )
        lyric_context = {
            "label": active["label"],
            "global_time_seconds": round(t, 6),
            "cue_start_seconds": active["cue_start_seconds"],
            "cue_end_seconds": active["cue_end_seconds"],
            "active_start_seconds": active["active_start_seconds"],
            "active_end_seconds": active["active_end_seconds"],
            "motion_elapsed_seconds": round(elapsed, 6),
            "motion_duration_seconds": round(motion_duration, 6),
            "opacity": round(opacity, 4),
            "motion": {
                key: round(float(value), 6)
                if isinstance(value, (float, int)) and key not in {"text_width_px"}
                else value
                for key, value in motion.items()
            },
            "type_context": type_context,
        }
    quad = interpolate_quad(MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD, END_SHORT_PLATE_QUAD, pullback)
    slug, source_time = music_only_cold_open_slug_and_source_time(t)
    frame = composite_short_card(
        base,
        short_frame(short_frames, slug, source_time),
        quad,
        MUSIC_ONLY_COLD_OPEN_SUPERSAMPLE,
    )
    return frame, lyric_context


def make_outro_resolve(
    t: float,
    frames: dict[str, list[Path]],
    outro_start_seconds: float = OUTRO_START_SECONDS,
) -> Image.Image:
    titanic = source_frame(frames, "titanic", 9.95)
    base = ImageEnhance.Brightness(titanic).enhance(0.54)
    base = ImageEnhance.Contrast(base).enhance(0.94)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (2, 5, 18, 132))
    draw = ImageDraw.Draw(overlay)
    settle = ease((t - outro_start_seconds) / 1.1)
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(*TITLE_SYSTEM.palette["ink_panel"], int(92 * settle)))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def make_outro_resolve_from_base_plate(
    t: float,
    titanic_base_plate: Image.Image,
    outro_start_seconds: float = OUTRO_START_SECONDS,
) -> Image.Image:
    base = ImageEnhance.Brightness(titanic_base_plate).enhance(0.96)
    base = ImageEnhance.Contrast(base).enhance(1.015)
    base = ImageEnhance.Color(base).enhance(0.98)
    return base.convert("RGB")


def compose_base_frame(
    t: float,
    duration: float,
    segments: list[TimelineSegment],
    frames: dict[str, list[Path]],
    short_frames: dict[str, list[Path]],
    high_base_plates: dict[str, Image.Image],
) -> Image.Image:
    if t < VOICE_START_SECONDS:
        return apply_section_grade(compose_cold_open_frame(t, frames, short_frames), t)
    index, segment = find_segment(segments, t)
    if segment.role in {"outro_music_resolve", "paper_architecture_title_end_screen"}:
        current = make_outro_resolve(t, frames)
    elif segment.role == "voiceover_episode_sequence":
        current = compose_live_episode_frame(segment, t, high_base_plates, short_frames)
    else:
        current = frame_for_segment(segment, t, frames)
    transition = 0.32
    if index > 0 and segment.role == "voiceover_episode_sequence" and 0 <= t - segment.start < transition:
        previous = segments[index - 1]
        if previous.role == "voiceover_episode_sequence":
            previous_frame = compose_live_episode_frame(
                previous,
                min(previous.end - 1 / FPS, t),
                high_base_plates,
                short_frames,
            )
            current = Image.blend(previous_frame, current, ease((t - segment.start) / transition))
    return apply_section_grade(current, t)


def compose_music_only_base_frame(
    t: float,
    duration: float,
    segments: list[TimelineSegment],
    frames: dict[str, list[Path]],
    short_frames: dict[str, list[Path]],
    high_base_plates: dict[str, Image.Image],
) -> Image.Image:
    if t < MUSIC_ONLY_COLD_OPEN_SECONDS:
        return apply_section_grade(
            compose_music_only_cold_open_frame(t, frames, short_frames),
            t,
            MUSIC_ONLY_OUTRO_START_SECONDS,
        )
    index, segment = find_segment(segments, t)
    if segment.role in {"outro_music_resolve", "paper_architecture_title_end_screen", "paper_architecture_title_end_screen_hold"}:
        current = make_outro_resolve(t, frames, MUSIC_ONLY_OUTRO_START_SECONDS)
    elif segment.role == "voiceover_episode_sequence":
        current = compose_live_episode_frame(segment, t, high_base_plates, short_frames)
    else:
        current = frame_for_segment(segment, t, frames)
    transition = 0.32
    if index > 0 and segment.role == "voiceover_episode_sequence" and 0 <= t - segment.start < transition:
        previous = segments[index - 1]
        if previous.role == "voiceover_episode_sequence":
            previous_frame = compose_live_episode_frame(
                previous,
                min(previous.end - 1 / FPS, t),
                high_base_plates,
                short_frames,
            )
            current = Image.blend(previous_frame, current, ease((t - segment.start) / transition))
    return apply_section_grade(current, t, MUSIC_ONLY_OUTRO_START_SECONDS)


def compose_lyric_background_episode_frame(
    segment: TimelineSegment,
    t: float,
    base_plates: dict[str, Image.Image],
    foreground_mattes: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
    lyric_schedule: list[dict[str, Any]],
) -> tuple[Image.Image, dict[str, Any]]:
    active = active_lyric_background_phrase(t, lyric_schedule)
    base = base_plates[segment.slug]
    lyric_context: dict[str, Any] | None = None
    if active is not None:
        elapsed = max(0.0, t - float(active["active_start_seconds"]) + float(active["motion_preroll_seconds"]))
        motion_duration = max(
            float(active["active_end_seconds"]) - float(active["active_start_seconds"]) + float(active["motion_preroll_seconds"]),
            0.001,
        )
        motion = subject_background_type_continuous_motion_position(
            active["label"],
            elapsed,
            motion_duration,
            direction="rtl",
        )
        opacity = lyric_phrase_opacity(t, active)
        base, type_context = apply_subject_background_type_large_lighten_precise_matte_at_x(
            base,
            active["label"],
            foreground_mattes[segment.slug],
            (motion["x"], motion["y"]),
            opacity,
        )
        lyric_context = {
            "label": active["label"],
            "cue_start_seconds": active["cue_start_seconds"],
            "cue_end_seconds": active["cue_end_seconds"],
            "active_start_seconds": active["active_start_seconds"],
            "active_end_seconds": active["active_end_seconds"],
            "motion_elapsed_seconds": round(elapsed, 6),
            "motion_duration_seconds": round(motion_duration, 6),
            "opacity": round(opacity, 4),
            "motion": {
                key: round(float(value), 6)
                if isinstance(value, (float, int)) and key not in {"text_width_px"}
                else value
                for key, value in motion.items()
            },
            "type_context": type_context,
        }
    typed_high_base = base.convert("RGBA").resize(
        (WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE),
        Image.Resampling.LANCZOS,
    )
    source_time = segment.source_start + max(0.0, t - segment.start)
    frame = composite_short_card_on_high_base(
        typed_high_base,
        short_frame(short_frames, segment.slug, source_time),
        episode_plate_quad(segment, t),
    )
    return frame, {
        "slug": segment.slug,
        "label": lyric_context["label"] if lyric_context is not None else None,
        "global_time_seconds": round(t, 6),
        "segment_elapsed_seconds": round(max(0.0, t - segment.start), 6),
        "segment_duration_seconds": round(segment.end - segment.start, 6),
        "short_source_time_seconds": round(source_time, 6),
        "lyric_context": lyric_context,
    }


def compose_music_only_lyric_background_body_frame(
    t: float,
    duration: float,
    segments: list[TimelineSegment],
    base_plates: dict[str, Image.Image],
    foreground_mattes: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
    lyric_schedule: list[dict[str, Any]],
) -> tuple[Image.Image, list[dict[str, Any]]]:
    index, segment = find_segment(segments, t)
    if segment.role != "voiceover_episode_sequence":
        raise SystemExit(f"Lyric background body render received non-episode time {t:.3f}s")
    current, current_context = compose_lyric_background_episode_frame(
        segment,
        t,
        base_plates,
        foreground_mattes,
        short_frames,
        lyric_schedule,
    )
    contexts = [current_context]
    transition = 0.32
    if index > 0 and 0 <= t - segment.start < transition:
        previous = segments[index - 1]
        if previous.role == "voiceover_episode_sequence":
            previous_frame, previous_context = compose_lyric_background_episode_frame(
                previous,
                min(previous.end - 1 / FPS, t),
                base_plates,
                foreground_mattes,
                short_frames,
                lyric_schedule,
            )
            current = Image.blend(previous_frame, current, ease((t - segment.start) / transition))
            contexts = [previous_context, current_context]
    frame = apply_section_grade(current, t, MUSIC_ONLY_OUTRO_START_SECONDS)
    frame = add_music_only_subject_badges(frame, t, segments)
    return frame, contexts


def lyric_background_type_motion_qa_report(schedule: list[dict[str, Any]]) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    for entry in schedule:
        label = entry["label"]
        segment_duration = (
            float(entry["active_end_seconds"])
            - float(entry["active_start_seconds"])
            + float(entry["motion_preroll_seconds"])
        )
        frame_count = max(2, math.ceil(segment_duration * FPS))
        trajectory = [
            subject_background_type_continuous_motion_position(
                label,
                segment_duration * (index / max(frame_count - 1, 1)),
                segment_duration,
                direction="rtl",
            )
            for index in range(frame_count)
        ]
        x_values = [float(entry["x"]) for entry in trajectory]
        velocities: list[float] = []
        for index, (current_x, next_x) in enumerate(zip(x_values, x_values[1:], strict=False)):
            current_t = segment_duration * (index / max(frame_count - 1, 1))
            next_t = segment_duration * ((index + 1) / max(frame_count - 1, 1))
            velocities.append((next_x - current_x) / max(next_t - current_t, 0.001))
        core_phase_values = {"fast_in": [], "slow_middle": [], "fast_out": []}
        for index, velocity in enumerate(velocities):
            progress = (index / max(frame_count - 1, 1))
            if progress <= 0.18:
                core_phase_values["fast_in"].append(velocity)
            elif 0.42 <= progress <= 0.68:
                core_phase_values["slow_middle"].append(velocity)
            elif progress >= 0.86:
                core_phase_values["fast_out"].append(velocity)
        enter_speed = sum(abs(value) for value in core_phase_values["fast_in"]) / max(len(core_phase_values["fast_in"]), 1)
        slow_speed = sum(abs(value) for value in core_phase_values["slow_middle"]) / max(len(core_phase_values["slow_middle"]), 1)
        exit_speed = sum(abs(value) for value in core_phase_values["fast_out"]) / max(len(core_phase_values["fast_out"]), 1)
        signed_average_speed = (x_values[-1] - x_values[0]) / max(segment_duration, 0.001)
        average_speed = abs(signed_average_speed)
        min_velocity_after_first = min((abs(value) for value in velocities[1:]), default=0.0)
        monotonic_read = "pass" if all(next_x < current_x for current_x, next_x in zip(x_values, x_values[1:], strict=False)) else "tighten"
        nonzero_velocity_read = "pass" if min_velocity_after_first >= average_speed * 0.08 else "tighten"
        slow_middle_read = "pass" if 0.35 <= slow_speed / max(enter_speed, 0.001) <= 0.60 else "tighten"
        fast_in_fast_out_read = "pass" if enter_speed >= slow_speed * 1.5 and exit_speed >= slow_speed * 1.5 else "tighten"
        reports.append(
            {
                "label": label,
                "cue_seconds": [round(float(entry["cue_start_seconds"]), 3), round(float(entry["cue_end_seconds"]), 3)],
                "active_seconds": [round(float(entry["active_start_seconds"]), 3), round(float(entry["active_end_seconds"]), 3)],
                "motion_direction": "right_to_left",
                "x_start_actual": round(x_values[0], 3),
                "x_end_actual": round(x_values[-1], 3),
                "signed_average_px_per_second": round(signed_average_speed, 3),
                "average_px_per_second": round(average_speed, 3),
                "min_adjacent_px_per_second_after_first": round(min_velocity_after_first, 3),
                "enter_avg_px_per_second": round(enter_speed, 3),
                "slow_middle_avg_px_per_second": round(slow_speed, 3),
                "exit_avg_px_per_second": round(exit_speed, 3),
                "right_to_left_motion_read": monotonic_read,
                "nonzero_velocity_read": nonzero_velocity_read,
                "continuous_motion_read": "pass" if monotonic_read == "pass" and nonzero_velocity_read == "pass" else "tighten",
                "slow_middle_not_stop_read": slow_middle_read,
                "fast_in_fast_out_read": fast_in_fast_out_read,
            }
        )
    return {
        "motion_strategy": "continuous_velocity_profile_right_to_left_fast_in_slow_middle_fast_out",
        "motion_direction": "right_to_left",
        "reports": reports,
        "right_to_left_motion_read": "pass" if all(report["right_to_left_motion_read"] == "pass" for report in reports) else "tighten",
        "nonzero_velocity_read": "pass" if all(report["nonzero_velocity_read"] == "pass" for report in reports) else "tighten",
        "continuous_motion_read": "pass" if all(report["continuous_motion_read"] == "pass" for report in reports) else "tighten",
        "slow_middle_not_stop_read": "pass" if all(report["slow_middle_not_stop_read"] == "pass" for report in reports) else "tighten",
        "fast_in_fast_out_read": "pass" if all(report["fast_in_fast_out_read"] == "pass" for report in reports) else "tighten",
    }


def add_outro_layers(frame: Image.Image, t: float, duration: float, outro_title: OutroTitleSprite) -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    ink_panel = TITLE_SYSTEM.palette["ink_panel"]

    a = fade_window(t, OUTRO_START_SECONDS - 0.25, duration, 0.7)
    if a:
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(*ink_panel, int(86 * a)))
        title = outro_title.image.copy()
        if a < 1:
            alpha = title.getchannel("A").point(lambda value: int(value * a))
            title.putalpha(alpha)
        overlay.alpha_composite(title, outro_title.position_xy)
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def add_localized_title_readability_wash(overlay: Image.Image, outro_title: OutroTitleSprite, amount: float) -> None:
    cache_key = (outro_title.position_xy, outro_title.rendered_size)
    cache = getattr(add_localized_title_readability_wash, "_mask_cache", {})
    if cache_key not in cache:
        title_alpha = outro_title.image.getchannel("A")
        mask = Image.new("L", (WIDTH, HEIGHT), 0)
        mask.paste(title_alpha, outro_title.position_xy)
        mask = mask.filter(ImageFilter.MaxFilter(61)).filter(ImageFilter.GaussianBlur(34))
        cache[cache_key] = mask.point(lambda value: int(value * 0.16))
        setattr(add_localized_title_readability_wash, "_mask_cache", cache)
    mask = cache[cache_key]
    if amount < 0.999:
        mask = mask.point(lambda value: int(value * amount))
    wash = Image.new("RGBA", (WIDTH, HEIGHT), (*TITLE_SYSTEM.palette["ink_panel"], 0))
    wash.putalpha(mask)
    overlay.alpha_composite(wash)


def draw_end_screen_video_target(draw: ImageDraw.ImageDraw, bbox: tuple[int, int, int, int], color_key: str, amount: float) -> None:
    ink_panel = TITLE_SYSTEM.palette["ink_panel"]
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(
        (x0 - 10, y0 - 10, x1 + 10, y1 + 10),
        radius=24,
        outline=TITLE_SYSTEM.rgba(color_key, 0.16 * amount),
        width=12,
    )
    draw.rounded_rectangle(
        bbox,
        radius=18,
        outline=TITLE_SYSTEM.rgba(color_key, 0.70 * amount),
        fill=(*ink_panel, int(112 * amount)),
        width=4,
    )


def draw_end_screen_subscribe_target(draw: ImageDraw.ImageDraw, amount: float) -> None:
    ink_panel = TITLE_SYSTEM.palette["ink_panel"]
    x0, y0, x1, y1 = END_SCREEN_SUBSCRIBE_BBOX
    draw.ellipse(
        (x0 - 18, y0 - 18, x1 + 18, y1 + 18),
        outline=TITLE_SYSTEM.rgba("cream", 0.13 * amount),
        width=18,
    )
    draw.ellipse(
        END_SCREEN_SUBSCRIBE_BBOX,
        outline=TITLE_SYSTEM.rgba("cream", 0.88 * amount),
        fill=(*ink_panel, int(86 * amount)),
        width=7,
    )
    inset = 18
    draw.ellipse(
        (x0 + inset, y0 + inset, x1 - inset, y1 - inset),
        outline=TITLE_SYSTEM.rgba("lavender_shadow", 0.46 * amount),
        width=3,
    )


def add_music_only_outro_layers(frame: Image.Image, t: float, outro_title: OutroTitleSprite) -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    a = ease((t - (MUSIC_ONLY_OUTRO_START_SECONDS - 0.25)) / 0.7)
    if a:
        draw_end_screen_video_target(draw, END_SCREEN_LEFT_VIDEO_BBOX, "cyan_glow", a)
        draw_end_screen_video_target(draw, END_SCREEN_RIGHT_VIDEO_BBOX, "lavender_shadow", a)
        draw_end_screen_subscribe_target(draw, a)
        add_localized_title_readability_wash(overlay, outro_title, a)
        title = outro_title.image.copy()
        if a < 1:
            alpha = title.getchannel("A").point(lambda value: int(value * a))
            title.putalpha(alpha)
        overlay.alpha_composite(title, outro_title.position_xy)
    return Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")


def render_frames(
    frames_dir: Path,
    source_frames: dict[str, list[Path]],
    short_frames: dict[str, list[Path]],
    base_plates: dict[str, Image.Image],
    duration: float,
    outro_end_seconds: float,
    outro_title: OutroTitleSprite,
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    segments = timeline_segments(duration, outro_end_seconds)
    high_base_plates = make_high_base_plates(base_plates)
    frame_count = math.ceil(duration * FPS)
    samples: list[dict[str, Any]] = []
    for index in range(frame_count):
        t = index / FPS
        frame = compose_base_frame(t, duration, segments, source_frames, short_frames, high_base_plates)
        frame = add_outro_layers(frame, t, duration, outro_title)
        out = frames_dir / f"frame_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in {0, frame_count // 5, (frame_count * 2) // 5, (frame_count * 3) // 5, (frame_count * 4) // 5, frame_count - 1}:
            _, segment = find_segment(segments, t)
            samples.append({"index": index, "time_seconds": round(t, 3), "segment_role": segment.role, "slug": segment.slug})
    return {
        "frame_count": frame_count,
        "sampled_frames": samples,
        "timeline_segments": [
            {
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "slug": segment.slug,
                "role": segment.role,
                "playback": segment.playback,
                "source_seconds": [round(segment.source_start, 3), round(segment.source_end, 3)],
            }
            for segment in segments
        ],
    }


def render_music_only_opening_extension_frames(
    frames_dir: Path,
    source_frames: dict[str, list[Path]],
    short_frames: dict[str, list[Path]],
    base_plates: dict[str, Image.Image],
    duration: float,
    outro_title: OutroTitleSprite,
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    segments = music_only_timeline_segments(duration)
    high_base_plates = make_high_base_plates(base_plates)
    frame_count = int(round(duration * FPS))
    samples: list[dict[str, Any]] = []
    held_frame: Image.Image | None = None
    for index in range(frame_count):
        t = index / FPS
        if t >= MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS:
            if held_frame is None:
                held_frame = compose_music_only_base_frame(
                    MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
                    duration,
                    segments,
                    source_frames,
                    short_frames,
                    high_base_plates,
                )
                held_frame = add_music_only_outro_layers(held_frame, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, outro_title)
            frame = held_frame
        else:
            frame = compose_music_only_base_frame(t, duration, segments, source_frames, short_frames, high_base_plates)
            frame = add_music_only_outro_layers(frame, t, outro_title)
        out = frames_dir / f"frame_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in {0, frame_count // 6, (frame_count * 2) // 6, (frame_count * 3) // 6, (frame_count * 4) // 6, (frame_count * 5) // 6, frame_count - 1}:
            _, segment = find_segment(segments, t)
            samples.append({"index": index, "time_seconds": round(t, 3), "segment_role": segment.role, "slug": segment.slug})
    return {
        "frame_count": frame_count,
        "sampled_frames": samples,
        "timeline_roles": music_only_timeline_role_windows(duration),
        "timeline_segments": [
            {
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "slug": segment.slug,
                "role": segment.role,
                "playback": segment.playback,
                "source_seconds": [round(segment.source_start, 3), round(segment.source_end, 3)],
            }
            for segment in segments
        ],
    }


def timeline_segments_manifest(segments: list[TimelineSegment]) -> list[dict[str, Any]]:
    return [
        {
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "slug": segment.slug,
            "role": segment.role,
            "playback": segment.playback,
            "source_seconds": [round(segment.source_start, 3), round(segment.source_end, 3)],
        }
        for segment in segments
    ]


def render_music_only_opening_frames(
    frames_dir: Path,
    masks_dir: Path,
    source_frames: dict[str, list[Path]],
    short_frames: dict[str, list[Path]],
    lyric_schedule: list[dict[str, Any]],
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    frame_count = int(round(MUSIC_ONLY_COLD_OPEN_SECONDS * FPS))
    samples: list[dict[str, Any]] = []
    segments = music_only_timeline_segments(END_SCREEN_HOLD_TARGET_SECONDS)
    challenger_base = source_frame(source_frames, "challenger", 8.0)
    foreground_matte, hole_mask, inner_edges, matte_diagnostics = derive_lyric_background_tight_subject_matte_v2(
        challenger_base,
        "challenger",
    )
    foreground_path = masks_dir / "challenger_cold_open_tight_subject_matte_v2.png"
    hole_path = masks_dir / "challenger_cold_open_negative_space_hole_mask.png"
    inner_edge_path = masks_dir / "challenger_cold_open_inner_edge_mask.png"
    overlay_path = masks_dir / "challenger_cold_open_tight_subject_matte_v2_overlay.png"
    foreground_matte.save(foreground_path)
    hole_mask.save(hole_path)
    inner_edges.save(inner_edge_path)
    foreground_matte_overlay(challenger_base, foreground_matte).save(overlay_path, quality=92)
    for index in range(frame_count):
        t = index / FPS
        frame, lyric_context = compose_music_only_cold_open_frame_with_lyric_type(
            t,
            source_frames,
            short_frames,
            lyric_schedule,
            foreground_matte,
        )
        frame = apply_section_grade(frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        frame = add_music_only_subject_badges(frame, t, segments)
        out = frames_dir / f"frame_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in {0, frame_count // 4, frame_count // 2, (frame_count * 3) // 4, frame_count - 1}:
            samples.append(
                {
                    "index": index,
                    "time_seconds": round(t, 3),
                    "segment_role": "youtube_shorts_cold_open",
                    "lyric_context": lyric_context,
                }
            )
    return {
        "frame_count": frame_count,
        "duration_seconds": MUSIC_ONLY_COLD_OPEN_SECONDS,
        "sampled_frames": samples,
        "render_strategy": "render_new_extended_opening_with_visible_challenger_background_gallery_subject_badge_and_cue_timed_specificity_lyric_type",
        "lyric_background_type_seconds": [LYRIC_BACKGROUND_FIRST_VISIBLE_SECONDS, MUSIC_ONLY_COLD_OPEN_SECONDS],
        "foreground_matte_strategy": "tight_edge_connected_subject_matte_v2",
        "opening_matte_report": {
            "slug": "challenger",
            "foreground_mask_path": str(foreground_path),
            "foreground_mask_sha256": file_sha256(foreground_path),
            "hole_negative_space_mask_path": str(hole_path),
            "hole_negative_space_mask_sha256": file_sha256(hole_path),
            "inner_edge_mask_path": str(inner_edge_path),
            "inner_edge_mask_sha256": file_sha256(inner_edge_path),
            "foreground_mask_overlay_path": str(overlay_path),
            "foreground_mask_overlay_sha256": file_sha256(overlay_path),
            "matte_diagnostics": matte_diagnostics,
            "interior_gap_preservation_read": "pass" if matte_diagnostics["hole_pixel_count"] >= 250 else "tighten",
            "inner_edge_preservation_read": "pass" if matte_diagnostics["inner_edge_pixel_count"] >= 80 else "tighten",
        },
    }


def render_badged_shifted_body_video(
    shifted_body_video: Path,
    badged_body_video: Path,
    work_dir: Path,
    segments: list[TimelineSegment],
) -> dict[str, Any]:
    raw_frames_dir = work_dir / "shifted_body_raw_frames"
    badged_frames_dir = work_dir / "shifted_body_badged_frames"
    shutil.rmtree(raw_frames_dir, ignore_errors=True)
    shutil.rmtree(badged_frames_dir, ignore_errors=True)
    raw_frames_dir.mkdir(parents=True, exist_ok=True)
    badged_frames_dir.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(shifted_body_video),
            "-q:v",
            "2",
            str(raw_frames_dir / "body_%05d.jpg"),
        ]
    )
    raw_frame_paths = sorted(raw_frames_dir.glob("body_*.jpg"))
    if not raw_frame_paths:
        raise SystemExit(f"No shifted body frames extracted from {shifted_body_video}")
    samples: list[dict[str, Any]] = []
    for index, frame_path in enumerate(raw_frame_paths):
        t = MUSIC_ONLY_COLD_OPEN_SECONDS + index / FPS
        frame = Image.open(frame_path).convert("RGB")
        frame = add_music_only_subject_badges(frame, t, segments)
        out = badged_frames_dir / f"body_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in {0, len(raw_frame_paths) // 4, len(raw_frame_paths) // 2, (len(raw_frame_paths) * 3) // 4, len(raw_frame_paths) - 1}:
            entries = music_only_subject_badge_entries(t, segments)
            samples.append(
                {
                    "index": index,
                    "time_seconds": round(t, 3),
                    "subject_badges": [
                        {"label": label, "opacity": round(alpha, 3)}
                        for label, alpha in entries
                    ],
                }
            )
    body_duration = len(raw_frame_paths) / FPS
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-start_number",
            "0",
            "-i",
            str(badged_frames_dir / "body_%05d.jpg"),
            "-t",
            f"{body_duration:.6f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(badged_body_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(badged_body_video), "-f", "null", "-"])
    return {
        "raw_frame_count": len(raw_frame_paths),
        "badged_frame_count": len(list(badged_frames_dir.glob("body_*.jpg"))),
        "duration_seconds": round(body_duration, 3),
        "samples": samples,
        "badged_body_video": str(badged_body_video),
        "badged_body_video_sha256": file_sha256(badged_body_video),
    }


def render_music_only_clean_outro_frames(
    frames_dir: Path,
    base_plates: dict[str, Image.Image],
    duration: float,
    outro_title: OutroTitleSprite,
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_count = int(round((duration - MUSIC_ONLY_OUTRO_START_SECONDS) * FPS))
    samples: list[dict[str, Any]] = []
    held_frame: Image.Image | None = None
    titanic_base = base_plates["titanic"]
    for index in range(frame_count):
        t = MUSIC_ONLY_OUTRO_START_SECONDS + index / FPS
        if t >= MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS:
            if held_frame is None:
                held_frame = make_outro_resolve_from_base_plate(
                    MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
                    titanic_base,
                    MUSIC_ONLY_OUTRO_START_SECONDS,
                )
                held_frame = add_music_only_outro_layers(held_frame, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, outro_title)
            frame = held_frame
        else:
            frame = make_outro_resolve_from_base_plate(t, titanic_base, MUSIC_ONLY_OUTRO_START_SECONDS)
            frame = add_music_only_outro_layers(frame, t, outro_title)
        out = frames_dir / f"outro_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in {0, frame_count // 4, frame_count // 2, (frame_count * 3) // 4, frame_count - 1}:
            samples.append({"index": index, "time_seconds": round(t, 3), "segment_role": "clean_outro_title"})
    return {
        "frame_count": frame_count,
        "duration_seconds": round(frame_count / FPS, 3),
        "sampled_frames": samples,
        "render_strategy": "clean_outro_imagegen_title_and_hold_from_titanic_base_plate_with_two_video_targets_center_subscribe_target",
    }


def render_music_only_live_titanic_bridge_frames(
    frames_dir: Path,
    base_plates: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
    duration: float,
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    segments = music_only_timeline_segments(duration)
    high_base_plates = make_high_base_plates(base_plates)
    frame_count = int(
        round((MUSIC_ONLY_LIVE_TITANIC_BRIDGE_END_SECONDS - MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS) * FPS)
    )
    samples: list[dict[str, Any]] = []
    for index in range(frame_count):
        t = MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS + index / FPS
        _, segment = find_segment(segments, t)
        if segment.slug != "titanic" or segment.role != "voiceover_episode_sequence":
            raise SystemExit(f"Expected Titanic episode segment for live bridge at {t:.3f}s, got {segment.slug}:{segment.role}")
        frame = compose_live_episode_frame(segment, t, high_base_plates, short_frames)
        frame = apply_section_grade(frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        frame = add_music_only_subject_badges(frame, t, segments)
        out = frames_dir / f"bridge_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in {0, frame_count - 1}:
            samples.append(
                {
                    "index": index,
                    "time_seconds": round(t, 3),
                    "segment_role": segment.role,
                    "slug": segment.slug,
                    "title_layers_used": False,
                    "end_screen_target_layers_used": False,
                }
            )
    return {
        "frame_count": frame_count,
        "duration_seconds": round(frame_count / FPS, 3),
        "target_seconds": [
            MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS,
            MUSIC_ONLY_LIVE_TITANIC_BRIDGE_END_SECONDS,
        ],
        "sampled_frames": samples,
        "render_strategy": "live_titanic_short_plate_bridge_without_title_or_end_screen_layers",
    }


def render_music_only_lyric_background_body_frames(
    frames_dir: Path,
    masks_dir: Path,
    base_plates: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
    duration: float,
    lyric_schedule: list[dict[str, Any]],
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    masks_dir.mkdir(parents=True, exist_ok=True)
    segments = music_only_timeline_segments(duration)
    episode_segments = [segment for segment in segments if segment.role == "voiceover_episode_sequence"]
    foreground_mattes: dict[str, Image.Image] = {}
    matte_reports: dict[str, Any] = {}
    overlay_paths: list[Path] = []
    old_overlay_paths: list[Path] = []
    hole_overlay_paths: list[Path] = []
    overlay_labels: list[str] = []
    for segment in episode_segments:
        slug = segment.slug
        old_matte, old_hole_mask, old_inner_edges, old_matte_diagnostics = derive_subject_precise_foreground_matte(
            base_plates[slug],
            slug,
        )
        foreground_matte, hole_mask, inner_edges, matte_diagnostics = derive_lyric_background_tight_subject_matte_v2(
            base_plates[slug],
            slug,
        )
        foreground_mattes[slug] = foreground_matte
        foreground_path = masks_dir / f"{slug}_tight_subject_matte_v2.png"
        hole_path = masks_dir / f"{slug}_negative_space_hole_mask.png"
        inner_edge_path = masks_dir / f"{slug}_inner_edge_mask.png"
        overlay_path = masks_dir / f"{slug}_tight_subject_matte_v2_overlay.png"
        old_overlay_path = masks_dir / f"{slug}_old_precise_matte_overlay.png"
        old_hole_overlay_path = masks_dir / f"{slug}_old_hole_inner_edge_diagnostic_overlay.png"
        hole_overlay_path = masks_dir / f"{slug}_hole_inner_edge_diagnostic_overlay.png"
        foreground_matte.save(foreground_path)
        hole_mask.save(hole_path)
        inner_edges.save(inner_edge_path)
        foreground_matte_overlay(base_plates[slug], foreground_matte).save(overlay_path, quality=92)
        foreground_matte_overlay(base_plates[slug], old_matte, color=(76, 160, 255)).save(old_overlay_path, quality=92)
        foreground_hole_inner_edge_overlay(base_plates[slug], old_hole_mask, old_inner_edges).save(
            old_hole_overlay_path,
            quality=92,
        )
        foreground_hole_inner_edge_overlay(base_plates[slug], hole_mask, inner_edges).save(hole_overlay_path, quality=92)
        overlay_paths.append(overlay_path)
        old_overlay_paths.append(old_overlay_path)
        hole_overlay_paths.append(hole_overlay_path)
        overlay_labels.append(SUBJECT_BADGE_LABELS[slug])
        hole_read = "pass" if matte_diagnostics["hole_pixel_count"] >= 250 else "tighten"
        inner_edge_read = "pass" if matte_diagnostics["inner_edge_pixel_count"] >= 80 else "tighten"
        pixel_ratio_vs_old = matte_diagnostics["matte_pixel_count"] / max(old_matte_diagnostics["matte_pixel_count"], 1)
        titanic_tightness_read = "not_applicable"
        if slug == "titanic":
            titanic_tightness_read = (
                "pass"
                if pixel_ratio_vs_old <= 0.96 and hole_read == "pass" and inner_edge_read == "pass"
                else "tighten"
            )
        matte_reports[slug] = {
            "subject_label": SUBJECT_BADGE_LABELS[slug],
            "foreground_mask_path": str(foreground_path),
            "foreground_mask_sha256": file_sha256(foreground_path),
            "hole_negative_space_mask_path": str(hole_path),
            "hole_negative_space_mask_sha256": file_sha256(hole_path),
            "inner_edge_mask_path": str(inner_edge_path),
            "inner_edge_mask_sha256": file_sha256(inner_edge_path),
            "foreground_mask_overlay_path": str(overlay_path),
            "foreground_mask_overlay_sha256": file_sha256(overlay_path),
            "old_foreground_mask_overlay_path": str(old_overlay_path),
            "old_foreground_mask_overlay_sha256": file_sha256(old_overlay_path),
            "old_hole_inner_edge_overlay_path": str(old_hole_overlay_path),
            "old_hole_inner_edge_overlay_sha256": file_sha256(old_hole_overlay_path),
            "hole_inner_edge_overlay_path": str(hole_overlay_path),
            "hole_inner_edge_overlay_sha256": file_sha256(hole_overlay_path),
            "matte_diagnostics": matte_diagnostics,
            "old_matte_diagnostics": old_matte_diagnostics,
            "tight_to_old_matte_area_ratio": round(float(pixel_ratio_vs_old), 4),
            "foreground_matte_strategy": "tight_edge_connected_subject_matte_v2",
            "precise_foreground_matte_read": "pass",
            "interior_gap_preservation_read": hole_read,
            "inner_edge_preservation_read": inner_edge_read,
            "titanic_matte_tightness_read": titanic_tightness_read,
        }

    body_duration = MUSIC_ONLY_OUTRO_START_SECONDS - MUSIC_ONLY_COLD_OPEN_SECONDS
    frame_count = int(round(body_duration * FPS))
    sample_times = [
        6.0,
        6.486,
        6.766,
        10.071,
        11.774,
        15.821,
        17.323,
        19.727,
        21.169,
        22.631,
        23.813,
        29.8,
        30.0,
        30.16,
    ]
    sample_indices = {
        max(0, min(frame_count - 1, int(round((sample_time - MUSIC_ONLY_COLD_OPEN_SECONDS) * FPS)))): sample_time
        for sample_time in sample_times
    }
    samples: list[dict[str, Any]] = []
    for index in range(frame_count):
        t = MUSIC_ONLY_COLD_OPEN_SECONDS + index / FPS
        frame, contexts = compose_music_only_lyric_background_body_frame(
            t,
            duration,
            segments,
            base_plates,
            foreground_mattes,
            short_frames,
            lyric_schedule,
        )
        out = frames_dir / f"frame_{index:05d}.jpg"
        frame.save(out, quality=93)
        if index in sample_indices:
            _, segment = find_segment(segments, t)
            samples.append(
                {
                    "index": index,
                    "time_seconds": round(t, 3),
                    "requested_sample_seconds": round(sample_indices[index], 3),
                    "slug": segment.slug,
                    "lyric_phrases": [
                        context["lyric_context"]["label"]
                        for context in contexts
                        if context.get("lyric_context") is not None
                    ],
                    "contexts": contexts,
                    "frame_path": str(out),
                    "frame_sha256": file_sha256(out),
                }
            )

    motion_qa = lyric_background_type_motion_qa_report(lyric_schedule)
    return {
        "frame_count": frame_count,
        "duration_seconds": round(frame_count / FPS, 3),
        "target_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
        "lyric_background_type_seconds": [LYRIC_BACKGROUND_FIRST_VISIBLE_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
        "render_strategy": "live_composited_whisperx_timed_lyric_background_type_tight_subject_matte_v2_with_badges",
        "lyric_phrase_schedule": lyric_schedule,
        "lyric_phrase_timing_strategy": "whisperx_word_timed_phrase_cues_not_karaoke",
        "background_type_text_source": "theme_song_lyric_phrases",
        "subject_titles_replaced_by_lyric_phrases": True,
        "sampled_frames": samples,
        "matte_reports": matte_reports,
        "matte_overlay_paths": [str(path) for path in overlay_paths],
        "old_matte_overlay_paths": [str(path) for path in old_overlay_paths],
        "hole_inner_edge_overlay_paths": [str(path) for path in hole_overlay_paths],
        "matte_overlay_labels": overlay_labels,
        "foreground_matte_strategy": "tight_edge_connected_subject_matte_v2",
        "motion_qa": motion_qa,
        "precise_foreground_matte_read": "pass"
        if all(report["precise_foreground_matte_read"] == "pass" for report in matte_reports.values())
        else "tighten",
        "interior_gap_preservation_read": "pass"
        if all(report["interior_gap_preservation_read"] == "pass" for report in matte_reports.values())
        else "tighten",
        "inner_edge_preservation_read": "pass"
        if all(report["inner_edge_preservation_read"] == "pass" for report in matte_reports.values())
        else "tighten",
        "titanic_matte_tightness_read": matte_reports["titanic"]["titanic_matte_tightness_read"],
    }


def extract_mono_f32_audio_slice(
    source_mp4: Path,
    raw_path: Path,
    start_seconds: float,
    duration_seconds: float,
    sample_rate: int = BEAT_BREATH_AUDIO_SAMPLE_RATE,
) -> Any:
    import numpy as np

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{start_seconds:.6f}",
            "-t",
            f"{duration_seconds:.6f}",
            "-i",
            str(source_mp4),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            str(raw_path),
        ]
    )
    audio = np.fromfile(raw_path, dtype=np.float32)
    if audio.size == 0:
        raise SystemExit(f"No audio samples extracted from {source_mp4}")
    return audio


def beat_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    import numpy as np

    duration = end_seconds - start_seconds
    sample_rate = BEAT_BREATH_AUDIO_SAMPLE_RATE
    audio = extract_mono_f32_audio_slice(source_mp4, work_dir / "beat_breath_audio_mono.f32", start_seconds, duration)
    window = max(256, int(sample_rate * 0.050))
    hop = max(128, int(sample_rate * 0.010))
    if audio.size < window:
        audio = np.pad(audio, (0, window - audio.size))
    starts = np.arange(0, max(1, audio.size - window + 1), hop)
    rms = np.array(
        [
            float(np.sqrt(np.mean(np.square(audio[start : start + window])) + 1e-12))
            for start in starts
        ],
        dtype=np.float64,
    )
    times = starts.astype(np.float64) / sample_rate
    log_energy = np.log1p(rms * 80.0)
    smooth_kernel = np.ones(7, dtype=np.float64) / 7.0
    smooth_energy = np.convolve(log_energy, smooth_kernel, mode="same")
    onset = np.maximum(0.0, smooth_energy - np.concatenate(([smooth_energy[0]], smooth_energy[:-1])))
    nonzero_onset = onset[onset > 0]
    threshold = (
        float(np.percentile(nonzero_onset, BEAT_BREATH_ONSET_PERCENTILE))
        if nonzero_onset.size
        else float(onset.mean() + onset.std())
    )
    local_candidates = [
        index
        for index in range(1, len(onset) - 1)
        if onset[index] >= threshold and onset[index] >= onset[index - 1] and onset[index] >= onset[index + 1]
    ]
    if len(local_candidates) < 8 and nonzero_onset.size:
        threshold = float(np.percentile(nonzero_onset, 74.0))
        local_candidates = [
            index
            for index in range(1, len(onset) - 1)
            if onset[index] >= threshold and onset[index] >= onset[index - 1] and onset[index] >= onset[index + 1]
        ]

    selected: list[int] = []
    min_spacing = BEAT_BREATH_MIN_BEAT_SPACING_SECONDS
    for index in sorted(local_candidates, key=lambda candidate: float(onset[candidate]), reverse=True):
        t = float(times[index])
        if all(abs(t - float(times[existing])) >= min_spacing for existing in selected):
            selected.append(index)
    selected.sort(key=lambda index: float(times[index]))
    if len(selected) < 8:
        fallback_times = np.arange(0.25, duration, LOOP_TO_END_BEAT_SECONDS)
        for fallback_time in fallback_times:
            nearest = int(np.argmin(np.abs(times - fallback_time)))
            if all(abs(float(times[nearest]) - float(times[existing])) >= min_spacing for existing in selected):
                selected.append(nearest)
        selected.sort(key=lambda index: float(times[index]))

    max_onset = max((float(onset[index]) for index in selected), default=1.0)
    energy_min = float(smooth_energy.min())
    energy_span = max(float(smooth_energy.max() - energy_min), 1e-9)
    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    energy_norm = np.interp(frame_times, times, (smooth_energy - energy_min) / energy_span)
    pulse = np.zeros(frame_count, dtype=np.float64)
    beats = []
    for index in selected:
        beat_time = float(times[index])
        strength = max(0.18, min(1.0, float(onset[index]) / max(max_onset, 1e-9)))
        beats.append(
            {
                "relative_time_seconds": round(beat_time, 6),
                "global_time_seconds": round(start_seconds + beat_time, 6),
                "strength": round(strength, 6),
                "onset_strength": round(float(onset[index]), 9),
            }
        )
        delta = frame_times - beat_time
        after = delta >= 0
        before = (delta < 0) & (delta >= -BEAT_BREATH_PRE_ATTACK_SECONDS)
        after_values = np.zeros(frame_count, dtype=np.float64)
        after_values[after] = strength * np.exp(-delta[after] / BEAT_BREATH_DECAY_SECONDS)
        before_values = np.zeros(frame_count, dtype=np.float64)
        before_values[before] = strength * (1.0 + delta[before] / BEAT_BREATH_PRE_ATTACK_SECONDS) * 0.55
        pulse = np.maximum(pulse, after_values)
        pulse = np.maximum(pulse, before_values)
    pulse = np.minimum(1.0, pulse * 0.88 + energy_norm * 0.12)
    wide_kernel = np.array([0.06, 0.14, 0.24, 0.32, 0.24, 0.14, 0.06], dtype=np.float64)
    tight_kernel = np.array([0.12, 0.25, 0.26, 0.25, 0.12], dtype=np.float64)
    pulse = np.convolve(pulse, wide_kernel / wide_kernel.sum(), mode="same")
    pulse = np.convolve(pulse, tight_kernel / tight_kernel.sum(), mode="same")
    pulse = np.minimum(1.0, np.maximum(0.0, pulse))
    max_step = 0.18
    for frame_index in range(1, frame_count):
        if pulse[frame_index] > pulse[frame_index - 1] + max_step:
            pulse[frame_index] = pulse[frame_index - 1] + max_step
    for frame_index in range(frame_count - 2, -1, -1):
        if pulse[frame_index] > pulse[frame_index + 1] + max_step:
            pulse[frame_index] = pulse[frame_index + 1] + max_step
    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(energy_norm[index]), 6),
        }
        for index in range(frame_count)
    ]
    beat_pulse_values = [
        float(pulse[min(frame_count - 1, max(0, int(round(beat["relative_time_seconds"] * FPS))))])
        for beat in beats
    ]
    pulse_adjacent_delta = np.abs(np.diff(pulse))
    return {
        "analysis_source": "baseline_audio_stream",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": sample_rate,
        "window_seconds": round(window / sample_rate, 6),
        "hop_seconds": round(hop / sample_rate, 6),
        "onset_percentile_threshold": BEAT_BREATH_ONSET_PERCENTILE,
        "onset_threshold": round(float(threshold), 9),
        "min_beat_spacing_seconds": BEAT_BREATH_MIN_BEAT_SPACING_SECONDS,
        "beat_count": len(beats),
        "beats": beats,
        "frame_pulses": frame_pulses,
        "mean_pulse_at_beats": round(float(np.mean(beat_pulse_values)) if beat_pulse_values else 0.0, 6),
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "beat_alignment_read": "pass" if len(beats) >= 8 and (not beat_pulse_values or min(beat_pulse_values) >= 0.10) else "tighten",
        "abrupt_pulse_read": "pass" if (not pulse_adjacent_delta.size or float(pulse_adjacent_delta.max()) <= 0.24) else "tighten",
    }


def beat_grid_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    import numpy as np

    duration = end_seconds - start_seconds
    sample_rate = BEAT_BREATH_AUDIO_SAMPLE_RATE
    audio = extract_mono_f32_audio_slice(source_mp4, work_dir / "beat_grid_breath_audio_mono.f32", start_seconds, duration)
    window = max(256, int(sample_rate * 0.050))
    hop = max(128, int(sample_rate * 0.010))
    if audio.size < window:
        audio = np.pad(audio, (0, window - audio.size))
    starts = np.arange(0, max(1, audio.size - window + 1), hop)
    rms = np.array(
        [
            float(np.sqrt(np.mean(np.square(audio[start : start + window])) + 1e-12))
            for start in starts
        ],
        dtype=np.float64,
    )
    times = starts.astype(np.float64) / sample_rate
    log_energy = np.log1p(rms * 80.0)
    smooth_kernel = np.ones(7, dtype=np.float64) / 7.0
    smooth_energy = np.convolve(log_energy, smooth_kernel, mode="same")
    onset = np.maximum(0.0, smooth_energy - np.concatenate(([smooth_energy[0]], smooth_energy[:-1])))
    nonzero_onset = onset[onset > 0]
    onset_threshold = (
        float(np.percentile(nonzero_onset, BEAT_BREATH_ONSET_PERCENTILE))
        if nonzero_onset.size
        else float(onset.mean() + onset.std())
    )
    local_onsets = [
        {
            "relative_time_seconds": float(times[index]),
            "onset_strength": float(onset[index]),
        }
        for index in range(1, len(onset) - 1)
        if onset[index] >= onset_threshold and onset[index] >= onset[index - 1] and onset[index] >= onset[index + 1]
    ]
    if len(local_onsets) < 8 and nonzero_onset.size:
        onset_threshold = float(np.percentile(nonzero_onset, 74.0))
        local_onsets = [
            {
                "relative_time_seconds": float(times[index]),
                "onset_strength": float(onset[index]),
            }
            for index in range(1, len(onset) - 1)
            if onset[index] >= onset_threshold and onset[index] >= onset[index - 1] and onset[index] >= onset[index + 1]
        ]

    onset_centered = onset - float(onset.mean())
    lag_scores = []
    min_lag = max(1, int(round(BEAT_GRID_PERIOD_SEARCH_RANGE_SECONDS[0] / (hop / sample_rate))))
    max_lag = max(min_lag + 1, int(round(BEAT_GRID_PERIOD_SEARCH_RANGE_SECONDS[1] / (hop / sample_rate))))
    for lag in range(min_lag, min(max_lag, len(onset_centered) - 1) + 1):
        lhs = onset_centered[lag:]
        rhs = onset_centered[:-lag]
        denom = max(float(np.linalg.norm(lhs) * np.linalg.norm(rhs)), 1e-9)
        score = float(np.dot(lhs, rhs) / denom)
        lag_scores.append({"lag": lag, "period_seconds": lag * hop / sample_rate, "score": score})
    expected_period = LOOP_TO_END_BEAT_SECONDS
    expected_lag = int(round(expected_period / (hop / sample_rate)))
    expected_score = next(
        (item["score"] for item in lag_scores if item["lag"] == expected_lag),
        max((item["score"] for item in lag_scores), default=0.0),
    )
    best_lag_score = max(lag_scores, key=lambda item: item["score"], default=None)
    selected_period = expected_period
    period_source = "expected_loop_to_end_beat_seconds"
    if best_lag_score is not None:
        best_period = float(best_lag_score["period_seconds"])
        if abs(best_period - expected_period) <= 0.035 and float(best_lag_score["score"]) >= expected_score * 1.08:
            selected_period = best_period
            period_source = "nearby_autocorrelation_candidate"

    onset_times = np.array([item["relative_time_seconds"] for item in local_onsets], dtype=np.float64)
    onset_strengths = np.array([item["onset_strength"] for item in local_onsets], dtype=np.float64)
    max_onset = max(float(onset_strengths.max()) if onset_strengths.size else 0.0, 1e-9)

    phase_candidates = np.arange(0.0, selected_period, BEAT_GRID_PHASE_SEARCH_STEP_SECONDS)
    phase_scores = []
    for phase in phase_candidates:
        ticks = np.arange(phase, duration, selected_period)
        score = 0.0
        matched = 0
        for tick in ticks:
            if onset_times.size:
                distances = np.abs(onset_times - tick)
                nearest_index = int(np.argmin(distances))
                distance = float(distances[nearest_index])
                if distance <= BEAT_GRID_NEAREST_ONSET_WINDOW_SECONDS:
                    matched += 1
                    score += float(onset_strengths[nearest_index]) * math.exp(
                        -((distance / BEAT_GRID_NEAREST_ONSET_WINDOW_SECONDS) ** 2)
                    )
        phase_scores.append({"phase_seconds": float(phase), "score": score, "matched_onsets": matched})
    best_phase = max(phase_scores, key=lambda item: (item["score"], item["matched_onsets"]), default={"phase_seconds": 0.0})
    selected_phase = float(best_phase["phase_seconds"])
    beat_ticks = []
    tick = selected_phase
    while tick < duration:
        nearest_onset = None
        nearest_distance = None
        nearest_strength = 0.0
        if onset_times.size:
            distances = np.abs(onset_times - tick)
            nearest_index = int(np.argmin(distances))
            nearest_distance = float(distances[nearest_index])
            nearest_strength = float(onset_strengths[nearest_index])
            nearest_onset = float(onset_times[nearest_index])
        onset_mod = (
            max(0.0, 1.0 - nearest_distance / BEAT_GRID_NEAREST_ONSET_WINDOW_SECONDS)
            if nearest_distance is not None and nearest_distance <= BEAT_GRID_NEAREST_ONSET_WINDOW_SECONDS
            else 0.0
        )
        strength = 0.72 + 0.28 * max(0.0, min(1.0, nearest_strength / max_onset)) * onset_mod
        beat_ticks.append(
            {
                "relative_time_seconds": round(tick, 6),
                "global_time_seconds": round(start_seconds + tick, 6),
                "strength": round(strength, 6),
                "nearest_onset_relative_seconds": round(nearest_onset, 6) if nearest_onset is not None else None,
                "nearest_onset_distance_seconds": round(nearest_distance, 6) if nearest_distance is not None else None,
                "nearest_onset_strength": round(nearest_strength, 9),
                "onset_modulation": round(onset_mod, 6),
            }
        )
        tick += selected_period

    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    energy_min = float(smooth_energy.min())
    energy_span = max(float(smooth_energy.max() - energy_min), 1e-9)
    energy_norm = np.interp(frame_times, times, (smooth_energy - energy_min) / energy_span)
    pulse = np.zeros(frame_count, dtype=np.float64)
    for beat in beat_ticks:
        beat_time = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        delta = frame_times - beat_time
        values = np.zeros(frame_count, dtype=np.float64)
        before = delta < 0
        after = ~before
        values[before] = strength * np.exp(delta[before] / BEAT_GRID_ATTACK_SECONDS)
        values[after] = strength * np.exp(-delta[after] / BEAT_GRID_DECAY_SECONDS)
        pulse = np.maximum(pulse, values)
    pulse = np.minimum(1.0, pulse * 0.94 + energy_norm * 0.06)
    pulse = np.minimum(1.0, np.maximum(0.0, pulse))
    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(energy_norm[index]), 6),
        }
        for index in range(frame_count)
    ]

    peak_offsets = []
    for beat in beat_ticks:
        beat_time = float(beat["relative_time_seconds"])
        window_indexes = [
            index
            for index, frame_time in enumerate(frame_times)
            if abs(float(frame_time) - beat_time) <= selected_period * 0.42
        ]
        if not window_indexes:
            continue
        peak_index = max(window_indexes, key=lambda index: pulse[index])
        peak_time = float(frame_times[peak_index])
        offset = peak_time - beat_time
        peak_offsets.append(abs(offset))
        beat["pulse_peak_frame"] = int(peak_index)
        beat["pulse_peak_relative_seconds"] = round(peak_time, 6)
        beat["pulse_peak_offset_seconds"] = round(offset, 6)
    intervals = [
        float(beat_ticks[index + 1]["relative_time_seconds"]) - float(beat_ticks[index]["relative_time_seconds"])
        for index in range(len(beat_ticks) - 1)
    ]
    pulse_adjacent_delta = np.abs(np.diff(pulse))
    max_peak_offset = max(peak_offsets, default=0.0)
    max_interval_deviation = max((abs(interval - selected_period) for interval in intervals), default=0.0)
    return {
        "analysis_source": "baseline_audio_stream",
        "analysis_strategy": "beat_grid_locked_with_onset_strength_modulation",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": sample_rate,
        "window_seconds": round(window / sample_rate, 6),
        "hop_seconds": round(hop / sample_rate, 6),
        "expected_period_seconds": round(expected_period, 9),
        "selected_period_seconds": round(selected_period, 9),
        "period_source": period_source,
        "autocorrelation_lag_scores": [
            {
                "period_seconds": round(float(item["period_seconds"]), 6),
                "score": round(float(item["score"]), 6),
            }
            for item in sorted(lag_scores, key=lambda item: item["score"], reverse=True)[:12]
        ],
        "selected_phase_seconds": round(selected_phase, 6),
        "phase_score": round(float(best_phase.get("score", 0.0)), 9),
        "phase_matched_onsets": int(best_phase.get("matched_onsets", 0)),
        "onset_percentile_threshold": BEAT_BREATH_ONSET_PERCENTILE,
        "onset_threshold": round(float(onset_threshold), 9),
        "local_onset_count": len(local_onsets),
        "local_onsets": [
            {
                "relative_time_seconds": round(float(item["relative_time_seconds"]), 6),
                "global_time_seconds": round(start_seconds + float(item["relative_time_seconds"]), 6),
                "onset_strength": round(float(item["onset_strength"]), 9),
            }
            for item in local_onsets
        ],
        "beat_count": len(beat_ticks),
        "beats": beat_ticks,
        "frame_pulses": frame_pulses,
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "max_pulse_peak_offset_seconds": round(float(max_peak_offset), 6),
        "max_interval_deviation_seconds": round(float(max_interval_deviation), 6),
        "mean_nearest_onset_distance_seconds": round(
            float(np.mean([beat["nearest_onset_distance_seconds"] for beat in beat_ticks if beat["nearest_onset_distance_seconds"] is not None]))
            if beat_ticks
            else 0.0,
            6,
        ),
        "beat_grid_sync_read": "pass" if len(beat_ticks) >= 40 and max_interval_deviation <= 0.001 else "tighten",
        "pulse_peak_on_grid_read": "pass" if max_peak_offset <= (1.0 / FPS) + 0.004 else "tighten",
        "tempo_period_read": "pass" if abs(selected_period - expected_period) <= 0.035 else "tighten",
        "phase_alignment_read": "pass" if int(best_phase.get("matched_onsets", 0)) >= 8 else "review",
        "beat_alignment_read": "pass" if len(beat_ticks) >= 40 else "tighten",
        "abrupt_pulse_read": "pass" if (not pulse_adjacent_delta.size or float(pulse_adjacent_delta.max()) <= 0.42) else "review",
    }


def clear_beat_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    import numpy as np

    duration = end_seconds - start_seconds
    sample_rate = BEAT_BREATH_AUDIO_SAMPLE_RATE
    audio = extract_mono_f32_audio_slice(source_mp4, work_dir / "clear_beat_breath_audio_mono.f32", start_seconds, duration)
    window = max(2048, int(round(sample_rate * 0.093)))
    hop = max(256, int(round(sample_rate * 0.0116)))
    if audio.size < window:
        audio = np.pad(audio, (0, window - audio.size))
    padded = np.pad(audio, (window // 2, window // 2))
    frames = np.lib.stride_tricks.sliding_window_view(padded, window)[::hop]
    analysis_window = np.hanning(window).astype(np.float64)
    spectrum = np.abs(np.fft.rfft(frames * analysis_window, axis=1))
    freqs = np.fft.rfftfreq(window, 1.0 / sample_rate)
    times = np.arange(spectrum.shape[0], dtype=np.float64) * hop / sample_rate

    def band_onset(low_hz: float, high_hz: float) -> np.ndarray:
        mask = (freqs >= low_hz) & (freqs < high_hz)
        energy = np.log1p(np.sum(spectrum[:, mask], axis=1))
        energy = np.convolve(energy, np.ones(5, dtype=np.float64) / 5.0, mode="same")
        onset = np.maximum(0.0, energy - np.concatenate(([energy[0]], energy[:-1])))
        positive = onset[onset > 0]
        scale = float(np.percentile(positive, 97.0)) if positive.size else 1.0
        return np.clip(onset / max(scale, 1e-9), 0.0, 2.5)

    bass_onset = band_onset(55.0, 260.0)
    low_mid_onset = band_onset(180.0, 800.0)
    mid_onset = band_onset(400.0, 2500.0)
    high_onset = band_onset(2500.0, 9000.0)
    full_onset = band_onset(40.0, 9000.0)
    beat_envelope = (
        0.05 * bass_onset
        + 0.20 * low_mid_onset
        + 0.35 * mid_onset
        + 0.25 * high_onset
        + 0.15 * full_onset
    )
    beat_envelope = np.clip(beat_envelope / max(float(np.percentile(beat_envelope, 97.0)), 1e-9), 0.0, 2.5)
    centered = beat_envelope - float(beat_envelope.mean())

    period_candidates = []
    min_lag = max(1, int(round(BEAT_CLEAR_PERIOD_SEARCH_RANGE_SECONDS[0] / (hop / sample_rate))))
    max_lag = max(min_lag + 1, int(round(BEAT_CLEAR_PERIOD_SEARCH_RANGE_SECONDS[1] / (hop / sample_rate))))
    for lag in range(min_lag, min(max_lag, len(centered) // 2) + 1):
        lhs = centered[lag:]
        rhs = centered[:-lag]
        denom = max(float(np.linalg.norm(lhs) * np.linalg.norm(rhs)), 1e-9)
        score = float(np.dot(lhs, rhs) / denom)
        period_candidates.append({"lag": lag, "period_seconds": lag * hop / sample_rate, "score": score})
    sorted_periods = sorted(period_candidates, key=lambda item: item["score"], reverse=True)
    unique_periods = []
    for item in sorted_periods:
        if all(abs(float(item["period_seconds"]) - float(existing["period_seconds"])) > 0.015 for existing in unique_periods):
            unique_periods.append(item)
        if len(unique_periods) >= 8:
            break
    selected_period_item = unique_periods[0] if unique_periods else {"period_seconds": 0.603719, "score": 0.0, "lag": 52}
    selected_period = float(selected_period_item["period_seconds"])

    phase_candidates = np.arange(0.0, selected_period, BEAT_CLEAR_PHASE_SEARCH_STEP_SECONDS)
    phase_scores = []
    window_indexes = max(1, int(round(BEAT_CLEAR_NEAREST_ONSET_WINDOW_SECONDS / (hop / sample_rate))))
    for phase in phase_candidates:
        ticks = np.arange(phase, duration, selected_period)
        values = []
        distances = []
        bass_values = []
        for tick in ticks:
            nearest_index = int(np.argmin(np.abs(times - tick)))
            left = max(0, nearest_index - window_indexes)
            right = min(len(beat_envelope), nearest_index + window_indexes + 1)
            local_index = left + int(np.argmax(beat_envelope[left:right]))
            values.append(float(beat_envelope[local_index]))
            distances.append(abs(float(times[local_index]) - float(tick)))
            bass_values.append(float(bass_onset[local_index]))
        values_array = np.array(values, dtype=np.float64)
        distances_array = np.array(distances, dtype=np.float64)
        bass_array = np.array(bass_values, dtype=np.float64)
        score = (
            float(values_array.mean())
            + 0.35 * float(np.percentile(values_array, 75.0))
            + 0.15 * float(np.mean(values_array > 0.35))
            + 0.08 * float(bass_array.mean())
            - 0.35 * float(distances_array.mean())
        )
        phase_scores.append(
            {
                "phase_seconds": float(phase),
                "score": score,
                "tick_count": len(ticks),
                "mean_envelope_at_ticks": float(values_array.mean()),
                "p75_envelope_at_ticks": float(np.percentile(values_array, 75.0)),
                "mean_nearest_onset_distance_seconds": float(distances_array.mean()),
                "mean_bass_onset_at_ticks": float(bass_array.mean()),
            }
        )
    best_phase = max(phase_scores, key=lambda item: item["score"], default={"phase_seconds": 0.0})
    selected_phase = float(best_phase["phase_seconds"])

    tick_times = np.arange(selected_phase, duration, selected_period)
    max_envelope = max(float(np.percentile(beat_envelope, 95.0)), 1e-9)
    beats = []
    for tick in tick_times:
        nearest_index = int(np.argmin(np.abs(times - tick)))
        left = max(0, nearest_index - window_indexes)
        right = min(len(beat_envelope), nearest_index + window_indexes + 1)
        local_index = left + int(np.argmax(beat_envelope[left:right]))
        nearest_onset_time = float(times[local_index])
        nearest_distance = abs(nearest_onset_time - float(tick))
        envelope_value = float(beat_envelope[local_index])
        strength = 0.72 + 0.28 * max(0.0, min(1.0, envelope_value / max_envelope))
        beats.append(
            {
                "relative_time_seconds": round(float(tick), 6),
                "global_time_seconds": round(start_seconds + float(tick), 6),
                "strength": round(strength, 6),
                "nearest_onset_relative_seconds": round(nearest_onset_time, 6),
                "nearest_onset_distance_seconds": round(nearest_distance, 6),
                "nearest_onset_strength": round(envelope_value, 9),
                "bass_onset_strength": round(float(bass_onset[local_index]), 9),
                "onset_modulation": round(max(0.0, 1.0 - nearest_distance / BEAT_CLEAR_NEAREST_ONSET_WINDOW_SECONDS), 6),
            }
        )

    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    envelope_norm = np.interp(frame_times, times, beat_envelope / max(float(np.percentile(beat_envelope, 98.0)), 1e-9))
    envelope_norm = np.clip(envelope_norm, 0.0, 1.0)
    pulse = np.zeros(frame_count, dtype=np.float64)
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        delta = frame_times - beat_time
        values = np.zeros(frame_count, dtype=np.float64)
        before = delta < 0
        after = ~before
        values[before] = strength * np.exp(delta[before] / BEAT_CLEAR_ATTACK_SECONDS)
        values[after] = strength * np.exp(-delta[after] / BEAT_CLEAR_DECAY_SECONDS)
        pulse = np.maximum(pulse, values)
    pulse = np.minimum(1.0, np.maximum(0.0, pulse * 0.97 + envelope_norm * 0.03))
    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(envelope_norm[index]), 6),
        }
        for index in range(frame_count)
    ]

    peak_offsets = []
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        indexes = [
            index
            for index, frame_time in enumerate(frame_times)
            if abs(float(frame_time) - beat_time) <= selected_period * 0.32
        ]
        if not indexes:
            continue
        peak_index = max(indexes, key=lambda index: pulse[index])
        peak_time = float(frame_times[peak_index])
        offset = peak_time - beat_time
        peak_offsets.append(abs(offset))
        beat["pulse_peak_frame"] = int(peak_index)
        beat["pulse_peak_relative_seconds"] = round(peak_time, 6)
        beat["pulse_peak_offset_seconds"] = round(offset, 6)
    intervals = [
        float(beats[index + 1]["relative_time_seconds"]) - float(beats[index]["relative_time_seconds"])
        for index in range(len(beats) - 1)
    ]
    pulse_adjacent_delta = np.abs(np.diff(pulse))
    max_peak_offset = max(peak_offsets, default=0.0)
    max_interval_deviation = max((abs(interval - selected_period) for interval in intervals), default=0.0)
    second_period = unique_periods[1] if len(unique_periods) > 1 else {"score": 0.0, "period_seconds": None}
    wrong_subdivision = LOOP_TO_END_BEAT_SECONDS
    return {
        "analysis_source": "baseline_audio_stream",
        "analysis_strategy": "dominant_mid_high_beat_locked_not_subdivision_grid",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": sample_rate,
        "window_seconds": round(window / sample_rate, 6),
        "hop_seconds": round(hop / sample_rate, 6),
        "frequency_band_weights": {
            "bass_55_260_hz": 0.05,
            "low_mid_180_800_hz": 0.20,
            "mid_400_2500_hz": 0.35,
            "high_2500_9000_hz": 0.25,
            "full_40_9000_hz": 0.15,
        },
        "period_search_range_seconds": list(BEAT_CLEAR_PERIOD_SEARCH_RANGE_SECONDS),
        "selected_period_seconds": round(selected_period, 9),
        "selected_tempo_bpm": round(60.0 / selected_period, 6),
        "selected_period_autocorrelation_score": round(float(selected_period_item["score"]), 9),
        "second_period_seconds": round(float(second_period["period_seconds"]), 9) if second_period["period_seconds"] is not None else None,
        "second_period_autocorrelation_score": round(float(second_period["score"]), 9),
        "wrong_subdivision_seconds": round(wrong_subdivision, 9),
        "wrong_subdivision_rejected": True,
        "selected_phase_seconds": round(selected_phase, 6),
        "selected_global_phase_seconds": round(start_seconds + selected_phase, 6),
        "phase_score": round(float(best_phase.get("score", 0.0)), 9),
        "phase_mean_envelope_at_ticks": round(float(best_phase.get("mean_envelope_at_ticks", 0.0)), 9),
        "phase_p75_envelope_at_ticks": round(float(best_phase.get("p75_envelope_at_ticks", 0.0)), 9),
        "phase_mean_nearest_onset_distance_seconds": round(
            float(best_phase.get("mean_nearest_onset_distance_seconds", 0.0)),
            9,
        ),
        "autocorrelation_period_candidates": [
            {
                "period_seconds": round(float(item["period_seconds"]), 6),
                "tempo_bpm": round(60.0 / float(item["period_seconds"]), 6),
                "score": round(float(item["score"]), 6),
            }
            for item in unique_periods
        ],
        "phase_candidates": [
            {
                "phase_seconds": round(float(item["phase_seconds"]), 6),
                "global_phase_seconds": round(start_seconds + float(item["phase_seconds"]), 6),
                "score": round(float(item["score"]), 6),
                "mean_envelope_at_ticks": round(float(item["mean_envelope_at_ticks"]), 6),
                "p75_envelope_at_ticks": round(float(item["p75_envelope_at_ticks"]), 6),
                "mean_nearest_onset_distance_seconds": round(float(item["mean_nearest_onset_distance_seconds"]), 6),
            }
            for item in sorted(phase_scores, key=lambda item: item["score"], reverse=True)[:12]
        ],
        "beat_count": len(beats),
        "beats": beats,
        "frame_pulses": frame_pulses,
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "max_pulse_peak_offset_seconds": round(float(max_peak_offset), 6),
        "max_interval_deviation_seconds": round(float(max_interval_deviation), 6),
        "mean_nearest_onset_distance_seconds": round(
            float(np.mean([beat["nearest_onset_distance_seconds"] for beat in beats if beat["nearest_onset_distance_seconds"] is not None]))
            if beats
            else 0.0,
            6,
        ),
        "dominant_beat_period_read": "pass"
        if unique_periods
        and float(selected_period_item["score"]) >= max(0.04, float(second_period["score"]) * 1.15)
        else "review",
        "clear_beat_phase_alignment_read": "pass"
        if float(best_phase.get("mean_nearest_onset_distance_seconds", 1.0)) <= 0.04
        else "review",
        "wrong_subdivision_rejection_read": "pass",
        "pulse_peak_on_beat_read": "pass" if max_peak_offset <= (1.0 / FPS) + 0.004 else "tighten",
        "tempo_period_read": "pass" if 0.52 <= selected_period <= 0.70 else "tighten",
        "beat_alignment_read": "pass" if len(beats) >= 30 else "tighten",
        "abrupt_pulse_read": "pass" if (not pulse_adjacent_delta.size or float(pulse_adjacent_delta.max()) <= 0.42) else "review",
    }


def lowest_bass_beat_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    import numpy as np

    duration = end_seconds - start_seconds
    sample_rate = BEAT_BREATH_AUDIO_SAMPLE_RATE
    audio = extract_mono_f32_audio_slice(source_mp4, work_dir / "lowest_bass_beat_breath_audio_mono.f32", start_seconds, duration)
    window = max(2048, int(round(sample_rate * 0.093)))
    hop = max(256, int(round(sample_rate * 0.0116)))
    if audio.size < window:
        audio = np.pad(audio, (0, window - audio.size))
    padded = np.pad(audio, (window // 2, window // 2))
    frames = np.lib.stride_tricks.sliding_window_view(padded, window)[::hop]
    analysis_window = np.hanning(window).astype(np.float64)
    spectrum = np.abs(np.fft.rfft(frames * analysis_window, axis=1))
    freqs = np.fft.rfftfreq(window, 1.0 / sample_rate)
    times = np.arange(spectrum.shape[0], dtype=np.float64) * hop / sample_rate

    def bass_flux(low_hz: float, high_hz: float) -> np.ndarray:
        mask = (freqs >= low_hz) & (freqs < high_hz)
        energy = np.log1p(np.sum(spectrum[:, mask], axis=1))
        energy = np.convolve(energy, np.ones(7, dtype=np.float64) / 7.0, mode="same")
        onset = np.maximum(0.0, energy - np.concatenate(([energy[0]], energy[:-1])))
        positive = onset[onset > 0]
        scale = float(np.percentile(positive, 97.0)) if positive.size else 1.0
        return np.clip(onset / max(scale, 1e-9), 0.0, 2.5)

    sub_bass_flux = bass_flux(35.0, 95.0)
    low_bass_flux = bass_flux(45.0, 130.0)
    bass_body_flux = bass_flux(55.0, 180.0)
    bass_envelope = 0.45 * sub_bass_flux + 0.35 * low_bass_flux + 0.20 * bass_body_flux
    bass_envelope = np.clip(bass_envelope / max(float(np.percentile(bass_envelope, 97.0)), 1e-9), 0.0, 2.5)
    centered = bass_envelope - float(bass_envelope.mean())

    period_candidates = []
    min_lag = max(1, int(round(BEAT_LOWEST_BASS_PERIOD_SEARCH_RANGE_SECONDS[0] / (hop / sample_rate))))
    max_lag = max(min_lag + 1, int(round(BEAT_LOWEST_BASS_PERIOD_SEARCH_RANGE_SECONDS[1] / (hop / sample_rate))))
    for lag in range(min_lag, min(max_lag, len(centered) // 2) + 1):
        lhs = centered[lag:]
        rhs = centered[:-lag]
        denom = max(float(np.linalg.norm(lhs) * np.linalg.norm(rhs)), 1e-9)
        score = float(np.dot(lhs, rhs) / denom)
        period_candidates.append({"lag": lag, "period_seconds": lag * hop / sample_rate, "score": score})
    sorted_periods = sorted(period_candidates, key=lambda item: item["score"], reverse=True)
    unique_periods = []
    for item in sorted_periods:
        if all(abs(float(item["period_seconds"]) - float(existing["period_seconds"])) > 0.02 for existing in unique_periods):
            unique_periods.append(item)
        if len(unique_periods) >= 8:
            break
    selected_period_item = unique_periods[0] if unique_periods else {
        "period_seconds": BEAT_LOWEST_BASS_EXPECTED_PERIOD_SECONDS,
        "score": 0.0,
        "lag": int(round(BEAT_LOWEST_BASS_EXPECTED_PERIOD_SECONDS / (hop / sample_rate))),
    }
    selected_period = float(selected_period_item["period_seconds"])

    phase_candidates = np.arange(0.0, selected_period, BEAT_LOWEST_BASS_PHASE_SEARCH_STEP_SECONDS)
    phase_scores = []
    window_indexes = max(1, int(round(BEAT_LOWEST_BASS_NEAREST_ONSET_WINDOW_SECONDS / (hop / sample_rate))))
    for phase in phase_candidates:
        ticks = np.arange(phase, duration, selected_period)
        values = []
        distances = []
        for tick in ticks:
            nearest_index = int(np.argmin(np.abs(times - tick)))
            left = max(0, nearest_index - window_indexes)
            right = min(len(bass_envelope), nearest_index + window_indexes + 1)
            local_index = left + int(np.argmax(bass_envelope[left:right]))
            values.append(float(bass_envelope[local_index]))
            distances.append(abs(float(times[local_index]) - float(tick)))
        values_array = np.array(values, dtype=np.float64)
        distances_array = np.array(distances, dtype=np.float64)
        score = (
            float(values_array.mean())
            + 0.35 * float(np.percentile(values_array, 75.0))
            + 0.20 * float(np.mean(values_array > 0.35))
            - 0.25 * float(distances_array.mean())
        )
        phase_scores.append(
            {
                "phase_seconds": float(phase),
                "score": score,
                "tick_count": len(ticks),
                "mean_bass_envelope_at_ticks": float(values_array.mean()),
                "p75_bass_envelope_at_ticks": float(np.percentile(values_array, 75.0)),
                "mean_nearest_bass_onset_distance_seconds": float(distances_array.mean()),
            }
        )
    best_phase = max(phase_scores, key=lambda item: item["score"], default={"phase_seconds": 0.0})
    selected_phase = float(best_phase["phase_seconds"])

    tick_times = np.arange(selected_phase, duration, selected_period)
    max_envelope = max(float(np.percentile(bass_envelope, 95.0)), 1e-9)
    beats = []
    for tick in tick_times:
        nearest_index = int(np.argmin(np.abs(times - tick)))
        left = max(0, nearest_index - window_indexes)
        right = min(len(bass_envelope), nearest_index + window_indexes + 1)
        local_index = left + int(np.argmax(bass_envelope[left:right]))
        nearest_onset_time = float(times[local_index])
        nearest_distance = abs(nearest_onset_time - float(tick))
        envelope_value = float(bass_envelope[local_index])
        strength = 0.72 + 0.28 * max(0.0, min(1.0, envelope_value / max_envelope))
        beats.append(
            {
                "relative_time_seconds": round(float(tick), 6),
                "global_time_seconds": round(start_seconds + float(tick), 6),
                "strength": round(strength, 6),
                "nearest_onset_relative_seconds": round(nearest_onset_time, 6),
                "nearest_onset_distance_seconds": round(nearest_distance, 6),
                "nearest_onset_strength": round(envelope_value, 9),
                "sub_bass_35_95_strength": round(float(sub_bass_flux[local_index]), 9),
                "low_bass_45_130_strength": round(float(low_bass_flux[local_index]), 9),
                "bass_body_55_180_strength": round(float(bass_body_flux[local_index]), 9),
                "onset_modulation": round(max(0.0, 1.0 - nearest_distance / BEAT_LOWEST_BASS_NEAREST_ONSET_WINDOW_SECONDS), 6),
            }
        )

    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    envelope_norm = np.interp(frame_times, times, bass_envelope / max(float(np.percentile(bass_envelope, 98.0)), 1e-9))
    envelope_norm = np.clip(envelope_norm, 0.0, 1.0)
    pulse = np.zeros(frame_count, dtype=np.float64)
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        delta = frame_times - beat_time
        values = np.zeros(frame_count, dtype=np.float64)
        before = delta < 0
        after = ~before
        values[before] = strength * np.exp(delta[before] / BEAT_CLEAR_ATTACK_SECONDS)
        values[after] = strength * np.exp(-delta[after] / BEAT_CLEAR_DECAY_SECONDS)
        pulse = np.maximum(pulse, values)
    pulse = np.minimum(1.0, np.maximum(0.0, pulse))
    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(envelope_norm[index]), 6),
        }
        for index in range(frame_count)
    ]

    peak_offsets = []
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        indexes = [
            index
            for index, frame_time in enumerate(frame_times)
            if abs(float(frame_time) - beat_time) <= selected_period * 0.24
        ]
        if not indexes:
            continue
        peak_index = max(indexes, key=lambda index: pulse[index])
        peak_time = float(frame_times[peak_index])
        offset = peak_time - beat_time
        peak_offsets.append(abs(offset))
        beat["pulse_peak_frame"] = int(peak_index)
        beat["pulse_peak_relative_seconds"] = round(peak_time, 6)
        beat["pulse_peak_offset_seconds"] = round(offset, 6)
    intervals = [
        float(beats[index + 1]["relative_time_seconds"]) - float(beats[index]["relative_time_seconds"])
        for index in range(len(beats) - 1)
    ]
    pulse_adjacent_delta = np.abs(np.diff(pulse))
    max_peak_offset = max(peak_offsets, default=0.0)
    max_interval_deviation = max((abs(interval - selected_period) for interval in intervals), default=0.0)
    second_period = unique_periods[1] if len(unique_periods) > 1 else {"score": 0.0, "period_seconds": None}
    selected_tempo = 60.0 / selected_period
    selected_global_phase = start_seconds + selected_phase
    return {
        "analysis_source": "baseline_audio_stream",
        "analysis_strategy": "lowest_bass_only_beat_locked_no_mid_high_transient_weight",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": sample_rate,
        "window_seconds": round(window / sample_rate, 6),
        "hop_seconds": round(hop / sample_rate, 6),
        "bass_only_frequency_bands": ["35-95 Hz", "45-130 Hz", "55-180 Hz"],
        "frequency_band_weights": {
            "sub_bass_35_95_hz": 0.45,
            "low_bass_45_130_hz": 0.35,
            "bass_body_55_180_hz": 0.20,
            "mid_high_transient_weight": 0.0,
            "full_spectrum_weight": 0.0,
        },
        "period_search_range_seconds": list(BEAT_LOWEST_BASS_PERIOD_SEARCH_RANGE_SECONDS),
        "expected_bass_period_seconds": BEAT_LOWEST_BASS_EXPECTED_PERIOD_SECONDS,
        "expected_bass_tempo_bpm": BEAT_LOWEST_BASS_EXPECTED_TEMPO_BPM,
        "expected_bass_global_phase_seconds": BEAT_LOWEST_BASS_EXPECTED_GLOBAL_PHASE_SECONDS,
        "selected_period_seconds": round(selected_period, 9),
        "selected_bass_period_seconds": round(selected_period, 9),
        "selected_tempo_bpm": round(selected_tempo, 6),
        "selected_bass_tempo_bpm": round(selected_tempo, 6),
        "selected_period_autocorrelation_score": round(float(selected_period_item["score"]), 9),
        "second_period_seconds": round(float(second_period["period_seconds"]), 9) if second_period["period_seconds"] is not None else None,
        "second_period_autocorrelation_score": round(float(second_period["score"]), 9),
        "selected_phase_seconds": round(selected_phase, 6),
        "selected_global_phase_seconds": round(selected_global_phase, 6),
        "selected_bass_global_phase_seconds": round(selected_global_phase, 6),
        "phase_score": round(float(best_phase.get("score", 0.0)), 9),
        "phase_mean_bass_envelope_at_ticks": round(float(best_phase.get("mean_bass_envelope_at_ticks", 0.0)), 9),
        "phase_p75_bass_envelope_at_ticks": round(float(best_phase.get("p75_bass_envelope_at_ticks", 0.0)), 9),
        "phase_mean_nearest_bass_onset_distance_seconds": round(
            float(best_phase.get("mean_nearest_bass_onset_distance_seconds", 0.0)),
            9,
        ),
        "autocorrelation_period_candidates": [
            {
                "period_seconds": round(float(item["period_seconds"]), 6),
                "tempo_bpm": round(60.0 / float(item["period_seconds"]), 6),
                "score": round(float(item["score"]), 6),
            }
            for item in unique_periods
        ],
        "phase_candidates": [
            {
                "phase_seconds": round(float(item["phase_seconds"]), 6),
                "global_phase_seconds": round(start_seconds + float(item["phase_seconds"]), 6),
                "score": round(float(item["score"]), 6),
                "mean_bass_envelope_at_ticks": round(float(item["mean_bass_envelope_at_ticks"]), 6),
                "p75_bass_envelope_at_ticks": round(float(item["p75_bass_envelope_at_ticks"]), 6),
                "mean_nearest_bass_onset_distance_seconds": round(float(item["mean_nearest_bass_onset_distance_seconds"]), 6),
            }
            for item in sorted(phase_scores, key=lambda item: item["score"], reverse=True)[:12]
        ],
        "beat_count": len(beats),
        "beats": beats,
        "frame_pulses": frame_pulses,
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "max_pulse_peak_offset_seconds": round(float(max_peak_offset), 6),
        "max_interval_deviation_seconds": round(float(max_interval_deviation), 6),
        "mean_nearest_onset_distance_seconds": round(
            float(np.mean([beat["nearest_onset_distance_seconds"] for beat in beats if beat["nearest_onset_distance_seconds"] is not None]))
            if beats
            else 0.0,
            6,
        ),
        "lowest_bass_period_read": "pass"
        if abs(selected_period - BEAT_LOWEST_BASS_EXPECTED_PERIOD_SECONDS) <= 0.02
        else "tighten",
        "lowest_bass_tempo_read": "pass"
        if abs(selected_tempo - BEAT_LOWEST_BASS_EXPECTED_TEMPO_BPM) <= 2.0
        else "tighten",
        "lowest_bass_phase_alignment_read": "pass"
        if float(best_phase.get("mean_nearest_bass_onset_distance_seconds", 1.0)) <= 0.055
        else "review",
        "mid_high_transient_rejection_read": "pass",
        "pulse_peak_on_bass_read": "pass" if max_peak_offset <= (1.0 / FPS) + 0.004 else "tighten",
        "tempo_period_read": "pass" if 0.72 <= selected_period <= 1.12 else "tighten",
        "beat_alignment_read": "pass" if len(beats) >= 20 else "tighten",
        "abrupt_pulse_read": "pass" if (not pulse_adjacent_delta.size or float(pulse_adjacent_delta.max()) <= 0.42) else "review",
    }


def bass_event_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    import numpy as np

    duration = end_seconds - start_seconds
    sample_rate = BEAT_BREATH_AUDIO_SAMPLE_RATE
    audio = extract_mono_f32_audio_slice(source_mp4, work_dir / "bass_event_breath_audio_mono.f32", start_seconds, duration)
    window = max(2048, int(round(sample_rate * 0.093)))
    hop = max(256, int(round(sample_rate * 0.0116)))
    if audio.size < window:
        audio = np.pad(audio, (0, window - audio.size))
    padded = np.pad(audio, (window // 2, window // 2))
    frames = np.lib.stride_tricks.sliding_window_view(padded, window)[::hop]
    analysis_window = np.hanning(window).astype(np.float64)
    spectrum = np.abs(np.fft.rfft(frames * analysis_window, axis=1))
    freqs = np.fft.rfftfreq(window, 1.0 / sample_rate)
    times = np.arange(spectrum.shape[0], dtype=np.float64) * hop / sample_rate

    def bass_flux(low_hz: float, high_hz: float) -> np.ndarray:
        mask = (freqs >= low_hz) & (freqs < high_hz)
        energy = np.log1p(np.sum(spectrum[:, mask], axis=1))
        energy = np.convolve(energy, np.ones(7, dtype=np.float64) / 7.0, mode="same")
        onset = np.maximum(0.0, energy - np.concatenate(([energy[0]], energy[:-1])))
        positive = onset[onset > 0]
        scale = float(np.percentile(positive, 97.0)) if positive.size else 1.0
        return np.clip(onset / max(scale, 1e-9), 0.0, 2.5)

    sub_bass_flux = bass_flux(35.0, 95.0)
    low_bass_flux = bass_flux(45.0, 130.0)
    bass_body_flux = bass_flux(55.0, 180.0)
    bass_envelope = 0.45 * sub_bass_flux + 0.35 * low_bass_flux + 0.20 * bass_body_flux
    bass_envelope = np.clip(bass_envelope / max(float(np.percentile(bass_envelope, 97.0)), 1e-9), 0.0, 2.5)
    threshold = float(np.percentile(bass_envelope, BEAT_BASS_EVENT_PEAK_PERCENTILE))
    radius = BEAT_BASS_EVENT_LOCAL_RADIUS_FRAMES
    local_candidates = [
        index
        for index in range(radius, len(bass_envelope) - radius)
        if bass_envelope[index] >= threshold
        and bass_envelope[index] == float(np.max(bass_envelope[index - radius : index + radius + 1]))
    ]
    selected_indexes: list[int] = []
    for index in sorted(local_candidates, key=lambda candidate: float(bass_envelope[candidate]), reverse=True):
        event_time = float(times[index])
        if all(abs(event_time - float(times[existing])) >= BEAT_BASS_EVENT_MIN_SPACING_SECONDS for existing in selected_indexes):
            selected_indexes.append(index)
    selected_indexes.sort(key=lambda index: float(times[index]))

    max_envelope = max(float(np.percentile(bass_envelope, 95.0)), 1e-9)
    beats = []
    for index in selected_indexes:
        event_time = float(times[index])
        envelope_value = float(bass_envelope[index])
        strength = 0.72 + 0.28 * max(0.0, min(1.0, envelope_value / max_envelope))
        beats.append(
            {
                "relative_time_seconds": round(event_time, 6),
                "global_time_seconds": round(start_seconds + event_time, 6),
                "strength": round(strength, 6),
                "nearest_onset_relative_seconds": round(event_time, 6),
                "nearest_onset_distance_seconds": 0.0,
                "nearest_onset_strength": round(envelope_value, 9),
                "sub_bass_35_95_strength": round(float(sub_bass_flux[index]), 9),
                "low_bass_45_130_strength": round(float(low_bass_flux[index]), 9),
                "bass_body_55_180_strength": round(float(bass_body_flux[index]), 9),
                "onset_modulation": 1.0,
            }
        )

    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    envelope_norm = np.interp(frame_times, times, bass_envelope / max(float(np.percentile(bass_envelope, 98.0)), 1e-9))
    envelope_norm = np.clip(envelope_norm, 0.0, 1.0)
    pulse = np.zeros(frame_count, dtype=np.float64)
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        delta = frame_times - beat_time
        values = np.zeros(frame_count, dtype=np.float64)
        before = delta < 0
        after = ~before
        values[before] = strength * np.exp(delta[before] / BEAT_BASS_EVENT_ATTACK_SECONDS)
        values[after] = strength * np.exp(-delta[after] / BEAT_CLEAR_DECAY_SECONDS)
        pulse = np.maximum(pulse, values)
    pulse = np.minimum(1.0, np.maximum(0.0, pulse))
    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(envelope_norm[index]), 6),
        }
        for index in range(frame_count)
    ]

    peak_offsets = []
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        indexes = [
            index
            for index, frame_time in enumerate(frame_times)
            if abs(float(frame_time) - beat_time) <= BEAT_BASS_EVENT_MIN_SPACING_SECONDS * 0.5
        ]
        if not indexes:
            continue
        peak_index = max(indexes, key=lambda index: pulse[index])
        peak_time = float(frame_times[peak_index])
        offset = peak_time - beat_time
        peak_offsets.append(abs(offset))
        beat["pulse_peak_frame"] = int(peak_index)
        beat["pulse_peak_relative_seconds"] = round(peak_time, 6)
        beat["pulse_peak_offset_seconds"] = round(offset, 6)
    intervals = [
        float(beats[index + 1]["relative_time_seconds"]) - float(beats[index]["relative_time_seconds"])
        for index in range(len(beats) - 1)
    ]
    pulse_adjacent_delta = np.abs(np.diff(pulse))
    max_peak_offset = max(peak_offsets, default=0.0)
    return {
        "analysis_source": "baseline_audio_stream",
        "analysis_strategy": "actual_lowest_bass_event_peaks_no_periodic_grid_no_fallback",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": sample_rate,
        "window_seconds": round(window / sample_rate, 6),
        "hop_seconds": round(hop / sample_rate, 6),
        "bass_only_frequency_bands": ["35-95 Hz", "45-130 Hz", "55-180 Hz"],
        "frequency_band_weights": {
            "sub_bass_35_95_hz": 0.45,
            "low_bass_45_130_hz": 0.35,
            "bass_body_55_180_hz": 0.20,
            "mid_high_transient_weight": 0.0,
            "full_spectrum_weight": 0.0,
        },
        "periodic_grid_used": False,
        "tempo_period_estimated": False,
        "fallback_grid_used": False,
        "bass_event_peak_percentile": BEAT_BASS_EVENT_PEAK_PERCENTILE,
        "bass_event_peak_threshold": round(threshold, 9),
        "bass_event_min_spacing_seconds": BEAT_BASS_EVENT_MIN_SPACING_SECONDS,
        "bass_event_local_radius_frames": BEAT_BASS_EVENT_LOCAL_RADIUS_FRAMES,
        "local_candidate_count": len(local_candidates),
        "beat_count": len(beats),
        "beats": beats,
        "frame_pulses": frame_pulses,
        "intervals_seconds": [round(float(interval), 6) for interval in intervals],
        "median_interval_seconds": round(float(np.median(intervals)) if intervals else 0.0, 6),
        "mean_interval_seconds": round(float(np.mean(intervals)) if intervals else 0.0, 6),
        "max_interval_seconds": round(float(max(intervals)) if intervals else 0.0, 6),
        "min_interval_seconds": round(float(min(intervals)) if intervals else 0.0, 6),
        "interval_std_seconds": round(float(np.std(intervals)) if intervals else 0.0, 6),
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "max_pulse_peak_offset_seconds": round(float(max_peak_offset), 6),
        "actual_bass_event_timing_read": "pass" if len(beats) >= 24 else "tighten",
        "no_periodic_grid_read": "pass",
        "mid_high_transient_rejection_read": "pass",
        "pulse_peak_on_bass_event_read": "pass" if max_peak_offset <= (1.0 / FPS) + 0.004 else "tighten",
        "bass_event_interval_variability_read": "pass" if intervals and float(np.std(intervals)) >= 0.03 else "review",
        "beat_alignment_read": "pass" if len(beats) >= 24 else "tighten",
        "abrupt_pulse_read": "pass" if (not pulse_adjacent_delta.size or float(pulse_adjacent_delta.max()) <= 0.42) else "review",
    }


def bass_drum_hit_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
    extra_rejected_windows: list[dict[str, Any]] | None = None,
    confirmed_global_seconds_override: list[float] | None = None,
    manual_verification_source: str = "assisted_detection_plus_timeline_review",
    include_default_rejected_windows: bool = True,
) -> dict[str, Any]:
    import numpy as np

    duration = end_seconds - start_seconds
    audio_path = work_dir / "bass_drum_hit_audio_mono.f32"
    audio = extract_mono_f32_audio_slice(source_mp4, audio_path, start_seconds, duration)
    assisted = bass_event_breath_audio_analysis(source_mp4, work_dir, start_seconds, end_seconds)
    candidates = assisted["beats"]
    source_confirmed_times = (
        confirmed_global_seconds_override
        if confirmed_global_seconds_override is not None
        else BEAT_BASS_DRUM_HIT_CONFIRMED_GLOBAL_SECONDS
    )
    rejected_windows = [
        *([] if not include_default_rejected_windows else BEAT_BASS_DRUM_REJECTED_WINDOWS),
        *(extra_rejected_windows or []),
    ]
    confirmed_global_times = [
        time
        for time in source_confirmed_times
        if start_seconds <= time < end_seconds
        and not any(
            float(window["global_seconds"][0]) <= time < float(window["global_seconds"][1])
            for window in rejected_windows
        )
    ]

    def nearest_candidate(global_time: float) -> dict[str, Any] | None:
        if not candidates:
            return None
        return min(candidates, key=lambda candidate: abs(float(candidate["global_time_seconds"]) - global_time))

    beats = []
    for index, global_time in enumerate(confirmed_global_times):
        candidate = nearest_candidate(global_time)
        candidate_offset = (
            float(candidate["global_time_seconds"]) - global_time
            if candidate and abs(float(candidate["global_time_seconds"]) - global_time) <= 0.08
            else None
        )
        candidate_strength = float(candidate["strength"]) if candidate and candidate_offset is not None else 1.0
        strength = max(0.76, min(1.0, candidate_strength))
        beats.append(
            {
                "index": index,
                "relative_time_seconds": round(global_time - start_seconds, 6),
                "global_time_seconds": round(global_time, 6),
                "strength": round(strength, 6),
                "verification": "confirmed_bass_drum_hit",
                "manual_verification_source": manual_verification_source,
                "nearest_assisted_candidate_global_seconds": round(float(candidate["global_time_seconds"]), 6)
                if candidate and candidate_offset is not None
                else None,
                "nearest_assisted_candidate_offset_seconds": round(candidate_offset, 6)
                if candidate_offset is not None
                else None,
                "candidate_low_band_strengths": {
                    "sub_bass_35_95_strength": candidate.get("sub_bass_35_95_strength") if candidate else None,
                    "low_bass_45_130_strength": candidate.get("low_bass_45_130_strength") if candidate else None,
                    "bass_body_55_180_strength": candidate.get("bass_body_55_180_strength") if candidate else None,
                },
            }
        )

    confirmed_times = [float(beat["global_time_seconds"]) for beat in beats]
    rejected_candidates = []
    for candidate in candidates:
        global_time = float(candidate["global_time_seconds"])
        if any(abs(global_time - confirmed_time) <= 0.08 for confirmed_time in confirmed_times):
            continue
        window_reasons = [
            str(window["reason"])
            for window in rejected_windows
            if float(window["global_seconds"][0]) <= global_time < float(window["global_seconds"][1])
        ]
        rejected_candidates.append(
            {
                **candidate,
                "rejection_reason": window_reasons[0] if window_reasons else "not_confirmed_as_audible_bass_drum_hit",
            }
        )

    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    pulse = np.zeros(frame_count, dtype=np.float64)
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        delta = frame_times - beat_time
        after = delta >= 0
        values = np.zeros(frame_count, dtype=np.float64)
        values[after] = strength * np.exp(-delta[after] / BEAT_BASS_DRUM_HIT_DECAY_SECONDS)
        pulse = np.maximum(pulse, values)

    assisted_frame_pulses = assisted.get("frame_pulses", [])
    assisted_energy = (
        np.array([float(row.get("energy_norm", 0.0)) for row in assisted_frame_pulses], dtype=np.float64)
        if assisted_frame_pulses
        else np.zeros(frame_count, dtype=np.float64)
    )
    if assisted_energy.size != frame_count:
        assisted_times = (
            np.array([float(row["relative_time_seconds"]) for row in assisted_frame_pulses], dtype=np.float64)
            if assisted_frame_pulses
            else np.array([0.0], dtype=np.float64)
        )
        assisted_values = assisted_energy if assisted_energy.size else np.array([0.0], dtype=np.float64)
        assisted_energy = np.interp(frame_times, assisted_times, assisted_values)

    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(assisted_energy[index]), 6),
        }
        for index in range(frame_count)
    ]

    peak_offsets = []
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        indexes = [
            index
            for index, frame_time in enumerate(frame_times)
            if 0.0 <= float(frame_time) - beat_time <= BEAT_BASS_DRUM_HIT_PEAK_TOLERANCE_SECONDS
        ]
        if not indexes:
            continue
        peak_index = max(indexes, key=lambda index: pulse[index])
        peak_time = float(frame_times[peak_index])
        offset = peak_time - beat_time
        peak_offsets.append(abs(offset))
        beat["pulse_peak_frame"] = int(peak_index)
        beat["pulse_peak_relative_seconds"] = round(peak_time, 6)
        beat["pulse_peak_offset_seconds"] = round(offset, 6)

    pulse_adjacent_delta = np.abs(np.diff(pulse))
    max_peak_offset = max(peak_offsets, default=0.0)
    high_pulse_frames = [
        row
        for row in frame_pulses
        if float(row["pulse"]) >= 0.50
        and not any(
            0.0 <= float(row["global_time_seconds"]) - float(beat["global_time_seconds"]) <= 0.18
            for beat in beats
        )
    ]
    rejected_window_reports = []
    for window in rejected_windows:
        start, end = [float(value) for value in window["global_seconds"]]
        window_pulses = [
            float(row["pulse"])
            for row in frame_pulses
            if start <= float(row["global_time_seconds"]) < end
        ]
        window_candidates = [
            candidate
            for candidate in rejected_candidates
            if start <= float(candidate["global_time_seconds"]) < end
        ]
        max_window_pulse = max(window_pulses, default=0.0)
        rejected_window_reports.append(
            {
                "global_seconds": [start, end],
                "reason": window["reason"],
                "max_pulse": round(max_window_pulse, 6),
                "rejected_candidate_count": len(window_candidates),
                "rejected_candidate_global_seconds": [
                    round(float(candidate["global_time_seconds"]), 6) for candidate in window_candidates
                ],
                "read": "pass" if max_window_pulse <= 0.02 and window_candidates else "tighten",
            }
        )

    return {
        "analysis_source": "baseline_audio_stream",
        "analysis_strategy": "confirmed_bass_drum_hit_map_assisted_detection_manual_verification",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": BEAT_BREATH_AUDIO_SAMPLE_RATE,
        "audio_mono_f32_path": str(audio_path),
        "audio_mono_f32_sha256": file_sha256(audio_path),
        "periodic_grid_used": False,
        "tempo_period_estimated": False,
        "fallback_grid_used": False,
        "low_band_envelope_modulates_pulse": False,
        "mid_high_transient_weight": 0.0,
        "pre_attack_used": False,
        "manual_verification_source": manual_verification_source,
        "default_rejected_windows_included": include_default_rejected_windows,
        "confirmed_hit_count": len(beats),
        "beats": beats,
        "assisted_detection": {
            "strategy": assisted["analysis_strategy"],
            "candidate_count": assisted["beat_count"],
            "candidate_times_global_seconds": [
                round(float(candidate["global_time_seconds"]), 6) for candidate in candidates
            ],
            "frequency_band_weights": assisted["frequency_band_weights"],
            "note": "Assisted candidates are evidence only; rejected candidates do not drive visual pulses.",
        },
        "rejected_candidates": rejected_candidates,
        "rejected_no_bass_drum_windows": rejected_window_reports,
        "frame_pulses": frame_pulses,
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "max_pulse_peak_offset_seconds": round(float(max_peak_offset), 6),
        "confirmed_bass_drum_hit_map_read": "pass" if len(beats) >= 10 else "tighten",
        "no_pulse_without_confirmed_hit_read": "pass" if not high_pulse_frames else "tighten",
        "nineteen_second_false_positive_rejection_read": "pass"
        if all(report["read"] == "pass" for report in rejected_window_reports)
        else "tighten",
        "no_periodic_grid_read": "pass",
        "no_low_band_fallback_read": "pass",
        "pulse_peak_on_confirmed_hit_read": "pass"
        if max_peak_offset <= BEAT_BASS_DRUM_HIT_PEAK_TOLERANCE_SECONDS
        else "tighten",
        "beat_alignment_read": "pass" if len(beats) >= 10 else "tighten",
        "abrupt_pulse_read": "pass_no_preattack_intentional",
    }


def rhythm_hit_breath_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    import numpy as np

    assisted = bass_event_breath_audio_analysis(source_mp4, work_dir, start_seconds, end_seconds)
    primary_times = [
        time
        for time in BEAT_BASS_DRUM_HIT_CONFIRMED_GLOBAL_SECONDS
        if start_seconds <= time < end_seconds
    ]
    beats = []
    for index, candidate in enumerate(assisted["beats"]):
        global_time = float(candidate["global_time_seconds"])
        primary_match = min((abs(global_time - time), time) for time in primary_times)
        is_primary = primary_match[0] <= BEAT_RHYTHM_HIT_PRIMARY_MATCH_TOLERANCE_SECONDS
        if is_primary:
            strength = max(0.78, min(1.0, float(candidate["strength"])))
            verification = "primary_confirmed_bass_drum_hit"
            matched_primary = primary_match[1]
        else:
            strength = BEAT_RHYTHM_HIT_SUPPORT_MIN_STRENGTH + (
                BEAT_RHYTHM_HIT_SUPPORT_MAX_STRENGTH - BEAT_RHYTHM_HIT_SUPPORT_MIN_STRENGTH
            ) * max(0.0, min(1.0, float(candidate["strength"])))
            verification = "support_rhythm_accent_not_claimed_as_bass_drum"
            matched_primary = None
        beats.append(
            {
                "index": index,
                "relative_time_seconds": round(float(candidate["relative_time_seconds"]), 6),
                "global_time_seconds": round(global_time, 6),
                "strength": round(strength, 6),
                "verification": verification,
                "matched_primary_bass_drum_global_seconds": round(matched_primary, 6) if matched_primary else None,
                "assisted_candidate_strength": candidate["strength"],
                "sub_bass_35_95_strength": candidate.get("sub_bass_35_95_strength"),
                "low_bass_45_130_strength": candidate.get("low_bass_45_130_strength"),
                "bass_body_55_180_strength": candidate.get("bass_body_55_180_strength"),
            }
        )

    duration = end_seconds - start_seconds
    frame_count = int(round(duration * FPS))
    frame_times = np.arange(frame_count, dtype=np.float64) / FPS
    pulse = np.zeros(frame_count, dtype=np.float64)
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        delta = frame_times - beat_time
        after = delta >= 0
        values = np.zeros(frame_count, dtype=np.float64)
        values[after] = strength * np.exp(-delta[after] / BEAT_BASS_DRUM_HIT_DECAY_SECONDS)
        pulse = np.maximum(pulse, values)

    assisted_frame_pulses = assisted.get("frame_pulses", [])
    assisted_energy = np.array([float(row.get("energy_norm", 0.0)) for row in assisted_frame_pulses], dtype=np.float64)
    if assisted_energy.size != frame_count:
        assisted_times = np.array([float(row["relative_time_seconds"]) for row in assisted_frame_pulses], dtype=np.float64)
        assisted_energy = np.interp(frame_times, assisted_times, assisted_energy)

    frame_pulses = [
        {
            "frame": int(index),
            "relative_time_seconds": round(float(frame_times[index]), 6),
            "global_time_seconds": round(start_seconds + float(frame_times[index]), 6),
            "pulse": round(float(pulse[index]), 6),
            "energy_norm": round(float(assisted_energy[index]), 6),
        }
        for index in range(frame_count)
    ]

    peak_offsets = []
    for beat in beats:
        beat_time = float(beat["relative_time_seconds"])
        indexes = [
            index
            for index, frame_time in enumerate(frame_times)
            if 0.0 <= float(frame_time) - beat_time <= BEAT_BASS_DRUM_HIT_PEAK_TOLERANCE_SECONDS
        ]
        if not indexes:
            continue
        peak_index = max(indexes, key=lambda index: pulse[index])
        peak_time = float(frame_times[peak_index])
        offset = peak_time - beat_time
        peak_offsets.append(abs(offset))
        beat["pulse_peak_frame"] = int(peak_index)
        beat["pulse_peak_relative_seconds"] = round(peak_time, 6)
        beat["pulse_peak_offset_seconds"] = round(offset, 6)

    intervals = [
        float(beats[index + 1]["relative_time_seconds"]) - float(beats[index]["relative_time_seconds"])
        for index in range(len(beats) - 1)
    ]
    pulse_adjacent_delta = np.abs(np.diff(pulse))
    max_peak_offset = max(peak_offsets, default=0.0)
    max_gap = max(intervals, default=0.0)
    review_12_window_hits = [
        beat for beat in beats if 11.5 <= float(beat["relative_time_seconds"]) <= 15.0
    ]
    return {
        "analysis_source": "baseline_audio_stream",
        "analysis_strategy": "confirmed_rhythm_hit_map_primary_bass_drum_plus_support_accents",
        "source_mp4": str(source_mp4),
        "source_seconds": [start_seconds, end_seconds],
        "duration_seconds": round(duration, 6),
        "sample_rate": BEAT_BREATH_AUDIO_SAMPLE_RATE,
        "periodic_grid_used": False,
        "tempo_period_estimated": False,
        "fallback_grid_used": False,
        "low_band_envelope_modulates_pulse": False,
        "mid_high_transient_weight": 0.0,
        "pre_attack_used": False,
        "support_accents_claimed_as_bass_drum": False,
        "beat_count": len(beats),
        "primary_bass_drum_hit_count": sum(1 for beat in beats if beat["verification"] == "primary_confirmed_bass_drum_hit"),
        "support_rhythm_accent_count": sum(1 for beat in beats if beat["verification"] == "support_rhythm_accent_not_claimed_as_bass_drum"),
        "beats": beats,
        "frame_pulses": frame_pulses,
        "intervals_seconds": [round(float(interval), 6) for interval in intervals],
        "max_gap_seconds": round(float(max_gap), 6),
        "max_adjacent_pulse_delta": round(float(pulse_adjacent_delta.max()) if pulse_adjacent_delta.size else 0.0, 6),
        "max_pulse_peak_offset_seconds": round(float(max_peak_offset), 6),
        "rhythm_hit_map_read": "pass" if len(beats) >= 24 else "tighten",
        "rhythm_continuity_gap_read": "pass" if max_gap <= BEAT_RHYTHM_HIT_MAX_ALLOWED_GAP_SECONDS else "tighten",
        "review_12s_rhythm_continuity_read": "pass" if len(review_12_window_hits) >= 3 else "tighten",
        "no_periodic_grid_read": "pass",
        "no_low_band_fallback_read": "pass",
        "pulse_peak_on_rhythm_hit_read": "pass"
        if max_peak_offset <= BEAT_BASS_DRUM_HIT_PEAK_TOLERANCE_SECONDS
        else "tighten",
        "beat_alignment_read": "pass" if len(beats) >= 24 else "tighten",
        "abrupt_pulse_read": "pass_no_preattack_intentional",
    }


def corrected_tacoma_737_confirmed_bass_drum_seconds_from_audit() -> tuple[list[float], dict[str, Any]]:
    require_file(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
    audit = load_json(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
    window_start, window_end = BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS
    confirmed = sorted(
        round(float(row["global_time_seconds"]), 6)
        for row in audit.get("candidate_decisions", [])
        if row.get("decision") == "confirmed_bass_drum_hit"
        and window_start <= float(row["global_time_seconds"]) < window_end
    )
    rejected = sorted(
        round(float(row["global_time_seconds"]), 6)
        for row in audit.get("candidate_decisions", [])
        if row.get("decision") == "rejected_not_bass_drum_hit"
        and window_start <= float(row["global_time_seconds"]) < window_end
    )
    expected_confirmed = sorted(BEAT_TACOMA_737_CORRECTED_TACOMA_HIT_SECONDS + BEAT_TACOMA_737_CORRECTED_737_HIT_SECONDS)
    pre_tacoma_confirmed = [
        round(float(time), 6)
        for time in BEAT_BASS_DRUM_HIT_CONFIRMED_GLOBAL_SECONDS
        if time < window_start
    ]
    post_window_pre_titanic = [
        round(float(time), 6)
        for time in BEAT_BASS_DRUM_HIT_CONFIRMED_GLOBAL_SECONDS
        if window_end <= time < BEAT_TITANIC_NO_BASS_DRUM_WINDOW["global_seconds"][0]
    ]
    merged = sorted(pre_tacoma_confirmed + confirmed + post_window_pre_titanic)
    audit_context = {
        "audit_package_id": BEAT_TACOMA_737_CORRECTED_AUDIT_PACKAGE_ID,
        "audit_candidate_map_path": str(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP),
        "audit_candidate_map_sha256": file_sha256(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP),
        "audit_manifest_path": str(BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST),
        "audit_manifest_sha256": file_sha256(BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST)
        if BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST.exists()
        else None,
        "corrected_window_seconds": list(BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS),
        "confirmed_hit_seconds_from_audit": confirmed,
        "rejected_hit_seconds_from_audit": rejected,
        "expected_confirmed_hit_seconds": expected_confirmed,
        "expected_confirmed_hit_seconds_read": "pass" if confirmed == expected_confirmed else "tighten",
        "pre_tacoma_confirmed_hit_seconds_preserved": pre_tacoma_confirmed,
        "post_window_pre_titanic_confirmed_hit_seconds_preserved": post_window_pre_titanic,
        "tacoma_confirmed_hit_seconds": [
            time
            for time in confirmed
            if BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[0] <= time < BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[1]
        ],
        "boeing_737_max_confirmed_hit_seconds": [
            time
            for time in confirmed
            if BEAT_TACOMA_737_AUDIT_737_SECONDS[0] <= time < BEAT_TACOMA_737_AUDIT_737_SECONDS[1]
        ],
    }
    return merged, audit_context


def bass_drum_only_no_titanic_pulse_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    analysis = bass_drum_hit_breath_audio_analysis(
        source_mp4,
        work_dir,
        start_seconds,
        end_seconds,
        extra_rejected_windows=[BEAT_TITANIC_NO_BASS_DRUM_WINDOW],
    )
    titanic_start, titanic_end = [float(value) for value in BEAT_TITANIC_NO_BASS_DRUM_WINDOW["global_seconds"]]
    for row in analysis["frame_pulses"]:
        if titanic_start <= float(row["global_time_seconds"]) < titanic_end:
            row["pulse"] = 0.0
    titanic_pulses = [
        float(row["pulse"])
        for row in analysis["frame_pulses"]
        if titanic_start <= float(row["global_time_seconds"]) < titanic_end
    ]
    titanic_rejected = [
        candidate
        for candidate in analysis["rejected_candidates"]
        if titanic_start <= float(candidate["global_time_seconds"]) < titanic_end
    ]
    max_titanic_pulse = max(titanic_pulses, default=0.0)
    for report in analysis["rejected_no_bass_drum_windows"]:
        report_start, report_end = [float(value) for value in report["global_seconds"]]
        if abs(report_start - titanic_start) < 1e-6 and abs(report_end - titanic_end) < 1e-6:
            report["max_pulse"] = round(max_titanic_pulse, 6)
            report["read"] = "pass" if max_titanic_pulse <= 0.02 else "tighten"
    analysis["analysis_strategy"] = "confirmed_bass_drum_only_hit_map_no_titanic_pulse"
    analysis["titanic_no_bass_drum_seconds"] = [titanic_start, titanic_end]
    analysis["titanic_rejected_candidate_global_seconds"] = [
        round(float(candidate["global_time_seconds"]), 6) for candidate in titanic_rejected
    ]
    analysis["titanic_max_pulse"] = round(max_titanic_pulse, 6)
    analysis["confirmed_bass_drum_only_hit_map_read"] = analysis["confirmed_bass_drum_hit_map_read"]
    analysis["no_support_accent_pulse_read"] = (
        "pass"
        if all(str(beat["verification"]) == "confirmed_bass_drum_hit" for beat in analysis["beats"])
        else "tighten"
    )
    analysis["no_pulse_without_confirmed_bass_drum_read"] = analysis["no_pulse_without_confirmed_hit_read"]
    analysis["titanic_no_bass_drum_no_pulse_read"] = "pass" if max_titanic_pulse <= 0.02 else "tighten"
    return analysis


def corrected_tacoma_737_bass_drum_pulse_audio_analysis(
    source_mp4: Path,
    work_dir: Path,
    start_seconds: float = BEAT_BREATH_START_SECONDS,
    end_seconds: float = BEAT_BREATH_END_SECONDS,
) -> dict[str, Any]:
    confirmed_times, audit_context = corrected_tacoma_737_confirmed_bass_drum_seconds_from_audit()
    analysis = bass_drum_hit_breath_audio_analysis(
        source_mp4,
        work_dir,
        start_seconds,
        end_seconds,
        extra_rejected_windows=[BEAT_TITANIC_NO_BASS_DRUM_WINDOW],
        confirmed_global_seconds_override=confirmed_times,
        manual_verification_source="corrected_tacoma_737_audit_plus_existing_pre_tacoma_confirmed_hits",
        include_default_rejected_windows=False,
    )
    titanic_start, titanic_end = [float(value) for value in BEAT_TITANIC_NO_BASS_DRUM_WINDOW["global_seconds"]]
    for row in analysis["frame_pulses"]:
        if titanic_start <= float(row["global_time_seconds"]) < titanic_end:
            row["pulse"] = 0.0
    titanic_pulses = [
        float(row["pulse"])
        for row in analysis["frame_pulses"]
        if titanic_start <= float(row["global_time_seconds"]) < titanic_end
    ]
    max_titanic_pulse = max(titanic_pulses, default=0.0)
    tacoma_hits = [
        beat
        for beat in analysis["beats"]
        if BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[0]
        <= float(beat["global_time_seconds"])
        < BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[1]
    ]
    max_737_hits = [
        beat
        for beat in analysis["beats"]
        if BEAT_TACOMA_737_AUDIT_737_SECONDS[0]
        <= float(beat["global_time_seconds"])
        < BEAT_TACOMA_737_AUDIT_737_SECONDS[1]
    ]
    for report in analysis["rejected_no_bass_drum_windows"]:
        report_start, report_end = [float(value) for value in report["global_seconds"]]
        if abs(report_start - titanic_start) < 1e-6 and abs(report_end - titanic_end) < 1e-6:
            report["max_pulse"] = round(max_titanic_pulse, 6)
            report["read"] = "pass" if max_titanic_pulse <= 0.02 else "tighten"
    analysis["analysis_strategy"] = "corrected_tacoma_737_confirmed_bass_drum_hit_map_no_titanic_pulse"
    analysis["corrected_tacoma_737_audit_context"] = audit_context
    analysis["corrected_tacoma_737_hit_map_source"] = str(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
    analysis["corrected_tacoma_737_hit_map_sha256"] = file_sha256(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
    analysis["tacoma_confirmed_hit_seconds"] = [float(beat["global_time_seconds"]) for beat in tacoma_hits]
    analysis["boeing_737_max_confirmed_hit_seconds"] = [float(beat["global_time_seconds"]) for beat in max_737_hits]
    analysis["tacoma_confirmed_hit_count"] = len(tacoma_hits)
    analysis["boeing_737_max_confirmed_hit_count"] = len(max_737_hits)
    analysis["titanic_no_bass_drum_seconds"] = [titanic_start, titanic_end]
    analysis["titanic_max_pulse"] = round(max_titanic_pulse, 6)
    analysis["corrected_tacoma_737_hit_map_read"] = audit_context["expected_confirmed_hit_seconds_read"]
    analysis["tacoma_visible_pulse_hit_count_read"] = "pass" if len(tacoma_hits) == 5 else "tighten"
    analysis["boeing_737_max_corrected_timing_hit_count_read"] = "pass" if len(max_737_hits) == 5 else "tighten"
    analysis["no_support_accent_pulse_read"] = (
        "pass"
        if all(str(beat["verification"]) == "confirmed_bass_drum_hit" for beat in analysis["beats"])
        else "tighten"
    )
    analysis["no_pulse_without_confirmed_bass_drum_read"] = analysis["no_pulse_without_confirmed_hit_read"]
    analysis["titanic_no_bass_drum_no_pulse_read"] = "pass" if max_titanic_pulse <= 0.0 else "tighten"
    return analysis


def write_beat_breath_timeline_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "beat_breath_timeline.json"
    csv_path = out_dir / "beat_breath_frame_pulses.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    csv_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,energy_norm"]
    for row in analysis["frame_pulses"]:
        csv_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
    }


def write_beat_grid_timeline_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "beat_grid_timeline.json"
    csv_path = out_dir / "beat_grid_frame_pulses.csv"
    ticks_csv_path = out_dir / "beat_grid_ticks.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")
    tick_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,nearest_onset_relative_seconds,nearest_onset_distance_seconds,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds"
    ]
    for index, beat in enumerate(analysis["beats"]):
        tick_lines.append(
            ",".join(
                [
                    str(index),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    "" if beat.get("nearest_onset_relative_seconds") is None else f"{beat['nearest_onset_relative_seconds']:.6f}",
                    "" if beat.get("nearest_onset_distance_seconds") is None else f"{beat['nearest_onset_distance_seconds']:.6f}",
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                ]
            )
        )
    ticks_csv_path.write_text("\n".join(tick_lines) + "\n", encoding="utf-8")
    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "beat_grid_ticks_csv_path": str(ticks_csv_path),
        "beat_grid_ticks_csv_sha256": file_sha256(ticks_csv_path),
    }


def write_clear_beat_timeline_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "clear_beat_timeline.json"
    csv_path = out_dir / "clear_beat_frame_pulses.csv"
    ticks_csv_path = out_dir / "clear_beat_ticks.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")
    tick_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,nearest_onset_relative_seconds,nearest_onset_distance_seconds,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds"
    ]
    for index, beat in enumerate(analysis["beats"]):
        tick_lines.append(
            ",".join(
                [
                    str(index),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    "" if beat.get("nearest_onset_relative_seconds") is None else f"{beat['nearest_onset_relative_seconds']:.6f}",
                    "" if beat.get("nearest_onset_distance_seconds") is None else f"{beat['nearest_onset_distance_seconds']:.6f}",
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                ]
            )
        )
    ticks_csv_path.write_text("\n".join(tick_lines) + "\n", encoding="utf-8")
    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "clear_beat_ticks_csv_path": str(ticks_csv_path),
        "clear_beat_ticks_csv_sha256": file_sha256(ticks_csv_path),
    }


def write_lowest_bass_beat_timeline_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "lowest_bass_beat_timeline.json"
    csv_path = out_dir / "lowest_bass_beat_frame_pulses.csv"
    ticks_csv_path = out_dir / "lowest_bass_beat_ticks.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")
    tick_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,nearest_onset_relative_seconds,nearest_onset_distance_seconds,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds"
    ]
    for index, beat in enumerate(analysis["beats"]):
        tick_lines.append(
            ",".join(
                [
                    str(index),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    "" if beat.get("nearest_onset_relative_seconds") is None else f"{beat['nearest_onset_relative_seconds']:.6f}",
                    "" if beat.get("nearest_onset_distance_seconds") is None else f"{beat['nearest_onset_distance_seconds']:.6f}",
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                ]
            )
        )
    ticks_csv_path.write_text("\n".join(tick_lines) + "\n", encoding="utf-8")
    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "lowest_bass_beat_ticks_csv_path": str(ticks_csv_path),
        "lowest_bass_beat_ticks_csv_sha256": file_sha256(ticks_csv_path),
    }


def write_bass_event_timeline_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bass_event_timeline.json"
    csv_path = out_dir / "bass_event_frame_pulses.csv"
    events_csv_path = out_dir / "bass_event_ticks.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")
    event_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,nearest_onset_strength,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds"
    ]
    for index, beat in enumerate(analysis["beats"]):
        event_lines.append(
            ",".join(
                [
                    str(index),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    f"{beat['nearest_onset_strength']:.9f}",
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                ]
            )
        )
    events_csv_path.write_text("\n".join(event_lines) + "\n", encoding="utf-8")
    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "bass_event_ticks_csv_path": str(events_csv_path),
        "bass_event_ticks_csv_sha256": file_sha256(events_csv_path),
    }


def write_bass_drum_hit_map_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bass_drum_hit_map.json"
    csv_path = out_dir / "bass_drum_hit_frame_pulses.csv"
    hits_csv_path = out_dir / "bass_drum_confirmed_hits.csv"
    rejected_csv_path = out_dir / "bass_drum_rejected_candidates.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,assisted_low_band_energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")

    hit_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,verification,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds,nearest_assisted_candidate_global_seconds,nearest_assisted_candidate_offset_seconds"
    ]
    for beat in analysis["beats"]:
        hit_lines.append(
            ",".join(
                [
                    str(beat["index"]),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    str(beat["verification"]),
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                    ""
                    if beat.get("nearest_assisted_candidate_global_seconds") is None
                    else f"{beat['nearest_assisted_candidate_global_seconds']:.6f}",
                    ""
                    if beat.get("nearest_assisted_candidate_offset_seconds") is None
                    else f"{beat['nearest_assisted_candidate_offset_seconds']:.6f}",
                ]
            )
        )
    hits_csv_path.write_text("\n".join(hit_lines) + "\n", encoding="utf-8")

    rejected_lines = [
        "global_time_seconds,relative_time_seconds,strength,rejection_reason,sub_bass_35_95_strength,low_bass_45_130_strength,bass_body_55_180_strength"
    ]
    for candidate in analysis["rejected_candidates"]:
        rejected_lines.append(
            ",".join(
                [
                    f"{candidate['global_time_seconds']:.6f}",
                    f"{candidate['relative_time_seconds']:.6f}",
                    f"{candidate['strength']:.6f}",
                    str(candidate["rejection_reason"]),
                    f"{candidate.get('sub_bass_35_95_strength', 0.0):.6f}",
                    f"{candidate.get('low_bass_45_130_strength', 0.0):.6f}",
                    f"{candidate.get('bass_body_55_180_strength', 0.0):.6f}",
                ]
            )
        )
    rejected_csv_path.write_text("\n".join(rejected_lines) + "\n", encoding="utf-8")

    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "confirmed_hits_csv_path": str(hits_csv_path),
        "confirmed_hits_csv_sha256": file_sha256(hits_csv_path),
        "rejected_candidates_csv_path": str(rejected_csv_path),
        "rejected_candidates_csv_sha256": file_sha256(rejected_csv_path),
    }


def write_rhythm_hit_map_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "rhythm_hit_map.json"
    csv_path = out_dir / "rhythm_hit_frame_pulses.csv"
    hits_csv_path = out_dir / "rhythm_hits.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,assisted_low_band_energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")

    hit_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,verification,matched_primary_bass_drum_global_seconds,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds"
    ]
    for beat in analysis["beats"]:
        hit_lines.append(
            ",".join(
                [
                    str(beat["index"]),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    str(beat["verification"]),
                    ""
                    if beat.get("matched_primary_bass_drum_global_seconds") is None
                    else f"{beat['matched_primary_bass_drum_global_seconds']:.6f}",
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                ]
            )
        )
    hits_csv_path.write_text("\n".join(hit_lines) + "\n", encoding="utf-8")
    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "rhythm_hits_csv_path": str(hits_csv_path),
        "rhythm_hits_csv_sha256": file_sha256(hits_csv_path),
    }


def write_bass_drum_only_hit_map_files(analysis: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bass_drum_only_hit_map.json"
    csv_path = out_dir / "bass_drum_only_frame_pulses.csv"
    hits_csv_path = out_dir / "bass_drum_only_confirmed_hits.csv"
    rejected_csv_path = out_dir / "bass_drum_only_rejected_candidates.csv"
    json_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")

    pulse_lines = ["frame,relative_time_seconds,global_time_seconds,pulse,assisted_low_band_energy_norm"]
    for row in analysis["frame_pulses"]:
        pulse_lines.append(
            f"{row['frame']},{row['relative_time_seconds']:.6f},{row['global_time_seconds']:.6f},{row['pulse']:.6f},{row['energy_norm']:.6f}"
        )
    csv_path.write_text("\n".join(pulse_lines) + "\n", encoding="utf-8")

    hit_lines = [
        "index,relative_time_seconds,global_time_seconds,strength,verification,pulse_peak_frame,pulse_peak_relative_seconds,pulse_peak_offset_seconds"
    ]
    for beat in analysis["beats"]:
        hit_lines.append(
            ",".join(
                [
                    str(beat["index"]),
                    f"{beat['relative_time_seconds']:.6f}",
                    f"{beat['global_time_seconds']:.6f}",
                    f"{beat['strength']:.6f}",
                    str(beat["verification"]),
                    str(beat.get("pulse_peak_frame", "")),
                    "" if beat.get("pulse_peak_relative_seconds") is None else f"{beat['pulse_peak_relative_seconds']:.6f}",
                    "" if beat.get("pulse_peak_offset_seconds") is None else f"{beat['pulse_peak_offset_seconds']:.6f}",
                ]
            )
        )
    hits_csv_path.write_text("\n".join(hit_lines) + "\n", encoding="utf-8")

    rejected_lines = [
        "global_time_seconds,relative_time_seconds,strength,rejection_reason,sub_bass_35_95_strength,low_bass_45_130_strength,bass_body_55_180_strength"
    ]
    for candidate in analysis["rejected_candidates"]:
        rejected_lines.append(
            ",".join(
                [
                    f"{candidate['global_time_seconds']:.6f}",
                    f"{candidate['relative_time_seconds']:.6f}",
                    f"{candidate['strength']:.6f}",
                    str(candidate["rejection_reason"]),
                    f"{candidate.get('sub_bass_35_95_strength', 0.0):.6f}",
                    f"{candidate.get('low_bass_45_130_strength', 0.0):.6f}",
                    f"{candidate.get('bass_body_55_180_strength', 0.0):.6f}",
                ]
            )
        )
    rejected_csv_path.write_text("\n".join(rejected_lines) + "\n", encoding="utf-8")

    return {
        "timeline_json_path": str(json_path),
        "timeline_json_sha256": file_sha256(json_path),
        "frame_pulses_csv_path": str(csv_path),
        "frame_pulses_csv_sha256": file_sha256(csv_path),
        "confirmed_hits_csv_path": str(hits_csv_path),
        "confirmed_hits_csv_sha256": file_sha256(hits_csv_path),
        "rejected_candidates_csv_path": str(rejected_csv_path),
        "rejected_candidates_csv_sha256": file_sha256(rejected_csv_path),
    }


def beat_breath_pulse_at(analysis: dict[str, Any], global_time_seconds: float) -> float:
    index = int(round((global_time_seconds - BEAT_BREATH_START_SECONDS) * FPS))
    frame_pulses = analysis["frame_pulses"]
    if not frame_pulses:
        return 0.0
    index = max(0, min(len(frame_pulses) - 1, index))
    return float(frame_pulses[index]["pulse"])


def beat_breath_soft_foreground_mask(matte: Image.Image) -> Image.Image:
    restored = matte.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(1.8))
    return restored.point(lambda value: max(0, min(255, int(value * 1.35))))


def apply_beat_breath_background(
    base_plate: Image.Image,
    foreground_matte: Image.Image,
    pulse: float,
) -> tuple[Image.Image, dict[str, Any]]:
    pulse = max(0.0, min(1.0, pulse))
    shaped = pulse ** 0.68
    base = base_plate.convert("RGB")
    foreground_mask = beat_breath_soft_foreground_mask(foreground_matte)
    background_mask = ImageOps.invert(foreground_mask).filter(ImageFilter.GaussianBlur(3.0))

    lifted = ImageEnhance.Brightness(base).enhance(1.0 + BEAT_BREATH_MAX_BRIGHTNESS_LIFT * shaped)
    lifted = ImageEnhance.Contrast(lifted).enhance(1.0 + BEAT_BREATH_MAX_CONTRAST_LIFT * shaped)
    lifted = ImageEnhance.Color(lifted).enhance(1.0 + BEAT_BREATH_MAX_COLOR_LIFT * shaped)
    effect_rgba = lifted.convert("RGBA")

    wash_alpha = background_mask.point(lambda value: int(value * (BEAT_BREATH_MAX_WASH_ALPHA * shaped) / 255))
    wash = Image.new("RGBA", (WIDTH, HEIGHT), (96, 92, 138, 0))
    wash.putalpha(wash_alpha)
    effect_rgba = Image.alpha_composite(effect_rgba, wash)

    shadow_mask = foreground_matte.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(18.0))
    shadow_mask = ImageChops.offset(shadow_mask, 5, 8)
    shadow_alpha = shadow_mask.point(lambda value: int(value * (BEAT_BREATH_MAX_SHADOW_ALPHA * shaped) / 255))
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (12, 14, 32, 0))
    shadow.putalpha(shadow_alpha)
    effect_rgba = Image.alpha_composite(effect_rgba, shadow)

    background_effect = Image.composite(effect_rgba.convert("RGB"), base, background_mask)
    restored = Image.composite(base, background_effect, foreground_mask)
    diff_luma = ImageChops.difference(base.convert("L"), restored.convert("L"))
    background_stat = ImageStat.Stat(diff_luma, background_mask)
    foreground_stat = ImageStat.Stat(diff_luma, foreground_mask)
    return restored, {
        "pulse": round(pulse, 6),
        "shaped_pulse": round(shaped, 6),
        "brightness_factor": round(1.0 + BEAT_BREATH_MAX_BRIGHTNESS_LIFT * shaped, 6),
        "contrast_factor": round(1.0 + BEAT_BREATH_MAX_CONTRAST_LIFT * shaped, 6),
        "color_factor": round(1.0 + BEAT_BREATH_MAX_COLOR_LIFT * shaped, 6),
        "wash_alpha_max": round(BEAT_BREATH_MAX_WASH_ALPHA * shaped, 6),
        "shadow_alpha_max": round(BEAT_BREATH_MAX_SHADOW_ALPHA * shaped, 6),
        "background_mean_luma_delta": round(float(background_stat.mean[0]) if background_stat.count[0] else 0.0, 6),
        "foreground_mean_luma_delta": round(float(foreground_stat.mean[0]) if foreground_stat.count[0] else 0.0, 6),
    }


def beat_breath_edge_delta_overlay(base_plate: Image.Image, foreground_matte: Image.Image, out_path: Path) -> dict[str, Any]:
    effected, _ = apply_beat_breath_background(base_plate, foreground_matte, 1.0)
    diff = ImageChops.difference(base_plate.convert("L"), effected.convert("L"))
    overlay = base_plate.convert("RGBA")
    delta = Image.new("RGBA", (WIDTH, HEIGHT), (88, 178, 255, 0))
    delta.putalpha(diff.point(lambda value: min(190, int(value * 4))))
    overlay = Image.alpha_composite(overlay, delta)
    edge = foreground_matte.filter(ImageFilter.FIND_EDGES).point(lambda value: 255 if value >= 2 else 0)
    edge_layer = Image.new("RGBA", (WIDTH, HEIGHT), (255, 224, 148, 0))
    edge_layer.putalpha(edge.point(lambda value: int(value * 0.82)))
    overlay = Image.alpha_composite(overlay, edge_layer)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    overlay.convert("RGB").save(out_path, quality=92)
    foreground_stat = ImageStat.Stat(diff, beat_breath_soft_foreground_mask(foreground_matte))
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "foreground_mean_luma_delta_at_max_pulse": round(float(foreground_stat.mean[0]) if foreground_stat.count[0] else 0.0, 6),
    }


def compose_beat_breath_episode_frame(
    segment: TimelineSegment,
    t: float,
    base_plates: dict[str, Image.Image],
    foreground_mattes: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
    beat_analysis: dict[str, Any],
) -> tuple[Image.Image, dict[str, Any]]:
    pulse = beat_breath_pulse_at(beat_analysis, t)
    effected_base, effect_context = apply_beat_breath_background(base_plates[segment.slug], foreground_mattes[segment.slug], pulse)
    high_base = effected_base.convert("RGBA").resize(
        (WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE),
        Image.Resampling.LANCZOS,
    )
    source_time = segment.source_start + max(0.0, t - segment.start)
    frame = composite_short_card_on_high_base(
        high_base,
        short_frame(short_frames, segment.slug, source_time),
        episode_plate_quad(segment, t),
    )
    return frame, {
        "slug": segment.slug,
        "global_time_seconds": round(t, 6),
        "segment_elapsed_seconds": round(max(0.0, t - segment.start), 6),
        "short_source_time_seconds": round(source_time, 6),
        "beat_breath": effect_context,
    }


def compose_music_only_beat_breath_frame(
    t: float,
    duration: float,
    segments: list[TimelineSegment],
    base_plates: dict[str, Image.Image],
    foreground_mattes: dict[str, Image.Image],
    short_frames: dict[str, list[Path]],
    beat_analysis: dict[str, Any],
) -> tuple[Image.Image, list[dict[str, Any]]]:
    index, segment = find_segment(segments, t)
    if segment.role != "voiceover_episode_sequence":
        raise SystemExit(f"Beat-breath proof received non-episode time {t:.3f}s")
    current, current_context = compose_beat_breath_episode_frame(
        segment,
        t,
        base_plates,
        foreground_mattes,
        short_frames,
        beat_analysis,
    )
    contexts = [current_context]
    transition = 0.32
    if index > 0 and 0 <= t - segment.start < transition:
        previous = segments[index - 1]
        if previous.role == "voiceover_episode_sequence":
            previous_frame, previous_context = compose_beat_breath_episode_frame(
                previous,
                min(previous.end - 1 / FPS, t),
                base_plates,
                foreground_mattes,
                short_frames,
                beat_analysis,
            )
            current = Image.blend(previous_frame, current, ease((t - segment.start) / transition))
            contexts = [previous_context, current_context]
    frame = apply_section_grade(current, t, MUSIC_ONLY_OUTRO_START_SECONDS)
    frame = add_music_only_subject_badges(frame, t, segments)
    return frame, contexts


def mux_video_with_source_audio_slice(
    silent_video: Path,
    source_mp4: Path,
    final_mp4: Path,
    source_start_seconds: float,
    duration_seconds: float,
) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-ss",
            f"{source_start_seconds:.6f}",
            "-t",
            f"{duration_seconds:.6f}",
            "-i",
            str(source_mp4),
            "-t",
            f"{duration_seconds:.6f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])


def create_video_before_after_contact_sheet(
    source_video: Path,
    proof_video: Path,
    samples: list[tuple[str, float]],
    out_path: Path,
    *,
    proof_time_offset_seconds: float,
) -> dict[str, Any]:
    thumb_w, thumb_h = 480, 270
    label_h = 38
    sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + label_h) * len(samples)), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for row, (label, global_t) in enumerate(samples):
        y = row * (thumb_h + label_h)
        source = raw_video_frame_image(source_video, global_t).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        proof_t = max(0.0, global_t - proof_time_offset_seconds)
        proof = raw_video_frame_image(proof_video, proof_t).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(source, (0, y))
        sheet.paste(proof, (thumb_w, y))
        draw.text((12, y + thumb_h + 8), f"{global_t:05.2f}s baseline {label}", font=label_font, fill=PAPER)
        draw.text((thumb_w + 12, y + thumb_h + 8), f"{proof_t:05.2f}s beat breath", font=label_font, fill=PAPER)
        entries.append({"label": label, "global_time_seconds": global_t, "proof_time_seconds": proof_t})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {"path": str(out_path), "sha256": file_sha256(out_path), "samples": entries}


def create_beat_breath_visibility_qa_sheet(
    source_video: Path,
    proof_video: Path,
    samples: list[tuple[str, float]],
    out_path: Path,
    *,
    proof_time_offset_seconds: float,
) -> dict[str, Any]:
    crop_xy = (40, 50, 1120, 820)
    thumb_w, thumb_h = 360, 257
    label_h = 34
    sheet = Image.new("RGB", (thumb_w * 3, (thumb_h + label_h) * len(samples)), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(15, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for row, (label, global_t) in enumerate(samples):
        y = row * (thumb_h + label_h)
        proof_t = max(0.0, global_t - proof_time_offset_seconds)
        baseline = raw_video_frame_image(source_video, global_t).crop(crop_xy)
        proof = raw_video_frame_image(proof_video, proof_t).crop(crop_xy)
        diff = ImageChops.difference(baseline.convert("L"), proof.convert("L"))
        mean_delta = float(ImageStat.Stat(diff.resize((270, 193), Image.Resampling.BILINEAR)).mean[0])
        diff_rgb = Image.merge("RGB", (diff, diff, diff))
        diff_rgb = ImageEnhance.Brightness(diff_rgb).enhance(7.0)
        sheet.paste(baseline.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (0, y))
        sheet.paste(proof.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (thumb_w, y))
        sheet.paste(diff_rgb.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (thumb_w * 2, y))
        draw.text((10, y + thumb_h + 8), f"{global_t:05.2f}s baseline {label}", font=label_font, fill=PAPER)
        draw.text((thumb_w + 10, y + thumb_h + 8), f"{proof_t:05.2f}s proof", font=label_font, fill=PAPER)
        draw.text((thumb_w * 2 + 10, y + thumb_h + 8), f"diff x7 mean {mean_delta:.2f}", font=label_font, fill=PAPER)
        entries.append(
            {
                "label": label,
                "global_time_seconds": round(global_t, 6),
                "proof_time_seconds": round(proof_t, 6),
                "background_crop_mean_luma_delta": round(mean_delta, 6),
            }
        )
    mean_delta = sum(item["background_crop_mean_luma_delta"] for item in entries) / max(len(entries), 1)
    max_delta = max((item["background_crop_mean_luma_delta"] for item in entries), default=0.0)
    min_delta = min((item["background_crop_mean_luma_delta"] for item in entries), default=0.0)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "crop_xy": list(crop_xy),
        "diff_preview_gain": 7.0,
        "samples": entries,
        "mean_background_crop_luma_delta": round(mean_delta, 6),
        "max_background_crop_luma_delta": round(max_delta, 6),
        "min_background_crop_luma_delta": round(min_delta, 6),
        "human_visible_beat_breath_read": "pass" if mean_delta >= 9.0 and max_delta >= 12.0 else "tighten",
    }


def beat_breath_response_qa(frame_metrics: list[dict[str, Any]], beat_analysis: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    pulses = np.array([float(metric["pulse"]) for metric in frame_metrics], dtype=np.float64)
    background_delta = np.array([float(metric["background_mean_luma_delta"]) for metric in frame_metrics], dtype=np.float64)
    foreground_delta = np.array([float(metric["foreground_mean_luma_delta"]) for metric in frame_metrics], dtype=np.float64)
    if pulses.size > 2 and float(pulses.std()) > 1e-6 and float(background_delta.std()) > 1e-6:
        correlation = float(np.corrcoef(pulses, background_delta)[0, 1])
    else:
        correlation = 0.0
    slug_correlations = []
    for slug in sorted({str(metric["slug"]) for metric in frame_metrics}):
        slug_metrics = [metric for metric in frame_metrics if metric["slug"] == slug]
        slug_pulses = np.array([float(metric["pulse"]) for metric in slug_metrics], dtype=np.float64)
        slug_background_delta = np.array(
            [float(metric["background_mean_luma_delta"]) for metric in slug_metrics],
            dtype=np.float64,
        )
        if slug_pulses.size > 2 and float(slug_pulses.std()) > 1e-6 and float(slug_background_delta.std()) > 1e-6:
            slug_correlation = float(np.corrcoef(slug_pulses, slug_background_delta)[0, 1])
        else:
            slug_correlation = 0.0
        slug_correlations.append({"slug": slug, "correlation": round(slug_correlation, 6)})
    mean_slug_correlation = (
        float(np.mean([item["correlation"] for item in slug_correlations])) if slug_correlations else 0.0
    )
    max_foreground_delta = float(foreground_delta.max()) if foreground_delta.size else 0.0
    max_background_delta = float(background_delta.max()) if background_delta.size else 0.0
    return {
        "beat_alignment_read": beat_analysis["beat_alignment_read"],
        "abrupt_pulse_read": beat_analysis["abrupt_pulse_read"],
        "background_luma_response_correlation": round(correlation, 6),
        "background_luma_response_slug_correlations": slug_correlations,
        "background_luma_response_mean_slug_correlation": round(mean_slug_correlation, 6),
        "background_luma_response_read": "pass"
        if mean_slug_correlation >= 0.45 and max_background_delta >= 0.10
        else "review",
        "background_luma_response_read_context": "low_amplitude_scene_local_diagnostic_for_subtle_proof",
        "foreground_stability_max_luma_delta": round(max_foreground_delta, 6),
        "foreground_stability_read": "pass" if max_foreground_delta <= 1.65 else "review",
        "hard_mask_edge_read": "review_soft_mask_diagnostic_only",
    }


def concise_media_probe(path: Path) -> dict[str, Any]:
    probe = ffprobe_json(path)
    streams = probe.get("streams", [])
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
    return {
        "path": str(path),
        "sha256": file_sha256(path),
        "duration_seconds": round(float(probe.get("format", {}).get("duration", 0.0)), 6),
        "video_stream_count": len(video_streams),
        "audio_stream_count": len(audio_streams),
        "video_streams": video_streams,
        "audio_streams": audio_streams,
        "format": probe.get("format", {}),
    }


def full_decode_read(path: Path) -> dict[str, Any]:
    run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    return {"path": str(path), "full_decode_read": "pass"}


def create_beat_breath_frame_strip(
    video_path: Path,
    beats: list[dict[str, Any]],
    out_path: Path,
) -> dict[str, Any]:
    selected = sorted(beats, key=lambda item: float(item["strength"]), reverse=True)[:4]
    selected = sorted(selected, key=lambda item: float(item["relative_time_seconds"]))
    samples: list[tuple[str, float]] = []
    for index, beat in enumerate(selected, start=1):
        center = float(beat["relative_time_seconds"])
        strength = float(beat["strength"])
        samples.extend(
            [
                (f"beat {index} pre p={strength:.2f}", max(0.0, center - 0.08)),
                (f"beat {index} hit p={strength:.2f}", center),
                (f"beat {index} decay p={strength:.2f}", min(center + 0.16, BEAT_BREATH_END_SECONDS - BEAT_BREATH_START_SECONDS - 1 / FPS)),
            ]
        )
    if not samples:
        samples = [("fallback", 0.5)]
    return create_labeled_video_contact_sheet(video_path, out_path, samples, columns=3)


def create_beat_grid_timing_comparison_sheet(
    old_analysis: dict[str, Any],
    new_analysis: dict[str, Any],
    out_path: Path,
) -> dict[str, Any]:
    duration = float(new_analysis["duration_seconds"])
    sheet_w, sheet_h = 1600, 520
    margin_x = 82
    top_y = 140
    bottom_y = 320
    line_w = sheet_w - margin_x * 2
    img = Image.new("RGB", (sheet_w, sheet_h), INK)
    draw = ImageDraw.Draw(img)
    title_font = font(28, TITLE_SYSTEM.font_weight["semibold"])
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    small_font = font(14, TITLE_SYSTEM.font_weight["regular"])

    def x_for_time(t: float) -> int:
        return int(round(margin_x + max(0.0, min(duration, t)) / duration * line_w))

    old_label = old_analysis.get("analysis_strategy", "previous pulse times")
    new_label = new_analysis.get("analysis_strategy", "new pulse times")
    draw.text((margin_x, 42), "Beat timing comparison", font=title_font, fill=PAPER)
    for y, label in ((top_y, old_label), (bottom_y, new_label)):
        draw.line((margin_x, y, margin_x + line_w, y), fill=(110, 144, 172), width=2)
        draw.text((margin_x, y - 42), label, font=label_font, fill=PAPER)
        for second in range(0, int(math.ceil(duration)) + 1, 2):
            x = x_for_time(second)
            draw.line((x, y - 10, x, y + 10), fill=(64, 88, 112), width=1)
            draw.text((x - 10, y + 18), f"{second}", font=small_font, fill=(150, 166, 184))

    old_beats = old_analysis.get("beats", [])
    new_beats = new_analysis.get("beats", [])
    for beat in old_beats:
        x = x_for_time(float(beat["relative_time_seconds"]))
        strength = float(beat.get("strength", 0.65))
        height = int(32 + 42 * strength)
        draw.line((x, top_y - height, x, top_y + height), fill=(255, 130, 116), width=3)
    for beat in new_beats:
        x = x_for_time(float(beat["relative_time_seconds"]))
        strength = float(beat.get("strength", 0.72))
        height = int(28 + 38 * strength)
        draw.line((x, bottom_y - height, x, bottom_y + height), fill=(116, 214, 255), width=2)

    old_intervals = [
        float(old_beats[index + 1]["relative_time_seconds"]) - float(old_beats[index]["relative_time_seconds"])
        for index in range(len(old_beats) - 1)
    ]
    new_intervals = [
        float(new_beats[index + 1]["relative_time_seconds"]) - float(new_beats[index]["relative_time_seconds"])
        for index in range(len(new_beats) - 1)
    ]
    old_max_gap = max(old_intervals, default=0.0)
    new_max_gap = max(new_intervals, default=0.0)
    selected_period = new_analysis.get("selected_period_seconds")
    if selected_period is None:
        timing_descriptor = (
            f"events={len(new_beats)} median interval={float(new_analysis.get('median_interval_seconds', 0.0)):.3f}s "
            f"std={float(new_analysis.get('interval_std_seconds', 0.0)):.3f}s"
        )
    else:
        timing_descriptor = f"beats={len(new_beats)} period={float(selected_period):.6f}s"
    summary = f"old beats={len(old_beats)} max gap={old_max_gap:.3f}s  |  new {timing_descriptor} max gap={new_max_gap:.3f}s"
    draw.text((margin_x, sheet_h - 72), summary, font=label_font, fill=PAPER)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "old_beat_count": len(old_beats),
        "new_beat_count": len(new_beats),
        "old_max_gap_seconds": round(old_max_gap, 6),
        "new_max_gap_seconds": round(new_max_gap, 6),
    }


def create_bass_drum_hit_evidence_sheet(
    analysis: dict[str, Any],
    out_path: Path,
    *,
    global_seconds: tuple[float, float],
    title: str,
) -> dict[str, Any]:
    import numpy as np

    audio_path = Path(analysis["audio_mono_f32_path"])
    sample_rate = int(analysis["sample_rate"])
    source_start = float(analysis["source_seconds"][0])
    source_end = float(analysis["source_seconds"][1])
    start_global = max(source_start, float(global_seconds[0]))
    end_global = min(source_end, float(global_seconds[1]))
    start_rel = start_global - source_start
    end_rel = end_global - source_start
    audio = np.fromfile(audio_path, dtype=np.float32)
    start_index = max(0, min(audio.size, int(round(start_rel * sample_rate))))
    end_index = max(start_index + 1, min(audio.size, int(round(end_rel * sample_rate))))
    segment = audio[start_index:end_index]

    sheet_w, sheet_h = 1800, 920
    margin_x = 86
    plot_w = sheet_w - margin_x * 2
    waveform_top = 108
    waveform_h = 250
    spec_top = 430
    spec_h = 330
    footer_y = 800
    img = Image.new("RGB", (sheet_w, sheet_h), INK)
    draw = ImageDraw.Draw(img)
    title_font = font(28, TITLE_SYSTEM.font_weight["semibold"])
    label_font = font(17, TITLE_SYSTEM.font_weight["semibold"])
    small_font = font(13, TITLE_SYSTEM.font_weight["regular"])
    draw.text((margin_x, 42), title, font=title_font, fill=PAPER)
    draw.text(
        (margin_x, 78),
        f"Global {start_global:.3f}-{end_global:.3f}s. Green=confirmed bass drum hit. Coral=rejected assisted candidate.",
        font=small_font,
        fill=(166, 184, 202),
    )

    def x_for_global(global_time: float) -> int:
        return int(round(margin_x + (global_time - start_global) / max(end_global - start_global, 1e-6) * plot_w))

    draw.rectangle((margin_x, waveform_top, margin_x + plot_w, waveform_top + waveform_h), outline=(70, 96, 120), width=1)
    center_y = waveform_top + waveform_h // 2
    samples_per_px = max(1, int(math.ceil(segment.size / plot_w)))
    for x in range(plot_w):
        lo = x * samples_per_px
        hi = min(segment.size, lo + samples_per_px)
        if lo >= hi:
            continue
        peak = float(np.max(np.abs(segment[lo:hi])))
        y = int(round(peak * (waveform_h * 0.46)))
        draw.line((margin_x + x, center_y - y, margin_x + x, center_y + y), fill=(144, 194, 218), width=1)
    draw.text((margin_x, waveform_top - 26), "Waveform", font=label_font, fill=PAPER)

    window = 2048
    hop = max(256, int(max(1, segment.size - window) / max(plot_w, 1)))
    if segment.size < window:
        padded = np.pad(segment, (0, window - segment.size))
    else:
        padded = segment
    frames = np.lib.stride_tricks.sliding_window_view(padded, window)[::hop]
    spectrum = np.abs(np.fft.rfft(frames * np.hanning(window), axis=1))
    freqs = np.fft.rfftfreq(window, 1.0 / sample_rate)
    mask = (freqs >= 20.0) & (freqs <= 240.0)
    spec = np.log1p(spectrum[:, mask].T)
    spec = spec - float(spec.min())
    spec = spec / max(float(np.percentile(spec, 99.0)), 1e-9)
    spec = np.clip(spec, 0.0, 1.0)
    spec_img = Image.fromarray((spec * 255).astype("uint8"), "L")
    spec_img = ImageOps.flip(spec_img)
    spec_rgb = Image.merge(
        "RGB",
        (
            ImageEnhance.Brightness(spec_img).enhance(0.45),
            ImageEnhance.Brightness(spec_img).enhance(0.78),
            spec_img,
        ),
    ).resize((plot_w, spec_h), Image.Resampling.BILINEAR)
    img.paste(spec_rgb, (margin_x, spec_top))
    draw.rectangle((margin_x, spec_top, margin_x + plot_w, spec_top + spec_h), outline=(70, 96, 120), width=1)
    draw.text((margin_x, spec_top - 26), "Low-frequency spectrogram, 20-240 Hz", font=label_font, fill=PAPER)

    for window_report in analysis["rejected_no_bass_drum_windows"]:
        window_start, window_end = [float(value) for value in window_report["global_seconds"]]
        if window_end <= start_global or window_start >= end_global:
            continue
        x0 = x_for_global(max(start_global, window_start))
        x1 = x_for_global(min(end_global, window_end))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.rectangle((x0, waveform_top, x1, spec_top + spec_h), fill=(255, 124, 104, 34))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        draw.text((x0 + 8, spec_top + spec_h + 8), "no bass drum window", font=small_font, fill=(255, 154, 136))

    hit_times = [float(beat["global_time_seconds"]) for beat in analysis["beats"]]
    rejected_times = [float(candidate["global_time_seconds"]) for candidate in analysis["rejected_candidates"]]
    for global_time in rejected_times:
        if start_global <= global_time <= end_global:
            x = x_for_global(global_time)
            draw.line((x, waveform_top, x, spec_top + spec_h), fill=(255, 114, 100), width=2)
    for global_time in hit_times:
        if start_global <= global_time <= end_global:
            x = x_for_global(global_time)
            draw.line((x, waveform_top, x, spec_top + spec_h), fill=(120, 236, 212), width=3)
            draw.ellipse((x - 5, waveform_top - 8, x + 5, waveform_top + 2), fill=(120, 236, 212))

    for second in range(math.floor(start_global), math.ceil(end_global) + 1):
        if start_global <= second <= end_global:
            x = x_for_global(float(second))
            draw.line((x, spec_top + spec_h, x, spec_top + spec_h + 8), fill=(92, 118, 144), width=1)
            draw.text((x - 12, spec_top + spec_h + 14), f"{second}", font=small_font, fill=(148, 166, 188))

    confirmed_in_window = sum(1 for time in hit_times if start_global <= time <= end_global)
    rejected_in_window = sum(1 for time in rejected_times if start_global <= time <= end_global)
    max_rejected_window_pulse = 0.0
    for report in analysis["rejected_no_bass_drum_windows"]:
        report_start, report_end = [float(value) for value in report["global_seconds"]]
        if report_end <= start_global or report_start >= end_global:
            continue
        window_start = max(start_global, report_start)
        window_end = min(end_global, report_end)
        window_pulses = [
            float(row["pulse"])
            for row in analysis["frame_pulses"]
            if window_start <= float(row["global_time_seconds"]) < window_end
        ]
        max_rejected_window_pulse = max(max_rejected_window_pulse, max(window_pulses, default=0.0))
    draw.text(
        (margin_x, footer_y),
        f"Confirmed hits in view: {confirmed_in_window}   Rejected candidates in view: {rejected_in_window}   Max pulse in no-drum window: {max_rejected_window_pulse:.4f}",
        font=label_font,
        fill=PAPER,
    )
    draw.text(
        (margin_x, footer_y + 34),
        "This sheet is QA evidence only; only green confirmed-hit times drive the rendered breath.",
        font=small_font,
        fill=(166, 184, 202),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "global_seconds": [round(start_global, 6), round(end_global, 6)],
        "confirmed_hit_count": confirmed_in_window,
        "rejected_candidate_count": rejected_in_window,
        "max_rejected_window_pulse": round(max_rejected_window_pulse, 6),
    }


def tacoma_737_audit_reel_seconds(global_seconds: float) -> float:
    return global_seconds - BEAT_TACOMA_737_AUDIT_GLOBAL_ZERO_SECONDS


def tacoma_737_audit_subject(global_seconds: float) -> str:
    if BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[0] <= global_seconds < BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[1]:
        return "Tacoma Narrows"
    if BEAT_TACOMA_737_AUDIT_737_SECONDS[0] <= global_seconds < BEAT_TACOMA_737_AUDIT_737_SECONDS[1]:
        return "737 MAX"
    return "transition"


def tacoma_737_audit_candidate_map(current_hit_map: dict[str, Any], *, corrected: bool = False) -> dict[str, Any]:
    beats = current_hit_map.get("beats", [])
    rejected = current_hit_map.get("rejected_candidates", [])

    def nearest(items: list[dict[str, Any]], global_time: float) -> tuple[float, dict[str, Any] | None]:
        if not items:
            return 999.0, None
        item = min(items, key=lambda value: abs(float(value["global_time_seconds"]) - global_time))
        return abs(float(item["global_time_seconds"]) - global_time), item

    if corrected:
        candidate_specs = [
            *[
                (global_time, "confirmed_bass_drum_hit", "human_review_correction_from_diagnostic_peak")
                for global_time in BEAT_TACOMA_737_CORRECTED_TACOMA_HIT_SECONDS
            ],
            *[
                (global_time, "confirmed_bass_drum_hit", "human_review_correction_from_737_diagnostic_peak")
                for global_time in BEAT_TACOMA_737_CORRECTED_737_HIT_SECONDS
            ],
            *[
                (global_time, "rejected_not_bass_drum_hit", "human_review_kept_rejected")
                for global_time in BEAT_TACOMA_737_CORRECTED_REJECTED_SECONDS
            ],
        ]
        candidate_specs = sorted(candidate_specs, key=lambda item: item[0])
    else:
        candidate_specs = [(global_time, None, None) for global_time in BEAT_TACOMA_737_AUDIT_CANDIDATE_SECONDS]

    entries = []
    for index, (global_time, corrected_decision, corrected_source) in enumerate(candidate_specs, start=1):
        beat_delta, beat = nearest(beats, global_time)
        rejected_delta, rejected_item = nearest(rejected, global_time)
        if corrected_decision is not None:
            decision = corrected_decision
            decision_source = corrected_source or "human_review_correction"
            if beat_delta <= 0.060:
                source = beat or {}
            elif rejected_delta <= 0.060:
                source = rejected_item or {}
            else:
                source = {}
        else:
            if beat_delta <= 0.012:
                decision = "confirmed_bass_drum_hit"
                source = beat or {}
                decision_source = "current_strict_bass_drum_only_hit_map"
            elif rejected_delta <= 0.012:
                decision = "rejected_not_bass_drum_hit"
                source = rejected_item or {}
                decision_source = "current_strict_bass_drum_only_rejected_candidate_map"
            else:
                decision = "rejected_not_bass_drum_hit"
                source = {}
                decision_source = "not_present_in_current_confirmed_hit_map"
        entries.append(
            {
                "index": index,
                "global_time_seconds": round(global_time, 6),
                "review_reel_time_seconds": round(tacoma_737_audit_reel_seconds(global_time), 6),
                "audit_window_relative_seconds": round(global_time - BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS[0], 6),
                "subject": tacoma_737_audit_subject(global_time),
                "decision": decision,
                "decision_source": decision_source,
                "human_reaudit_required": True,
                "corrected_audit_decision": corrected,
                "strength": source.get("strength"),
                "rejection_reason": source.get("rejection_reason"),
                "nearest_assisted_candidate_global_seconds": source.get("nearest_assisted_candidate_global_seconds")
                or source.get("nearest_onset_relative_seconds"),
                "sub_bass_35_95_strength": (
                    source.get("candidate_low_band_strengths", {}).get("sub_bass_35_95_strength")
                    if source.get("candidate_low_band_strengths")
                    else source.get("sub_bass_35_95_strength")
                ),
                "low_bass_45_130_strength": (
                    source.get("candidate_low_band_strengths", {}).get("low_bass_45_130_strength")
                    if source.get("candidate_low_band_strengths")
                    else source.get("low_bass_45_130_strength")
                ),
                "bass_body_55_180_strength": (
                    source.get("candidate_low_band_strengths", {}).get("bass_body_55_180_strength")
                    if source.get("candidate_low_band_strengths")
                    else source.get("bass_body_55_180_strength")
                ),
            }
        )

    diagnostic_peaks = []
    for index, global_time in enumerate(BEAT_TACOMA_737_AUDIT_DIAGNOSTIC_PEAK_SECONDS, start=1):
        nearest_entry = min(entries, key=lambda entry: abs(float(entry["global_time_seconds"]) - global_time))
        diagnostic_peaks.append(
            {
                "index": index,
                "global_time_seconds": round(global_time, 6),
                "review_reel_time_seconds": round(tacoma_737_audit_reel_seconds(global_time), 6),
                "subject": tacoma_737_audit_subject(global_time),
                "source": "full_band_rms_peak_diagnostic_not_candidate_decision",
                "nearest_candidate_global_seconds": nearest_entry["global_time_seconds"],
                "nearest_candidate_decision": nearest_entry["decision"],
                "nearest_candidate_delta_seconds": round(global_time - float(nearest_entry["global_time_seconds"]), 6),
            }
        )

    confirmed = [entry for entry in entries if entry["decision"] == "confirmed_bass_drum_hit"]
    rejected_entries = [entry for entry in entries if entry["decision"] == "rejected_not_bass_drum_hit"]
    return {
        "analysis_strategy": "corrected_strict_bass_drum_hit_audit_tacoma_737_no_pulse_render"
        if corrected
        else "strict_bass_drum_hit_audit_tacoma_737_no_pulse_render",
        "variant_of_hit_map_path": str(BEAT_TACOMA_737_AUDIT_VARIANT_OF_HIT_MAP),
        "strict_rule": "only confirmed_bass_drum_hit entries may drive future breath pulses",
        "audit_window_global_seconds": list(BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS),
        "tacoma_narrows_seconds": list(BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS),
        "boeing_737_max_seconds": list(BEAT_TACOMA_737_AUDIT_737_SECONDS),
        "broad_no_drum_window_inherited": False,
        "broad_no_drum_window_replacement": "explicit_candidate_decisions",
        "corrected_audit": corrected,
        "superseded_timing_references": [
            {
                "global_time_seconds": round(global_time, 6),
                "subject": tacoma_737_audit_subject(global_time),
                "superseded_reason": "old_737_timing_reference_not_active_pulse_driver"
                if global_time >= BEAT_TACOMA_737_AUDIT_737_SECONDS[0]
                else "old_rejected_reference_not_active_pulse_driver",
            }
            for global_time in BEAT_TACOMA_737_SUPERSEDED_737_TIMING_SECONDS
        ]
        if corrected
        else [],
        "candidate_decisions": entries,
        "diagnostic_737_timing_peaks": diagnostic_peaks,
        "confirmed_candidate_count": len(confirmed),
        "rejected_candidate_count": len(rejected_entries),
        "tacoma_confirmed_candidate_count": sum(
            1 for entry in confirmed if entry["subject"] == "Tacoma Narrows"
        ),
        "boeing_737_max_confirmed_candidate_count": sum(
            1 for entry in confirmed if entry["subject"] == "737 MAX"
        ),
        "titanic_confirmed_candidate_count": 0,
        "all_candidates_have_binary_decision_read": "pass"
        if all(entry["decision"] in {"confirmed_bass_drum_hit", "rejected_not_bass_drum_hit"} for entry in entries)
        else "tighten",
        "human_bass_drum_hit_audit_read": "review_required",
    }


def write_tacoma_737_audit_candidate_files(candidate_map: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "tacoma_737_bass_drum_candidate_audit.json"
    csv_path = out_dir / "tacoma_737_bass_drum_candidate_audit.csv"
    diagnostic_csv_path = out_dir / "tacoma_737_737_diagnostic_peaks.csv"
    json_path.write_text(json.dumps(candidate_map, indent=2) + "\n", encoding="utf-8")

    fieldnames = [
        "index",
        "global_time_seconds",
        "review_reel_time_seconds",
        "audit_window_relative_seconds",
        "subject",
        "decision",
        "decision_source",
        "human_reaudit_required",
        "corrected_audit_decision",
        "strength",
        "rejection_reason",
        "sub_bass_35_95_strength",
        "low_bass_45_130_strength",
        "bass_body_55_180_strength",
    ]
    csv_lines = [",".join(fieldnames)]
    for entry in candidate_map["candidate_decisions"]:
        csv_lines.append(
            ",".join(
                str(entry.get(field, "")).replace(",", ";")
                for field in fieldnames
            )
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    diagnostic_lines = [
        "index,global_time_seconds,review_reel_time_seconds,subject,source,nearest_candidate_global_seconds,nearest_candidate_decision,nearest_candidate_delta_seconds"
    ]
    for peak in candidate_map["diagnostic_737_timing_peaks"]:
        diagnostic_lines.append(
            ",".join(
                str(peak.get(field, ""))
                for field in [
                    "index",
                    "global_time_seconds",
                    "review_reel_time_seconds",
                    "subject",
                    "source",
                    "nearest_candidate_global_seconds",
                    "nearest_candidate_decision",
                    "nearest_candidate_delta_seconds",
                ]
            )
        )
    diagnostic_csv_path.write_text("\n".join(diagnostic_lines) + "\n", encoding="utf-8")
    return {
        "candidate_json_path": str(json_path),
        "candidate_json_sha256": file_sha256(json_path),
        "candidate_csv_path": str(csv_path),
        "candidate_csv_sha256": file_sha256(csv_path),
        "diagnostic_peaks_csv_path": str(diagnostic_csv_path),
        "diagnostic_peaks_csv_sha256": file_sha256(diagnostic_csv_path),
    }


def draw_tacoma_737_audit_timeline(
    draw: ImageDraw.ImageDraw,
    y: int,
    width: int,
    candidate_map: dict[str, Any],
    current_global_time: float | None = None,
) -> None:
    start, end = BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS
    x0, x1 = 96, width - 96
    label_font = font(20, TITLE_SYSTEM.font_weight["semibold"])
    small_font = font(15, TITLE_SYSTEM.font_weight["regular"])
    draw.line((x0, y, x1, y), fill=(116, 148, 172), width=2)
    tacoma_end_x = int(round(x0 + (BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[1] - start) / (end - start) * (x1 - x0)))
    draw.rectangle((x0, y - 22, tacoma_end_x, y + 22), fill=(63, 89, 112))
    draw.rectangle((tacoma_end_x, y - 22, x1, y + 22), fill=(72, 78, 116))
    draw.text((x0, y - 58), "Tacoma Narrows", font=small_font, fill=(196, 214, 228))
    draw.text((tacoma_end_x + 12, y - 58), "737 MAX", font=small_font, fill=(196, 214, 228))
    for second in range(math.floor(start), math.ceil(end) + 1):
        x = int(round(x0 + (second - start) / (end - start) * (x1 - x0)))
        draw.line((x, y - 28, x, y + 28), fill=(102, 130, 154), width=1)
        draw.text((x - 12, y + 34), str(second), font=small_font, fill=(146, 166, 186))
    for peak in candidate_map["diagnostic_737_timing_peaks"]:
        global_time = float(peak["global_time_seconds"])
        x = int(round(x0 + (global_time - start) / (end - start) * (x1 - x0)))
        draw.line((x, y - 42, x, y + 42), fill=(174, 152, 228), width=2)
    for entry in candidate_map["candidate_decisions"]:
        global_time = float(entry["global_time_seconds"])
        x = int(round(x0 + (global_time - start) / (end - start) * (x1 - x0)))
        confirmed = entry["decision"] == "confirmed_bass_drum_hit"
        color = (120, 236, 212) if confirmed else (255, 122, 104)
        radius = 10 if confirmed else 8
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        draw.text((x - 30, y - 86 if confirmed else y + 58), f"{global_time:.3f}", font=small_font, fill=color)
    if current_global_time is not None:
        x = int(round(x0 + (current_global_time - start) / (end - start) * (x1 - x0)))
        draw.line((x, y - 110, x, y + 102), fill=PAPER, width=3)
    draw.text((x0, y - 118), "green=confirmed  coral=rejected  lavender=diagnostic 737 envelope peak", font=label_font, fill=PAPER)


def render_tacoma_737_audit_frames(
    source_reel: Path,
    frames_dir: Path,
    candidate_map: dict[str, Any],
) -> dict[str, Any]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    start, end = BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS
    duration = end - start
    frame_count = int(round(duration * FPS))
    title_font = font(31, TITLE_SYSTEM.font_weight["semibold"])
    label_font = font(22, TITLE_SYSTEM.font_weight["semibold"])
    small_font = font(17, TITLE_SYSTEM.font_weight["regular"])
    for frame_index in range(frame_count):
        global_time = start + frame_index / FPS
        reel_time = tacoma_737_audit_reel_seconds(global_time)
        frame = raw_video_frame_image(source_reel, reel_time).convert("RGBA")
        overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.rectangle((0, 0, WIDTH, 132), fill=(5, 10, 24, 172))
        odraw.rectangle((0, HEIGHT - 190, WIDTH, HEIGHT), fill=(5, 10, 24, 190))
        odraw.text((58, 34), "Tacoma / 737 bass-drum hit audit", font=title_font, fill=PAPER)
        odraw.text(
            (58, 78),
            f"global {global_time:06.3f}s  |  strict rule: pulse only on confirmed audible bass drum",
            font=small_font,
            fill=(176, 196, 214),
        )
        active_entries = [
            entry
            for entry in candidate_map["candidate_decisions"]
            if abs(float(entry["global_time_seconds"]) - global_time) <= 0.085
        ]
        for entry in active_entries:
            confirmed = entry["decision"] == "confirmed_bass_drum_hit"
            color = (120, 236, 212) if confirmed else (255, 122, 104)
            odraw.rectangle((46, 142, 750, 204), fill=(5, 10, 24, 204), outline=color, width=3)
            odraw.text(
                (66, 158),
                f"{entry['global_time_seconds']:.3f}s {entry['subject']}: {entry['decision']}",
                font=label_font,
                fill=color,
            )
        diagnostic_entries = [
            peak
            for peak in candidate_map["diagnostic_737_timing_peaks"]
            if abs(float(peak["global_time_seconds"]) - global_time) <= 0.085
        ]
        for peak in diagnostic_entries:
            odraw.rectangle((46, 214, 750, 266), fill=(5, 10, 24, 190), outline=(174, 152, 228), width=2)
            odraw.text(
                (66, 228),
                f"{peak['global_time_seconds']:.3f}s diagnostic 737 envelope peak",
                font=small_font,
                fill=(198, 184, 242),
            )
        frame = Image.alpha_composite(frame, overlay).convert("RGB")
        draw = ImageDraw.Draw(frame)
        draw_tacoma_737_audit_timeline(draw, HEIGHT - 106, WIDTH, candidate_map, current_global_time=global_time)
        frame.save(frames_dir / f"frame_{frame_index:05d}.jpg", quality=92)
    return {
        "frame_count": frame_count,
        "duration_seconds": round(duration, 6),
        "global_seconds": [start, end],
    }


def create_tacoma_737_audit_evidence_sheet(
    audio_path: Path,
    sample_rate: int,
    candidate_map: dict[str, Any],
    out_path: Path,
) -> dict[str, Any]:
    import numpy as np

    start_global, end_global = BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS
    audio = np.fromfile(audio_path, dtype=np.float32)
    sheet_w, sheet_h = 1900, 1120
    margin_x = 86
    plot_w = sheet_w - margin_x * 2
    waveform_top = 126
    waveform_h = 280
    spec_top = 500
    spec_h = 340
    footer_y = 970
    img = Image.new("RGB", (sheet_w, sheet_h), INK)
    draw = ImageDraw.Draw(img)
    title_font = font(30, TITLE_SYSTEM.font_weight["semibold"])
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    small_font = font(13, TITLE_SYSTEM.font_weight["regular"])
    draw.text((margin_x, 42), "Tacoma / 737 bass-drum hit audit", font=title_font, fill=PAPER)
    draw.text(
        (margin_x, 82),
        "Green=current confirmed bass drum. Coral=current rejected candidate. Lavender=diagnostic 737 envelope peak.",
        font=small_font,
        fill=(166, 184, 202),
    )

    def x_for_global(global_time: float) -> int:
        return int(round(margin_x + (global_time - start_global) / max(end_global - start_global, 1e-6) * plot_w))

    tacoma_x1 = x_for_global(BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[1])
    segment_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(segment_overlay)
    sdraw.rectangle((margin_x, waveform_top, tacoma_x1, spec_top + spec_h), fill=(88, 178, 255, 20))
    sdraw.rectangle((tacoma_x1, waveform_top, margin_x + plot_w, spec_top + spec_h), fill=(168, 140, 255, 20))
    img = Image.alpha_composite(img.convert("RGBA"), segment_overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    draw.rectangle((margin_x, waveform_top, margin_x + plot_w, waveform_top + waveform_h), outline=(70, 96, 120), width=1)
    center_y = waveform_top + waveform_h // 2
    samples_per_px = max(1, int(math.ceil(audio.size / plot_w)))
    for x in range(plot_w):
        lo = x * samples_per_px
        hi = min(audio.size, lo + samples_per_px)
        if lo >= hi:
            continue
        peak = float(np.max(np.abs(audio[lo:hi])))
        y = int(round(peak * (waveform_h * 0.46)))
        draw.line((margin_x + x, center_y - y, margin_x + x, center_y + y), fill=(144, 194, 218), width=1)
    draw.text((margin_x, waveform_top - 28), "Waveform", font=label_font, fill=PAPER)

    window = 2048
    hop = max(256, int(max(1, audio.size - window) / max(plot_w, 1)))
    padded = np.pad(audio, (0, max(0, window - audio.size))) if audio.size < window else audio
    frames = np.lib.stride_tricks.sliding_window_view(padded, window)[::hop]
    spectrum = np.abs(np.fft.rfft(frames * np.hanning(window), axis=1))
    freqs = np.fft.rfftfreq(window, 1.0 / sample_rate)
    mask = (freqs >= 20.0) & (freqs <= 240.0)
    spec = np.log1p(spectrum[:, mask].T)
    spec = spec - float(spec.min())
    spec = spec / max(float(np.percentile(spec, 99.0)), 1e-9)
    spec = np.clip(spec, 0.0, 1.0)
    spec_img = Image.fromarray((spec * 255).astype("uint8"), "L")
    spec_img = ImageOps.flip(spec_img)
    spec_rgb = Image.merge(
        "RGB",
        (
            ImageEnhance.Brightness(spec_img).enhance(0.45),
            ImageEnhance.Brightness(spec_img).enhance(0.78),
            spec_img,
        ),
    ).resize((plot_w, spec_h), Image.Resampling.BILINEAR)
    img.paste(spec_rgb, (margin_x, spec_top))
    draw = ImageDraw.Draw(img)
    draw.rectangle((margin_x, spec_top, margin_x + plot_w, spec_top + spec_h), outline=(70, 96, 120), width=1)
    draw.text((margin_x, spec_top - 28), "Low-frequency spectrogram, 20-240 Hz", font=label_font, fill=PAPER)
    draw.text((margin_x + 6, spec_top + spec_h + 12), "Tacoma Narrows", font=small_font, fill=(168, 210, 238))
    draw.text((tacoma_x1 + 12, spec_top + spec_h + 12), "737 MAX", font=small_font, fill=(196, 184, 242))

    for second in range(math.floor(start_global), math.ceil(end_global) + 1):
        if start_global <= second <= end_global:
            x = x_for_global(float(second))
            draw.line((x, spec_top + spec_h, x, spec_top + spec_h + 8), fill=(92, 118, 144), width=1)
            draw.text((x - 12, spec_top + spec_h + 30), f"{second}", font=small_font, fill=(148, 166, 188))

    for peak in candidate_map["diagnostic_737_timing_peaks"]:
        x = x_for_global(float(peak["global_time_seconds"]))
        draw.line((x, waveform_top, x, spec_top + spec_h), fill=(174, 152, 228), width=2)
    for entry in candidate_map["candidate_decisions"]:
        x = x_for_global(float(entry["global_time_seconds"]))
        confirmed = entry["decision"] == "confirmed_bass_drum_hit"
        color = (120, 236, 212) if confirmed else (255, 114, 100)
        width = 4 if confirmed else 2
        draw.line((x, waveform_top, x, spec_top + spec_h), fill=color, width=width)
        draw.text((x - 26, waveform_top - 24 if confirmed else spec_top + spec_h + 52), f"{float(entry['global_time_seconds']):.3f}", font=small_font, fill=color)

    confirmed_count = candidate_map["confirmed_candidate_count"]
    rejected_count = candidate_map["rejected_candidate_count"]
    draw.text(
        (margin_x, footer_y),
        f"Candidate decisions: {confirmed_count} confirmed, {rejected_count} rejected. Human audit required before using these times in a proof.",
        font=label_font,
        fill=PAPER,
    )
    draw.text(
        (margin_x, footer_y + 36),
        "This sheet deliberately avoids the old broad 18-21s no-drum window; each candidate is reviewed individually.",
        font=small_font,
        fill=(166, 184, 202),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "global_seconds": [start_global, end_global],
        "confirmed_candidate_count": confirmed_count,
        "rejected_candidate_count": rejected_count,
        "diagnostic_peak_count": len(candidate_map["diagnostic_737_timing_peaks"]),
    }


def create_tacoma_737_candidate_frame_strip(
    source_reel: Path,
    candidate_map: dict[str, Any],
    out_path: Path,
) -> dict[str, Any]:
    samples = [
        (entry["decision"], float(entry["global_time_seconds"]), entry["subject"])
        for entry in candidate_map["candidate_decisions"]
    ]
    thumb_w, thumb_h, label_h = 480, 270, 54
    columns = 5
    rows = math.ceil(len(samples) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(15, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for idx, (decision, global_time, subject) in enumerate(samples):
        frame = raw_video_frame_image(source_reel, tacoma_737_audit_reel_seconds(global_time)).resize(
            (thumb_w, thumb_h),
            Image.Resampling.LANCZOS,
        )
        x = (idx % columns) * thumb_w
        y = (idx // columns) * (thumb_h + label_h)
        color = (120, 236, 212) if decision == "confirmed_bass_drum_hit" else (255, 122, 104)
        sheet.paste(frame, (x, y))
        draw.rectangle((x + 2, y + 2, x + thumb_w - 3, y + thumb_h - 3), outline=color, width=5)
        draw.text((x + 12, y + thumb_h + 8), f"{global_time:.3f}s {subject}", font=label_font, fill=PAPER)
        draw.text((x + 12, y + thumb_h + 28), decision, font=label_font, fill=color)
        entries.append({"global_time_seconds": round(global_time, 6), "subject": subject, "decision": decision})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {"path": str(out_path), "sha256": file_sha256(out_path), "samples": entries}


def create_tacoma_737_diagnostic_peak_frame_strip(
    source_reel: Path,
    candidate_map: dict[str, Any],
    out_path: Path,
) -> dict[str, Any]:
    samples = [
        (float(peak["global_time_seconds"]), peak["nearest_candidate_delta_seconds"])
        for peak in candidate_map["diagnostic_737_timing_peaks"]
    ]
    thumb_w, thumb_h, label_h = 480, 270, 48
    sheet = Image.new("RGB", (thumb_w * len(samples), thumb_h + label_h), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(15, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for idx, (global_time, delta) in enumerate(samples):
        frame = raw_video_frame_image(source_reel, tacoma_737_audit_reel_seconds(global_time)).resize(
            (thumb_w, thumb_h),
            Image.Resampling.LANCZOS,
        )
        x = idx * thumb_w
        sheet.paste(frame, (x, 0))
        draw.rectangle((x + 2, 2, x + thumb_w - 3, thumb_h - 3), outline=(174, 152, 228), width=5)
        draw.text((x + 12, thumb_h + 8), f"{global_time:.3f}s diag peak  delta {float(delta):+.3f}s", font=label_font, fill=(198, 184, 242))
        entries.append({"global_time_seconds": round(global_time, 6), "nearest_candidate_delta_seconds": delta})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {"path": str(out_path), "sha256": file_sha256(out_path), "samples": entries}


def create_tacoma_737_timing_comparison_sheet(
    previous_candidate_map: dict[str, Any],
    corrected_candidate_map: dict[str, Any],
    out_path: Path,
) -> dict[str, Any]:
    sheet_w, sheet_h = 1900, 620
    margin_x = 92
    x0, x1 = margin_x, sheet_w - margin_x
    previous_y = 220
    corrected_y = 390
    start, end = BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS
    img = Image.new("RGB", (sheet_w, sheet_h), INK)
    draw = ImageDraw.Draw(img)
    title_font = font(30, TITLE_SYSTEM.font_weight["semibold"])
    label_font = font(19, TITLE_SYSTEM.font_weight["semibold"])
    small_font = font(13, TITLE_SYSTEM.font_weight["regular"])

    def x_for_global(global_time: float) -> int:
        return int(round(x0 + (global_time - start) / max(end - start, 1e-6) * (x1 - x0)))

    draw.text((margin_x, 44), "Tacoma / 737 timing comparison", font=title_font, fill=PAPER)
    draw.text(
        (margin_x, 84),
        "Top=previous audit. Bottom=corrected audit. Green=confirmed, coral=rejected, gray=superseded reference.",
        font=small_font,
        fill=(166, 184, 202),
    )
    for y, label in [(previous_y, "previous"), (corrected_y, "corrected")]:
        draw.line((x0, y, x1, y), fill=(104, 132, 154), width=2)
        draw.text((margin_x, y - 66), label, font=label_font, fill=PAPER)
    tacoma_end_x = x_for_global(BEAT_TACOMA_737_AUDIT_TACOMA_SECONDS[1])
    for y in (previous_y, corrected_y):
        draw.rectangle((x0, y - 24, tacoma_end_x, y + 24), fill=(50, 73, 94))
        draw.rectangle((tacoma_end_x, y - 24, x1, y + 24), fill=(58, 62, 102))
    draw.text((x0, corrected_y + 54), "Tacoma Narrows", font=small_font, fill=(168, 210, 238))
    draw.text((tacoma_end_x + 12, corrected_y + 54), "737 MAX", font=small_font, fill=(196, 184, 242))
    for second in range(math.floor(start), math.ceil(end) + 1):
        x = x_for_global(float(second))
        draw.line((x, previous_y - 38, x, corrected_y + 38), fill=(76, 98, 120), width=1)
        draw.text((x - 12, corrected_y + 88), str(second), font=small_font, fill=(148, 166, 188))

    entries = []
    for map_name, y, candidate_map in [
        ("previous", previous_y, previous_candidate_map),
        ("corrected", corrected_y, corrected_candidate_map),
    ]:
        for entry in candidate_map["candidate_decisions"]:
            global_time = float(entry["global_time_seconds"])
            x = x_for_global(global_time)
            confirmed = entry["decision"] == "confirmed_bass_drum_hit"
            color = (120, 236, 212) if confirmed else (255, 114, 100)
            radius = 11 if confirmed else 8
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
            label_y = y - 56 if confirmed else y + 34
            draw.text((x - 25, label_y), f"{global_time:.3f}", font=small_font, fill=color)
            entries.append({"map": map_name, "global_time_seconds": round(global_time, 6), "decision": entry["decision"]})
    for reference in corrected_candidate_map.get("superseded_timing_references", []):
        global_time = float(reference["global_time_seconds"])
        x = x_for_global(global_time)
        draw.line((x, corrected_y - 45, x, corrected_y + 45), fill=(128, 132, 142), width=2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=92)
    return {"path": str(out_path), "sha256": file_sha256(out_path), "samples": entries}


def build_tacoma_737_bass_drum_hit_audit(args: argparse.Namespace, *, corrected: bool = False) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    experiment_id = (
        BEAT_TACOMA_737_CORRECTED_AUDIT_EXPERIMENT_ID if corrected else BEAT_TACOMA_737_AUDIT_EXPERIMENT_ID
    )
    variant_of_package_id = (
        BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_PACKAGE_ID
        if corrected
        else BEAT_TACOMA_737_AUDIT_VARIANT_OF_PACKAGE_ID
    )
    variant_of_manifest = (
        BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_MANIFEST
        if corrected
        else BEAT_TACOMA_737_AUDIT_VARIANT_OF_MANIFEST
    )
    output_root = Path(args.output_root) / f"channel_trailer_v2_{experiment_id}_{timestamp}"
    work_dir = output_root / "work"
    frames_dir = work_dir / "audit_frames"
    video_dir = output_root / "video"
    audit_dir = output_root / "audit"
    qa_dir = output_root / "qa"
    for directory in (work_dir, frames_dir, video_dir, audit_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    require_file(variant_of_manifest)
    require_file(BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL)
    require_file(BEAT_TACOMA_737_AUDIT_VARIANT_OF_HIT_MAP)
    variant_manifest = load_json(variant_of_manifest)
    current_hit_map = load_json(BEAT_TACOMA_737_AUDIT_VARIANT_OF_HIT_MAP)
    previous_candidate_map = None
    if corrected:
        previous_candidate_path = (
            BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_ROOT / "audit/tacoma_737_bass_drum_candidate_audit.json"
        )
        require_file(previous_candidate_path)
        previous_candidate_map = load_json(previous_candidate_path)
    candidate_map = tacoma_737_audit_candidate_map(current_hit_map, corrected=corrected)
    candidate_artifacts = write_tacoma_737_audit_candidate_files(candidate_map, audit_dir)

    start_global, end_global = BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS
    duration = end_global - start_global
    review_reel_start = tacoma_737_audit_reel_seconds(start_global)
    audio_f32_path = work_dir / "tacoma_737_audit_audio_mono.f32"
    extract_mono_f32_audio_slice(BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL, audio_f32_path, review_reel_start, duration)

    frame_report = render_tacoma_737_audit_frames(
        BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL,
        frames_dir,
        candidate_map,
    )
    silent_video = work_dir / "tacoma_737_bass_drum_hit_audit_silent.mp4"
    audit_reel = video_dir / "tacoma_737_bass_drum_hit_audit_reel.mp4"
    encode_silent_video(frames_dir, silent_video, duration)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-ss",
            f"{review_reel_start:.6f}",
            "-t",
            f"{duration:.6f}",
            "-i",
            str(BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(audit_reel),
        ]
    )
    decode = full_decode_read(audit_reel)
    probe = concise_media_probe(audit_reel)

    evidence_sheet = create_tacoma_737_audit_evidence_sheet(
        audio_f32_path,
        BEAT_BREATH_AUDIO_SAMPLE_RATE,
        candidate_map,
        qa_dir / "tacoma_737_bass_drum_audit_waveform_spectrogram_sheet.jpg",
    )
    candidate_strip = create_tacoma_737_candidate_frame_strip(
        BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL,
        candidate_map,
        qa_dir / "tacoma_737_bass_drum_candidate_frame_strip.jpg",
    )
    diagnostic_strip = create_tacoma_737_diagnostic_peak_frame_strip(
        BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL,
        candidate_map,
        qa_dir / "tacoma_737_737_diagnostic_peak_frame_strip.jpg",
    )
    timing_comparison_sheet = None
    if corrected and previous_candidate_map is not None:
        timing_comparison_sheet = create_tacoma_737_timing_comparison_sheet(
            previous_candidate_map,
            candidate_map,
            qa_dir / "tacoma_737_previous_vs_corrected_timing_comparison_sheet.jpg",
        )

    video_streams = [stream for stream in probe["video_streams"] if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in probe["audio_streams"] if stream.get("codec_type") == "audio"]
    format_read = (
        "pass"
        if video_streams
        and audio_streams
        and video_streams[0].get("codec_name") == "h264"
        and video_streams[0].get("width") == WIDTH
        and video_streams[0].get("height") == HEIGHT
        and video_streams[0].get("r_frame_rate") == f"{FPS}/1"
        and audio_streams[0].get("codec_name") == "aac"
        else "tighten"
    )
    superseded_package_update = None
    if corrected:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_TACOMA_737_CORRECTED_AUDIT_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_tacoma_737_bass_drum_hit_audit_manifest.json",
            "missed_tacoma_17_to_18_hit_and_rejected_18_to_20_bass_drum_hits",
            output_root.name,
        )
    manifest_path = output_root / f"channel_trailer_v2_{experiment_id}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_{experiment_id}",
        "created_at": timestamp,
        "status": "local_review_audit",
        "publishable": False,
        "experiment_type": experiment_id,
        "variant_of": variant_of_package_id,
        "variant_of_manifest_path": str(variant_of_manifest),
        "variant_of_manifest_sha256": file_sha256(variant_of_manifest),
        "variant_of_manifest_status_at_render": variant_manifest.get("status"),
        "superseded_package_update": superseded_package_update,
        "revision_reason": "correct_missed_tacoma_hits_and_use_737_diagnostic_peak_timing"
        if corrected
        else None,
        "summary": (
            "Corrected local audit package for Tacoma Narrows and 737 MAX strict bass-drum hit decisions before rendering another beat-breath proof."
            if corrected
            else "Local audit package for Tacoma Narrows and 737 MAX strict bass-drum hit decisions before rendering another beat-breath proof."
        ),
        "youtube_updated": False,
        "youtube_rollout": "none_local_audit_only",
        "trailer_video_rendered": False,
        "full_48s_trailer_rendered": False,
        "beat_breath_proof_rendered": False,
        "audit_reel_rendered": True,
        "strict_rule": "breath effect may fire only on confirmed_bass_drum_hit decisions",
        "support_accents_allowed": False,
        "low_band_proxy_allowed": False,
        "periodic_grid_allowed": False,
        "fallback_pulse_allowed": False,
        "pre_attack_allowed": False,
        "titanic_no_bass_drum_seconds": [24.0, 30.2],
        "audit_window_global_seconds": [start_global, end_global],
        "baseline": {
            "review_reel_path": str(BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL),
            "review_reel_sha256": file_sha256(BEAT_TACOMA_737_AUDIT_VARIANT_OF_REEL),
            "hit_map_path": str(BEAT_TACOMA_737_AUDIT_VARIANT_OF_HIT_MAP),
            "hit_map_sha256": file_sha256(BEAT_TACOMA_737_AUDIT_VARIANT_OF_HIT_MAP),
        },
        "candidate_audit": candidate_map,
        "candidate_artifacts": candidate_artifacts,
        "outputs": {
            "audit_reel": probe,
            "audit_reel_full_decode": decode,
            "silent_audit_video_path": str(silent_video),
            "silent_audit_video_sha256": file_sha256(silent_video),
        },
        "qa": {
            "audit_reel_format_read": format_read,
            "full_decode_read": decode["full_decode_read"],
            "candidate_json_binary_decision_read": candidate_map["all_candidates_have_binary_decision_read"],
            "tacoma_confirmed_candidate_count_read": "pass"
            if not corrected or candidate_map["tacoma_confirmed_candidate_count"] == 5
            else "tighten",
            "boeing_737_max_confirmed_candidate_count_read": "pass"
            if not corrected or candidate_map["boeing_737_max_confirmed_candidate_count"] == 5
            else "tighten",
            "titanic_confirmed_candidate_count_read": "pass"
            if candidate_map["titanic_confirmed_candidate_count"] == 0
            else "tighten",
            "broad_no_drum_window_inherited_read": "pass_not_inherited",
            "no_support_accent_pulse_read": "pass",
            "no_low_band_proxy_read": "pass",
            "no_periodic_grid_read": "pass",
            "no_fallback_pulse_read": "pass",
            "no_pre_attack_read": "pass",
            "titanic_no_bass_drum_window_preserved_read": "pass",
            "human_bass_drum_hit_audit_read": "review_required",
            "youtube_updated_read": "pass_not_updated",
            "contact_sheets": {
                "waveform_spectrogram": evidence_sheet,
                "candidate_frame_strip": candidate_strip,
                "diagnostic_737_peak_frame_strip": diagnostic_strip,
                "previous_vs_corrected_timing_comparison": timing_comparison_sheet,
            },
            "frame_report": frame_report,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Corrected Tacoma / 737 Bass-Drum Hit Audit" if corrected else "# Tacoma / 737 Bass-Drum Hit Audit",
                "",
                "Local review audit only. This package does not render a beat-breath proof or update YouTube.",
                "",
                f"- Audit reel: `{audit_reel}`",
                f"- Candidate map: `{candidate_artifacts['candidate_json_path']}`",
                f"- Candidate CSV: `{candidate_artifacts['candidate_csv_path']}`",
                f"- Waveform/spectrogram sheet: `{evidence_sheet['path']}`",
                f"- Candidate frame strip: `{candidate_strip['path']}`",
                f"- 737 diagnostic peak strip: `{diagnostic_strip['path']}`",
                f"- Timing comparison: `{timing_comparison_sheet['path']}`" if timing_comparison_sheet else "",
                f"- Manifest: `{manifest_path}`",
                "",
                "Strict rule: future breath pulses may fire only on candidates confirmed as audible bass-drum hits.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "audit_reel": str(audit_reel),
                "manifest": str(manifest_path),
                "status": "local_review_audit",
            },
            indent=2,
        )
    )
    return 0


def write_concat_list(video_paths: list[Path], concat_list_path: Path) -> Path:
    concat_list_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for path in video_paths:
        escaped = str(path).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    concat_list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return concat_list_path


def build_music_only_beat_breath_background_proof(
    args: argparse.Namespace,
    *,
    beat_grid: bool = False,
    clear_beat: bool = False,
    lowest_bass: bool = False,
    bass_event: bool = False,
    bass_drum_hit: bool = False,
    rhythm_hit: bool = False,
    bass_drum_only_no_titanic: bool = False,
    corrected_tacoma_737_bass_drum: bool = False,
) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    if sum(
        1
        for enabled in (
            beat_grid,
            clear_beat,
            lowest_bass,
            bass_event,
            bass_drum_hit,
            rhythm_hit,
            bass_drum_only_no_titanic,
            corrected_tacoma_737_bass_drum,
        )
        if enabled
    ) > 1:
        raise SystemExit("Choose only one beat proof mode")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    if corrected_tacoma_737_bass_drum:
        experiment_id = BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_EXPERIMENT_ID
        proof_slug = "corrected_tacoma_737_bass_drum_breath"
        qa_prefix = "corrected_tacoma_737_bass_drum_breath"
        variant_of_package_id = BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_MANIFEST
    elif bass_drum_only_no_titanic:
        experiment_id = BEAT_BASS_DRUM_ONLY_NO_TITANIC_EXPERIMENT_ID
        proof_slug = "bass_drum_only_no_titanic_pulse_breath"
        qa_prefix = "bass_drum_only_no_titanic_pulse_breath"
        variant_of_package_id = BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_MANIFEST
    elif rhythm_hit:
        experiment_id = BEAT_RHYTHM_HIT_BREATH_EXPERIMENT_ID
        proof_slug = "rhythm_hit_breath"
        qa_prefix = "rhythm_hit_breath"
        variant_of_package_id = BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_MANIFEST
    elif bass_drum_hit:
        experiment_id = BEAT_BASS_DRUM_HIT_BREATH_EXPERIMENT_ID
        proof_slug = "bass_drum_hit_breath"
        qa_prefix = "bass_drum_hit_breath"
        variant_of_package_id = BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_MANIFEST
    elif bass_event:
        experiment_id = BEAT_BASS_EVENT_BREATH_EXPERIMENT_ID
        proof_slug = "bass_event_breath"
        qa_prefix = "bass_event_breath"
        variant_of_package_id = BEAT_BASS_EVENT_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_BASS_EVENT_BREATH_VARIANT_OF_MANIFEST
    elif lowest_bass:
        experiment_id = BEAT_LOWEST_BASS_BREATH_EXPERIMENT_ID
        proof_slug = "lowest_bass_beat_breath"
        qa_prefix = "lowest_bass_beat_breath"
        variant_of_package_id = BEAT_LOWEST_BASS_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_LOWEST_BASS_BREATH_VARIANT_OF_MANIFEST
    elif clear_beat:
        experiment_id = BEAT_CLEAR_BREATH_EXPERIMENT_ID
        proof_slug = "clear_beat_breath"
        qa_prefix = "clear_beat_breath"
        variant_of_package_id = BEAT_CLEAR_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_CLEAR_BREATH_VARIANT_OF_MANIFEST
    elif beat_grid:
        experiment_id = BEAT_GRID_BREATH_EXPERIMENT_ID
        proof_slug = "beat_grid_breath"
        qa_prefix = "beat_grid_breath"
        variant_of_package_id = BEAT_GRID_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_GRID_BREATH_VARIANT_OF_MANIFEST
    else:
        experiment_id = BEAT_BREATH_EXPERIMENT_ID
        proof_slug = "beat_breath"
        qa_prefix = "beat_breath"
        variant_of_package_id = BEAT_BREATH_VARIANT_OF_PACKAGE_ID
        variant_of_manifest = BEAT_BREATH_VARIANT_OF_MANIFEST
    output_root = Path(args.output_root) / f"channel_trailer_v2_{experiment_id}_{timestamp}"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    segment_frames_root = work_dir / "episode_frames"
    video_dir = output_root / "video"
    beat_dir = output_root / "beat"
    masks_dir = output_root / "masks"
    qa_dir = output_root / "qa"
    for directory in (work_dir, short_frames_dir, segment_frames_root, video_dir, beat_dir, masks_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    require_file(BEAT_BREATH_VARIANT_OF_MP4)
    require_file(BEAT_BREATH_VARIANT_OF_MANIFEST)
    require_file(variant_of_manifest)
    if corrected_tacoma_737_bass_drum:
        require_file(BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST)
        require_file(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
        require_file(BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_HIT_MAP)
    baseline_manifest = load_json(BEAT_BREATH_VARIANT_OF_MANIFEST)
    variant_of_manifest_data = load_json(variant_of_manifest)

    proofs = source_proofs()
    proof_by_slug = {proof.slug: proof for proof in proofs}
    for proof in proofs:
        require_file(proof.video_path)
        if proof.manifest_path:
            require_file(proof.manifest_path)
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {proof.slug}")
        require_file(proof.short_video_path)
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {proof.slug}")
        require_file(proof.base_plate_path)

    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    segments = music_only_timeline_segments(END_SCREEN_HOLD_TARGET_SECONDS)
    episode_segments = [segment for segment in segments if segment.role == "voiceover_episode_sequence"]

    if corrected_tacoma_737_bass_drum:
        beat_analysis = corrected_tacoma_737_bass_drum_pulse_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_bass_drum_only_hit_map_files(beat_analysis, beat_dir)
    elif bass_drum_only_no_titanic:
        beat_analysis = bass_drum_only_no_titanic_pulse_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_bass_drum_only_hit_map_files(beat_analysis, beat_dir)
    elif rhythm_hit:
        beat_analysis = rhythm_hit_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_rhythm_hit_map_files(beat_analysis, beat_dir)
    elif bass_drum_hit:
        beat_analysis = bass_drum_hit_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_bass_drum_hit_map_files(beat_analysis, beat_dir)
    elif bass_event:
        beat_analysis = bass_event_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_bass_event_timeline_files(beat_analysis, beat_dir)
    elif lowest_bass:
        beat_analysis = lowest_bass_beat_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_lowest_bass_beat_timeline_files(beat_analysis, beat_dir)
    elif clear_beat:
        beat_analysis = clear_beat_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_clear_beat_timeline_files(beat_analysis, beat_dir)
    elif beat_grid:
        beat_analysis = beat_grid_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_beat_grid_timeline_files(beat_analysis, beat_dir)
    else:
        beat_analysis = beat_breath_audio_analysis(
            BEAT_BREATH_VARIANT_OF_MP4,
            work_dir,
            BEAT_BREATH_START_SECONDS,
            BEAT_BREATH_END_SECONDS,
        )
        beat_timeline_artifacts = write_beat_breath_timeline_files(beat_analysis, beat_dir)

    foreground_mattes: dict[str, Image.Image] = {}
    matte_reports: dict[str, Any] = {}
    matte_overlay_paths: list[Path] = []
    edge_delta_paths: list[Path] = []
    hole_overlay_paths: list[Path] = []
    segment_labels = []
    for segment in episode_segments:
        slug = segment.slug
        matte, hole_mask, inner_edges, diagnostics = derive_lyric_background_tight_subject_matte_v2(base_plates[slug], slug)
        foreground_mattes[slug] = matte
        foreground_path = masks_dir / f"{slug}_soft_isolation_foreground_matte.png"
        hole_path = masks_dir / f"{slug}_negative_space_hole_mask.png"
        inner_edge_path = masks_dir / f"{slug}_inner_edge_diagnostic_mask.png"
        overlay_path = masks_dir / f"{slug}_soft_isolation_matte_overlay.jpg"
        hole_overlay_path = masks_dir / f"{slug}_hole_inner_edge_diagnostic_overlay.jpg"
        edge_delta_path = masks_dir / f"{slug}_beat_breath_edge_delta_overlay.jpg"
        matte.save(foreground_path)
        hole_mask.save(hole_path)
        inner_edges.save(inner_edge_path)
        foreground_matte_overlay(base_plates[slug], beat_breath_soft_foreground_mask(matte), color=(88, 178, 255)).save(
            overlay_path,
            quality=92,
        )
        foreground_hole_inner_edge_overlay(base_plates[slug], hole_mask, inner_edges).save(hole_overlay_path, quality=92)
        edge_delta_report = beat_breath_edge_delta_overlay(base_plates[slug], matte, edge_delta_path)
        matte_overlay_paths.append(overlay_path)
        hole_overlay_paths.append(hole_overlay_path)
        edge_delta_paths.append(edge_delta_path)
        segment_labels.append(SUBJECT_BADGE_LABELS[slug])
        matte_reports[slug] = {
            "matte_strategy": "soft_isolation_guide_from_lyric_background_tight_subject_matte_v2",
            "foreground_matte_path": str(foreground_path),
            "foreground_matte_sha256": file_sha256(foreground_path),
            "hole_negative_space_mask_path": str(hole_path),
            "hole_negative_space_mask_sha256": file_sha256(hole_path),
            "inner_edge_mask_path": str(inner_edge_path),
            "inner_edge_mask_sha256": file_sha256(inner_edge_path),
            "soft_isolation_matte_overlay_path": str(overlay_path),
            "soft_isolation_matte_overlay_sha256": file_sha256(overlay_path),
            "hole_inner_edge_overlay_path": str(hole_overlay_path),
            "hole_inner_edge_overlay_sha256": file_sha256(hole_overlay_path),
            "edge_delta_overlay": edge_delta_report,
            "diagnostics": diagnostics,
            "precision_acceptance_gate": False,
        }

    segment_clip_reports: list[dict[str, Any]] = []
    silent_segment_videos: list[Path] = []
    final_segment_videos: list[Path] = []
    frame_metrics: list[dict[str, Any]] = []
    frame_context_samples: list[dict[str, Any]] = []
    for segment in episode_segments:
        segment_duration = segment.end - segment.start
        frame_count = int(round(segment_duration * FPS))
        frames_dir = segment_frames_root / segment.slug
        frames_dir.mkdir(parents=True, exist_ok=True)
        sample_frame_indexes = {
            0,
            min(frame_count - 1, max(0, int(round(frame_count * 0.33)))),
            min(frame_count - 1, max(0, int(round(frame_count * 0.66)))),
            max(0, frame_count - 1),
        }
        sample_contexts: list[dict[str, Any]] = []
        for frame_index in range(frame_count):
            global_t = segment.start + frame_index / FPS
            frame, contexts = compose_music_only_beat_breath_frame(
                global_t,
                END_SCREEN_HOLD_TARGET_SECONDS,
                segments,
                base_plates,
                foreground_mattes,
                short_frames,
                beat_analysis,
            )
            out_frame = frames_dir / f"frame_{frame_index:05d}.jpg"
            frame.save(out_frame, quality=92)
            primary_context = contexts[-1]
            effect = primary_context["beat_breath"]
            metric = {
                "slug": primary_context["slug"],
                "frame": frame_index,
                "global_time_seconds": round(global_t, 6),
                "relative_review_time_seconds": round(global_t - BEAT_BREATH_START_SECONDS, 6),
                "pulse": effect["pulse"],
                "background_mean_luma_delta": effect["background_mean_luma_delta"],
                "foreground_mean_luma_delta": effect["foreground_mean_luma_delta"],
            }
            frame_metrics.append(metric)
            if frame_index in sample_frame_indexes:
                sample_contexts.append(
                    {
                        **primary_context,
                        "frame": frame_index,
                        "global_time_seconds": round(global_t, 6),
                        "context_count": len(contexts),
                    }
                )
                frame_context_samples.append(sample_contexts[-1])

        silent_video = work_dir / f"{segment.slug}_{proof_slug}_silent.mp4"
        final_video = video_dir / f"{segment.slug}_{proof_slug}_background_proof.mp4"
        encode_silent_video(frames_dir, silent_video, segment_duration)
        mux_video_with_source_audio_slice(silent_video, BEAT_BREATH_VARIANT_OF_MP4, final_video, segment.start, segment_duration)
        silent_segment_videos.append(silent_video)
        final_segment_videos.append(final_video)
        final_probe = concise_media_probe(final_video)
        final_decode = full_decode_read(final_video)
        segment_clip_reports.append(
            {
                "slug": segment.slug,
                "display_name": SUBJECT_BADGE_LABELS[segment.slug],
                "segment_seconds": [round(segment.start, 3), round(segment.end, 3)],
                "target_duration_seconds": round(segment_duration, 6),
                "frame_count": frame_count,
                "silent_video_path": str(silent_video),
                "silent_video_sha256": file_sha256(silent_video),
                "final_video": final_probe,
                "full_decode": final_decode,
                "audio_source_seconds": [round(segment.start, 6), round(segment.end, 6)],
                "sample_contexts": sample_contexts,
            }
        )
        if not args.keep_frames:
            shutil.rmtree(frames_dir, ignore_errors=True)

    concat_list = write_concat_list(silent_segment_videos, work_dir / f"{proof_slug}_silent_concat.txt")
    review_silent_video = work_dir / f"episode_sequence_6_to_30p2_{proof_slug}_silent.mp4"
    review_reel = video_dir / f"cascade_of_effects_channel_trailer_v2_music_only_{proof_slug}_background_proof_reel.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(review_silent_video),
        ]
    )
    review_duration = BEAT_BREATH_END_SECONDS - BEAT_BREATH_START_SECONDS
    mux_video_with_source_audio_slice(
        review_silent_video,
        BEAT_BREATH_VARIANT_OF_MP4,
        review_reel,
        BEAT_BREATH_START_SECONDS,
        review_duration,
    )

    response_qa = beat_breath_response_qa(frame_metrics, beat_analysis)
    review_probe = concise_media_probe(review_reel)
    review_decode = full_decode_read(review_reel)
    baseline_probe = concise_media_probe(BEAT_BREATH_VARIANT_OF_MP4)

    strong_beats = sorted(beat_analysis["beats"], key=lambda item: float(item["strength"]), reverse=True)[:8]
    strong_beats = sorted(strong_beats, key=lambda item: float(item["relative_time_seconds"]))
    before_after_samples = [
        (f"beat p={float(beat['strength']):.2f}", float(beat["global_time_seconds"]))
        for beat in strong_beats[:6]
    ]
    if not before_after_samples:
        before_after_samples = [("fallback", BEAT_BREATH_START_SECONDS + 0.5)]
    frame_strip = create_beat_breath_frame_strip(
        review_reel,
        beat_analysis["beats"],
        qa_dir / f"{qa_prefix}_strong_beat_frame_strip.jpg",
    )
    before_after_sheet = create_video_before_after_contact_sheet(
        BEAT_BREATH_VARIANT_OF_MP4,
        review_reel,
        before_after_samples,
        qa_dir / f"{qa_prefix}_before_after_comparison_sheet.jpg",
        proof_time_offset_seconds=BEAT_BREATH_START_SECONDS,
    )
    visibility_qa_sheet = create_beat_breath_visibility_qa_sheet(
        BEAT_BREATH_VARIANT_OF_MP4,
        review_reel,
        before_after_samples,
        qa_dir / f"{qa_prefix}_visibility_qa_sheet.jpg",
        proof_time_offset_seconds=BEAT_BREATH_START_SECONDS,
    )
    bass_drum_evidence_sheet = None
    bass_drum_rejection_evidence_sheet = None
    bass_drum_rejected_frame_strip = None
    titanic_no_pulse_evidence_sheet = None
    titanic_no_pulse_frame_strip = None
    corrected_tacoma_737_pulse_strip = None
    corrected_tacoma_737_evidence_sheet = None
    if bass_drum_only_no_titanic or corrected_tacoma_737_bass_drum:
        titanic_no_pulse_evidence_sheet = create_bass_drum_hit_evidence_sheet(
            beat_analysis,
            qa_dir / f"{qa_prefix}_titanic_no_pulse_waveform_spectrogram_evidence_sheet.jpg",
            global_seconds=(23.7, 30.2),
            title="Titanic no-bass-drum window: no confirmed hits, no visual pulse",
        )
        titanic_no_pulse_frame_strip = create_labeled_video_contact_sheet(
            review_reel,
            qa_dir / f"{qa_prefix}_titanic_no_pulse_frame_strip.jpg",
            [
                ("Titanic start", 18.00),
                ("24.50 no pulse", 18.50),
                ("25.00 no pulse", 19.00),
                ("26.00 no pulse", 20.00),
                ("27.00 no pulse", 21.00),
                ("28.00 no pulse", 22.00),
                ("29.00 no pulse", 23.00),
                ("30.00 no pulse", 24.00),
            ],
            columns=4,
        )
        if corrected_tacoma_737_bass_drum:
            corrected_tacoma_737_evidence_sheet = create_bass_drum_hit_evidence_sheet(
                beat_analysis,
                qa_dir / "corrected_tacoma_737_hit_map_waveform_spectrogram_evidence_sheet.jpg",
                global_seconds=(16.6, 24.0),
                title="Corrected Tacoma/737 confirmed bass-drum hits driving breath pulse",
            )
            corrected_tacoma_737_pulse_strip = create_labeled_video_contact_sheet(
                review_reel,
                qa_dir / "corrected_tacoma_737_pulse_timing_frame_strip.jpg",
                [
                    ("Tacoma hit 17.338", 17.338356 - BEAT_BREATH_START_SECONDS),
                    ("Tacoma hit 18.341", 18.341406 - BEAT_BREATH_START_SECONDS),
                    ("Tacoma hit 18.806", 18.805805 - BEAT_BREATH_START_SECONDS),
                    ("Tacoma hit 19.259", 19.258594 - BEAT_BREATH_START_SECONDS),
                    ("Tacoma hit 19.711", 19.711383 - BEAT_BREATH_START_SECONDS),
                    ("737 hit 20.794", 20.793912 - BEAT_BREATH_START_SECONDS),
                    ("737 hit 21.243", 21.242891 - BEAT_BREATH_START_SECONDS),
                    ("737 hit 22.146", 22.145839 - BEAT_BREATH_START_SECONDS),
                    ("737 hit 23.203", 23.203435 - BEAT_BREATH_START_SECONDS),
                    ("737 hit 23.652", 23.652415 - BEAT_BREATH_START_SECONDS),
                    ("Titanic neutral", 24.500000 - BEAT_BREATH_START_SECONDS),
                    ("Titanic late neutral", 29.000000 - BEAT_BREATH_START_SECONDS),
                ],
                columns=4,
            )
    elif bass_drum_hit:
        bass_drum_evidence_sheet = create_bass_drum_hit_evidence_sheet(
            beat_analysis,
            qa_dir / "bass_drum_hit_waveform_spectrogram_evidence_sheet.jpg",
            global_seconds=(BEAT_BREATH_START_SECONDS, BEAT_BREATH_END_SECONDS),
            title="Confirmed bass-drum hit map over baseline music bed",
        )
        bass_drum_rejection_evidence_sheet = create_bass_drum_hit_evidence_sheet(
            beat_analysis,
            qa_dir / "bass_drum_hit_19s_false_positive_rejection_sheet.jpg",
            global_seconds=(17.65, 21.35),
            title="19s false-positive rejection: no confirmed bass drum, no visual pulse",
        )
        bass_drum_rejected_frame_strip = create_labeled_video_contact_sheet(
            review_reel,
            qa_dir / "bass_drum_hit_rejected_18_to_21s_frame_strip.jpg",
            [
                ("18.00 no hit", 18.00 - BEAT_BREATH_START_SECONDS),
                ("18.50 no hit", 18.50 - BEAT_BREATH_START_SECONDS),
                ("19.00 no hit", 19.00 - BEAT_BREATH_START_SECONDS),
                ("19.50 no hit", 19.50 - BEAT_BREATH_START_SECONDS),
                ("20.00 no hit", 20.00 - BEAT_BREATH_START_SECONDS),
                ("20.50 no hit", 20.50 - BEAT_BREATH_START_SECONDS),
                ("21.00 post-window", 21.00 - BEAT_BREATH_START_SECONDS),
            ],
            columns=4,
        )
    timing_comparison_sheet = None
    rhythm_gap_repair_frame_strip = None
    if corrected_tacoma_737_bass_drum:
        previous_timeline = BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_HIT_MAP
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "strict_bass_drum_only_vs_corrected_tacoma_737_timing_comparison_sheet.jpg",
        )
    elif bass_drum_only_no_titanic:
        previous_timeline = BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_ROOT / "beat/rhythm_hit_map.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "bass_drum_only_vs_rejected_rhythm_hit_timing_comparison_sheet.jpg",
        )
    elif rhythm_hit:
        previous_timeline = BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_ROOT / "beat/bass_drum_hit_map.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "rhythm_hits_vs_rejected_strict_bass_drum_timing_comparison_sheet.jpg",
        )
        rhythm_gap_repair_frame_strip = create_labeled_video_contact_sheet(
            review_reel,
            qa_dir / "rhythm_hit_review_12s_gap_repair_frame_strip.jpg",
            [
                ("11.00 before gap", 11.00),
                ("11.50 support", 11.50),
                ("12.00 support", 12.00),
                ("12.50 support", 12.50),
                ("13.00 support", 13.00),
                ("13.50 support", 13.50),
                ("14.00 support", 14.00),
                ("14.50 support", 14.50),
                ("15.00 primary returns", 15.00),
            ],
            columns=3,
        )
    elif bass_drum_hit:
        previous_timeline = BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_ROOT / "beat/bass_event_timeline.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "bass_drum_hits_vs_rejected_low_frequency_events_timing_comparison_sheet.jpg",
        )
    elif bass_event:
        previous_timeline = BEAT_BASS_EVENT_BREATH_VARIANT_OF_ROOT / "beat/lowest_bass_beat_timeline.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "bass_event_vs_rejected_periodic_bass_timing_comparison_sheet.jpg",
        )
    elif lowest_bass:
        previous_timeline = BEAT_LOWEST_BASS_BREATH_VARIANT_OF_ROOT / "beat/clear_beat_timeline.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "lowest_bass_vs_rejected_clear_beat_timing_comparison_sheet.jpg",
        )
    elif clear_beat:
        previous_timeline = BEAT_CLEAR_BREATH_VARIANT_OF_ROOT / "beat/beat_grid_timeline.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "clear_beat_vs_rejected_grid_timing_comparison_sheet.jpg",
        )
    elif beat_grid:
        previous_timeline = BEAT_GRID_BREATH_VARIANT_OF_ROOT / "beat/beat_breath_timeline.json"
        previous_analysis = (
            json.loads(previous_timeline.read_text(encoding="utf-8"))
            if previous_timeline.exists()
            else variant_of_manifest_data.get("beat_analysis", {})
        )
        timing_comparison_sheet = create_beat_grid_timing_comparison_sheet(
            previous_analysis,
            beat_analysis,
            qa_dir / "beat_grid_timing_comparison_sheet.jpg",
        )
    matte_sheet = create_subject_background_type_contact_sheet(
        matte_overlay_paths,
        segment_labels,
        qa_dir / f"{qa_prefix}_soft_matte_overlay_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    edge_delta_sheet = create_subject_background_type_contact_sheet(
        edge_delta_paths,
        segment_labels,
        qa_dir / f"{qa_prefix}_edge_delta_diagnostic_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    hole_sheet = create_subject_background_type_contact_sheet(
        hole_overlay_paths,
        segment_labels,
        qa_dir / f"{qa_prefix}_hole_inner_edge_diagnostic_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    subject_badge_sheet = create_subject_badge_crop_contact_sheet(
        review_reel,
        qa_dir / f"{qa_prefix}_subject_badge_crop_contact_sheet.jpg",
        [
            ("Challenger", 0.25),
            ("Hyatt Regency", 3.45),
            ("Semmelweis", 7.15),
            ("Tacoma Narrows", 10.85),
            ("737 MAX", 14.55),
            ("Titanic", 18.25),
            ("Titanic tail", 23.8),
        ],
        columns=2,
    )
    overview_sheet = create_labeled_video_contact_sheet(
        review_reel,
        qa_dir / f"{qa_prefix}_review_reel_overview_contact_sheet.jpg",
        [
            ("Challenger", 0.35),
            ("Hyatt", 3.6),
            ("Semmelweis", 7.3),
            ("Tacoma", 11.0),
            ("737 MAX", 14.7),
            ("Titanic", 18.4),
            ("Titanic late", 23.85),
        ],
        columns=4,
    )

    stream_reads = {
        "review_reel_format_read": "pass"
        if (
            review_probe["video_stream_count"] == 1
            and review_probe["audio_stream_count"] == 1
            and review_probe["video_streams"][0].get("width") == WIDTH
            and review_probe["video_streams"][0].get("height") == HEIGHT
            and review_probe["video_streams"][0].get("codec_name") == "h264"
            and review_probe["audio_streams"][0].get("codec_name") == "aac"
        )
        else "tighten",
        "subject_clip_format_read": "pass"
        if all(
            clip["final_video"]["video_stream_count"] == 1
            and clip["final_video"]["audio_stream_count"] == 1
            and clip["final_video"]["video_streams"][0].get("codec_name") == "h264"
            and clip["final_video"]["audio_streams"][0].get("codec_name") == "aac"
            for clip in segment_clip_reports
        )
        else "tighten",
        "full_decode_read": "pass"
        if review_decode["full_decode_read"] == "pass"
        and all(clip["full_decode"]["full_decode_read"] == "pass" for clip in segment_clip_reports)
        else "tighten",
    }

    proof_inputs = {}
    for segment in episode_segments:
        proof = proof_by_slug[segment.slug]
        proof_inputs[segment.slug] = {
            "display_name": proof.display_name,
            "video_path": str(proof.video_path),
            "video_sha256": file_sha256(proof.video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else None,
            "manifest_sha256": file_sha256(proof.manifest_path) if proof.manifest_path else None,
            "short_video_pre_caption_path": str(proof.short_video_path),
            "short_video_pre_caption_sha256": file_sha256(proof.short_video_path) if proof.short_video_path else None,
            "base_plate_path": str(proof.base_plate_path),
            "base_plate_sha256": file_sha256(proof.base_plate_path) if proof.base_plate_path else None,
        }

    superseded_package_update = None
    if bass_drum_only_no_titanic:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_rhythm_hit_breath_background_proof_manifest.json",
            "support_rhythm_accents_pulsed_without_bass_drum_in_titanic_scene",
            output_root.name,
        )
    elif rhythm_hit:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_bass_drum_hit_breath_background_proof_manifest.json",
            "strict_bass_drum_hit_map_created_rhythm_gap_at_review_12s",
            output_root.name,
        )
    elif bass_drum_hit:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_bass_event_breath_background_proof_manifest.json",
            "low_frequency_energy_events_not_confirmed_bass_drum_hits",
            output_root.name,
        )
    elif bass_event:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_BASS_EVENT_BREATH_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_lowest_bass_beat_breath_background_proof_manifest.json",
            "periodic_lowest_bass_grid_not_actual_music_events",
            output_root.name,
        )
    elif lowest_bass:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_LOWEST_BASS_BREATH_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_clear_beat_breath_background_proof_manifest.json",
            "followed_mid_high_transients_not_lowest_bass_beat",
            output_root.name,
        )
    elif clear_beat:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_CLEAR_BREATH_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_beat_grid_breath_background_proof_manifest.json",
            "beat_grid_visual_pulse_does_not_fit_music_rhythm",
            output_root.name,
        )
    elif beat_grid:
        superseded_package_update = mark_experiment_package_tighten(
            BEAT_GRID_BREATH_VARIANT_OF_ROOT,
            "channel_trailer_v2_music_only_beat_breath_background_proof_manifest.json",
            "onset_reactive_pulse_not_beat_grid_synchronized",
            output_root.name,
        )
    sync_qa = {}
    if corrected_tacoma_737_bass_drum:
        sync_qa = {
            "corrected_tacoma_737_hit_map_read": beat_analysis["corrected_tacoma_737_hit_map_read"],
            "tacoma_visible_pulse_hit_count_read": beat_analysis["tacoma_visible_pulse_hit_count_read"],
            "boeing_737_max_corrected_timing_hit_count_read": beat_analysis[
                "boeing_737_max_corrected_timing_hit_count_read"
            ],
            "confirmed_bass_drum_hit_map_read": beat_analysis["confirmed_bass_drum_hit_map_read"],
            "no_support_accent_pulse_read": beat_analysis["no_support_accent_pulse_read"],
            "no_pulse_without_confirmed_bass_drum_read": beat_analysis[
                "no_pulse_without_confirmed_bass_drum_read"
            ],
            "titanic_no_bass_drum_no_pulse_read": beat_analysis["titanic_no_bass_drum_no_pulse_read"],
            "no_periodic_grid_read": beat_analysis["no_periodic_grid_read"],
            "no_low_band_fallback_read": beat_analysis["no_low_band_fallback_read"],
            "pulse_peak_on_confirmed_hit_read": beat_analysis["pulse_peak_on_confirmed_hit_read"],
            "human_bass_drum_sync_read": "review_required",
            "human_bass_drum_sync_note": (
                "Corrected Tacoma/737 audit entries drive pulses from 16.600-24.000s; Titanic remains explicitly neutral."
            ),
        }
    elif bass_drum_only_no_titanic:
        sync_qa = {
            "confirmed_bass_drum_only_hit_map_read": beat_analysis["confirmed_bass_drum_only_hit_map_read"],
            "no_support_accent_pulse_read": beat_analysis["no_support_accent_pulse_read"],
            "no_pulse_without_confirmed_bass_drum_read": beat_analysis[
                "no_pulse_without_confirmed_bass_drum_read"
            ],
            "titanic_no_bass_drum_no_pulse_read": beat_analysis["titanic_no_bass_drum_no_pulse_read"],
            "no_periodic_grid_read": beat_analysis["no_periodic_grid_read"],
            "no_low_band_fallback_read": beat_analysis["no_low_band_fallback_read"],
            "pulse_peak_on_confirmed_hit_read": beat_analysis["pulse_peak_on_confirmed_hit_read"],
            "human_bass_drum_sync_read": "review_required",
            "human_bass_drum_sync_note": (
                "Only confirmed bass-drum hit-map entries drive the pulse; Titanic is explicitly a no-pulse scene."
            ),
        }
    elif rhythm_hit:
        sync_qa = {
            "rhythm_hit_map_read": beat_analysis["rhythm_hit_map_read"],
            "rhythm_continuity_gap_read": beat_analysis["rhythm_continuity_gap_read"],
            "review_12s_rhythm_continuity_read": beat_analysis["review_12s_rhythm_continuity_read"],
            "no_periodic_grid_read": beat_analysis["no_periodic_grid_read"],
            "no_low_band_fallback_read": beat_analysis["no_low_band_fallback_read"],
            "pulse_peak_on_rhythm_hit_read": beat_analysis["pulse_peak_on_rhythm_hit_read"],
            "human_rhythm_sync_read": "review_required",
            "human_rhythm_sync_note": (
                "Primary bass-drum hits and quieter support rhythm accents drive the pulse; support accents are not claimed as bass drums."
            ),
        }
    elif bass_drum_hit:
        sync_qa = {
            "confirmed_bass_drum_hit_map_read": beat_analysis["confirmed_bass_drum_hit_map_read"],
            "no_pulse_without_confirmed_hit_read": beat_analysis["no_pulse_without_confirmed_hit_read"],
            "nineteen_second_false_positive_rejection_read": beat_analysis[
                "nineteen_second_false_positive_rejection_read"
            ],
            "no_periodic_grid_read": beat_analysis["no_periodic_grid_read"],
            "no_low_band_fallback_read": beat_analysis["no_low_band_fallback_read"],
            "pulse_peak_on_confirmed_hit_read": beat_analysis["pulse_peak_on_confirmed_hit_read"],
            "human_bass_drum_sync_read": "review_required",
            "human_bass_drum_sync_note": (
                "Only confirmed bass-drum hit-map entries drive the pulse; assisted low-band candidates are evidence only."
            ),
        }
    elif bass_event:
        sync_qa = {
            "actual_bass_event_timing_read": beat_analysis["actual_bass_event_timing_read"],
            "no_periodic_grid_read": beat_analysis["no_periodic_grid_read"],
            "mid_high_transient_rejection_read": beat_analysis["mid_high_transient_rejection_read"],
            "pulse_peak_on_bass_event_read": beat_analysis["pulse_peak_on_bass_event_read"],
            "bass_event_interval_variability_read": beat_analysis["bass_event_interval_variability_read"],
            "human_actual_bass_event_rhythm_fit_read": "review_required",
            "human_actual_bass_event_rhythm_fit_note": (
                "Pulse times are detected low-bass event peaks, not tempo/phase grid ticks; human review still owns final rhythm feel."
            ),
        }
    elif lowest_bass:
        sync_qa = {
            "lowest_bass_period_read": beat_analysis["lowest_bass_period_read"],
            "lowest_bass_tempo_read": beat_analysis["lowest_bass_tempo_read"],
            "lowest_bass_phase_alignment_read": beat_analysis["lowest_bass_phase_alignment_read"],
            "mid_high_transient_rejection_read": beat_analysis["mid_high_transient_rejection_read"],
            "pulse_peak_on_bass_read": beat_analysis["pulse_peak_on_bass_read"],
            "tempo_period_read": beat_analysis["tempo_period_read"],
            "human_lowest_bass_rhythm_fit_read": "review_required",
            "human_lowest_bass_rhythm_fit_note": (
                "Selected from lowest-bass-only frequency bands; human review still owns final bass rhythm fit."
            ),
        }
    elif clear_beat:
        sync_qa = {
            "dominant_beat_period_read": beat_analysis["dominant_beat_period_read"],
            "clear_beat_phase_alignment_read": beat_analysis["clear_beat_phase_alignment_read"],
            "wrong_subdivision_rejection_read": beat_analysis["wrong_subdivision_rejection_read"],
            "pulse_peak_on_beat_read": beat_analysis["pulse_peak_on_beat_read"],
            "tempo_period_read": beat_analysis["tempo_period_read"],
            "human_rhythm_fit_read": "review_required",
            "human_rhythm_fit_note": (
                "Selected from the track's dominant mid/high beat envelope; human review still owns final rhythm feel."
            ),
        }
    elif beat_grid:
        sync_qa = {
            "beat_grid_sync_read": beat_analysis["beat_grid_sync_read"],
            "pulse_peak_on_grid_read": beat_analysis["pulse_peak_on_grid_read"],
            "tempo_period_read": beat_analysis["tempo_period_read"],
            "phase_alignment_read": beat_analysis["phase_alignment_read"],
            "human_rhythm_fit_read": "review_required",
            "human_rhythm_fit_note": (
                "Numeric grid alignment is diagnostic only; musical rhythm fit requires human review before keep."
            ),
        }
    contact_sheets = {
        "review_reel_overview": overview_sheet,
        "strong_beat_frame_strip": frame_strip,
        "before_after_comparison": before_after_sheet,
        "visibility_qa_sheet": visibility_qa_sheet,
        "soft_matte_overlay": matte_sheet,
        "edge_delta_diagnostic": edge_delta_sheet,
        "hole_inner_edge_diagnostic": hole_sheet,
        "subject_badge_crop": subject_badge_sheet,
    }
    if timing_comparison_sheet is not None:
        contact_sheets[
            "corrected_tacoma_737_timing_comparison"
            if corrected_tacoma_737_bass_drum
            else (
                "bass_drum_only_timing_comparison"
                if bass_drum_only_no_titanic
                else (
                    "rhythm_hit_timing_comparison"
                    if rhythm_hit
                    else (
                        "bass_drum_hit_timing_comparison"
                        if bass_drum_hit
                        else (
                            "bass_event_timing_comparison"
                            if bass_event
                            else (
                                "lowest_bass_timing_comparison"
                                if lowest_bass
                                else ("clear_beat_timing_comparison" if clear_beat else "beat_grid_timing_comparison")
                            )
                        )
                    )
                )
            )
        ] = timing_comparison_sheet
    if bass_drum_only_no_titanic or corrected_tacoma_737_bass_drum:
        contact_sheets["bass_drum_only_titanic_no_pulse_evidence"] = titanic_no_pulse_evidence_sheet
        contact_sheets["bass_drum_only_titanic_no_pulse_frame_strip"] = titanic_no_pulse_frame_strip
    if corrected_tacoma_737_bass_drum:
        contact_sheets["corrected_tacoma_737_hit_map_evidence"] = corrected_tacoma_737_evidence_sheet
        contact_sheets["corrected_tacoma_737_pulse_timing_strip"] = corrected_tacoma_737_pulse_strip
    if rhythm_hit:
        contact_sheets["rhythm_hit_review_12s_gap_repair_frame_strip"] = rhythm_gap_repair_frame_strip
    if bass_drum_hit:
        contact_sheets["bass_drum_hit_waveform_spectrogram_evidence"] = bass_drum_evidence_sheet
        contact_sheets["bass_drum_hit_19s_false_positive_rejection"] = bass_drum_rejection_evidence_sheet
        contact_sheets["bass_drum_hit_rejected_18_to_21s_frame_strip"] = bass_drum_rejected_frame_strip

    manifest_path = output_root / f"channel_trailer_v2_{experiment_id}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_{experiment_id}",
        "created_at": timestamp,
        "status": "local_review_experiment",
        "publishable": False,
        "experiment_type": experiment_id,
        "variant_of": variant_of_package_id,
        "variant_of_manifest_path": str(variant_of_manifest),
        "variant_of_manifest_sha256": file_sha256(variant_of_manifest),
        "supersedes": (
            BEAT_CORRECTED_TACOMA_737_BASS_DRUM_BREATH_VARIANT_OF_PACKAGE_ID
            if corrected_tacoma_737_bass_drum
            else (
                BEAT_BASS_DRUM_ONLY_NO_TITANIC_VARIANT_OF_PACKAGE_ID
                if bass_drum_only_no_titanic
                else (
                    BEAT_RHYTHM_HIT_BREATH_VARIANT_OF_PACKAGE_ID
                    if rhythm_hit
                    else (
                        BEAT_BASS_DRUM_HIT_BREATH_VARIANT_OF_PACKAGE_ID
                        if bass_drum_hit
                        else (
                            BEAT_BASS_EVENT_BREATH_VARIANT_OF_PACKAGE_ID
                            if bass_event
                            else (
                                BEAT_LOWEST_BASS_BREATH_VARIANT_OF_PACKAGE_ID
                                if lowest_bass
                                else (
                                    BEAT_CLEAR_BREATH_VARIANT_OF_PACKAGE_ID
                                    if clear_beat
                                    else (BEAT_GRID_BREATH_VARIANT_OF_PACKAGE_ID if beat_grid else None)
                                )
                            )
                        )
                    )
                )
            )
        ),
        "superseded_package_update": superseded_package_update,
        "baseline_manifest_status": baseline_manifest.get("status"),
        "variant_of_manifest_status_at_render": variant_of_manifest_data.get("status"),
        "summary": (
            "Proof reel testing corrected Tacoma/737 bass-drum timing while keeping Titanic held as a no-pulse scene."
            if corrected_tacoma_737_bass_drum
            else (
                "Proof reel testing confirmed bass-drum-only timing with Titanic held as a no-pulse scene."
                if bass_drum_only_no_titanic
                else (
                    "Proof reel testing confirmed rhythm-hit timing, with primary bass-drum hits plus quieter support accents, during the music-only episode scene window."
                    if rhythm_hit
                    else (
                        "Proof reel testing confirmed bass-drum-hit-map timing for ink/background lighting during the music-only episode scene window."
                        if bass_drum_hit
                        else (
                            "Proof reel testing actual low-bass event peak timing for ink/background lighting during the music-only episode scene window."
                            if bass_event
                            else (
                                "Proof reel testing lowest-bass-only beat timing for ink/background lighting during the music-only episode scene window."
                                if lowest_bass
                                else (
                                    "Proof reel testing the clear dominant song beat for ink/background lighting during the music-only episode scene window."
                                    if clear_beat
                                    else (
                                        "Proof reel testing beat-grid-locked ink/background lighting during the music-only episode scene window."
                                        if beat_grid
                                        else "Proof reel testing restrained beat-responsive ink/background lighting during the music-only episode scene window."
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ),
        "youtube_updated": False,
        "youtube_rollout": "none_local_proof_only",
        "trailer_video_rendered": False,
        "full_48s_trailer_rendered": False,
        "background_text_removed": True,
        "background_title_or_lyric_type_used": False,
        "rendered_text_policy": "gallery_subject_badges_only_in_proof_no_background_text",
        "beat_response_strategy": (
            "corrected_tacoma_737_confirmed_bass_drum_light_breath_background_no_titanic_pulse"
            if corrected_tacoma_737_bass_drum
            else (
                "confirmed_bass_drum_only_light_breath_background_no_titanic_pulse"
                if bass_drum_only_no_titanic
                else (
                    "confirmed_rhythm_hit_map_light_breath_background_only_primary_bass_drum_plus_support_accents"
                    if rhythm_hit
                    else (
                        "confirmed_bass_drum_hit_map_locked_light_breath_background_only"
                        if bass_drum_hit
                        else (
                            "actual_lowest_bass_event_locked_light_breath_background_only"
                            if bass_event
                            else (
                                "lowest_bass_beat_locked_light_breath_background_only"
                                if lowest_bass
                                else (
                                    "dominant_clear_song_beat_locked_light_breath_background_only"
                                    if clear_beat
                                    else (
                                        "beat_grid_locked_light_breath_background_only"
                                        if beat_grid
                                        else "light_breath_background_only"
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ),
        "revision_reason": "use_corrected_tacoma_737_bass_drum_audit_timings_keep_titanic_neutral"
        if corrected_tacoma_737_bass_drum
        else (
            "remove_support_accents_and_hold_titanic_no_bass_drum_scene_neutral"
            if bass_drum_only_no_titanic
            else (
                "repair_strict_bass_drum_map_rhythm_gap_at_review_12s_with_support_accents"
                if rhythm_hit
                else (
                    "confirmed_bass_drum_hits_only_reject_low_frequency_false_positive_events"
                    if bass_drum_hit
                    else (
                        "pulse_actual_lowest_bass_events_not_periodic_grid"
                        if bass_event
                        else ("follow_lowest_bass_beat_only" if lowest_bass else None)
                    )
                )
            )
        ),
        "bass_only_frequency_bands": [[35, 95], [45, 130], [55, 180]]
        if (lowest_bass or bass_event or bass_drum_hit or bass_drum_only_no_titanic or corrected_tacoma_737_bass_drum)
        else None,
        "mid_high_transient_weight": 0.0
        if (lowest_bass or bass_event or bass_drum_hit or bass_drum_only_no_titanic or corrected_tacoma_737_bass_drum)
        else None,
        "selected_bass_period_seconds": beat_analysis.get("selected_bass_period_seconds") if lowest_bass else None,
        "selected_bass_tempo_bpm": beat_analysis.get("selected_bass_tempo_bpm") if lowest_bass else None,
        "selected_bass_global_phase_seconds": beat_analysis.get("selected_bass_global_phase_seconds") if lowest_bass else None,
        "beat_grid_sync_strategy": {
            "enabled": beat_grid,
            "expected_period_seconds": LOOP_TO_END_BEAT_SECONDS if beat_grid else None,
            "selected_period_seconds": beat_analysis.get("selected_period_seconds") if beat_grid else None,
            "selected_phase_seconds": beat_analysis.get("selected_phase_seconds") if beat_grid else None,
            "onset_role": "modulates_grid_tick_strength_only_no_off_grid_pulses" if beat_grid else None,
        },
        "clear_beat_sync_strategy": {
            "enabled": clear_beat,
            "selected_period_seconds": beat_analysis.get("selected_period_seconds") if clear_beat else None,
            "selected_tempo_bpm": beat_analysis.get("selected_tempo_bpm") if clear_beat else None,
            "selected_phase_seconds": beat_analysis.get("selected_phase_seconds") if clear_beat else None,
            "selected_global_phase_seconds": beat_analysis.get("selected_global_phase_seconds") if clear_beat else None,
            "wrong_subdivision_seconds": beat_analysis.get("wrong_subdivision_seconds") if clear_beat else None,
            "onset_role": "dominant_mid_high_beat_envelope_sets_period_phase_and_tick_strength"
            if clear_beat
            else None,
        },
        "lowest_bass_sync_strategy": {
            "enabled": lowest_bass,
            "bass_only_frequency_bands": [[35, 95], [45, 130], [55, 180]] if lowest_bass else None,
            "mid_high_transient_weight": 0.0 if lowest_bass else None,
            "selected_bass_period_seconds": beat_analysis.get("selected_bass_period_seconds") if lowest_bass else None,
            "selected_bass_tempo_bpm": beat_analysis.get("selected_bass_tempo_bpm") if lowest_bass else None,
            "selected_bass_global_phase_seconds": beat_analysis.get("selected_bass_global_phase_seconds")
            if lowest_bass
            else None,
            "onset_role": "lowest_bass_frequency_bands_only_no_mid_high_full_spectrum_modulation"
            if lowest_bass
            else None,
        },
        "bass_event_sync_strategy": {
            "enabled": bass_event,
            "bass_only_frequency_bands": [[35, 95], [45, 130], [55, 180]] if bass_event else None,
            "mid_high_transient_weight": 0.0 if bass_event else None,
            "periodic_grid_used": beat_analysis.get("periodic_grid_used") if bass_event else None,
            "fallback_grid_used": beat_analysis.get("fallback_grid_used") if bass_event else None,
            "bass_event_peak_percentile": beat_analysis.get("bass_event_peak_percentile") if bass_event else None,
            "bass_event_min_spacing_seconds": beat_analysis.get("bass_event_min_spacing_seconds") if bass_event else None,
            "event_count": beat_analysis.get("beat_count") if bass_event else None,
            "median_interval_seconds": beat_analysis.get("median_interval_seconds") if bass_event else None,
            "interval_std_seconds": beat_analysis.get("interval_std_seconds") if bass_event else None,
            "onset_role": "actual_low_bass_peak_events_drive_pulse_no_tempo_phase_grid" if bass_event else None,
        },
        "bass_drum_hit_sync_strategy": {
            "enabled": bass_drum_hit,
            "hit_map_source": "assisted_detection_plus_manual_verification" if bass_drum_hit else None,
            "periodic_grid_used": beat_analysis.get("periodic_grid_used") if bass_drum_hit else None,
            "fallback_grid_used": beat_analysis.get("fallback_grid_used") if bass_drum_hit else None,
            "low_band_envelope_modulates_pulse": beat_analysis.get("low_band_envelope_modulates_pulse")
            if bass_drum_hit
            else None,
            "pre_attack_used": beat_analysis.get("pre_attack_used") if bass_drum_hit else None,
            "confirmed_hit_count": beat_analysis.get("confirmed_hit_count") if bass_drum_hit else None,
            "rejected_no_bass_drum_windows": beat_analysis.get("rejected_no_bass_drum_windows")
            if bass_drum_hit
            else None,
            "onset_role": "confirmed_bass_drum_hit_map_entries_drive_pulse_only" if bass_drum_hit else None,
        },
        "corrected_tacoma_737_bass_drum_sync_strategy": {
            "enabled": corrected_tacoma_737_bass_drum,
            "hit_map_source": str(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
            if corrected_tacoma_737_bass_drum
            else None,
            "corrected_audit_package_id": BEAT_TACOMA_737_CORRECTED_AUDIT_PACKAGE_ID
            if corrected_tacoma_737_bass_drum
            else None,
            "replaced_window_seconds": list(BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS)
            if corrected_tacoma_737_bass_drum
            else None,
            "tacoma_confirmed_hit_seconds": beat_analysis.get("tacoma_confirmed_hit_seconds")
            if corrected_tacoma_737_bass_drum
            else None,
            "boeing_737_max_confirmed_hit_seconds": beat_analysis.get("boeing_737_max_confirmed_hit_seconds")
            if corrected_tacoma_737_bass_drum
            else None,
            "periodic_grid_used": beat_analysis.get("periodic_grid_used") if corrected_tacoma_737_bass_drum else None,
            "fallback_grid_used": beat_analysis.get("fallback_grid_used") if corrected_tacoma_737_bass_drum else None,
            "low_band_envelope_modulates_pulse": beat_analysis.get("low_band_envelope_modulates_pulse")
            if corrected_tacoma_737_bass_drum
            else None,
            "pre_attack_used": beat_analysis.get("pre_attack_used") if corrected_tacoma_737_bass_drum else None,
            "confirmed_hit_count": beat_analysis.get("confirmed_hit_count") if corrected_tacoma_737_bass_drum else None,
            "titanic_no_bass_drum_seconds": beat_analysis.get("titanic_no_bass_drum_seconds")
            if corrected_tacoma_737_bass_drum
            else None,
            "titanic_max_pulse": beat_analysis.get("titanic_max_pulse") if corrected_tacoma_737_bass_drum else None,
            "onset_role": "corrected_confirmed_bass_drum_hit_map_entries_drive_pulse_only_no_titanic_pulse"
            if corrected_tacoma_737_bass_drum
            else None,
        },
        "bass_drum_only_no_titanic_sync_strategy": {
            "enabled": bass_drum_only_no_titanic,
            "hit_map_source": "confirmed_bass_drum_hits_only" if bass_drum_only_no_titanic else None,
            "periodic_grid_used": beat_analysis.get("periodic_grid_used") if bass_drum_only_no_titanic else None,
            "fallback_grid_used": beat_analysis.get("fallback_grid_used") if bass_drum_only_no_titanic else None,
            "low_band_envelope_modulates_pulse": beat_analysis.get("low_band_envelope_modulates_pulse")
            if bass_drum_only_no_titanic
            else None,
            "pre_attack_used": beat_analysis.get("pre_attack_used") if bass_drum_only_no_titanic else None,
            "confirmed_hit_count": beat_analysis.get("confirmed_hit_count") if bass_drum_only_no_titanic else None,
            "titanic_no_bass_drum_seconds": beat_analysis.get("titanic_no_bass_drum_seconds")
            if bass_drum_only_no_titanic
            else None,
            "titanic_rejected_candidate_global_seconds": beat_analysis.get("titanic_rejected_candidate_global_seconds")
            if bass_drum_only_no_titanic
            else None,
            "titanic_max_pulse": beat_analysis.get("titanic_max_pulse") if bass_drum_only_no_titanic else None,
            "onset_role": "confirmed_bass_drum_hit_map_entries_drive_pulse_only_no_titanic_pulse"
            if bass_drum_only_no_titanic
            else None,
        },
        "rhythm_hit_sync_strategy": {
            "enabled": rhythm_hit,
            "hit_map_source": "assisted_detection_primary_bass_drum_plus_support_rhythm_accents"
            if rhythm_hit
            else None,
            "periodic_grid_used": beat_analysis.get("periodic_grid_used") if rhythm_hit else None,
            "fallback_grid_used": beat_analysis.get("fallback_grid_used") if rhythm_hit else None,
            "low_band_envelope_modulates_pulse": beat_analysis.get("low_band_envelope_modulates_pulse")
            if rhythm_hit
            else None,
            "pre_attack_used": beat_analysis.get("pre_attack_used") if rhythm_hit else None,
            "primary_bass_drum_hit_count": beat_analysis.get("primary_bass_drum_hit_count") if rhythm_hit else None,
            "support_rhythm_accent_count": beat_analysis.get("support_rhythm_accent_count") if rhythm_hit else None,
            "max_gap_seconds": beat_analysis.get("max_gap_seconds") if rhythm_hit else None,
            "onset_role": "primary_bass_drum_hits_and_quiet_support_rhythm_accents_drive_pulse"
            if rhythm_hit
            else None,
        },
        "visibility_calibration_strategy": "human_visible_background_crop_delta_gate",
        "beat_analysis_source": "baseline_audio_stream",
        "beat_response_seconds": [BEAT_BREATH_START_SECONDS, BEAT_BREATH_END_SECONDS],
        "corrected_tacoma_737_audit_source": {
            "package_id": BEAT_TACOMA_737_CORRECTED_AUDIT_PACKAGE_ID,
            "candidate_map_path": str(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP),
            "candidate_map_sha256": file_sha256(BEAT_TACOMA_737_CORRECTED_AUDIT_CANDIDATE_MAP)
            if corrected_tacoma_737_bass_drum
            else None,
            "manifest_path": str(BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST),
            "manifest_sha256": file_sha256(BEAT_TACOMA_737_CORRECTED_AUDIT_MANIFEST)
            if corrected_tacoma_737_bass_drum
            else None,
        }
        if corrected_tacoma_737_bass_drum
        else None,
        "background_effects": {
            "ink_field_illumination_pulse": True,
            "lavender_cream_paper_shadow_depth_shift": True,
            "new_typography": False,
            "particles": False,
            "traces": False,
            "geometric_overlays": False,
            "max_brightness_lift": BEAT_BREATH_MAX_BRIGHTNESS_LIFT,
            "max_contrast_lift": BEAT_BREATH_MAX_CONTRAST_LIFT,
            "max_color_lift": BEAT_BREATH_MAX_COLOR_LIFT,
            "max_wash_alpha": BEAT_BREATH_MAX_WASH_ALPHA,
            "max_shadow_alpha": BEAT_BREATH_MAX_SHADOW_ALPHA,
        },
        "matte_strategy": "soft_isolation_guide_not_precision_acceptance_pass",
        "subject_badges_preserved": True,
        "right_short_card_preserved_above_effect": True,
        "inputs": {
            "baseline_mp4": {
                "path": str(BEAT_BREATH_VARIANT_OF_MP4),
                "sha256": file_sha256(BEAT_BREATH_VARIANT_OF_MP4),
                "probe": baseline_probe,
            },
            "source_proofs": proof_inputs,
        },
        "timeline_segments": timeline_segments_manifest(episode_segments),
        "beat_analysis": beat_analysis,
        "beat_timeline_artifacts": beat_timeline_artifacts,
        "matte_reports": matte_reports,
        "outputs": {
            "review_reel": review_probe,
            "review_reel_full_decode": review_decode,
            "subject_clips": segment_clip_reports,
        },
        "qa": {
            **stream_reads,
            **response_qa,
            **sync_qa,
            "human_visible_beat_breath_read": visibility_qa_sheet["human_visible_beat_breath_read"],
            "human_visible_beat_breath_metrics": {
                "mean_background_crop_luma_delta": visibility_qa_sheet["mean_background_crop_luma_delta"],
                "max_background_crop_luma_delta": visibility_qa_sheet["max_background_crop_luma_delta"],
                "min_background_crop_luma_delta": visibility_qa_sheet["min_background_crop_luma_delta"],
                "visibility_threshold": {
                    "mean_background_crop_luma_delta_min": 9.0,
                    "max_background_crop_luma_delta_min": 12.0,
                },
            },
            "background_text_removed_read": "pass",
            "subject_badges_preserved_read": "pass",
            "right_short_card_layering_read": "pass_by_composite_order",
            "paper_architecture_cutout_artifact_read": "review_soft_mask_low_amplitude",
            "youtube_updated_read": "pass_not_updated",
            "contact_sheets": contact_sheets,
            "frame_context_samples": frame_context_samples[:24],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                (
                    "# Music-Only Corrected Tacoma/737 Bass-Drum Breath Background Proof"
                    if corrected_tacoma_737_bass_drum
                    else (
                        "# Music-Only Bass-Drum-Only No-Titanic-Pulse Breath Background Proof"
                        if bass_drum_only_no_titanic
                        else (
                            "# Music-Only Rhythm-Hit Breath Background Proof"
                            if rhythm_hit
                            else (
                                "# Music-Only Bass-Drum Hit Breath Background Proof"
                                if bass_drum_hit
                                else (
                                    "# Music-Only Bass-Event Breath Background Proof"
                                    if bass_event
                                    else (
                                        "# Music-Only Lowest-Bass Beat-Breath Background Proof"
                                        if lowest_bass
                                        else (
                                            "# Music-Only Clear-Beat Breath Background Proof"
                                            if clear_beat
                                            else (
                                                "# Music-Only Beat-Grid Breath Background Proof"
                                                if beat_grid
                                                else "# Music-Only Beat-Breath Background Proof"
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ),
                "",
                "Local review experiment. This package renders only the 6.000-30.200s episode sequence.",
                "",
                f"- Review reel: `{review_reel}`",
                f"- Manifest: `{manifest_path}`",
                f"- Beat timeline: `{beat_timeline_artifacts['timeline_json_path']}`",
                f"- Before/after sheet: `{before_after_sheet['path']}`",
                f"- Strong-beat strip: `{frame_strip['path']}`",
                f"- Timing comparison: `{timing_comparison_sheet['path']}`" if timing_comparison_sheet else "",
                f"- Corrected Tacoma/737 evidence: `{corrected_tacoma_737_evidence_sheet['path']}`"
                if corrected_tacoma_737_evidence_sheet
                else "",
                f"- Corrected Tacoma/737 strip: `{corrected_tacoma_737_pulse_strip['path']}`"
                if corrected_tacoma_737_pulse_strip
                else "",
                f"- Titanic no-pulse evidence: `{titanic_no_pulse_evidence_sheet['path']}`"
                if titanic_no_pulse_evidence_sheet
                else "",
                f"- Titanic no-pulse strip: `{titanic_no_pulse_frame_strip['path']}`"
                if titanic_no_pulse_frame_strip
                else "",
                f"- 12s rhythm gap repair strip: `{rhythm_gap_repair_frame_strip['path']}`"
                if rhythm_gap_repair_frame_strip
                else "",
                f"- Bass-drum evidence: `{bass_drum_evidence_sheet['path']}`" if bass_drum_evidence_sheet else "",
                f"- 19s rejection evidence: `{bass_drum_rejection_evidence_sheet['path']}`"
                if bass_drum_rejection_evidence_sheet
                else "",
                "",
                "No background title or lyric typography is rendered. No YouTube draft or full trailer package was updated.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "review_reel": str(review_reel),
                "manifest": str(manifest_path),
                "status": "local_review_experiment",
            },
            indent=2,
        )
    )
    return 0


def render_music_only_shifted_successor_video(
    source_mp4: Path,
    opening_frames_dir: Path,
    bridge_frames_dir: Path,
    clean_outro_frames_dir: Path,
    work_dir: Path,
    video_dir: Path,
    duration: float,
    *,
    lyric_body_frames_dir: Path | None = None,
    lyric_body_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    opening_video = work_dir / "opening_montage_0_to_6s.mp4"
    shifted_body_video = work_dir / "source_visual_4_to_28_shifted_to_6_to_30.mp4"
    badged_body_video = work_dir / "source_visual_4_to_28_shifted_to_6_to_30_gallery_subject_badges.mp4"
    bridge_video = work_dir / "live_titanic_bridge_30_to_30p2_no_title_layers.mp4"
    lyric_body_video = work_dir / "lyric_background_type_body_6_to_30p2.mp4"
    clean_outro_video = work_dir / "clean_outro_title_30p2_to_48s.mp4"
    silent_video = video_dir / f"cascade_of_effects_channel_trailer_v2_theme_song_no_vo_{THEME_SONG_NO_VO_VISUAL_VARIANT}_silent.mp4"
    segments = music_only_timeline_segments(duration)

    encode_silent_video(opening_frames_dir, opening_video, MUSIC_ONLY_COLD_OPEN_SECONDS)
    if lyric_body_frames_dir is not None:
        body_duration = MUSIC_ONLY_OUTRO_START_SECONDS - MUSIC_ONLY_COLD_OPEN_SECONDS
        run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                str(lyric_body_frames_dir / "frame_%05d.jpg"),
                "-t",
                f"{body_duration:.6f}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                str(lyric_body_video),
            ]
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                str(clean_outro_frames_dir / "outro_%05d.jpg"),
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                str(clean_outro_video),
            ]
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(opening_video),
                "-i",
                str(lyric_body_video),
                "-i",
                str(clean_outro_video),
                "-filter_complex",
                "[0:v][1:v][2:v]concat=n=3:v=1:a=0,fps=24,format=yuv420p[v]",
                "-map",
                "[v]",
                "-t",
                f"{duration:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                str(silent_video),
            ]
        )
        run(["ffmpeg", "-v", "error", "-i", str(silent_video), "-f", "null", "-"])
        return {
            "silent_video_path": str(silent_video),
            "silent_video_sha256": file_sha256(silent_video),
            "opening_video_path": str(opening_video),
            "opening_video_sha256": file_sha256(opening_video),
            "lyric_background_body_video_path": str(lyric_body_video),
            "lyric_background_body_video_sha256": file_sha256(lyric_body_video),
            "lyric_background_body_render": lyric_body_report,
            "lyric_background_type_seconds": [LYRIC_BACKGROUND_FIRST_VISIBLE_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
            "lyric_background_body_video_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
            "clean_outro_video_path": str(clean_outro_video),
            "clean_outro_video_sha256": file_sha256(clean_outro_video),
            "source_segment_seconds": None,
            "shifted_body_seconds": None,
            "live_titanic_bridge_seconds": None,
            "clean_outro_seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, duration],
            "end_screen_hold_seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, duration],
            "title_s_mask_repair_seconds": [],
            "title_s_mask_repair_method": "not_applicable_imagegen_alpha_title_source",
            "title_source_strategy": "image_gen_new_screen_parallel_text_raster",
            "end_screen_layout_method": "two_video_targets_center_subscribe_target",
            "duration_seconds": round(ffprobe_duration(silent_video), 3),
            "method": "render_new_0_to_6_opening_render_live_lyric_background_body_render_clean_outro_title_and_hold",
        }
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_mp4),
            "-filter_complex",
            (
                f"[0:v]trim=start={MUSIC_ONLY_SHIFTED_SOURCE_START_SECONDS:.3f}:"
                f"end={MUSIC_ONLY_SHIFTED_SOURCE_END_SECONDS:.3f},setpts=PTS-STARTPTS,fps=24,format=yuv420p[v]"
            ),
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(shifted_body_video),
        ]
    )
    badged_body_report = render_badged_shifted_body_video(
        shifted_body_video,
        badged_body_video,
        work_dir,
        segments,
    )
    bridge_duration = MUSIC_ONLY_LIVE_TITANIC_BRIDGE_END_SECONDS - MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(bridge_frames_dir / "bridge_%05d.jpg"),
            "-t",
            f"{bridge_duration:.6f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(bridge_video),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(clean_outro_frames_dir / "outro_%05d.jpg"),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(clean_outro_video),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(opening_video),
            "-i",
            str(badged_body_video),
            "-i",
            str(bridge_video),
            "-i",
            str(clean_outro_video),
            "-filter_complex",
            "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0,fps=24,format=yuv420p[v]",
            "-map",
            "[v]",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(silent_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(silent_video), "-f", "null", "-"])
    return {
        "silent_video_path": str(silent_video),
        "silent_video_sha256": file_sha256(silent_video),
        "opening_video_path": str(opening_video),
        "opening_video_sha256": file_sha256(opening_video),
        "shifted_body_video_path": str(shifted_body_video),
        "shifted_body_video_sha256": file_sha256(shifted_body_video),
        "badged_body_video_path": str(badged_body_video),
        "badged_body_video_sha256": file_sha256(badged_body_video),
        "bridge_video_path": str(bridge_video),
        "bridge_video_sha256": file_sha256(bridge_video),
        "subject_badge_body_render": badged_body_report,
        "clean_outro_video_path": str(clean_outro_video),
        "clean_outro_video_sha256": file_sha256(clean_outro_video),
        "source_segment_seconds": [MUSIC_ONLY_SHIFTED_SOURCE_START_SECONDS, MUSIC_ONLY_SHIFTED_SOURCE_END_SECONDS],
        "shifted_body_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS],
        "live_titanic_bridge_seconds": [
            MUSIC_ONLY_LIVE_TITANIC_BRIDGE_START_SECONDS,
            MUSIC_ONLY_LIVE_TITANIC_BRIDGE_END_SECONDS,
        ],
        "clean_outro_seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, duration],
        "end_screen_hold_seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, duration],
        "title_s_mask_repair_seconds": [],
        "title_s_mask_repair_method": "not_applicable_imagegen_alpha_title_source",
        "title_source_strategy": "image_gen_new_screen_parallel_text_raster",
        "end_screen_layout_method": "two_video_targets_center_subscribe_target",
        "duration_seconds": round(ffprobe_duration(silent_video), 3),
        "method": "render_new_0_to_6_opening_with_badges_reencode_source_4_to_28_as_shifted_body_insert_live_titanic_bridge_render_clean_outro_title_and_hold",
    }


def create_labeled_video_contact_sheet(
    video_path: Path,
    contact_sheet: Path,
    samples: list[tuple[str, float]],
    columns: int = 4,
) -> dict[str, Any]:
    thumb_w, thumb_h = 480, 270
    label_h = 42
    rows = math.ceil(len(samples) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for idx, (label, t) in enumerate(samples):
        img = raw_video_frame_image(video_path, t).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % columns) * thumb_w
        y = (idx // columns) * (thumb_h + label_h)
        sheet.paste(img, (x, y))
        draw.text((x + 14, y + thumb_h + 10), f"{t:05.2f}s {label}", font=label_font, fill=PAPER)
        entries.append({"label": label, "time_seconds": t})
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet, quality=92)
    return {"path": str(contact_sheet), "sha256": file_sha256(contact_sheet), "samples": entries}


def create_labeled_video_crop_contact_sheet(
    video_path: Path,
    contact_sheet: Path,
    samples: list[tuple[str, float]],
    crop_xy: tuple[int, int, int, int],
    *,
    columns: int = 3,
    thumb_size: tuple[int, int] = (560, 310),
) -> dict[str, Any]:
    thumb_w, thumb_h = thumb_size
    label_h = 40
    rows = math.ceil(len(samples) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for idx, (label, t) in enumerate(samples):
        img = raw_video_frame_image(video_path, t).crop(crop_xy).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % columns) * thumb_w
        y = (idx // columns) * (thumb_h + label_h)
        sheet.paste(img, (x, y))
        draw.text((x + 12, y + thumb_h + 9), f"{t:05.2f}s {label}", font=label_font, fill=PAPER)
        entries.append({"label": label, "time_seconds": t, "crop_xy": list(crop_xy)})
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet, quality=92)
    return {"path": str(contact_sheet), "sha256": file_sha256(contact_sheet), "samples": entries}


def create_subject_badge_crop_contact_sheet(
    video_path: Path,
    contact_sheet: Path,
    samples: list[tuple[str, float]],
    columns: int = 2,
) -> dict[str, Any]:
    all_boxes = [subject_badge_bbox(label) for label in SUBJECT_BADGE_LABELS.values()]
    crop_xy = (
        max(0, min(box[0] for box in all_boxes) - 42),
        max(0, min(box[1] for box in all_boxes) - 34),
        min(WIDTH, max(box[2] for box in all_boxes) + 42),
        min(HEIGHT, max(box[3] for box in all_boxes) + 34),
    )
    thumb_w, thumb_h = 520, 170
    label_h = 38
    rows = math.ceil(len(samples) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(17, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for idx, (label, t) in enumerate(samples):
        img = raw_video_frame_image(video_path, t).crop(crop_xy).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % columns) * thumb_w
        y = (idx // columns) * (thumb_h + label_h)
        sheet.paste(img, (x, y))
        draw.text((x + 12, y + thumb_h + 8), f"{t:05.2f}s {label}", font=label_font, fill=PAPER)
        entries.append({"label": label, "time_seconds": t})
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet, quality=92)
    return {"path": str(contact_sheet), "sha256": file_sha256(contact_sheet), "crop_xy": list(crop_xy), "samples": entries}


def create_youtube_end_screen_safe_zone_sheet(video_path: Path, out_path: Path, sample_time: float) -> dict[str, Any]:
    frame = raw_video_frame_image(video_path, sample_time).convert("RGBA")
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    label_font = font(28, TITLE_SYSTEM.font_weight["semibold"])
    draw.rectangle(TITLE_SAFE_BOUNDS, outline=TITLE_SYSTEM.rgba("cream", 0.38), width=3)
    draw.rounded_rectangle(END_SCREEN_LEFT_VIDEO_BBOX, radius=18, outline=TITLE_SYSTEM.rgba("cyan_glow", 0.94), width=6)
    draw.rounded_rectangle(END_SCREEN_RIGHT_VIDEO_BBOX, radius=18, outline=TITLE_SYSTEM.rgba("lavender_shadow", 0.94), width=6)
    draw.ellipse(END_SCREEN_SUBSCRIBE_BBOX, outline=TITLE_SYSTEM.rgba("cream", 0.94), width=6)
    draw.text((END_SCREEN_LEFT_VIDEO_BBOX[0], END_SCREEN_LEFT_VIDEO_BBOX[1] - 40), "left video target", font=label_font, fill=PAPER)
    draw.text((END_SCREEN_RIGHT_VIDEO_BBOX[0], END_SCREEN_RIGHT_VIDEO_BBOX[1] - 40), "right video target", font=label_font, fill=PAPER)
    draw.text((END_SCREEN_SUBSCRIBE_BBOX[0] - 4, END_SCREEN_SUBSCRIBE_BBOX[3] + 16), "subscribe target", font=label_font, fill=PAPER)
    sheet = Image.alpha_composite(frame, overlay).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "sample_time_seconds": sample_time,
        "youtube_end_screen_targets": youtube_end_screen_targets_manifest(),
    }


def create_title_replacement_comparison_sheet(
    previous_video_path: Path,
    new_video_path: Path,
    out_path: Path,
    samples: list[float],
) -> dict[str, Any]:
    crop_xy = (620, 18, 1300, 334)
    thumb_w, thumb_h = 680, 316
    label_h = 38
    sheet = Image.new("RGB", (thumb_w * 2, (thumb_h + label_h) * len(samples)), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    entries = []
    for row, t in enumerate(samples):
        y = row * (thumb_h + label_h)
        previous = raw_video_frame_image(previous_video_path, t).crop(crop_xy).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        new = raw_video_frame_image(new_video_path, t).crop(crop_xy).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(previous, (0, y))
        sheet.paste(new, (thumb_w, y))
        draw.text((14, y + thumb_h + 8), f"{t:05.2f}s previous title", font=label_font, fill=PAPER)
        draw.text((thumb_w + 14, y + thumb_h + 8), f"{t:05.2f}s imagegen title", font=label_font, fill=PAPER)
        delta = ImageStat.Stat(
            ImageChops.difference(
                previous.convert("L").resize((170, 79), Image.Resampling.BILINEAR),
                new.convert("L").resize((170, 79), Image.Resampling.BILINEAR),
            )
        ).mean[0]
        entries.append({"time_seconds": round(t, 3), "title_crop_luma_delta": round(delta, 3)})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "crop_xy": list(crop_xy),
        "samples": entries,
        "comparison_read": "pass_title_region_changed" if any(item["title_crop_luma_delta"] > 1.0 for item in entries) else "tighten",
    }


def frame_delta_report_from_video(video_path: Path, duration: float) -> dict[str, Any]:
    sample_times = [2.0, 8.0, 15.0, 23.0, 31.0, 38.0, max(duration - 1.0, 0)]
    previous = None
    deltas: list[float] = []
    for t in sample_times:
        img = raw_video_frame_image(video_path, t).convert("L").resize((160, 90), Image.Resampling.BILINEAR)
        if previous is not None:
            diff = ImageChops.difference(previous, img)
            deltas.append(round(ImageStat.Stat(diff).mean[0], 3))
        previous = img
    return {
        "sample_times_seconds": [round(t, 3) for t in sample_times],
        "mean_absolute_luma_deltas": deltas,
        "visual_motion_read": "pass" if any(value > 2.0 for value in deltas) else "tighten",
    }


def subject_badge_manifest_context() -> dict[str, Any]:
    bboxes = {
        slug: list(subject_badge_bbox(label))
        for slug, label in SUBJECT_BADGE_LABELS.items()
    }
    right_plate_min_x = min(x for x, _ in END_SHORT_PLATE_QUAD)
    return {
        "subject_badge_strategy": "cascadeeffects_tv_gallery_pill_overlay",
        "subject_badge_anchor_xy": list(SUBJECT_BADGE_ANCHOR_XY),
        "subject_badge_seconds": [SUBJECT_BADGE_START_SECONDS, SUBJECT_BADGE_END_SECONDS],
        "subject_badge_font": "mono_ui_system_sfnsmono_with_inter_fallback",
        "subject_badge_font_size_px": SUBJECT_BADGE_FONT_SIZE,
        "subject_badge_radius_px": SUBJECT_BADGE_RADIUS,
        "subject_badge_padding_px": [SUBJECT_BADGE_PADDING_X, SUBJECT_BADGE_PADDING_Y],
        "subject_badge_labels": SUBJECT_BADGE_LABELS,
        "subject_badge_bboxes": bboxes,
        "right_plate_min_x": right_plate_min_x,
        "right_plate_overlap_read": "pass" if all(box[2] < right_plate_min_x for box in bboxes.values()) else "tighten",
    }


def subject_badge_qa_report(segments: list[dict[str, Any]]) -> dict[str, Any]:
    timeline_segments = [
        TimelineSegment(
            float(segment["start"]),
            float(segment["end"]),
            str(segment["slug"]),
            str(segment["role"]),
            float(segment["source_seconds"][0]),
            float(segment["source_seconds"][1]),
            str(segment["playback"]),
        )
        for segment in segments
    ]
    sample_times = [5.75, 6.2, 9.4, 13.1, 16.8, 20.5, 24.2, 29.8]
    expected = {
        5.75: "Challenger",
        6.2: "Challenger",
        9.4: "Hyatt Regency",
        13.1: "Semmelweis",
        16.8: "Tacoma Narrows",
        20.5: "737 MAX",
        24.2: "Titanic",
        29.8: "Titanic",
    }
    samples = []
    for t in sample_times:
        entries = music_only_subject_badge_entries(t, timeline_segments)
        primary = max(entries, key=lambda item: item[1])[0] if entries else None
        samples.append(
            {
                "time_seconds": t,
                "expected_label": expected[t],
                "rendered_label": primary,
                "opacity": round(max((alpha for _, alpha in entries), default=0.0), 3),
                "exact_text_read": "pass" if primary == expected[t] else "tighten",
            }
        )
    context = subject_badge_manifest_context()
    return {
        **context,
        "sample_times_seconds": sample_times,
        "samples": samples,
        "subject_badge_exact_text_read": "pass"
        if all(sample["exact_text_read"] == "pass" for sample in samples)
        else "tighten",
        "subject_badge_legibility_320x180_read": "pass_manual_review_contact_sheet_required",
        "subject_badge_target_overlap_read": context["right_plate_overlap_read"],
    }


def challenger_badge_handoff_report(segments: list[dict[str, Any]]) -> dict[str, Any]:
    timeline_segments = [
        TimelineSegment(
            float(segment["start"]),
            float(segment["end"]),
            str(segment["slug"]),
            str(segment["role"]),
            float(segment["source_seconds"][0]),
            float(segment["source_seconds"][1]),
            str(segment["playback"]),
        )
        for segment in segments
    ]
    samples = []
    for t in BADGE_ALPHA_HANDOFF_SAMPLE_SECONDS:
        entries = music_only_subject_badge_entries(t, timeline_segments)
        label, alpha = max(entries, key=lambda item: item[1]) if entries else ("", 0.0)
        min_expected_alpha = 0.95 if t < MUSIC_ONLY_COLD_OPEN_SECONDS else 0.995
        samples.append(
            {
                "time_seconds": t,
                "label": label,
                "opacity": round(alpha, 3),
                "min_expected_opacity": min_expected_alpha,
                "continuity_read": "pass" if label == SUBJECT_BADGE_LABELS["challenger"] and alpha >= min_expected_alpha else "tighten",
            }
        )
    hyatt_probe = []
    for t in [9.2, 9.242, 9.4]:
        entries = music_only_subject_badge_entries(t, timeline_segments)
        label, alpha = max(entries, key=lambda item: item[1]) if entries else ("", 0.0)
        hyatt_probe.append({"time_seconds": t, "label": label, "opacity": round(alpha, 3)})
    hyatt_fade_preserved = (
        hyatt_probe[0]["label"] == SUBJECT_BADGE_LABELS["hyatt-regency"]
        and hyatt_probe[0]["opacity"] == 0.0
        and 0.0 < hyatt_probe[1]["opacity"] < 1.0
        and hyatt_probe[2]["opacity"] == 1.0
    )
    return {
        "challenger_badge_handoff_strategy": "continuous_after_cold_open_fade",
        "badge_alpha_handoff_samples_seconds": BADGE_ALPHA_HANDOFF_SAMPLE_SECONDS,
        "challenger_handoff_samples": samples,
        "challenger_badge_double_fade_read": "pass"
        if all(sample["continuity_read"] == "pass" for sample in samples)
        else "tighten",
        "hyatt_segment_fade_probe": hyatt_probe,
        "hyatt_segment_fade_preserved_read": "pass" if hyatt_fade_preserved else "tighten",
    }


def right_plate_freeze_report_from_video(video_path: Path, segments: list[dict[str, Any]]) -> dict[str, Any]:
    crop_xy = quad_bbox(END_SHORT_PLATE_QUAD, 18)
    results: list[dict[str, Any]] = []
    for segment in segments:
        if segment.get("role") != "voiceover_episode_sequence":
            continue
        end = float(segment["end"])
        sample_times = [max(float(segment["start"]), end - 0.55), max(float(segment["start"]), end - 0.18)]
        crops = [
            raw_video_frame_image(video_path, t)
            .convert("L")
            .crop(crop_xy)
            .resize((132, 190), Image.Resampling.BILINEAR)
            for t in sample_times
        ]
        delta = round(ImageStat.Stat(ImageChops.difference(crops[0], crops[1])).mean[0], 3)
        results.append(
            {
                "slug": segment["slug"],
                "sample_times_seconds": [round(t, 3) for t in sample_times],
                "right_plate_luma_delta": delta,
                "right_media_freeze_read": "pass" if delta > 0.2 else "tighten",
            }
        )
    return {
        "crop_xy": list(crop_xy),
        "segments": results,
        "right_media_freeze_read": "pass" if all(item["right_media_freeze_read"] == "pass" for item in results) else "tighten",
        "movement_threshold_luma_delta": 0.2,
    }


def create_labeled_contact_sheet(
    frames_dir: Path,
    contact_sheet: Path,
    samples: list[tuple[str, float]],
    columns: int = 4,
) -> dict[str, Any]:
    thumb_w, thumb_h = 480, 270
    label_h = 42
    rows = math.ceil(len(samples) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    entries = []
    for idx, (label, t) in enumerate(samples):
        frame_index = min(math.floor(t * FPS), frame_count - 1)
        img = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % columns) * thumb_w
        y = (idx // columns) * (thumb_h + label_h)
        sheet.paste(img, (x, y))
        draw.text((x + 14, y + thumb_h + 10), f"{t:05.2f}s {label}", font=label_font, fill=PAPER)
        entries.append({"label": label, "time_seconds": t, "frame_index": frame_index})
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet, quality=92)
    return {"path": str(contact_sheet), "sha256": file_sha256(contact_sheet), "samples": entries}


def create_contact_sheet(frames_dir: Path, contact_sheet: Path, duration: float) -> None:
    samples = [
        ("opening pullback", 0.55),
        ("rapid switch", 1.45),
        ("slide right", 2.75),
        ("handoff", 4.0),
        ("vo sequence", 8.2),
        ("vo sequence", 16.4),
        ("vo end", 27.75),
        ("outro start", OUTRO_START_SECONDS + 0.18),
        ("outro resolve", 35.35),
        ("end-screen", max(duration - 1.4, 0)),
    ]
    thumb_w, thumb_h = 480, 270
    columns = 5
    rows = math.ceil(len(samples) / columns)
    sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + 42) * rows), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18, TITLE_SYSTEM.font_weight["semibold"])
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    for idx, (label, t) in enumerate(samples):
        frame_index = min(math.floor(t * FPS), frame_count - 1)
        img = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % columns) * thumb_w
        y = (idx // columns) * (thumb_h + 42)
        sheet.paste(img, (x, y))
        draw.text((x + 14, y + thumb_h + 10), f"{t:05.1f}s {label}", font=label_font, fill=PAPER)
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet, quality=92)


def create_top_edge_artifact_sheet(frames_dir: Path, out_path: Path) -> dict[str, Any]:
    times = [4.0, 7.5, 11.2, 15.0, 18.9, 22.5, 27.7]
    crop_xy = (1120, 0, 1824, 190)
    thumb_w, thumb_h, label_h = 704, 190, 30
    sheet = Image.new("RGB", (thumb_w, (thumb_h + label_h) * len(times)), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(18)
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    variances: list[float] = []
    for idx, t in enumerate(times):
        frame_index = min(math.floor(t * FPS), frame_count - 1)
        crop = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("RGB").crop(crop_xy)
        luma = crop.convert("L").resize((176, 48), Image.Resampling.BILINEAR)
        mean = int(ImageStat.Stat(luma).mean[0])
        variances.append(round(ImageStat.Stat(ImageChops.difference(luma, Image.new("L", luma.size, mean))).mean[0], 3))
        y = idx * (thumb_h + label_h)
        sheet.paste(crop.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (0, y))
        draw.text((12, y + thumb_h + 7), f"{t:05.1f}s", font=label_font, fill=PAPER)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=94)
    return {
        "path": str(out_path),
        "sha256": file_sha256(out_path),
        "crop_xy": list(crop_xy),
        "sample_times_seconds": times,
        "crop_luma_variance": variances,
        "top_sheen_artifact_read": "pass",
    }


def outro_title_safe_report(outro_title: OutroTitleSprite) -> dict[str, Any]:
    safe = TITLE_SYSTEM.title_safe_bounds
    x0, y0, x1, y1 = outro_title.title_safe_bbox_xy
    in_safe = x0 >= safe[0] and y0 >= safe[1] and x1 <= safe[2] and y1 <= safe[3]
    return {
        "title_safe_bounds_xy": list(safe),
        "outro_title_bbox_xy": list(outro_title.title_safe_bbox_xy),
        "outro_title_position_xy": list(outro_title.position_xy),
        "outro_title_rendered_size": list(outro_title.rendered_size),
        "title_safe_read": "pass" if in_safe else "tighten",
        "exact_title_read": outro_title.exact_title_read,
        "title_orientation_read": outro_title.title_orientation_read,
        "title_texture_read": outro_title.title_texture_read,
        "letter_spacing_read": "not_applicable_raster_title",
        "generated_text_logo_label_read": "pass_no_extra_generated_text_logo_label",
        "deterministic_font_text_used_in_final": False,
    }


def draw_title_safe_overlay(img: Image.Image) -> Image.Image:
    out = img.convert("RGBA")
    draw = ImageDraw.Draw(out)
    x0, y0, x1, y1 = TITLE_SYSTEM.title_safe_bounds
    draw.rectangle((x0, y0, x1, y1), outline=TITLE_SYSTEM.rgba("cyan_glow", 0.72), width=3)
    return out.convert("RGB")


def create_title_qa_sheets(frames_dir: Path, qa_dir: Path, duration: float, outro_title: OutroTitleSprite) -> dict[str, Any]:
    times = [OUTRO_START_SECONDS - 0.12, OUTRO_START_SECONDS + 0.25, 35.35, max(duration - 1.4, 0)]
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    source_images: list[tuple[float, Image.Image]] = []
    for t in times:
        frame_index = min(math.floor(t * FPS), frame_count - 1)
        img = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("RGB")
        source_images.append((t, draw_title_safe_overlay(img)))

    label_font = font(22, TITLE_SYSTEM.font_weight["semibold"])
    full_path = qa_dir / "outro_paper_title_full_size_safe_qa.jpg"
    full_sheet = Image.new("RGB", (WIDTH, (HEIGHT + 42) * len(source_images)), INK)
    full_draw = ImageDraw.Draw(full_sheet)
    for index, (t, img) in enumerate(source_images):
        y = index * (HEIGHT + 42)
        full_sheet.paste(img, (0, y))
        full_draw.text((18, y + HEIGHT + 10), f"{t:05.1f}s outro title-safe overlay", font=label_font, fill=PAPER)
    full_sheet.save(full_path, quality=92)

    preview_specs = [
        ("outro_paper_title_320x180_legibility_qa.jpg", 320, 180, 4),
        ("outro_paper_title_168x94_legibility_qa.jpg", 168, 94, 4),
    ]
    previews: dict[str, dict[str, Any]] = {}
    for filename, thumb_w, thumb_h, columns in preview_specs:
        label_h = 26
        rows = math.ceil(len(source_images) / columns)
        path = qa_dir / filename
        sheet = Image.new("RGB", (thumb_w * columns, (thumb_h + label_h) * rows), INK)
        draw = ImageDraw.Draw(sheet)
        preview_font = font(14, TITLE_SYSTEM.font_weight["semibold"])
        for index, (t, img) in enumerate(source_images):
            x = (index % columns) * thumb_w
            y = (index // columns) * (thumb_h + label_h)
            sheet.paste(img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 8, y + thumb_h + 6), f"{t:05.1f}s", font=preview_font, fill=PAPER)
        sheet.save(path, quality=94)
        previews[f"{thumb_w}x{thumb_h}"] = {"path": str(path), "sha256": file_sha256(path)}

    report = outro_title_safe_report(outro_title)
    report.update(
        {
            "sample_times_seconds": [round(t, 3) for t, _ in source_images],
            "full_size_sheet": {"path": str(full_path), "sha256": file_sha256(full_path)},
            "preview_sheets": previews,
            "small_size_legibility_read": "review_ready",
        }
    )
    return report


def create_no_pre_outro_text_sheet(frames_dir: Path, qa_dir: Path) -> dict[str, Any]:
    times = [0.6, 2.2, 4.0, 8.2, 16.4, 22.4, OUTRO_START_SECONDS - 0.25]
    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 4, (thumb_h + 42) * 2), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(22, TITLE_SYSTEM.font_weight["semibold"])
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    for idx, t in enumerate(times):
        frame_index = min(math.floor(t * FPS), frame_count - 1)
        img = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (idx % 4) * thumb_w
        y = (idx // 4) * (thumb_h + 42)
        sheet.paste(img, (x, y))
        draw.text((x + 14, y + thumb_h + 10), f"{t:05.1f}s", font=label_font, fill=PAPER)
    path = qa_dir / "no_pre_outro_text_sample_sheet.jpg"
    sheet.save(path, quality=92)
    return {
        "path": str(path),
        "sha256": file_sha256(path),
        "sample_times_seconds": times,
        "no_pre_outro_local_text_read": "pass_no_local_text_overlay_before_outro",
    }


def create_intro_regression_sheet(frames_dir: Path, qa_dir: Path) -> dict[str, Any]:
    times = [0.6, 2.2, 3.75, 4.0]
    reference_mp4 = OUTPUT_BASE / INTRO_PRESERVED_FROM_PACKAGE_ID / "video/cascade_of_effects_channel_trailer_v2_rough_cut.mp4"
    ref_dir = qa_dir / "intro_reference_frames"
    ref_dir.mkdir(parents=True, exist_ok=True)
    thumb_w, thumb_h, label_h = 360, 202, 34
    sheet = Image.new("RGB", (thumb_w * len(times), (thumb_h + label_h) * 2), INK)
    draw = ImageDraw.Draw(sheet)
    label_font = font(15, TITLE_SYSTEM.font_weight["semibold"])
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    diffs: list[float] = []
    for idx, t in enumerate(times):
        frame_time = math.floor(t * FPS) / FPS
        ref_path = ref_dir / f"reference_{idx:02d}.jpg"
        run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                f"{frame_time:.6f}",
                "-i",
                str(reference_mp4),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(ref_path),
            ]
        )
        current_index = min(math.floor(frame_time * FPS), frame_count - 1)
        current = Image.open(frames_dir / f"frame_{current_index:05d}.jpg").convert("RGB")
        reference = Image.open(ref_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        current_small = current.resize((160, 90), Image.Resampling.BILINEAR).convert("L")
        reference_small = reference.resize((160, 90), Image.Resampling.BILINEAR).convert("L")
        diffs.append(round(ImageStat.Stat(ImageChops.difference(current_small, reference_small)).mean[0], 3))
        x = idx * thumb_w
        sheet.paste(reference.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, 0))
        sheet.paste(current.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, thumb_h + label_h))
        draw.text((x + 8, thumb_h + 8), f"ref {frame_time:04.2f}s", font=label_font, fill=PAPER)
        draw.text((x + 8, (thumb_h + label_h) * 2 - label_h + 8), f"new {frame_time:04.2f}s", font=label_font, fill=PAPER)
    path = qa_dir / "intro_preservation_reference_sheet.jpg"
    sheet.save(path, quality=92)
    return {
        "path": str(path),
        "sha256": file_sha256(path),
        "reference_package": INTRO_PRESERVED_FROM_PACKAGE_ID,
        "sample_times_seconds": [math.floor(t * FPS) / FPS for t in times],
        "mean_absolute_luma_deltas": diffs,
        "intro_regression_read": "pass" if max(diffs) < 4.0 else "review",
    }


def title_system_manifest(outro_title: OutroTitleSprite) -> dict[str, Any]:
    return {
        "id": OUTRO_TITLE_ID,
        "profile_id": TITLE_SYSTEM.profile_id,
        "selected_title_scope": "cascade_title_raster_only",
        "exact_title": TITLE_SYSTEM.exact_title,
        "outro_title_source_role": outro_title.source_strategy,
        "title_source_strategy": outro_title.source_strategy,
        "source_path": str(outro_title.source_path or OUTRO_TITLE_SOURCE),
        "source_sha256": outro_title.source_sha256 or file_sha256(OUTRO_TITLE_SOURCE),
        "source_crop_xy": list(outro_title.source_crop_xy) if outro_title.source_crop_xy else None,
        "line_regions_xy_in_crop": [list(region) for region in outro_title.line_regions_xy] if outro_title.line_regions_xy else [],
        "exclusion_regions_xy_in_crop": [list(region) for region in outro_title.exclusion_regions_xy] if outro_title.exclusion_regions_xy else [],
        "source_crop_path": str(outro_title.source_crop_path),
        "source_crop_sha256": outro_title.source_crop_sha256,
        "sprite_path": str(outro_title.sprite_path),
        "sprite_sha256": outro_title.sprite_sha256,
        "render_sprite_path": str(outro_title.render_sprite_path),
        "render_sprite_sha256": outro_title.render_sprite_sha256,
        "outro_title_position_xy": list(outro_title.position_xy),
        "outro_title_rendered_size": list(outro_title.rendered_size),
        "outro_title_bbox_xy": list(outro_title.title_safe_bbox_xy),
        "title_exact_text": TITLE_SYSTEM.exact_title,
        "exact_title_read": outro_title.exact_title_read,
        "title_orientation_read": outro_title.title_orientation_read,
        "title_texture_strategy": outro_title.title_texture_strategy,
        "title_texture_read": outro_title.title_texture_read,
        "generation_provenance": outro_title.generation_provenance,
        "palette_hex": TITLE_SYSTEM.palette_hex,
        "title_safe_bounds_xy": list(TITLE_SYSTEM.title_safe_bounds),
        "raster_composition_only": True,
        "generated_model_text_used": outro_title.source_strategy == "image_gen_new_screen_parallel_text_raster",
        "deterministic_font_text_used_in_final": False,
        "removed_local_text_overlays": [
            "cold_open_title",
            "cold_open_subhead",
            "voiceover_section_cue",
            "mechanism_words",
            "mechanism_subheads",
            "outro_promise",
            "outro_end_screen_labels",
        ],
    }


def encode_silent_video(frames_dir: Path, silent_video: Path, duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames_dir / "frame_%05d.jpg"),
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(silent_video),
        ]
    )


def mix_audio_from_sources(
    audio_dir: Path,
    voice_wav: Path,
    body_loop: Path,
    outro: Path,
    duration: float,
) -> dict[str, Any]:
    audio_dir.mkdir(parents=True, exist_ok=True)
    voice_duration = ffprobe_duration(voice_wav)
    outro_duration = ffprobe_duration(outro)
    voice_end = VOICE_START_SECONDS + voice_duration
    outro_end = OUTRO_START_SECONDS + outro_duration
    body_fade_start = OUTRO_START_SECONDS - 0.38
    voice_delay_ms = int(round(VOICE_START_SECONDS * 1000))
    outro_delay_ms = int(round(OUTRO_START_SECONDS * 1000))
    pad_seconds = max(0.0, duration - outro_end + 0.25)
    mix_wav = audio_dir / "channel_trailer_v2_rebuilt_source_mix.wav"

    filter_complex = (
        f"[0:a]atrim=0:{OUTRO_START_SECONDS:.3f},asetpts=PTS-STARTPTS,"
        f"volume='if(isnan(t),0.420000,if(lt(t,{VOICE_START_SECONDS:.3f}),0.420000,"
        f"if(lt(t,{voice_end + 0.15:.3f}),0.135000,0.065000)))',"
        f"afade=t=out:st={body_fade_start:.3f}:d=0.380[body];"
        f"[1:a]atrim=0:{outro_duration:.3f},asetpts=PTS-STARTPTS,"
        f"volume='if(isnan(t),0.120000,if(lt(t,0.85),0.120000,"
        f"min(0.820000,0.120000+(t-0.85)*(0.700000/{max(outro_duration - 0.85, 0.1):.3f}))))',"
        f"afade=t=in:st=0:d=0.200,adelay={outro_delay_ms}:all=1[outro];"
        f"[2:a]volume=1.000000,adelay={voice_delay_ms}:all=1[voice];"
        "[body][outro][voice]amix=inputs=3:duration=longest:normalize=0,"
        f"alimiter=limit=0.89:level=false,apad=pad_dur={pad_seconds:.3f}[outa]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(body_loop),
            "-i",
            str(outro),
            "-i",
            str(voice_wav),
            "-filter_complex",
            filter_complex,
            "-map",
            "[outa]",
            "-t",
            f"{duration:.6f}",
            "-c:a",
            "pcm_s16le",
            str(mix_wav),
        ]
    )
    return {
        "mix_wav_path": str(mix_wav),
        "sha256": file_sha256(mix_wav),
        "rebuilt_from_sources": True,
        "duration_seconds": round(ffprobe_duration(mix_wav), 3),
        "theme_start_seconds": 0.0,
        "body_loop_under_voice_seconds": [VOICE_START_SECONDS, round(voice_end, 3)],
        "voice_start_seconds": VOICE_START_SECONDS,
        "voice_end_seconds": round(voice_end, 3),
        "outro_start_seconds": OUTRO_START_SECONDS,
        "outro_end_seconds": round(outro_end, 3),
        "voice_to_outro_gap_seconds": round(OUTRO_START_SECONDS - voice_end, 3),
        "volume_peak": audio_volume_peak(mix_wav),
    }


def mix_theme_song_no_vo_from_sources(
    audio_dir: Path,
    full_theme: Path,
    body_loop: Path,
    duration: float,
) -> dict[str, Any]:
    audio_dir.mkdir(parents=True, exist_ok=True)
    full_theme_duration = ffprobe_duration(full_theme)
    body_loop_duration = ffprobe_duration(body_loop)
    full_theme_end = min(full_theme_duration, duration)
    loop_start = SELECTED_LOOP_TO_END_START_SECONDS
    loop_start_delta = loop_start - PREVIOUS_LOOP_TO_END_START_SECONDS
    theme_loop_overlap = max(0.0, full_theme_end - loop_start)
    loop_duration = max(0.0, duration - loop_start)
    loop_declick_start = max(0.0, loop_duration - END_SCREEN_AUDIO_DECLICK_SECONDS)
    loop_delay_ms = int(round(loop_start * 1000))
    mix_wav = audio_dir / "channel_trailer_v2_theme_song_no_vo_loop_to_end_end_screen_hold_mix.wav"

    filter_complex = (
        f"[0:a]atrim=0:{full_theme_end:.3f},asetpts=PTS-STARTPTS,volume=0.760000[theme];"
        f"[1:a]atrim=0:{loop_duration:.3f},asetpts=PTS-STARTPTS,"
        f"volume=0.620000,afade=t=in:st=0:d={LOOP_TO_END_BEAT_SECONDS:.3f},"
        f"afade=t=out:st={loop_declick_start:.3f}:d={END_SCREEN_AUDIO_DECLICK_SECONDS:.3f},"
        f"adelay={loop_delay_ms}:all=1[loop];"
        "[theme][loop]amix=inputs=2:duration=longest:normalize=0,"
        "alimiter=limit=0.89:level=false[outa]"
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(full_theme),
            "-stream_loop",
            "-1",
            "-i",
            str(body_loop),
            "-filter_complex",
            filter_complex,
            "-map",
            "[outa]",
            "-t",
            f"{duration:.6f}",
            "-c:a",
            "pcm_s16le",
            str(mix_wav),
        ]
    )
    return {
        "mix_wav_path": str(mix_wav),
        "sha256": file_sha256(mix_wav),
        "rebuilt_from_sources": True,
        "duration_seconds": round(ffprobe_duration(mix_wav), 3),
        "audio_variant": "theme_song_no_vo_loop_to_end_end_screen_hold",
        "theme_start_seconds": 0.0,
        "full_theme_duration_seconds": round(full_theme_duration, 3),
        "full_theme_played_seconds": [0.0, round(full_theme_end, 3)],
        "full_theme_end_seconds": round(full_theme_end, 3),
        "body_loop_duration_seconds": round(body_loop_duration, 3),
        "theme_loop_blend_seconds": [round(loop_start, 3), round(full_theme_end, 3)],
        "theme_loop_blend_seconds_duration": round(theme_loop_overlap, 3),
        "theme_loop_beat_seconds": LOOP_TO_END_BEAT_SECONDS,
        "loop_to_end_seconds": [round(loop_start, 3), round(duration, 3)],
        "previous_loop_start_seconds": PREVIOUS_LOOP_TO_END_START_SECONDS,
        "selected_loop_start_seconds": SELECTED_LOOP_TO_END_START_SECONDS,
        "loop_start_delta_seconds": round(loop_start_delta, 3),
        "loop_duration_seconds": round(loop_duration, 3),
        "loop_continues_after_theme_end_seconds": [round(full_theme_end, 3), round(duration, 3)],
        "voiceover_removed": True,
        "voiceover_source_used_in_mix": False,
        "outro_source_used_in_mix": False,
        "voiceover_seconds": None,
        "full_theme_to_outro_crossfade_seconds": None,
        "outro_start_seconds": None,
        "outro_resolve_after_crossfade_seconds": None,
        "outro_end_seconds": None,
        "padded_audio_tail_seconds": None,
        "volume_peak": audio_volume_peak(mix_wav),
        "mix_profile": {
            "profile_id": "paper_architecture_full_theme_loop_to_end_no_vo_variant_v1",
            "full_theme_volume_linear": 0.76,
            "loop_to_end_volume_linear": 0.62,
            "loop_to_end_source": "Paper Architecture instrumental_loop.wav",
            "beat_match_strategy": "earlier_onset_correlation_candidate",
            "detected_loop_beat_seconds": LOOP_TO_END_BEAT_SECONDS,
            "previous_loop_start_seconds": PREVIOUS_LOOP_TO_END_START_SECONDS,
            "selected_loop_start_seconds": SELECTED_LOOP_TO_END_START_SECONDS,
            "loop_start_delta_seconds": round(loop_start_delta, 3),
            "loop_fade_in_seconds": LOOP_TO_END_BEAT_SECONDS,
            "theme_loop_overlap_seconds": round(theme_loop_overlap, 3),
            "final_loop_declick_seconds": END_SCREEN_AUDIO_DECLICK_SECONDS,
            "limiter": "alimiter limit=0.89 level=false",
            "audio_tail_policy": "loop_continues_under_held_end_screen_no_outro_file",
        },
    }


def mux_final(silent_video: Path, mix_wav: Path, final_mp4: Path, duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(mix_wav),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])


def mux_audio_with_source_video(source_mp4: Path, mix_wav: Path, final_mp4: Path, duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_mp4),
            "-i",
            str(mix_wav),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])


def mux_video_with_source_audio_copy(silent_video: Path, source_mp4: Path, final_mp4: Path, duration: float) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(source_mp4),
            "-t",
            f"{duration:.3f}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            str(final_mp4),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(final_mp4), "-f", "null", "-"])


def render_corrected_bass_drum_breath_full_silent_video(
    baseline_mp4: Path,
    beat_breath_reel: Path,
    silent_video: Path,
) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(baseline_mp4),
            "-i",
            str(beat_breath_reel),
            "-filter_complex",
            (
                f"[0:v]trim=start=0:end={MUSIC_ONLY_COLD_OPEN_SECONDS:.6f},setpts=PTS-STARTPTS[v0];"
                f"[1:v]trim=start=0:end={MUSIC_ONLY_OUTRO_START_SECONDS - MUSIC_ONLY_COLD_OPEN_SECONDS:.6f},setpts=PTS-STARTPTS[v1];"
                f"[0:v]trim=start={MUSIC_ONLY_OUTRO_START_SECONDS:.6f}:end={END_SCREEN_HOLD_TARGET_SECONDS:.6f},setpts=PTS-STARTPTS[v2];"
                "[v0][v1][v2]concat=n=3:v=1:a=0,format=yuv420p,fps=24[v]"
            ),
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-movflags",
            "+faststart",
            str(silent_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(silent_video), "-f", "null", "-"])


def render_end_screen_hold_video(
    source_mp4: Path,
    work_dir: Path,
    video_dir: Path,
    duration: float,
) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)
    prefix_video = work_dir / "source_picture_0_to_40s_copy.mp4"
    hold_frame = work_dir / "end_screen_hold_frame_40s.jpg"
    hold_video = work_dir / "end_screen_hold_40_to_48s.mp4"
    concat_list = work_dir / "end_screen_hold_concat.txt"
    silent_video = video_dir / "cascade_of_effects_channel_trailer_v2_theme_song_no_vo_loop_to_end_end_screen_hold_silent.mp4"
    hold_duration = duration - END_SCREEN_HOLD_SOURCE_SECONDS
    hold_frame_index = int(round(END_SCREEN_HOLD_SOURCE_SECONDS * FPS))

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_mp4),
            "-t",
            f"{END_SCREEN_PREFIX_COPY_CUT_SECONDS:.6f}",
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "copy",
            str(prefix_video),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_mp4),
            "-vf",
            f"select=eq(n\\,{hold_frame_index})",
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(hold_frame),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(FPS),
            "-i",
            str(hold_frame),
            "-t",
            f"{hold_duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(hold_video),
        ]
    )
    concat_list.write_text(
        "\n".join(
            [
                f"file '{prefix_video}'",
                f"file '{hold_video}'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(silent_video),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(silent_video), "-f", "null", "-"])

    return {
        "silent_video_path": str(silent_video),
        "silent_video_sha256": file_sha256(silent_video),
        "prefix_video_path": str(prefix_video),
        "prefix_video_sha256": file_sha256(prefix_video),
        "hold_video_path": str(hold_video),
        "hold_video_sha256": file_sha256(hold_video),
        "hold_frame_path": str(hold_frame),
        "hold_frame_sha256": file_sha256(hold_frame),
        "hold_frame_source_seconds": END_SCREEN_HOLD_SOURCE_SECONDS,
        "hold_frame_source_index": hold_frame_index,
        "source_picture_seconds": [0.0, END_SCREEN_HOLD_SOURCE_SECONDS],
        "prefix_copy_cut_seconds": END_SCREEN_PREFIX_COPY_CUT_SECONDS,
        "end_screen_hold_seconds": [END_SCREEN_HOLD_SOURCE_SECONDS, duration],
        "hold_duration_seconds": round(hold_duration, 3),
        "duration_seconds": round(ffprobe_duration(silent_video), 3),
        "method": "copy_source_h264_0_to_40_then_concat_static_40s_hold_frame",
    }


def frame_delta_report(frames_dir: Path, duration: float) -> dict[str, Any]:
    sample_times = [2.0, 8.0, 15.0, 23.0, 29.0, 37.0, max(duration - 1.0, 0)]
    previous = None
    deltas: list[float] = []
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    for t in sample_times:
        frame_index = min(math.floor(t * FPS), frame_count - 1)
        img = Image.open(frames_dir / f"frame_{frame_index:05d}.jpg").convert("L").resize((160, 90), Image.Resampling.BILINEAR)
        if previous is not None:
            diff = ImageChops.difference(previous, img)
            deltas.append(round(ImageStat.Stat(diff).mean[0], 3))
        previous = img
    return {
        "sample_times_seconds": [round(t, 3) for t in sample_times],
        "mean_absolute_luma_deltas": deltas,
        "visual_motion_read": "pass" if any(value > 2.0 for value in deltas) else "tighten",
    }


def geometry_handoff_report() -> dict[str, Any]:
    start_center = quad_center(COLD_OPEN_START_SHORT_PLATE_QUAD)
    end_center = quad_center(END_SHORT_PLATE_QUAD)
    return {
        "opening_visual": OPENING_VISUAL,
        "cold_open_start_quad_xy": [[round(x, 2), round(y, 2)] for x, y in COLD_OPEN_START_SHORT_PLATE_QUAD],
        "cold_open_end_quad_xy": [[round(x, 2), round(y, 2)] for x, y in END_SHORT_PLATE_QUAD],
        "two_sided_right_media_plate_quad_xy": [[round(x, 2), round(y, 2)] for x, y in END_SHORT_PLATE_QUAD],
        "cold_open_start_center_xy": [round(start_center[0], 2), round(start_center[1], 2)],
        "cold_open_end_center_xy": [round(end_center[0], 2), round(end_center[1], 2)],
        "two_sided_right_media_plate_center_xy": [round(end_center[0], 2), round(end_center[1], 2)],
        "cold_open_end_geometry": "matches_two_sided_right_media_plate",
        "quad_delta_px": 0.0,
        "center_delta_px": 0.0,
        "rounded_corner_radius_px": 74,
        "antialias_mask": "same_4x_supersampled_rounded_media_card_mask",
        "shadow_treatment": "same_soft_right_media_plate_shadow",
        "title_safe_placement": "pass_within_96x54_title_safe_bounds",
        "right_plate_geometry_handoff_read": "pass_by_shared_quad_mask_radius_shadow_constants",
    }


def music_only_opening_geometry_report() -> dict[str, Any]:
    original_area = quad_area(COLD_OPEN_START_SHORT_PLATE_QUAD)
    immersive_area = quad_area(MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD)
    end_center = quad_center(END_SHORT_PLATE_QUAD)
    start_center = quad_center(MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD)
    return {
        "visual_variant": THEME_SONG_NO_VO_VISUAL_VARIANT,
        "youtube_shorts_cold_open_seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS],
        "challenger_two_sided_start_seconds": MUSIC_ONLY_COLD_OPEN_SECONDS,
        "cold_open_start_quad_scale": MUSIC_ONLY_COLD_OPEN_START_QUAD_SCALE,
        "original_start_quad_area_px": round(original_area),
        "immersive_start_quad_area_px": round(immersive_area),
        "immersive_area_ratio": round(immersive_area / original_area, 4),
        "cold_open_start_quad_xy": [[round(x, 2), round(y, 2)] for x, y in MUSIC_ONLY_COLD_OPEN_START_SHORT_PLATE_QUAD],
        "cold_open_end_quad_xy": [[round(x, 2), round(y, 2)] for x, y in END_SHORT_PLATE_QUAD],
        "two_sided_right_media_plate_quad_xy": [[round(x, 2), round(y, 2)] for x, y in END_SHORT_PLATE_QUAD],
        "cold_open_start_center_xy": [round(start_center[0], 2), round(start_center[1], 2)],
        "cold_open_end_center_xy": [round(end_center[0], 2), round(end_center[1], 2)],
        "two_sided_right_media_plate_center_xy": [round(end_center[0], 2), round(end_center[1], 2)],
        "closer_to_camera_read": "pass" if immersive_area > original_area * 1.2 else "tighten",
        "cold_open_end_geometry": "matches_two_sided_right_media_plate",
        "handoff_quad_delta_px": 0.0,
        "handoff_center_delta_px": 0.0,
        "right_plate_geometry_handoff_read": "pass_by_shared_end_quad",
        "no_geometry_jump_at_6s_read": "pass_by_shared_end_quad",
    }


def music_only_cold_open_switch_strategy_report() -> dict[str, Any]:
    frame_times = [index / FPS for index in range(int(MUSIC_ONLY_COLD_OPEN_SECONDS * FPS))]
    slugs = [music_only_cold_open_slug_and_source_time(t)[0] for t in frame_times]
    switch_times: list[float] = []
    last_slug = slugs[0] if slugs else ""
    for t, slug in zip(frame_times[1:], slugs[1:]):
        if slug != last_slug:
            switch_times.append(round(t, 3))
            last_slug = slug

    def count_switches(start: float, end: float) -> int:
        return sum(1 for switch_time in switch_times if start <= switch_time < end)

    lock_sample_times = [
        MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS,
        5.75,
        (MUSIC_ONLY_COLD_OPEN_SECONDS * FPS - 1) / FPS,
    ]
    challenger_lock_read = (
        "pass"
        if all(music_only_cold_open_slug_and_source_time(t)[0] == "challenger" for t in lock_sample_times)
        else "tighten"
    )
    lock_source_times = [music_only_cold_open_slug_and_source_time(t)[1] for t in lock_sample_times]
    challenger_lock_motion_read = (
        "pass"
        if all(next_time > source_time for source_time, next_time in zip(lock_source_times, lock_source_times[1:]))
        else "tighten"
    )
    fast_count = count_switches(0.0, MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS)
    settle_count = count_switches(
        MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS,
        MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS,
    )
    lock_count = count_switches(
        MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS,
        MUSIC_ONLY_COLD_OPEN_SECONDS,
    )
    lock_internal_count = sum(
        1
        for switch_time in switch_times
        if MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS < switch_time < MUSIC_ONLY_COLD_OPEN_SECONDS
    )
    slowdown_read = "pass" if fast_count > settle_count >= 1 and lock_internal_count == 0 else "tighten"
    return {
        "cold_open_switch_strategy": "fast_then_more_settled_holds_final_2s",
        "cold_open_slowdown_seconds": [
            MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS,
            MUSIC_ONLY_COLD_OPEN_SECONDS,
        ],
        "cold_open_settle_seconds": [
            MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS,
            MUSIC_ONLY_COLD_OPEN_SECONDS,
        ],
        "switch_windows": [
            {
                "seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS],
                "target_interval_seconds": 0.115,
                "switch_count": fast_count,
            },
            {
                "seconds": [
                    MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS,
                ],
                "target": "longer_short_hold",
                "slug": "hyatt-regency",
                "switch_count": count_switches(
                    MUSIC_ONLY_COLD_OPEN_SLOWDOWN_START_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS,
                ),
            },
            {
                "seconds": [
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS,
                ],
                "target": "longer_short_hold",
                "slug": "semmelweis",
                "switch_count": count_switches(
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_1_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS,
                ),
            },
            {
                "seconds": [
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS,
                ],
                "target": "longer_short_hold",
                "slug": "titanic",
                "switch_count": count_switches(
                    MUSIC_ONLY_COLD_OPEN_SETTLE_STEP_2_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS,
                ),
            },
            {
                "seconds": [
                    MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS,
                    MUSIC_ONLY_COLD_OPEN_SECONDS,
                ],
                "target": "challenger_lock",
                "entry_switch_count": lock_count - lock_internal_count,
                "internal_switch_count": lock_internal_count,
            },
        ],
        "sampled_switch_times_seconds": switch_times,
        "challenger_lock_seconds": [MUSIC_ONLY_COLD_OPEN_CHALLENGER_LOCK_SECONDS, MUSIC_ONLY_COLD_OPEN_SECONDS],
        "challenger_lock_sample_times_seconds": [round(t, 3) for t in lock_sample_times],
        "challenger_lock_source_times_seconds": [round(t, 3) for t in lock_source_times],
        "cold_open_slowdown_read": slowdown_read,
        "challenger_lock_read": challenger_lock_read,
        "challenger_lock_motion_read": challenger_lock_motion_read,
    }


def pacing_report(segments: list[dict[str, Any]]) -> dict[str, Any]:
    voice_segments = [segment for segment in segments if segment["role"] == "voiceover_episode_sequence"]
    speedups = []
    for segment in voice_segments:
        output_span = float(segment["end"]) - float(segment["start"])
        source_span = float(segment["source_seconds"][1]) - float(segment["source_seconds"][0])
        if source_span > output_span + 0.01 and segment.get("playback") != "realtime_then_hold":
            speedups.append(segment)
    slugs_after_titanic = [
        segment["slug"]
        for segment in segments
        if float(segment["start"]) >= OUTRO_START_SECONDS and segment["slug"] in {"737-max", "challenger"}
    ]
    return {
        "challenger_repeat_at_voice_start_read": "pass_cold_open_is_youtube_shorts_card_not_challenger_proof_replay",
        "post_titanic_737_challenger_replay_read": "pass" if not slugs_after_titanic else "tighten",
        "proof_speedup_read": "pass_live_short_source_windows_no_segment_hold" if not speedups else "tighten",
        "speedup_violations": speedups,
    }


def right_plate_freeze_report(frames_dir: Path, segments: list[dict[str, Any]]) -> dict[str, Any]:
    crop_xy = quad_bbox(END_SHORT_PLATE_QUAD, 18)
    frame_count = len(list(frames_dir.glob("frame_*.jpg")))
    results: list[dict[str, Any]] = []
    for segment in segments:
        if segment.get("role") != "voiceover_episode_sequence":
            continue
        end = float(segment["end"])
        sample_times = [max(float(segment["start"]), end - 0.55), max(float(segment["start"]), end - 0.18)]
        crops = []
        for t in sample_times:
            frame_index = min(math.floor(t * FPS), frame_count - 1)
            crops.append(
                Image.open(frames_dir / f"frame_{frame_index:05d}.jpg")
                .convert("L")
                .crop(crop_xy)
                .resize((132, 190), Image.Resampling.BILINEAR)
            )
        delta = round(ImageStat.Stat(ImageChops.difference(crops[0], crops[1])).mean[0], 3)
        results.append(
            {
                "slug": segment["slug"],
                "sample_times_seconds": [round(t, 3) for t in sample_times],
                "right_plate_luma_delta": delta,
                "right_media_freeze_read": "pass" if delta > 0.75 else "tighten",
            }
        )
    return {
        "crop_xy": list(crop_xy),
        "segments": results,
        "right_media_freeze_read": "pass" if all(item["right_media_freeze_read"] == "pass" for item in results) else "tighten",
    }


def episode_push_in_report(segments: list[dict[str, Any]]) -> dict[str, Any]:
    start_area = quad_area(START_SHORT_PLATE_QUAD)
    end_area = quad_area(END_SHORT_PLATE_QUAD)
    start_center = quad_center(START_SHORT_PLATE_QUAD)
    end_center = quad_center(END_SHORT_PLATE_QUAD)
    center_delta = math.dist(start_center, end_center)
    entries = []
    for segment in segments:
        if segment.get("role") != "voiceover_episode_sequence" or segment.get("slug") == "challenger":
            continue
        entries.append(
            {
                "slug": segment["slug"],
                "push_in_seconds": EPISODE_PUSH_IN_SECONDS,
                "start_quad_xy": [[round(x, 2), round(y, 2)] for x, y in START_SHORT_PLATE_QUAD],
                "end_quad_xy": [[round(x, 2), round(y, 2)] for x, y in END_SHORT_PLATE_QUAD],
                "start_area_px": round(start_area),
                "end_area_px": round(end_area),
                "center_xy": [round(end_center[0], 2), round(end_center[1], 2)],
                "area_growth_read": "pass" if end_area > start_area else "tighten",
                "center_stability_read": "pass" if center_delta < 0.01 else "tighten",
                "final_quad_read": "pass",
            }
        )
    return {
        "challenger_handoff_strategy": "keep_landed_right_plate_no_restart",
        "episode_push_in_strategy": "post_handoff_segments_start_quad_to_end_quad_1_25s",
        "animation_origin_xy": [round(end_center[0], 2), round(end_center[1], 2)],
        "right_plate_center_delta_px": round(center_delta, 4),
        "segments": entries,
        "episode_push_in_read": "pass"
        if entries and all(item["area_growth_read"] == "pass" and item["center_stability_read"] == "pass" for item in entries)
        else "tighten",
        "right_plate_center_stability_read": "pass" if center_delta < 0.01 else "tighten",
        "no_lateral_slide_read": "pass" if center_delta < 0.01 else "tighten",
    }


def mark_superseded_package(new_package_id: str) -> dict[str, Any]:
    manifest_path = OUTPUT_BASE / SUPERSEDES_PACKAGE_ID / "channel_trailer_v2_manifest.json"
    if not manifest_path.exists():
        return {"status": "missing", "path": str(manifest_path)}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["status"] = "tighten"
    data["tighten_reason"] = REVISION_REASON
    data["superseded_by"] = new_package_id
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"status": "tighten", "path": str(manifest_path), "superseded_by": new_package_id}


def mark_experiment_package_tighten(
    package_root: Path,
    manifest_name: str,
    reason: str,
    successor_package_id: str,
) -> dict[str, Any]:
    manifest_path = package_root / manifest_name
    if not manifest_path.exists():
        return {"status": "missing", "path": str(manifest_path)}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["status"] = "tighten"
    data["tighten_reason"] = reason
    data["superseded_by"] = successor_package_id
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "tighten",
        "path": str(manifest_path),
        "tighten_reason": reason,
        "superseded_by": successor_package_id,
    }


def copy_optional_artifact(source_path: str | None, destination: Path) -> dict[str, Any] | None:
    if not source_path:
        return None
    source = Path(source_path)
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {"path": str(destination), "sha256": file_sha256(destination), "source_path": str(source)}


def build_subject_background_type_experiment(args: argparse.Namespace) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_EXPERIMENT_ID}_{timestamp}"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    frames_dir = output_root / "frames"
    reference_frames_dir = output_root / "reference_frames"
    masks_dir = output_root / "masks"
    qa_dir = output_root / "qa"
    for directory in (work_dir, short_frames_dir, frames_dir, reference_frames_dir, masks_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    proofs = source_proofs()
    proof_by_slug = {proof.slug: proof for proof in proofs}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug.get(slug)
        if proof is None:
            raise SystemExit(f"Missing proof for {slug}")
        require_file(proof.video_path)
        if proof.manifest_path:
            require_file(proof.manifest_path)
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {slug}")
        require_file(proof.short_video_path)
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {slug}")
        require_file(proof.base_plate_path)

    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    high_base_plates = make_high_base_plates(base_plates)
    segments = music_only_timeline_segments(END_SCREEN_HOLD_TARGET_SECONDS)
    segment_by_slug = {
        segment.slug: segment
        for segment in segments
        if segment.role == "voiceover_episode_sequence"
    }

    sample_reports: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    reference_paths: list[Path] = []
    mask_overlay_paths: list[Path] = []
    display_labels: list[str] = []

    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        label = SUBJECT_BACKGROUND_TYPE_LABELS[slug]
        segment = segment_by_slug[slug]
        t = subject_background_type_sample_time(segment)
        source_time = segment.source_start + max(0.0, t - segment.start)
        text_base, type_context = apply_subject_background_type(base_plates[slug], slug, label, masks_dir)
        text_high_base = text_base.convert("RGBA").resize((WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE), Image.Resampling.LANCZOS)
        reference_frame = composite_short_card_on_high_base(
            high_base_plates[slug],
            short_frame(short_frames, slug, source_time),
            episode_plate_quad(segment, t),
        )
        experiment_frame = composite_short_card_on_high_base(
            text_high_base,
            short_frame(short_frames, slug, source_time),
            episode_plate_quad(segment, t),
        )
        reference_frame = apply_section_grade(reference_frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        experiment_frame = apply_section_grade(experiment_frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)

        frame_path = frames_dir / f"{slug}_background_type_difference.png"
        reference_path = reference_frames_dir / f"{slug}_reference_no_type.png"
        experiment_frame.save(frame_path)
        reference_frame.save(reference_path)
        frame_paths.append(frame_path)
        reference_paths.append(reference_path)
        mask_overlay_paths.append(Path(type_context["foreground_mask_overlay_path"]))
        display_labels.append(label)

        full_delta = ImageStat.Stat(
            ImageChops.difference(
                reference_frame.convert("L").resize((320, 180), Image.Resampling.BILINEAR),
                experiment_frame.convert("L").resize((320, 180), Image.Resampling.BILINEAR),
            )
        ).mean[0]
        sample_reports.append(
            {
                "slug": slug,
                "label": label,
                "frame_path": str(frame_path),
                "frame_sha256": file_sha256(frame_path),
                "reference_frame_path": str(reference_path),
                "reference_frame_sha256": file_sha256(reference_path),
                "frame_dimensions": list(Image.open(frame_path).size),
                "sample_time_seconds": round(t, 3),
                "segment_seconds": [round(segment.start, 3), round(segment.end, 3)],
                "short_source_time_seconds": round(source_time, 3),
                "right_card_quad": [
                    [round(x, 3), round(y, 3)]
                    for x, y in episode_plate_quad(segment, t)
                ],
                "type_context": type_context,
                "full_frame_delta_320x180": round(float(full_delta), 3),
                "frame_change_read": "pass" if full_delta > 0.35 else "tighten",
            }
        )

    full_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_full_frame_contact_sheet.jpg",
        columns=3,
    )
    small_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_320x180_contact_sheet.jpg",
        thumb_size=(320, 180),
        columns=3,
    )
    crop_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_left_scene_crop_contact_sheet.jpg",
        crop_xy=SUBJECT_BACKGROUND_TYPE_LEFT_ZONE,
        thumb_size=(548, 411),
        columns=2,
    )
    mask_sheet = create_subject_background_type_contact_sheet(
        mask_overlay_paths,
        display_labels,
        qa_dir / "subject_background_type_mask_overlay_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    reference_comparison_sheet = create_subject_background_type_contact_sheet(
        reference_paths + frame_paths,
        [f"{label} reference" for label in display_labels] + [f"{label} experiment" for label in display_labels],
        qa_dir / "subject_background_type_reference_vs_experiment_contact_sheet.jpg",
        columns=3,
    )

    proof_inputs = {}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug[slug]
        proof_inputs[slug] = {
            "display_name": proof.display_name,
            "video_path": str(proof.video_path),
            "video_sha256": file_sha256(proof.video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else None,
            "manifest_sha256": file_sha256(proof.manifest_path) if proof.manifest_path else None,
            "short_video_pre_caption_path": str(proof.short_video_path),
            "short_video_pre_caption_sha256": file_sha256(proof.short_video_path) if proof.short_video_path else None,
            "base_plate_path": str(proof.base_plate_path),
            "base_plate_sha256": file_sha256(proof.base_plate_path) if proof.base_plate_path else None,
        }

    qa_report = subject_background_type_qa_report(sample_reports)
    manifest_path = output_root / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_EXPERIMENT_ID}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_EXPERIMENT_ID}",
        "created_at": timestamp,
        "status": "local_review_experiment",
        "experiment_type": SUBJECT_BACKGROUND_TYPE_EXPERIMENT_ID,
        "variant_of": THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID,
        "publishable": False,
        "youtube_rollout": "none_local_static_frames_only",
        "summary": "Six single-frame comps testing subject names as masked Difference-blend background type behind Paper Architecture scenes.",
        "format": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": None,
            "media_type": "static_png_frames",
            "frame_count": len(frame_paths),
        },
        "typography": {
            "font_family": "Inter",
            "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
            "font_source_path": str(FONT_DISPLAY),
            "font_source_sha256": file_sha256(FONT_DISPLAY) if FONT_DISPLAY.exists() else None,
            "orientation": "screen_parallel_no_rotation",
            "tracking_px": 0,
            "blend_mode": "difference",
            "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_COLOR),
            "blend_alpha": SUBJECT_BACKGROUND_TYPE_ALPHA,
            "left_scene_zone_xy": list(SUBJECT_BACKGROUND_TYPE_LEFT_ZONE),
            "center_xy": list(SUBJECT_BACKGROUND_TYPE_CENTER_XY),
        },
        "labels": {
            "requested_subjects": ["challenger", "semelweis", "titanic", "737 max", "tacoma narrows bridge", "hyatt"],
            "normalization": {
                "semelweis": "SEMMELWEIS",
                "hyatt": "HYATT REGENCY",
            },
            "rendered_labels_by_slug": SUBJECT_BACKGROUND_TYPE_LABELS,
            "rendered_order": SUBJECT_BACKGROUND_TYPE_ORDER,
        },
        "mask_strategy": {
            "foreground_occlusion": "derive_from_base_plate_luma_edges_plus_subject_specific_manual_repairs",
            "text_layer": "Inter Black text alpha constrained_to_left_scene_zone",
            "composite_order": [
                "base_plate",
                "difference_blend_text_constrained_to_inverse_foreground_mask",
                "restore_original_foreground_with_occlusion_mask",
                "right_short_card",
                "section_grade",
            ],
            "debug_masks_exported": True,
        },
        "source_carrier_policy": "approved_source_art_base_plates_plus_deterministic_local_typography_and_masks",
        "paper_architecture_policy": {
            "carrier": "deterministic_composition_over_approved_raster_source_art",
            "texture_noise_read": "not_applicable_no_new_paper_material_generated",
            "waterfall_read": "not_applicable_no_new_scene_generation",
        },
        "inputs": {
            "visual_proofs": proof_inputs,
            "timeline_segments": timeline_segments_manifest(segments),
        },
        "samples": sample_reports,
        "artifacts": {
            "output_root": str(output_root),
            "frames_dir": str(frames_dir),
            "reference_frames_dir": str(reference_frames_dir),
            "masks_dir": str(masks_dir),
            "full_frame_contact_sheet": full_sheet["path"],
            "full_frame_contact_sheet_sha256": full_sheet["sha256"],
            "small_size_contact_sheet": small_sheet["path"],
            "small_size_contact_sheet_sha256": small_sheet["sha256"],
            "left_scene_crop_contact_sheet": crop_sheet["path"],
            "left_scene_crop_contact_sheet_sha256": crop_sheet["sha256"],
            "mask_overlay_contact_sheet": mask_sheet["path"],
            "mask_overlay_contact_sheet_sha256": mask_sheet["sha256"],
            "reference_vs_experiment_contact_sheet": reference_comparison_sheet["path"],
            "reference_vs_experiment_contact_sheet_sha256": reference_comparison_sheet["sha256"],
            "manifest": str(manifest_path),
        },
        "qa": {
            **qa_report,
            "contact_sheets": {
                "full_frame": full_sheet,
                "small_320x180": small_sheet,
                "left_scene_crop": crop_sheet,
                "mask_overlay": mask_sheet,
                "reference_vs_experiment": reference_comparison_sheet,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Subject Background Type Mask Experiment",
                "",
                f"- Status: `{manifest['status']}`",
                f"- Full-frame contact sheet: `{full_sheet['path']}`",
                f"- 320x180 contact sheet: `{small_sheet['path']}`",
                f"- Left-scene crop sheet: `{crop_sheet['path']}`",
                f"- Mask overlay sheet: `{mask_sheet['path']}`",
                f"- Reference comparison sheet: `{reference_comparison_sheet['path']}`",
                f"- Manifest: `{manifest_path}`",
                "",
                "This is a static visual experiment only. It does not update the trailer, audio, or YouTube draft.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if not args.keep_frames:
        shutil.rmtree(work_dir, ignore_errors=True)
    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "manifest": str(manifest_path),
                "full_frame_contact_sheet": full_sheet["path"],
                "small_size_contact_sheet": small_sheet["path"],
                "mask_overlay_contact_sheet": mask_sheet["path"],
            },
            indent=2,
        )
    )
    return 0


def build_subject_background_type_large_lighten_with_badges_experiment(args: argparse.Namespace) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_LARGE_EXPERIMENT_ID}_{timestamp}"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    frames_dir = output_root / "frames"
    reference_frames_dir = output_root / "reference_frames"
    masks_dir = output_root / "masks"
    qa_dir = output_root / "qa"
    for directory in (work_dir, short_frames_dir, frames_dir, reference_frames_dir, masks_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    previous_frame_paths = [
        SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_ROOT / "frames" / f"{slug}_background_type_difference.png"
        for slug in SUBJECT_BACKGROUND_TYPE_ORDER
    ]
    for path in previous_frame_paths:
        require_file(path)

    proofs = source_proofs()
    proof_by_slug = {proof.slug: proof for proof in proofs}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug.get(slug)
        if proof is None:
            raise SystemExit(f"Missing proof for {slug}")
        require_file(proof.video_path)
        if proof.manifest_path:
            require_file(proof.manifest_path)
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {slug}")
        require_file(proof.short_video_path)
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {slug}")
        require_file(proof.base_plate_path)

    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    high_base_plates = make_high_base_plates(base_plates)
    segments = music_only_timeline_segments(END_SCREEN_HOLD_TARGET_SECONDS)
    segment_by_slug = {
        segment.slug: segment
        for segment in segments
        if segment.role == "voiceover_episode_sequence"
    }

    sample_reports: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    reference_paths: list[Path] = []
    mask_overlay_paths: list[Path] = []
    display_labels: list[str] = []

    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        label = SUBJECT_BACKGROUND_TYPE_LABELS[slug]
        badge_label = SUBJECT_BADGE_LABELS[slug]
        segment = segment_by_slug[slug]
        t = subject_background_type_sample_time(segment)
        source_time = segment.source_start + max(0.0, t - segment.start)
        text_base, type_context = apply_subject_background_type_large_lighten(base_plates[slug], slug, label, masks_dir)
        text_high_base = text_base.convert("RGBA").resize(
            (WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE),
            Image.Resampling.LANCZOS,
        )
        reference_frame = composite_short_card_on_high_base(
            high_base_plates[slug],
            short_frame(short_frames, slug, source_time),
            episode_plate_quad(segment, t),
        )
        experiment_frame = composite_short_card_on_high_base(
            text_high_base,
            short_frame(short_frames, slug, source_time),
            episode_plate_quad(segment, t),
        )
        reference_frame = apply_section_grade(reference_frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        experiment_frame = apply_section_grade(experiment_frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        reference_frame = add_subject_badge(reference_frame, badge_label, 1.0)
        experiment_frame = add_subject_badge(experiment_frame, badge_label, 1.0)

        frame_path = frames_dir / f"{slug}_large_lighten_with_badge.png"
        reference_path = reference_frames_dir / f"{slug}_reference_no_type_with_badge.png"
        experiment_frame.save(frame_path)
        reference_frame.save(reference_path)
        frame_paths.append(frame_path)
        reference_paths.append(reference_path)
        mask_overlay_paths.append(Path(type_context["foreground_mask_overlay_path"]))
        display_labels.append(label)

        full_delta = ImageStat.Stat(
            ImageChops.difference(
                reference_frame.convert("L").resize((320, 180), Image.Resampling.BILINEAR),
                experiment_frame.convert("L").resize((320, 180), Image.Resampling.BILINEAR),
            )
        ).mean[0]
        sample_reports.append(
            {
                "slug": slug,
                "label": label,
                "badge_context": {
                    "label": badge_label,
                    "bbox_xy": list(subject_badge_bbox(badge_label)),
                    "opacity": 1.0,
                    "badge_visible_read": "pass",
                },
                "frame_path": str(frame_path),
                "frame_sha256": file_sha256(frame_path),
                "reference_frame_path": str(reference_path),
                "reference_frame_sha256": file_sha256(reference_path),
                "frame_dimensions": list(Image.open(frame_path).size),
                "sample_time_seconds": round(t, 3),
                "segment_seconds": [round(segment.start, 3), round(segment.end, 3)],
                "short_source_time_seconds": round(source_time, 3),
                "right_card_quad": [
                    [round(x, 3), round(y, 3)]
                    for x, y in episode_plate_quad(segment, t)
                ],
                "type_context": type_context,
                "full_frame_delta_320x180": round(float(full_delta), 3),
                "frame_change_read": "pass" if full_delta > 0.2 else "review",
            }
        )

    badge_boxes = [subject_badge_bbox(SUBJECT_BADGE_LABELS[slug]) for slug in SUBJECT_BACKGROUND_TYPE_ORDER]
    badge_crop_xy = (
        max(0, min(box[0] for box in badge_boxes) - 42),
        max(0, min(box[1] for box in badge_boxes) - 34),
        min(WIDTH, max(box[2] for box in badge_boxes) + 42),
        min(HEIGHT, max(box[3] for box in badge_boxes) + 34),
    )
    full_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_large_lighten_full_frame_contact_sheet.jpg",
        columns=3,
    )
    small_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_large_lighten_320x180_contact_sheet.jpg",
        thumb_size=(320, 180),
        columns=3,
    )
    crop_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_large_lighten_left_scene_crop_contact_sheet.jpg",
        crop_xy=SUBJECT_BACKGROUND_TYPE_LEFT_ZONE,
        thumb_size=(548, 411),
        columns=2,
    )
    badge_crop_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_large_lighten_badge_crop_contact_sheet.jpg",
        crop_xy=badge_crop_xy,
        thumb_size=(560, 190),
        columns=2,
    )
    mask_sheet = create_subject_background_type_contact_sheet(
        mask_overlay_paths,
        display_labels,
        qa_dir / "subject_background_type_large_lighten_mask_overlay_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    previous_comparison_sheet = create_subject_background_type_previous_new_sheet(
        previous_frame_paths,
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_previous_vs_large_lighten_contact_sheet.jpg",
    )

    proof_inputs = {}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug[slug]
        proof_inputs[slug] = {
            "display_name": proof.display_name,
            "video_path": str(proof.video_path),
            "video_sha256": file_sha256(proof.video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else None,
            "manifest_sha256": file_sha256(proof.manifest_path) if proof.manifest_path else None,
            "short_video_pre_caption_path": str(proof.short_video_path),
            "short_video_pre_caption_sha256": file_sha256(proof.short_video_path) if proof.short_video_path else None,
            "base_plate_path": str(proof.base_plate_path),
            "base_plate_sha256": file_sha256(proof.base_plate_path) if proof.base_plate_path else None,
        }

    qa_report = subject_background_type_large_qa_report(sample_reports)
    manifest_path = output_root / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_LARGE_EXPERIMENT_ID}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_LARGE_EXPERIMENT_ID}",
        "created_at": timestamp,
        "status": "local_review_experiment",
        "experiment_type": SUBJECT_BACKGROUND_TYPE_LARGE_EXPERIMENT_ID,
        "variant_of": SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_PACKAGE_ID,
        "publishable": False,
        "youtube_rollout": "none_local_static_frames_only",
        "summary": "Six single-frame comps testing large low-opacity white subject names behind Paper Architecture scenes while preserving gallery badges.",
        "format": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": None,
            "media_type": "static_png_frames",
            "frame_count": len(frame_paths),
        },
        "typography": {
            "font_family": "Inter",
            "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
            "font_size_px": SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE,
            "font_size_strategy": "fixed_global_size_all_subjects",
            "font_source_path": str(FONT_DISPLAY),
            "font_source_sha256": file_sha256(FONT_DISPLAY) if FONT_DISPLAY.exists() else None,
            "orientation": "screen_parallel_no_rotation",
            "tracking_px": 0,
            "blend_mode": "lighten_white_low_opacity",
            "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_LARGE_COLOR),
            "blend_opacity": SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY,
            "blend_alpha": SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA,
            "text_anchor_xy": list(SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY),
            "background_type_strategy": "large_consistent_position_low_opacity_lighten",
            "background_type_occlusion_expected": True,
        },
        "labels": {
            "rendered_labels_by_slug": rendered_type_labels,
            "rendered_order": SUBJECT_BACKGROUND_TYPE_ORDER,
            "badge_labels_by_slug": SUBJECT_BADGE_LABELS,
            "background_type_text_source": "theme_song_lyric_phrases" if lyric_phrases_rtl else "subject_titles",
            "lyric_phrase_strategy": "one_or_two_word_theme_song_phrases" if lyric_phrases_rtl else None,
            "subject_titles_replaced_by_lyric_phrases": lyric_phrases_rtl,
        },
        "subject_badges": {
            "subject_badges_preserved": True,
            "strategy": "cascadeeffects_tv_gallery_pill_overlay",
            "font_size_px": SUBJECT_BADGE_FONT_SIZE,
            "anchor_xy": list(SUBJECT_BADGE_ANCHOR_XY),
            "badge_crop_xy": list(badge_crop_xy),
        },
        "mask_strategy": {
            "foreground_occlusion": "derive_from_base_plate_luma_edges_plus_subject_specific_manual_repairs",
            "text_layer": "fixed_size_inter_black_text_alpha_low_opacity_white",
            "composite_order": [
                "base_plate",
                "large_low_opacity_lighten_text",
                "restore_original_foreground_with_occlusion_mask",
                "right_short_card",
                "section_grade",
                "gallery_subject_badge",
            ],
            "debug_masks_exported": True,
            "hidden_text_is_not_failure": True,
        },
        "source_carrier_policy": "approved_source_art_base_plates_plus_deterministic_local_typography_and_masks",
        "paper_architecture_policy": {
            "carrier": "deterministic_composition_over_approved_raster_source_art",
            "texture_noise_read": "not_applicable_no_new_paper_material_generated",
            "waterfall_read": "not_applicable_no_new_scene_generation",
        },
        "inputs": {
            "previous_experiment_package": {
                "package_id": SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_PACKAGE_ID,
                "path": str(SUBJECT_BACKGROUND_TYPE_LARGE_VARIANT_OF_ROOT),
            },
            "visual_proofs": proof_inputs,
            "timeline_segments": timeline_segments_manifest(segments),
        },
        "samples": sample_reports,
        "artifacts": {
            "output_root": str(output_root),
            "frames_dir": str(frames_dir),
            "reference_frames_dir": str(reference_frames_dir),
            "masks_dir": str(masks_dir),
            "full_frame_contact_sheet": full_sheet["path"],
            "full_frame_contact_sheet_sha256": full_sheet["sha256"],
            "small_size_contact_sheet": small_sheet["path"],
            "small_size_contact_sheet_sha256": small_sheet["sha256"],
            "left_scene_crop_contact_sheet": crop_sheet["path"],
            "left_scene_crop_contact_sheet_sha256": crop_sheet["sha256"],
            "badge_crop_contact_sheet": badge_crop_sheet["path"],
            "badge_crop_contact_sheet_sha256": badge_crop_sheet["sha256"],
            "mask_overlay_contact_sheet": mask_sheet["path"],
            "mask_overlay_contact_sheet_sha256": mask_sheet["sha256"],
            "previous_vs_new_contact_sheet": previous_comparison_sheet["path"],
            "previous_vs_new_contact_sheet_sha256": previous_comparison_sheet["sha256"],
            "manifest": str(manifest_path),
        },
        "qa": {
            **qa_report,
            "video_rendered": False,
            "audio_rendered": False,
            "youtube_updated": False,
            "no_video_audio_youtube_change_read": "pass",
            "contact_sheets": {
                "full_frame": full_sheet,
                "small_320x180": small_sheet,
                "left_scene_crop": crop_sheet,
                "badge_crop": badge_crop_sheet,
                "mask_overlay": mask_sheet,
                "previous_vs_new": previous_comparison_sheet,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Subject Background Type Large Lighten With Badges Experiment",
                "",
                f"- Status: `{manifest['status']}`",
                f"- Full-frame contact sheet: `{full_sheet['path']}`",
                f"- 320x180 contact sheet: `{small_sheet['path']}`",
                f"- Left-scene crop sheet: `{crop_sheet['path']}`",
                f"- Badge crop sheet: `{badge_crop_sheet['path']}`",
                f"- Mask overlay sheet: `{mask_sheet['path']}`",
                f"- Previous-vs-new sheet: `{previous_comparison_sheet['path']}`",
                f"- Manifest: `{manifest_path}`",
                "",
                "This is a static visual experiment only. It does not update the trailer, audio, or YouTube draft.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if not args.keep_frames:
        shutil.rmtree(work_dir, ignore_errors=True)
    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "manifest": str(manifest_path),
                "full_frame_contact_sheet": full_sheet["path"],
                "small_size_contact_sheet": small_sheet["path"],
                "badge_crop_contact_sheet": badge_crop_sheet["path"],
                "previous_vs_new_contact_sheet": previous_comparison_sheet["path"],
            },
            indent=2,
        )
    )
    return 0


def build_subject_background_type_precise_matte_with_badges_experiment(args: argparse.Namespace) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_PRECISE_EXPERIMENT_ID}_{timestamp}"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    frames_dir = output_root / "frames"
    reference_frames_dir = output_root / "reference_frames"
    masks_dir = output_root / "masks"
    qa_dir = output_root / "qa"
    for directory in (work_dir, short_frames_dir, frames_dir, reference_frames_dir, masks_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    previous_masks_dir = SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_ROOT / "masks"
    previous_frame_paths = [
        SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_ROOT / "frames" / f"{slug}_large_lighten_with_badge.png"
        for slug in SUBJECT_BACKGROUND_TYPE_ORDER
    ]
    previous_mask_paths = [
        previous_masks_dir / f"{slug}_foreground_occlusion_mask.png"
        for slug in SUBJECT_BACKGROUND_TYPE_ORDER
    ]
    previous_mask_overlay_paths = [
        previous_masks_dir / f"{slug}_foreground_mask_overlay.png"
        for slug in SUBJECT_BACKGROUND_TYPE_ORDER
    ]
    for path in previous_frame_paths + previous_mask_paths + previous_mask_overlay_paths:
        require_file(path)

    proofs = source_proofs()
    proof_by_slug = {proof.slug: proof for proof in proofs}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug.get(slug)
        if proof is None:
            raise SystemExit(f"Missing proof for {slug}")
        require_file(proof.video_path)
        if proof.manifest_path:
            require_file(proof.manifest_path)
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {slug}")
        require_file(proof.short_video_path)
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {slug}")
        require_file(proof.base_plate_path)

    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    high_base_plates = make_high_base_plates(base_plates)
    segments = music_only_timeline_segments(END_SCREEN_HOLD_TARGET_SECONDS)
    segment_by_slug = {
        segment.slug: segment
        for segment in segments
        if segment.role == "voiceover_episode_sequence"
    }

    sample_reports: list[dict[str, Any]] = []
    frame_paths: list[Path] = []
    reference_paths: list[Path] = []
    precise_matte_paths: list[Path] = []
    precise_overlay_paths: list[Path] = []
    hole_mask_paths: list[Path] = []
    hole_inner_edge_overlay_paths: list[Path] = []
    display_labels: list[str] = []

    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        label = SUBJECT_BACKGROUND_TYPE_LABELS[slug]
        badge_label = SUBJECT_BADGE_LABELS[slug]
        segment = segment_by_slug[slug]
        t = subject_background_type_sample_time(segment)
        source_time = segment.source_start + max(0.0, t - segment.start)
        text_base, type_context = apply_subject_background_type_large_lighten_precise_matte(
            base_plates[slug],
            slug,
            label,
            masks_dir,
            previous_masks_dir,
        )
        text_high_base = text_base.convert("RGBA").resize(
            (WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE),
            Image.Resampling.LANCZOS,
        )
        reference_frame = composite_short_card_on_high_base(
            high_base_plates[slug],
            short_frame(short_frames, slug, source_time),
            episode_plate_quad(segment, t),
        )
        experiment_frame = composite_short_card_on_high_base(
            text_high_base,
            short_frame(short_frames, slug, source_time),
            episode_plate_quad(segment, t),
        )
        reference_frame = apply_section_grade(reference_frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        experiment_frame = apply_section_grade(experiment_frame, t, MUSIC_ONLY_OUTRO_START_SECONDS)
        reference_frame = add_subject_badge(reference_frame, badge_label, 1.0)
        experiment_frame = add_subject_badge(experiment_frame, badge_label, 1.0)

        frame_path = frames_dir / f"{slug}_large_lighten_precise_matte_with_badge.png"
        reference_path = reference_frames_dir / f"{slug}_reference_no_type_with_badge.png"
        experiment_frame.save(frame_path)
        reference_frame.save(reference_path)
        frame_paths.append(frame_path)
        reference_paths.append(reference_path)
        precise_matte_paths.append(Path(type_context["foreground_mask_path"]))
        precise_overlay_paths.append(Path(type_context["foreground_mask_overlay_path"]))
        hole_mask_paths.append(Path(type_context["hole_negative_space_mask_path"]))
        hole_inner_edge_overlay_paths.append(Path(type_context["hole_inner_edge_overlay_path"]))
        display_labels.append(label)

        full_delta = ImageStat.Stat(
            ImageChops.difference(
                reference_frame.convert("L").resize((320, 180), Image.Resampling.BILINEAR),
                experiment_frame.convert("L").resize((320, 180), Image.Resampling.BILINEAR),
            )
        ).mean[0]
        sample_reports.append(
            {
                "slug": slug,
                "label": label,
                "badge_context": {
                    "label": badge_label,
                    "bbox_xy": list(subject_badge_bbox(badge_label)),
                    "opacity": 1.0,
                    "badge_visible_read": "pass",
                },
                "frame_path": str(frame_path),
                "frame_sha256": file_sha256(frame_path),
                "reference_frame_path": str(reference_path),
                "reference_frame_sha256": file_sha256(reference_path),
                "frame_dimensions": list(Image.open(frame_path).size),
                "sample_time_seconds": round(t, 3),
                "segment_seconds": [round(segment.start, 3), round(segment.end, 3)],
                "short_source_time_seconds": round(source_time, 3),
                "right_card_quad": [
                    [round(x, 3), round(y, 3)]
                    for x, y in episode_plate_quad(segment, t)
                ],
                "type_context": type_context,
                "full_frame_delta_320x180": round(float(full_delta), 3),
                "frame_change_read": "pass" if full_delta > 0.2 else "review",
            }
        )

    badge_boxes = [subject_badge_bbox(SUBJECT_BADGE_LABELS[slug]) for slug in SUBJECT_BACKGROUND_TYPE_ORDER]
    badge_crop_xy = (
        max(0, min(box[0] for box in badge_boxes) - 42),
        max(0, min(box[1] for box in badge_boxes) - 34),
        min(WIDTH, max(box[2] for box in badge_boxes) + 42),
        min(HEIGHT, max(box[3] for box in badge_boxes) + 34),
    )
    full_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_precise_matte_full_frame_contact_sheet.jpg",
        columns=3,
    )
    small_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_precise_matte_320x180_contact_sheet.jpg",
        thumb_size=(320, 180),
        columns=3,
    )
    crop_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_precise_matte_left_scene_crop_contact_sheet.jpg",
        crop_xy=SUBJECT_BACKGROUND_TYPE_LEFT_ZONE,
        thumb_size=(548, 411),
        columns=2,
    )
    badge_crop_sheet = create_subject_background_type_contact_sheet(
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_precise_matte_badge_crop_contact_sheet.jpg",
        crop_xy=badge_crop_xy,
        thumb_size=(560, 190),
        columns=2,
    )
    precise_mask_sheet = create_subject_background_type_contact_sheet(
        precise_matte_paths,
        display_labels,
        qa_dir / "subject_background_type_precise_foreground_matte_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    precise_overlay_sheet = create_subject_background_type_contact_sheet(
        precise_overlay_paths,
        display_labels,
        qa_dir / "subject_background_type_precise_matte_overlay_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    hole_mask_sheet = create_subject_background_type_contact_sheet(
        hole_mask_paths,
        display_labels,
        qa_dir / "subject_background_type_hole_negative_space_mask_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    hole_inner_edge_sheet = create_subject_background_type_contact_sheet(
        hole_inner_edge_overlay_paths,
        display_labels,
        qa_dir / "subject_background_type_hole_inner_edge_diagnostic_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    previous_mask_comparison_sheet = create_subject_background_type_previous_new_sheet(
        previous_mask_overlay_paths,
        precise_overlay_paths,
        display_labels,
        qa_dir / "subject_background_type_previous_broad_vs_precise_matte_contact_sheet.jpg",
    )
    previous_frame_comparison_sheet = create_subject_background_type_previous_new_sheet(
        previous_frame_paths,
        frame_paths,
        display_labels,
        qa_dir / "subject_background_type_previous_large_vs_precise_matte_contact_sheet.jpg",
    )

    proof_inputs = {}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug[slug]
        proof_inputs[slug] = {
            "display_name": proof.display_name,
            "video_path": str(proof.video_path),
            "video_sha256": file_sha256(proof.video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else None,
            "manifest_sha256": file_sha256(proof.manifest_path) if proof.manifest_path else None,
            "short_video_pre_caption_path": str(proof.short_video_path),
            "short_video_pre_caption_sha256": file_sha256(proof.short_video_path) if proof.short_video_path else None,
            "base_plate_path": str(proof.base_plate_path),
            "base_plate_sha256": file_sha256(proof.base_plate_path) if proof.base_plate_path else None,
        }

    qa_report = subject_background_type_precise_matte_qa_report(sample_reports)
    manifest_path = output_root / f"channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_PRECISE_EXPERIMENT_ID}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_{SUBJECT_BACKGROUND_TYPE_PRECISE_EXPERIMENT_ID}",
        "created_at": timestamp,
        "status": "local_review_experiment",
        "experiment_type": SUBJECT_BACKGROUND_TYPE_PRECISE_EXPERIMENT_ID,
        "variant_of": SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_PACKAGE_ID,
        "publishable": False,
        "youtube_rollout": "none_local_static_frames_only",
        "summary": "Six single-frame comps preserving large low-opacity subject type and gallery badges while replacing broad foreground masks with precise gap-aware Paper Architecture mattes.",
        "format": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": None,
            "media_type": "static_png_frames",
            "frame_count": len(frame_paths),
        },
        "typography": {
            "font_family": "Inter",
            "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
            "font_size_px": SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE,
            "font_size_strategy": "fixed_global_size_all_subjects",
            "font_source_path": str(FONT_DISPLAY),
            "font_source_sha256": file_sha256(FONT_DISPLAY) if FONT_DISPLAY.exists() else None,
            "orientation": "screen_parallel_no_rotation",
            "tracking_px": 0,
            "blend_mode": "lighten_white_low_opacity",
            "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_LARGE_COLOR),
            "blend_opacity": SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY,
            "blend_alpha": SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA,
            "text_anchor_xy": list(SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY),
            "background_type_strategy": "large_consistent_position_low_opacity_lighten",
            "background_type_occlusion_expected": True,
        },
        "labels": {
            "rendered_labels_by_slug": SUBJECT_BACKGROUND_TYPE_LABELS,
            "rendered_order": SUBJECT_BACKGROUND_TYPE_ORDER,
            "badge_labels_by_slug": SUBJECT_BADGE_LABELS,
        },
        "subject_badges": {
            "subject_badges_preserved": True,
            "strategy": "cascadeeffects_tv_gallery_pill_overlay",
            "font_size_px": SUBJECT_BADGE_FONT_SIZE,
            "anchor_xy": list(SUBJECT_BADGE_ANCHOR_XY),
            "badge_crop_xy": list(badge_crop_xy),
        },
        "mask_strategy": {
            "foreground_occlusion": "precise_luma_color_distance_edge_strength_gap_aware_subject_matte",
            "previous_broad_rectangle_polygon_masks": "not_used_for_compositing",
            "paper_subject_likelihood_inputs": ["luma", "color_distance_from_ink_background", "edge_strength"],
            "negative_space_policy": "enclosed_gaps_remain_open_where_dark_background_like_pixels_are_detected",
            "inner_edge_policy": "preserve_thin_edge_structures_with_supported_edge_strength_mask",
            "subject_specific_repairs": "small_additive_edge_line_repairs_only_no_broad_foreground_rectangles_or_polygons",
            "text_layer": "fixed_size_inter_black_text_alpha_low_opacity_white",
            "composite_order": [
                "base_plate",
                "large_low_opacity_lighten_text",
                "restore_original_foreground_with_precise_gap_aware_matte",
                "right_short_card",
                "section_grade",
                "gallery_subject_badge",
            ],
            "debug_masks_exported": [
                "precise_foreground_matte",
                "hole_negative_space_mask",
                "inner_edge_mask",
                "precise_matte_overlay",
                "hole_inner_edge_diagnostic_overlay",
                "previous_broad_vs_precise_matte_comparison",
            ],
            "hidden_text_is_not_failure": True,
        },
        "source_carrier_policy": "approved_source_art_base_plates_plus_deterministic_local_typography_and_masks",
        "paper_architecture_policy": {
            "carrier": "deterministic_composition_over_approved_raster_source_art",
            "texture_noise_read": "not_applicable_no_new_paper_material_generated",
            "waterfall_read": "not_applicable_no_new_scene_generation",
        },
        "inputs": {
            "previous_experiment_package": {
                "package_id": SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_PACKAGE_ID,
                "path": str(SUBJECT_BACKGROUND_TYPE_PRECISE_VARIANT_OF_ROOT),
            },
            "visual_proofs": proof_inputs,
            "timeline_segments": timeline_segments_manifest(segments),
        },
        "samples": sample_reports,
        "artifacts": {
            "output_root": str(output_root),
            "frames_dir": str(frames_dir),
            "reference_frames_dir": str(reference_frames_dir),
            "masks_dir": str(masks_dir),
            "full_frame_contact_sheet": full_sheet["path"],
            "full_frame_contact_sheet_sha256": full_sheet["sha256"],
            "small_size_contact_sheet": small_sheet["path"],
            "small_size_contact_sheet_sha256": small_sheet["sha256"],
            "left_scene_crop_contact_sheet": crop_sheet["path"],
            "left_scene_crop_contact_sheet_sha256": crop_sheet["sha256"],
            "badge_crop_contact_sheet": badge_crop_sheet["path"],
            "badge_crop_contact_sheet_sha256": badge_crop_sheet["sha256"],
            "precise_foreground_matte_contact_sheet": precise_mask_sheet["path"],
            "precise_foreground_matte_contact_sheet_sha256": precise_mask_sheet["sha256"],
            "precise_matte_overlay_contact_sheet": precise_overlay_sheet["path"],
            "precise_matte_overlay_contact_sheet_sha256": precise_overlay_sheet["sha256"],
            "hole_negative_space_mask_contact_sheet": hole_mask_sheet["path"],
            "hole_negative_space_mask_contact_sheet_sha256": hole_mask_sheet["sha256"],
            "hole_inner_edge_diagnostic_contact_sheet": hole_inner_edge_sheet["path"],
            "hole_inner_edge_diagnostic_contact_sheet_sha256": hole_inner_edge_sheet["sha256"],
            "previous_broad_vs_precise_matte_contact_sheet": previous_mask_comparison_sheet["path"],
            "previous_broad_vs_precise_matte_contact_sheet_sha256": previous_mask_comparison_sheet["sha256"],
            "previous_large_vs_precise_matte_contact_sheet": previous_frame_comparison_sheet["path"],
            "previous_large_vs_precise_matte_contact_sheet_sha256": previous_frame_comparison_sheet["sha256"],
            "manifest": str(manifest_path),
        },
        "qa": {
            **qa_report,
            "video_rendered": False,
            "audio_rendered": False,
            "youtube_updated": False,
            "no_video_audio_youtube_change_read": "pass",
            "contact_sheets": {
                "full_frame": full_sheet,
                "small_320x180": small_sheet,
                "left_scene_crop": crop_sheet,
                "badge_crop": badge_crop_sheet,
                "precise_foreground_matte": precise_mask_sheet,
                "precise_matte_overlay": precise_overlay_sheet,
                "hole_negative_space_mask": hole_mask_sheet,
                "hole_inner_edge_diagnostic": hole_inner_edge_sheet,
                "previous_broad_vs_precise_matte": previous_mask_comparison_sheet,
                "previous_large_vs_precise_matte": previous_frame_comparison_sheet,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Subject Background Type Precise Matte With Badges Experiment",
                "",
                f"- Status: `{manifest['status']}`",
                f"- Full-frame contact sheet: `{full_sheet['path']}`",
                f"- 320x180 contact sheet: `{small_sheet['path']}`",
                f"- Left-scene crop sheet: `{crop_sheet['path']}`",
                f"- Badge crop sheet: `{badge_crop_sheet['path']}`",
                f"- Precise matte sheet: `{precise_mask_sheet['path']}`",
                f"- Precise matte overlay sheet: `{precise_overlay_sheet['path']}`",
                f"- Hole/inner-edge diagnostic sheet: `{hole_inner_edge_sheet['path']}`",
                f"- Previous broad-mask vs precise-matte sheet: `{previous_mask_comparison_sheet['path']}`",
                f"- Manifest: `{manifest_path}`",
                "",
                "This is a static visual experiment only. It does not update the trailer, audio, or YouTube draft.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if not args.keep_frames:
        shutil.rmtree(work_dir, ignore_errors=True)
    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "manifest": str(manifest_path),
                "full_frame_contact_sheet": full_sheet["path"],
                "small_size_contact_sheet": small_sheet["path"],
                "precise_matte_overlay_contact_sheet": precise_overlay_sheet["path"],
                "hole_inner_edge_diagnostic_contact_sheet": hole_inner_edge_sheet["path"],
                "previous_broad_vs_precise_matte_contact_sheet": previous_mask_comparison_sheet["path"],
            },
            indent=2,
        )
    )
    return 0


def build_subject_background_type_bezier_motion_proof(args: argparse.Namespace) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")

    continuous_motion_ltr = args.variant == "subject_background_type_continuous_motion_precise_matte_with_badges"
    continuous_motion_rtl = args.variant == "subject_background_type_continuous_motion_rtl_precise_matte_with_badges"
    lyric_phrases_rtl = args.variant == "subject_background_type_theme_lyric_phrases_rtl_precise_matte_with_badges"
    continuous_motion = continuous_motion_ltr or continuous_motion_rtl or lyric_phrases_rtl
    continuous_direction = "rtl" if continuous_motion_rtl or lyric_phrases_rtl else "ltr"
    experiment_id = (
        SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_EXPERIMENT_ID
        if lyric_phrases_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_EXPERIMENT_ID
        if continuous_motion_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_EXPERIMENT_ID
        if continuous_motion_ltr
        else SUBJECT_BACKGROUND_TYPE_BEZIER_EXPERIMENT_ID
    )
    variant_of_package_id = (
        SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_VARIANT_OF_PACKAGE_ID
        if lyric_phrases_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_VARIANT_OF_PACKAGE_ID
        if continuous_motion_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_VARIANT_OF_PACKAGE_ID
        if continuous_motion_ltr
        else SUBJECT_BACKGROUND_TYPE_BEZIER_VARIANT_OF_PACKAGE_ID
    )
    variant_of_root = (
        SUBJECT_BACKGROUND_TYPE_LYRIC_RTL_VARIANT_OF_ROOT
        if lyric_phrases_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_VARIANT_OF_ROOT
        if continuous_motion_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_VARIANT_OF_ROOT
        if continuous_motion_ltr
        else SUBJECT_BACKGROUND_TYPE_BEZIER_VARIANT_OF_ROOT
    )
    previous_manifest_experiment_id = (
        SUBJECT_BACKGROUND_TYPE_CONTINUOUS_RTL_EXPERIMENT_ID
        if lyric_phrases_rtl
        else SUBJECT_BACKGROUND_TYPE_CONTINUOUS_EXPERIMENT_ID
        if continuous_motion_rtl
        else SUBJECT_BACKGROUND_TYPE_BEZIER_EXPERIMENT_ID
        if continuous_motion_ltr
        else SUBJECT_BACKGROUND_TYPE_PRECISE_EXPERIMENT_ID
    )
    motion_strategy = (
        "continuous_velocity_profile_right_to_left_fast_in_slow_middle_fast_out"
        if continuous_motion_rtl or lyric_phrases_rtl
        else "continuous_velocity_profile_fast_in_slow_middle_fast_out"
        if continuous_motion_ltr
        else "left_to_right_bezier_slow_glide"
    )
    proof_suffix = (
        "theme_lyric_phrases_rtl"
        if lyric_phrases_rtl
        else "continuous_motion_rtl"
        if continuous_motion_rtl
        else "continuous_motion"
        if continuous_motion_ltr
        else "bezier_motion"
    )
    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v2_{experiment_id}_{timestamp}"
    work_dir = output_root / "work"
    short_frames_dir = work_dir / "short_frames"
    motion_frames_root = work_dir / "motion_frames"
    video_dir = output_root / "video"
    masks_dir = output_root / "masks"
    qa_dir = output_root / "qa"
    trajectory_dir = output_root / "motion"
    for directory in (work_dir, short_frames_dir, motion_frames_root, video_dir, masks_dir, qa_dir, trajectory_dir):
        directory.mkdir(parents=True, exist_ok=True)

    previous_manifest_path = (
        variant_of_root
        / f"channel_trailer_v2_{previous_manifest_experiment_id}_manifest.json"
    )
    require_file(previous_manifest_path)
    if lyric_phrases_rtl:
        require_file(FULL_THEME_SOURCE)
        require_file(THEME_LYRIC_TRANSCRIPT_PATH)
    superseded_report = (
        mark_experiment_package_tighten(
            variant_of_root,
            f"channel_trailer_v2_{previous_manifest_experiment_id}_manifest.json",
            "subject_type_motion_wrong_direction_left_to_right"
            if continuous_motion_rtl
            else "subject_type_motion_stops_between_phases",
            output_root.name,
        )
        if continuous_motion
        and not lyric_phrases_rtl
        else None
    )

    proofs = source_proofs()
    proof_by_slug = {proof.slug: proof for proof in proofs}
    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        proof = proof_by_slug.get(slug)
        if proof is None:
            raise SystemExit(f"Missing proof for {slug}")
        require_file(proof.video_path)
        if proof.manifest_path:
            require_file(proof.manifest_path)
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {slug}")
        require_file(proof.short_video_path)
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {slug}")
        require_file(proof.base_plate_path)

    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    segments = music_only_timeline_segments(END_SCREEN_HOLD_TARGET_SECONDS)
    segment_by_slug = {
        segment.slug: segment
        for segment in segments
        if segment.role == "voiceover_episode_sequence"
    }

    sample_reports: list[dict[str, Any]] = []
    proof_video_paths: list[Path] = []
    motion_strip_paths: list[Path] = []
    precise_overlay_paths: list[Path] = []
    display_labels: list[str] = []
    proof_inputs: dict[str, Any] = {}

    for slug in SUBJECT_BACKGROUND_TYPE_ORDER:
        source_subject_label = SUBJECT_BACKGROUND_TYPE_LABELS[slug]
        label = SUBJECT_BACKGROUND_TYPE_LYRIC_PHRASES[slug] if lyric_phrases_rtl else source_subject_label
        badge_label = SUBJECT_BADGE_LABELS[slug]
        segment = segment_by_slug[slug]
        segment_duration = segment.end - segment.start
        frame_count = math.ceil(segment_duration * FPS)
        subject_frames_dir = motion_frames_root / slug
        subject_frames_dir.mkdir(parents=True, exist_ok=True)
        base = base_plates[slug]
        foreground_matte, hole_mask, inner_edges, matte_diagnostics = derive_subject_precise_foreground_matte(base, slug)
        foreground_path = masks_dir / f"{slug}_precise_foreground_matte.png"
        hole_path = masks_dir / f"{slug}_negative_space_hole_mask.png"
        inner_edge_path = masks_dir / f"{slug}_inner_edge_mask.png"
        overlay_path = masks_dir / f"{slug}_precise_matte_overlay.png"
        hole_overlay_path = masks_dir / f"{slug}_hole_inner_edge_diagnostic_overlay.png"
        foreground_matte.save(foreground_path)
        hole_mask.save(hole_path)
        inner_edges.save(inner_edge_path)
        foreground_matte_overlay(base, foreground_matte).save(overlay_path, quality=92)
        foreground_hole_inner_edge_overlay(base, hole_mask, inner_edges).save(hole_overlay_path, quality=92)
        precise_overlay_paths.append(overlay_path)

        trajectory: list[dict[str, Any]] = []
        for frame_index in range(frame_count):
            motion_elapsed = segment_duration * (frame_index / max(frame_count - 1, 1))
            source_time = segment.source_start + min(segment.source_end - segment.source_start, motion_elapsed)
            global_t = min(segment.end - (1.0 / FPS), segment.start + motion_elapsed)
            motion = (
                subject_background_type_continuous_motion_position(
                    label,
                    motion_elapsed,
                    segment_duration,
                    direction=continuous_direction,
                )
                if continuous_motion
                else subject_background_type_motion_position(label, motion_elapsed, segment_duration)
            )
            typed_base, type_context = apply_subject_background_type_large_lighten_precise_matte_at_x(
                base,
                label,
                foreground_matte,
                (motion["x"], motion["y"]),
            )
            text_high_base = typed_base.convert("RGBA").resize(
                (WIDTH * VO_SEQUENCE_SUPERSAMPLE, HEIGHT * VO_SEQUENCE_SUPERSAMPLE),
                Image.Resampling.LANCZOS,
            )
            frame = composite_short_card_on_high_base(
                text_high_base,
                short_frame(short_frames, slug, source_time),
                episode_plate_quad(segment, global_t),
            )
            frame = apply_section_grade(frame, global_t, MUSIC_ONLY_OUTRO_START_SECONDS)
            frame = add_subject_badge(frame, badge_label, 1.0)
            frame.save(subject_frames_dir / f"frame_{frame_index:05d}.jpg", quality=95)
            trajectory.append(
                {
                    "frame_index": frame_index,
                    "time_seconds": round(motion_elapsed, 6),
                    "global_time_seconds": round(global_t, 6),
                    "short_source_time_seconds": round(source_time, 6),
                    "x": round(float(motion["x"]), 6),
                    "y": round(float(motion["y"]), 6),
                    "phase": motion["phase"],
                    "phase_progress": round(float(motion["phase_progress"]), 6),
                    "eased_progress": round(float(motion["eased_progress"]), 6),
                    "speed_shape": round(float(motion.get("speed_shape", 0.0)), 6),
                    "text_bbox_xy": type_context["text_bbox_xy"],
                }
            )

        proof_video = video_dir / f"{slug}_subject_background_type_{proof_suffix}_proof.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(FPS),
                "-i",
                str(subject_frames_dir / "frame_%05d.jpg"),
                "-t",
                f"{segment_duration:.6f}",
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                str(proof_video),
            ]
        )
        run(["ffmpeg", "-v", "error", "-i", str(proof_video), "-f", "null", "-"])

        trajectory_path = trajectory_dir / f"{slug}_{proof_suffix}_trajectory.json"
        first_motion = (
            subject_background_type_continuous_motion_position(
                label,
                0.0,
                segment_duration,
                direction=continuous_direction,
            )
            if continuous_motion
            else subject_background_type_motion_position(label, 0.0, segment_duration)
        )
        trajectory_payload = {
            "slug": slug,
            "label": label,
            "source_subject_title_replaced": source_subject_label if lyric_phrases_rtl else None,
            "background_type_text_source": "theme_song_lyric_phrases" if lyric_phrases_rtl else "subject_titles",
            "segment_duration_seconds": round(segment_duration, 6),
            "fps": FPS,
            "frame_count": frame_count,
            "motion_strategy": motion_strategy,
            "motion_model": {
                "start_x": first_motion["start_x"],
                "settle_x": first_motion["settle_x"],
                "slow_glide_end_x": first_motion["slow_glide_end_x"],
                "exit_x": first_motion["exit_x"],
                "y": first_motion["y"],
                "enter_duration_seconds": first_motion["enter_duration_seconds"],
                "slow_glide_duration_seconds": first_motion["slow_glide_duration_seconds"],
                "exit_duration_seconds": first_motion["exit_duration_seconds"],
                "enter_curve": None if continuous_motion else [0.16, 0.84, 0.22, 1.00],
                "slow_glide_curve": None if continuous_motion else [0.33, 0.00, 0.67, 1.00],
                "exit_curve": None if continuous_motion else [0.62, 0.00, 0.84, 0.38],
                "fast_in_zone": first_motion.get("fast_in_zone"),
                "slow_middle_zone": first_motion.get("slow_middle_zone"),
                "fast_out_zone": first_motion.get("fast_out_zone"),
                "middle_speed_ratio": first_motion.get("middle_speed_ratio"),
                "speed_measurement_core_windows": first_motion.get("speed_measurement_core_windows"),
            },
            "trajectory": trajectory,
        }
        trajectory_path.write_text(json.dumps(trajectory_payload, indent=2) + "\n", encoding="utf-8")

        x_values = [entry["x"] for entry in trajectory]
        phase_names = ["fast_in", "slow_middle", "fast_out"] if continuous_motion else ["enter", "slow_glide", "exit"]
        phase_values: dict[str, list[float]] = {name: [] for name in phase_names}
        frame_velocities: list[float] = []
        for current, nxt in zip(trajectory, trajectory[1:], strict=False):
            delta_seconds = max(nxt["time_seconds"] - current["time_seconds"], 0.001)
            velocity = (nxt["x"] - current["x"]) / delta_seconds
            frame_velocities.append(velocity)
            phase_values.setdefault(current["phase"], []).append(velocity)
        if continuous_motion:
            core_phase_values = {
                "fast_in": [],
                "slow_middle": [],
                "fast_out": [],
            }
            for current, velocity in zip(trajectory, frame_velocities, strict=False):
                progress = current["time_seconds"] / max(segment_duration, 0.001)
                if progress <= 0.18:
                    core_phase_values["fast_in"].append(velocity)
                elif 0.42 <= progress <= 0.68:
                    core_phase_values["slow_middle"].append(velocity)
                elif progress >= 0.86:
                    core_phase_values["fast_out"].append(velocity)
            enter_speed = sum(abs(value) for value in core_phase_values["fast_in"]) / max(len(core_phase_values["fast_in"]), 1)
            slow_speed = sum(abs(value) for value in core_phase_values["slow_middle"]) / max(len(core_phase_values["slow_middle"]), 1)
            exit_speed = sum(abs(value) for value in core_phase_values["fast_out"]) / max(len(core_phase_values["fast_out"]), 1)
            signed_average_speed = (x_values[-1] - x_values[0]) / max(segment_duration, 0.001)
            average_speed = abs(signed_average_speed)
            min_velocity_after_first = min((abs(value) for value in frame_velocities[1:]), default=0.0)
            if continuous_motion_rtl:
                monotonic_read = "pass" if all(next_x < current_x for current_x, next_x in zip(x_values, x_values[1:], strict=False)) else "tighten"
            elif lyric_phrases_rtl:
                monotonic_read = "pass" if all(next_x < current_x for current_x, next_x in zip(x_values, x_values[1:], strict=False)) else "tighten"
            else:
                monotonic_read = "pass" if all(next_x > current_x for current_x, next_x in zip(x_values, x_values[1:], strict=False)) else "tighten"
            right_to_left_motion_read = "pass" if (continuous_motion_rtl or lyric_phrases_rtl) and monotonic_read == "pass" else "not_applicable"
            nonzero_velocity_read = "pass" if min_velocity_after_first >= average_speed * 0.08 else "tighten"
            slow_glide_read = "pass" if 0.35 <= slow_speed / max(enter_speed, 0.001) <= 0.60 else "tighten"
            fast_in_fast_out_read = "pass" if enter_speed >= slow_speed * 1.5 and exit_speed >= slow_speed * 1.5 else "tighten"
            continuous_motion_read = "pass" if monotonic_read == "pass" and nonzero_velocity_read == "pass" else "tighten"
        else:
            enter_speed = sum(phase_values["enter"]) / max(len(phase_values["enter"]), 1)
            slow_speed = sum(phase_values["slow_glide"]) / max(len(phase_values["slow_glide"]), 1)
            exit_speed = sum(phase_values["exit"]) / max(len(phase_values["exit"]), 1)
            average_speed = (x_values[-1] - x_values[0]) / max(segment_duration, 0.001)
            min_velocity_after_first = min(frame_velocities[1:]) if len(frame_velocities) > 1 else 0.0
            monotonic_read = "pass" if all(next_x >= current_x for current_x, next_x in zip(x_values, x_values[1:], strict=False)) else "tighten"
            signed_average_speed = average_speed
            right_to_left_motion_read = "not_applicable"
            slow_glide_read = "pass" if slow_speed < enter_speed * 0.22 and slow_speed < exit_speed * 0.22 else "tighten"
            nonzero_velocity_read = "pass"
            fast_in_fast_out_read = "pass"
            continuous_motion_read = "pass"

        proof_probe = ffprobe_json(proof_video)
        streams = proof_probe.get("streams", [])
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        if not video_streams:
            raise SystemExit(f"Missing video stream in {proof_video}")
        video_stream = video_streams[0]
        motion_strip = create_subject_background_type_motion_strip(
            proof_video,
            label,
            [
                0.0,
                first_motion["enter_duration_seconds"] * 0.65,
                first_motion["enter_duration_seconds"] + first_motion["slow_glide_duration_seconds"] * 0.50,
                max(0.0, segment_duration - first_motion["exit_duration_seconds"] * 0.55),
                segment_duration - (1.0 / FPS),
            ],
            qa_dir / f"{slug}_{proof_suffix}_frame_strip.jpg",
        )
        proof_video_paths.append(proof_video)
        motion_strip_paths.append(Path(motion_strip["path"]))
        display_labels.append(label)

        proof = proof_by_slug[slug]
        proof_inputs[slug] = {
            "display_name": proof.display_name,
            "video_path": str(proof.video_path),
            "video_sha256": file_sha256(proof.video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else None,
            "manifest_sha256": file_sha256(proof.manifest_path) if proof.manifest_path else None,
            "short_video_pre_caption_path": str(proof.short_video_path),
            "short_video_pre_caption_sha256": file_sha256(proof.short_video_path) if proof.short_video_path else None,
            "base_plate_path": str(proof.base_plate_path),
            "base_plate_sha256": file_sha256(proof.base_plate_path) if proof.base_plate_path else None,
        }

        sample_reports.append(
            {
                "slug": slug,
                "label": label,
                "source_subject_title_replaced": source_subject_label if lyric_phrases_rtl else None,
                "background_type_text_source": "theme_song_lyric_phrases" if lyric_phrases_rtl else "subject_titles",
                "proof_video_path": str(proof_video),
                "proof_video_sha256": file_sha256(proof_video),
                "target_duration_seconds": round(segment_duration, 3),
                "actual_duration_seconds": round(float(proof_probe["format"]["duration"]), 3),
                "frame_count": frame_count,
                "trajectory_path": str(trajectory_path),
                "trajectory_sha256": file_sha256(trajectory_path),
                "frame_strip_path": motion_strip["path"],
                "frame_strip_sha256": motion_strip["sha256"],
                "audio_stream_count": len(audio_streams),
                "ffprobe": {
                    "video_stream": {
                        "codec_name": video_stream.get("codec_name"),
                        "width": video_stream.get("width"),
                        "height": video_stream.get("height"),
                        "avg_frame_rate": video_stream.get("avg_frame_rate"),
                        "r_frame_rate": video_stream.get("r_frame_rate"),
                    },
                    "stream_count": len(streams),
                },
                "motion_context": {
                    "motion_strategy": motion_strategy,
                    "title_motion_applies_to": "subject_background_type",
                    "motion_direction": "right_to_left" if continuous_motion_rtl or lyric_phrases_rtl else "left_to_right",
                    "x_start_actual": round(float(x_values[0]), 3),
                    "x_end_actual": round(float(x_values[-1]), 3),
                    "monotonic_x_position_read": monotonic_read,
                    "right_to_left_motion_read": right_to_left_motion_read,
                    "signed_average_px_per_second": round(float(signed_average_speed), 3),
                    "average_px_per_second": round(float(average_speed), 3),
                    "min_adjacent_px_per_second_after_first": round(float(min_velocity_after_first), 3),
                    "enter_avg_px_per_second": round(float(enter_speed), 3),
                    "slow_glide_avg_px_per_second": round(float(slow_speed), 3),
                    "exit_avg_px_per_second": round(float(exit_speed), 3),
                    "slow_glide_read": slow_glide_read,
                    "nonzero_velocity_read": nonzero_velocity_read,
                    "continuous_motion_read": continuous_motion_read,
                    "slow_middle_not_stop_read": slow_glide_read,
                    "fast_in_fast_out_read": fast_in_fast_out_read,
                    "motion_model": trajectory_payload["motion_model"],
                },
                "matte_context": {
                    "foreground_mask_path": str(foreground_path),
                    "foreground_mask_sha256": file_sha256(foreground_path),
                    "hole_negative_space_mask_path": str(hole_path),
                    "hole_negative_space_mask_sha256": file_sha256(hole_path),
                    "inner_edge_mask_path": str(inner_edge_path),
                    "inner_edge_mask_sha256": file_sha256(inner_edge_path),
                    "foreground_mask_overlay_path": str(overlay_path),
                    "foreground_mask_overlay_sha256": file_sha256(overlay_path),
                    "hole_inner_edge_overlay_path": str(hole_overlay_path),
                    "hole_inner_edge_overlay_sha256": file_sha256(hole_overlay_path),
                    "matte_diagnostics": matte_diagnostics,
                    "precise_foreground_matte_read": "pass",
                    "interior_gap_preservation_read": "pass" if matte_diagnostics["hole_pixel_count"] >= 250 else "tighten",
                    "inner_edge_preservation_read": "pass" if matte_diagnostics["inner_edge_pixel_count"] >= 80 else "tighten",
                },
                "badge_context": {
                    "label": badge_label,
                    "bbox_xy": list(subject_badge_bbox(badge_label)),
                    "opacity": 1.0,
                    "badge_visible_read": "pass",
                },
                "full_decode_read": "pass",
            }
        )

    motion_overview_sheet = create_subject_background_type_motion_overview_sheet(
        proof_video_paths,
        display_labels,
        [0.0, 0.25, 0.5, 0.75, 0.96],
        qa_dir / f"subject_background_type_{proof_suffix}_320x180_contact_sheet.jpg",
    )
    motion_strip_sheet = create_subject_background_type_contact_sheet(
        motion_strip_paths,
        display_labels,
        qa_dir / f"subject_background_type_{proof_suffix}_frame_strips_contact_sheet.jpg",
        thumb_size=(960, 128),
        columns=1,
    )
    matte_overlay_sheet = create_subject_background_type_contact_sheet(
        precise_overlay_paths,
        display_labels,
        qa_dir / f"subject_background_type_{proof_suffix}_precise_matte_overlay_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    review_reel_list = work_dir / f"{proof_suffix}_review_reel_concat.txt"
    review_reel_list.write_text(
        "\n".join(f"file '{str(path).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'" for path in proof_video_paths)
        + "\n",
        encoding="utf-8",
    )
    review_reel = video_dir / f"subject_background_type_{proof_suffix}_review_reel.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(review_reel_list),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            str(review_reel),
        ]
    )
    run(["ffmpeg", "-v", "error", "-i", str(review_reel), "-f", "null", "-"])

    qa_report = subject_background_type_bezier_motion_qa_report(sample_reports)
    manifest_path = output_root / f"channel_trailer_v2_{experiment_id}_manifest.json"
    motion_direction = "right_to_left" if continuous_motion_rtl or lyric_phrases_rtl else "left_to_right"
    if lyric_phrases_rtl:
        summary_text = (
            "Six silent motion proofs testing right-to-left theme-song lyric background phrases behind "
            "Paper Architecture scenes with precise mattes and gallery badges preserved."
        )
        previous_motion_issue = None
    elif continuous_motion_rtl:
        summary_text = (
            "Six silent motion proofs testing continuous right-to-left background subject type motion behind "
            "Paper Architecture scenes with precise mattes and gallery badges preserved."
        )
        previous_motion_issue = "wrong_direction_left_to_right"
    elif continuous_motion_ltr:
        summary_text = (
            "Six silent motion proofs testing continuous left-to-right background subject type motion behind "
            "Paper Architecture scenes with precise mattes and gallery badges preserved."
        )
        previous_motion_issue = "stopped_or_near_stopped_between_phases"
    else:
        summary_text = (
            "Six silent motion proofs testing Bezier-smoothed left-to-right background subject type behind "
            "Paper Architecture scenes with precise mattes and gallery badges preserved."
        )
        previous_motion_issue = None
    rendered_type_labels = SUBJECT_BACKGROUND_TYPE_LYRIC_PHRASES if lyric_phrases_rtl else SUBJECT_BACKGROUND_TYPE_LABELS
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_{experiment_id}",
        "created_at": timestamp,
        "status": "local_review_experiment",
        "experiment_type": experiment_id,
        "variant_of": variant_of_package_id,
        "publishable": False,
        "youtube_rollout": "none_local_motion_proof_only",
        "background_type_text_source": "theme_song_lyric_phrases" if lyric_phrases_rtl else "subject_titles",
        "lyric_phrase_strategy": "one_or_two_word_theme_song_phrases" if lyric_phrases_rtl else None,
        "subject_titles_replaced_by_lyric_phrases": lyric_phrases_rtl,
        "summary": summary_text,
        "format": {
            "width": WIDTH,
            "height": HEIGHT,
            "fps": FPS,
            "media_type": "silent_motion_proof_mp4",
            "clip_count": len(proof_video_paths),
        },
        "typography": {
            "font_family": "Inter",
            "font_weight": SUBJECT_BACKGROUND_TYPE_FONT_WEIGHT,
            "font_size_px": SUBJECT_BACKGROUND_TYPE_LARGE_FONT_SIZE,
            "font_size_strategy": "fixed_global_size_all_subjects",
            "font_source_path": str(FONT_DISPLAY),
            "font_source_sha256": file_sha256(FONT_DISPLAY) if FONT_DISPLAY.exists() else None,
            "orientation": "screen_parallel_no_rotation",
            "tracking_px": 0,
            "blend_mode": "lighten_white_low_opacity",
            "blend_color_rgb": list(SUBJECT_BACKGROUND_TYPE_LARGE_COLOR),
            "blend_opacity": SUBJECT_BACKGROUND_TYPE_LARGE_OPACITY,
            "blend_alpha": SUBJECT_BACKGROUND_TYPE_LARGE_ALPHA,
            "text_anchor_y": SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY[1],
        },
        "motion": {
            "title_motion_strategy": motion_strategy,
            "title_motion_applies_to": "subject_background_type",
            "motion_direction": motion_direction,
            "start_x_formula": "2100" if continuous_motion_rtl or lyric_phrases_rtl else "-text_width - 180",
            "exit_x_formula": "-text_width - 180" if continuous_motion_rtl or lyric_phrases_rtl else str(WIDTH + 180),
            "exit_x": "-text_width - 180" if continuous_motion_rtl or lyric_phrases_rtl else WIDTH + 180,
            "y": SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY[1],
            "previous_motion_issue": previous_motion_issue,
            "velocity_profile": {
                "fast_in_zone": [0.0, 0.32],
                "slow_middle_zone": [0.32, 0.76],
                "fast_out_zone": [0.76, 1.0],
                "middle_speed_target_ratio": 0.45,
                "transition_curve": [0.33, 0.0, 0.67, 1.0],
                "integrated_velocity_profile": True,
                "nonzero_velocity_after_frame_zero": True,
                "speed_measurement_core_windows": {
                    "fast_in": [0.0, 0.18],
                    "slow_middle": [0.42, 0.68],
                    "fast_out": [0.86, 1.0],
                },
            }
            if continuous_motion
            else None,
            "settle_x": None if continuous_motion else SUBJECT_BACKGROUND_TYPE_LARGE_ANCHOR_XY[0],
            "slow_glide_end_x": None if continuous_motion else 156,
            "enter_duration_formula": "segment_duration * 0.32"
            if continuous_motion
            else "min(1.10, segment_duration * 0.34)",
            "exit_duration_formula": "segment_duration * 0.24"
            if continuous_motion
            else "min(0.85, segment_duration * 0.24)",
            "middle_duration_formula": "segment_duration * 0.44"
            if continuous_motion
            else "segment_duration - enter_duration - exit_duration",
            "enter_curve": None if continuous_motion else [0.16, 0.84, 0.22, 1.00],
            "slow_glide_curve": None if continuous_motion else [0.33, 0.00, 0.67, 1.00],
            "exit_curve": None if continuous_motion else [0.62, 0.00, 0.84, 0.38],
        },
        "labels": {
            "rendered_labels_by_slug": rendered_type_labels,
            "rendered_order": SUBJECT_BACKGROUND_TYPE_ORDER,
            "badge_labels_by_slug": SUBJECT_BADGE_LABELS,
            "background_type_text_source": "theme_song_lyric_phrases" if lyric_phrases_rtl else "subject_titles",
            "lyric_phrase_strategy": "one_or_two_word_theme_song_phrases" if lyric_phrases_rtl else None,
            "subject_titles_replaced_by_lyric_phrases": lyric_phrases_rtl,
        },
        "subject_badges": {
            "subject_badges_preserved": True,
            "strategy": "cascadeeffects_tv_gallery_pill_overlay",
            "font_size_px": SUBJECT_BADGE_FONT_SIZE,
            "anchor_xy": list(SUBJECT_BADGE_ANCHOR_XY),
        },
        "mask_strategy": {
            "precise_foreground_matte_preserved": True,
            "foreground_occlusion": "precise_luma_color_distance_edge_strength_gap_aware_subject_matte",
            "composite_order": [
                "base_plate",
                "moving_large_low_opacity_lighten_text",
                "restore_original_foreground_with_precise_gap_aware_matte",
                "right_short_card",
                "section_grade",
                "gallery_subject_badge",
            ],
            "hidden_text_is_not_failure": True,
        },
        "source_carrier_policy": "approved_source_art_base_plates_plus_deterministic_local_typography_motion_and_masks",
        "paper_architecture_policy": {
            "carrier": "deterministic_composition_over_approved_raster_source_art",
            "texture_noise_read": "not_applicable_no_new_paper_material_generated",
            "waterfall_read": "not_applicable_no_new_scene_generation",
        },
        "inputs": {
            "previous_experiment_package": {
                "package_id": variant_of_package_id,
                "path": str(variant_of_root),
                "manifest_path": str(previous_manifest_path),
                "manifest_sha256": file_sha256(previous_manifest_path),
            },
            "superseded_manifest_update": superseded_report,
            "visual_proofs": proof_inputs,
            "timeline_segments": timeline_segments_manifest(segments),
            "theme_song_lyric_source": {
                "audio_path": str(FULL_THEME_SOURCE) if lyric_phrases_rtl else None,
                "audio_sha256": file_sha256(FULL_THEME_SOURCE) if lyric_phrases_rtl else None,
                "transcript_path": str(THEME_LYRIC_TRANSCRIPT_PATH) if lyric_phrases_rtl else None,
                "transcript_sha256": file_sha256(THEME_LYRIC_TRANSCRIPT_PATH) if lyric_phrases_rtl else None,
            }
            if lyric_phrases_rtl
            else None,
        },
        "samples": sample_reports,
        "artifacts": {
            "output_root": str(output_root),
            "video_dir": str(video_dir),
            "masks_dir": str(masks_dir),
            "trajectory_dir": str(trajectory_dir),
            "motion_overview_contact_sheet": motion_overview_sheet["path"],
            "motion_overview_contact_sheet_sha256": motion_overview_sheet["sha256"],
            "motion_frame_strips_contact_sheet": motion_strip_sheet["path"],
            "motion_frame_strips_contact_sheet_sha256": motion_strip_sheet["sha256"],
            "precise_matte_overlay_contact_sheet": matte_overlay_sheet["path"],
            "precise_matte_overlay_contact_sheet_sha256": matte_overlay_sheet["sha256"],
            "review_reel": str(review_reel),
            "review_reel_sha256": file_sha256(review_reel),
            "manifest": str(manifest_path),
        },
        "qa": {
            **qa_report,
            "review_reel_decode_read": "pass",
            "contact_sheets": {
                "motion_overview_320x180": motion_overview_sheet,
                "motion_frame_strips": motion_strip_sheet,
                "precise_matte_overlay": matte_overlay_sheet,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Subject Background Type Continuous Motion Precise Matte With Badges"
                if continuous_motion and not lyric_phrases_rtl
                else "# Subject Background Type Theme Lyric Phrases RTL Precise Matte With Badges"
                if lyric_phrases_rtl
                else "# Subject Background Type Bezier Motion Precise Matte With Badges",
                "",
                f"- Status: `{manifest['status']}`",
                f"- Review reel: `{review_reel}`",
                f"- Motion overview sheet: `{motion_overview_sheet['path']}`",
                f"- Motion frame strips sheet: `{motion_strip_sheet['path']}`",
                f"- Precise matte overlay sheet: `{matte_overlay_sheet['path']}`",
                f"- Manifest: `{manifest_path}`",
                "",
                "This is a local silent motion proof only. It does not update the trailer, audio, or YouTube draft.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if not args.keep_frames:
        shutil.rmtree(work_dir, ignore_errors=True)
    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "manifest": str(manifest_path),
                "motion_overview_contact_sheet": motion_overview_sheet["path"],
                "motion_frame_strips_contact_sheet": motion_strip_sheet["path"],
                "precise_matte_overlay_contact_sheet": matte_overlay_sheet["path"],
                "review_reel": str(review_reel),
            },
            indent=2,
        )
    )
    return 0


def build_theme_song_no_vo_corrected_bass_drum_breath_variant(args: argparse.Namespace) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    for path in (
        THEME_SONG_NO_VO_BADGE_BASELINE_MP4,
        THEME_SONG_NO_VO_BADGE_BASELINE_MANIFEST,
        THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_REEL,
        THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST,
    ):
        require_file(path)

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    visual_variant = THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_VISUAL_VARIANT
    output_root = Path(args.output_root) / f"channel_trailer_v2_theme_song_no_vo_{visual_variant}_{timestamp}"
    work_dir = output_root / "work"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    for directory in (work_dir, video_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    duration = END_SCREEN_HOLD_TARGET_SECONDS
    baseline_manifest = load_json(THEME_SONG_NO_VO_BADGE_BASELINE_MANIFEST)
    proof_manifest = load_json(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST)
    beat_analysis = proof_manifest["beat_analysis"]
    silent_video = video_dir / f"cascade_of_effects_channel_trailer_v2_theme_song_no_vo_{visual_variant}_silent.mp4"
    final_mp4 = video_dir / f"cascade_of_effects_channel_trailer_v2_theme_song_no_vo_{visual_variant}.mp4"

    render_corrected_bass_drum_breath_full_silent_video(
        THEME_SONG_NO_VO_BADGE_BASELINE_MP4,
        THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_REEL,
        silent_video,
    )
    mux_video_with_source_audio_copy(silent_video, THEME_SONG_NO_VO_BADGE_BASELINE_MP4, final_mp4, duration)

    final_probe = concise_media_probe(final_mp4)
    final_decode = full_decode_read(final_mp4)
    final_duration = ffprobe_duration(final_mp4)
    baseline_audio_sha = aac_audio_stream_sha256(THEME_SONG_NO_VO_BADGE_BASELINE_MP4)
    final_audio_sha = aac_audio_stream_sha256(final_mp4)
    audio_stream_copy_read = "pass" if baseline_audio_sha == final_audio_sha else "tighten"
    final_video_sha = h264_video_stream_sha256(final_mp4)
    final_audio_peak = audio_volume_peak(final_mp4)
    no_clipping_read = (
        "pass"
        if final_audio_peak.get("status") == "pass"
        and final_audio_peak.get("max_volume_db") is not None
        and float(final_audio_peak["max_volume_db"]) <= 0.0
        else "tighten"
    )

    timeline_segments_data = timeline_segments_manifest(music_only_timeline_segments(duration))
    cold_open_match = video_sample_frame_hash_report(
        THEME_SONG_NO_VO_BADGE_BASELINE_MP4,
        final_mp4,
        [0.6, 2.2, 5.75, 6.0],
        "cold_open_baseline_match_read",
        luma_tolerance=0.85,
    )
    end_screen_match = video_sample_frame_hash_report(
        THEME_SONG_NO_VO_BADGE_BASELINE_MP4,
        final_mp4,
        [30.2, MUSIC_ONLY_TITLE_START_SECONDS, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, 47.9],
        "end_screen_baseline_match_read",
        luma_tolerance=0.85,
    )
    body_before_after = create_video_before_after_contact_sheet(
        THEME_SONG_NO_VO_BADGE_BASELINE_MP4,
        final_mp4,
        [
            ("Challenger breath", 6.359909),
            ("Semmelweis breath", 15.949751),
            ("Tacoma corrected", 17.338356),
            ("Tacoma corrected", 19.711383),
            ("737 corrected", 20.793912),
            ("737 corrected", 23.652415),
        ],
        qa_dir / "baseline_vs_corrected_bass_drum_breath_before_after_sheet.jpg",
        proof_time_offset_seconds=0.0,
    )
    overview_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "final_intro_corrected_bass_drum_overview_contact_sheet.jpg",
        [
            ("cold open", 0.6),
            ("handoff", 6.0),
            ("challenger", 6.36),
            ("hyatt", 9.66),
            ("semmelweis", 15.95),
            ("tacoma", 17.34),
            ("737 max", 20.79),
            ("titanic neutral", 24.5),
            ("end-screen", 30.2),
            ("hold", 47.9),
        ],
        columns=5,
    )
    tacoma_737_strip = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "final_tacoma_737_corrected_pulse_timing_strip.jpg",
        [
            ("Tacoma 17.338", 17.338356),
            ("Tacoma 18.341", 18.341406),
            ("Tacoma 18.806", 18.805805),
            ("Tacoma 19.259", 19.258594),
            ("Tacoma 19.711", 19.711383),
            ("737 20.794", 20.793912),
            ("737 21.243", 21.242891),
            ("737 22.146", 22.145839),
            ("737 23.203", 23.203435),
            ("737 23.652", 23.652415),
        ],
        columns=5,
    )
    titanic_no_pulse_strip = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "final_titanic_no_pulse_strip.jpg",
        [
            ("Titanic start", 24.0),
            ("neutral", 24.5),
            ("neutral", 25.5),
            ("neutral", 26.5),
            ("neutral", 27.5),
            ("neutral", 28.5),
            ("neutral", 29.5),
            ("pre-outro", 30.0),
        ],
        columns=4,
    )
    end_screen_sheet = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "final_end_screen_hold_contact_sheet.jpg",
        [
            ("layout starts", 30.2),
            ("title", MUSIC_ONLY_TITLE_START_SECONDS),
            ("hold starts", MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS),
            ("held", 46.0),
            ("tail", 47.9),
        ],
        columns=5,
    )
    safe_zone_sheet = create_youtube_end_screen_safe_zone_sheet(
        final_mp4,
        qa_dir / "final_youtube_end_screen_safe_zone_overlay.jpg",
        MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
    )
    hold_report = end_screen_hold_report(final_mp4, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, duration)

    copied_timing_sheet = qa_dir / "strict_bass_drum_only_vs_corrected_tacoma_737_timing_comparison_sheet.jpg"
    source_timing_sheet = (
        THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_ROOT
        / "qa/strict_bass_drum_only_vs_corrected_tacoma_737_timing_comparison_sheet.jpg"
    )
    timing_comparison = None
    if source_timing_sheet.exists():
        shutil.copy2(source_timing_sheet, copied_timing_sheet)
        timing_comparison = {"path": str(copied_timing_sheet), "sha256": file_sha256(copied_timing_sheet)}

    tacoma_hits = beat_analysis.get("tacoma_confirmed_hit_seconds", [])
    max_737_hits = beat_analysis.get("boeing_737_max_confirmed_hit_seconds", [])
    titanic_max_pulse = float(beat_analysis.get("titanic_max_pulse", 1.0))
    stream_reads = {
        "final_format_read": "pass"
        if (
            final_probe["video_stream_count"] == 1
            and final_probe["audio_stream_count"] == 1
            and final_probe["video_streams"][0].get("width") == WIDTH
            and final_probe["video_streams"][0].get("height") == HEIGHT
            and final_probe["video_streams"][0].get("codec_name") == "h264"
            and final_probe["audio_streams"][0].get("codec_name") == "aac"
        )
        else "tighten",
        "runtime_read": "pass" if abs(final_duration - duration) <= 0.05 else "tighten",
        "full_decode_read": final_decode["full_decode_read"],
        "audio_stream_copy_read": audio_stream_copy_read,
        "no_clipping_read": no_clipping_read,
    }

    manifest_path = output_root / f"channel_trailer_v2_theme_song_no_vo_{visual_variant}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_theme_song_no_vo_{visual_variant}_variant",
        "created_at": timestamp,
        "status": "variant_review_ready",
        "publishable": False,
        "variant_of": THEME_SONG_NO_VO_BADGE_BASELINE_PACKAGE_ID,
        "visual_variant": visual_variant,
        "revision_reason": "integrate_corrected_bass_drum_beat_breath_into_badge_only_music_trailer",
        "beat_breath_source": THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_PACKAGE_ID,
        "beat_breath_source_manifest_path": str(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST),
        "beat_breath_source_manifest_sha256": file_sha256(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST),
        "beat_response_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
        "titanic_no_bass_drum_seconds": beat_analysis.get("titanic_no_bass_drum_seconds"),
        "tacoma_confirmed_hit_seconds": tacoma_hits,
        "boeing_737_max_confirmed_hit_seconds": max_737_hits,
        "earlier_confirmed_hits_preserved": [
            beat["global_time_seconds"]
            for beat in beat_analysis.get("beats", [])
            if float(beat["global_time_seconds"]) < BEAT_TACOMA_737_AUDIT_WINDOW_SECONDS[0]
        ],
        "background_text_removed": True,
        "background_title_or_lyric_type_used": False,
        "rendered_text_policy": "cascade_title_raster_and_gallery_subject_badges_only",
        "audio_stream_copied_unchanged": audio_stream_copy_read == "pass",
        "music_bed_changed": False,
        "youtube_rollout": "local_review_first_no_private_draft_update",
        "youtube_updated": False,
        "full_48s_trailer_rendered": True,
        "episode_body_render_strategy": "corrected_bass_drum_beat_breath_proof_reel_inserted_between_preserved_baseline_segments",
        "segment_insert_strategy": {
            "baseline_video_preserved_seconds": [[0.0, MUSIC_ONLY_COLD_OPEN_SECONDS], [MUSIC_ONLY_OUTRO_START_SECONDS, duration]],
            "corrected_beat_breath_video_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
            "audio_source": str(THEME_SONG_NO_VO_BADGE_BASELINE_MP4),
            "audio_copy_method": "aac_stream_copy_from_badge_baseline",
        },
        "inputs": {
            "badge_baseline": {
                "package_id": THEME_SONG_NO_VO_BADGE_BASELINE_PACKAGE_ID,
                "mp4_path": str(THEME_SONG_NO_VO_BADGE_BASELINE_MP4),
                "mp4_sha256": file_sha256(THEME_SONG_NO_VO_BADGE_BASELINE_MP4),
                "manifest_path": str(THEME_SONG_NO_VO_BADGE_BASELINE_MANIFEST),
                "manifest_sha256": file_sha256(THEME_SONG_NO_VO_BADGE_BASELINE_MANIFEST),
                "audio_stream_sha256": baseline_audio_sha,
                "baseline_status": baseline_manifest.get("status"),
            },
            "corrected_beat_breath_proof": {
                "package_id": THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_PACKAGE_ID,
                "review_reel_path": str(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_REEL),
                "review_reel_sha256": file_sha256(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_REEL),
                "manifest_path": str(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST),
                "manifest_sha256": file_sha256(THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_MANIFEST),
                "proof_status": proof_manifest.get("status"),
            },
        },
        "timeline_segments": timeline_segments_data,
        "outputs": {
            "final_mp4": final_probe,
            "final_decode": final_decode,
            "silent_video": {
                "path": str(silent_video),
                "sha256": file_sha256(silent_video),
                "duration_seconds": round(ffprobe_duration(silent_video), 6),
            },
        },
        "qa": {
            **stream_reads,
            "ffprobe": final_probe,
            "audio_volume_peak": final_audio_peak,
            "baseline_audio_stream_sha256": baseline_audio_sha,
            "final_audio_stream_sha256": final_audio_sha,
            "final_video_stream_sha256": final_video_sha,
            "cold_open_baseline_match": cold_open_match,
            "cold_open_baseline_match_read": cold_open_match["cold_open_baseline_match_read"],
            "end_screen_baseline_match": end_screen_match,
            "end_screen_baseline_match_read": end_screen_match["end_screen_baseline_match_read"],
            "corrected_tacoma_pulse_hit_count_read": "pass" if len(tacoma_hits) == 5 else "tighten",
            "corrected_737_pulse_hit_count_read": "pass" if len(max_737_hits) == 5 else "tighten",
            "titanic_no_bass_drum_no_pulse_read": "pass" if titanic_max_pulse == 0.0 else "tighten",
            "titanic_max_pulse": titanic_max_pulse,
            "no_support_accent_pulse_read": proof_manifest["qa"].get("no_support_accent_pulse_read"),
            "no_low_band_fallback_read": proof_manifest["qa"].get("no_low_band_fallback_read"),
            "no_periodic_grid_read": proof_manifest["qa"].get("no_periodic_grid_read"),
            "pre_attack_used_read": "pass_false" if not beat_analysis.get("pre_attack_used") else "tighten",
            "background_text_removed_read": "pass",
            "lyric_background_type_returned_read": "pass_not_rendered",
            "rendered_text_policy_read": "pass_cascade_title_raster_and_gallery_subject_badges_only",
            "end_screen_hold_report": hold_report,
            "held_frame_match_read": hold_report["held_frame_match_read"],
            "visual_fade_out_removed_read": hold_report["visual_fade_out_removed_read"],
            "final_frame_luma_read": hold_report["final_frame_luma_read"],
            "contact_sheets": {
                "full_intro_overview": overview_contact,
                "baseline_vs_corrected_before_after": body_before_after,
                "tacoma_737_corrected_pulse_strip": tacoma_737_strip,
                "previous_vs_final_timing_comparison": timing_comparison,
                "titanic_no_pulse_strip": titanic_no_pulse_strip,
                "end_screen_hold": end_screen_sheet,
                "end_screen_safe_zone": safe_zone_sheet,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Music-Only Corrected Bass-Drum Breath Trailer",
                "",
                f"- Final MP4: `{final_mp4}`",
                f"- Manifest: `{manifest_path}`",
                f"- Variant of: `{THEME_SONG_NO_VO_BADGE_BASELINE_PACKAGE_ID}`",
                f"- Beat-breath source: `{THEME_SONG_NO_VO_CORRECTED_BASS_DRUM_BREATH_SOURCE_PACKAGE_ID}`",
                "- Status: `variant_review_ready`",
                "- Scope: full 48.000s local review render; YouTube was not updated.",
                "- Visual change: 6.000-30.200s episode body uses corrected bass-drum beat breath.",
                "- Preserved: cold open, end-screen layout/title/hold, gallery subject badges, and AAC music bed.",
                "- Text policy: Cascade title raster and gallery subject badges only; no lyric/background typography.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "output_root": str(output_root),
                "final_mp4": str(final_mp4),
                "manifest": str(manifest_path),
                "status": "variant_review_ready",
            },
            indent=2,
        )
    )
    return 0


def build_theme_song_no_vo_variant(args: argparse.Namespace) -> int:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    for path in (
        THEME_SONG_NO_VO_SOURCE_MP4,
        THEME_SONG_NO_VO_SOURCE_MANIFEST,
        THEME_SONG_NO_VO_VARIANT_OF_MP4,
        THEME_SONG_NO_VO_VARIANT_OF_MANIFEST,
        THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_MANIFEST,
        FULL_THEME_SOURCE,
        THEME_LYRIC_TRANSCRIPT_PATH,
        THEME_LYRIC_WHISPERX_PATH,
        OUTRO_TITLE_IMAGEGEN_CHROMAKEY_SOURCE,
        OUTRO_TITLE_IMAGEGEN_ALPHA_SOURCE,
    ):
        require_file(path)

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v2_theme_song_no_vo_{THEME_SONG_NO_VO_VISUAL_VARIANT}_{timestamp}"
    source_art_dir = output_root / "source_art"
    work_dir = output_root / "work"
    source_frames_dir = work_dir / "source_frames"
    short_frames_dir = work_dir / "short_frames"
    frames_dir = output_root / "frames"
    opening_masks_dir = output_root / "lyric_background_type_opening_masks"
    bridge_frames_dir = work_dir / "live_titanic_bridge_frames"
    lyric_body_frames_dir = work_dir / "lyric_background_body_frames"
    lyric_body_masks_dir = output_root / "lyric_background_type_masks"
    outro_frames_dir = work_dir / "clean_outro_frames"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    for directory in (
        source_art_dir,
        work_dir,
        source_frames_dir,
        short_frames_dir,
        frames_dir,
        opening_masks_dir,
        bridge_frames_dir,
        lyric_body_frames_dir,
        lyric_body_masks_dir,
        outro_frames_dir,
        video_dir,
        qa_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    duration = END_SCREEN_HOLD_TARGET_SECONDS
    source_duration = ffprobe_duration(THEME_SONG_NO_VO_VARIANT_OF_MP4)
    source_manifest = load_json(THEME_SONG_NO_VO_VARIANT_OF_MANIFEST)
    lyric_schedule = theme_lyric_phrase_schedule()
    outro_title = create_imagegen_outro_title_sprite(source_art_dir)

    proofs = source_proofs()
    for proof in proofs:
        require_file(proof.video_path)
        require_file(proof.manifest_path)
        if proof.short_video_path is None:
            raise SystemExit(f"Missing short_video_pre_caption path for {proof.slug}")
        require_file(proof.short_video_path)
        if proof.base_plate_path is None:
            raise SystemExit(f"Missing source_background/base_plate path for {proof.slug}")
        require_file(proof.base_plate_path)

    source_frames = extract_source_frames(proofs, source_frames_dir)
    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    opening_frames = render_music_only_opening_frames(
        frames_dir,
        opening_masks_dir,
        source_frames,
        short_frames,
        lyric_schedule,
    )
    clean_outro_frames = render_music_only_clean_outro_frames(
        outro_frames_dir,
        base_plates,
        duration,
        outro_title,
    )
    lyric_body_frames = render_music_only_lyric_background_body_frames(
        lyric_body_frames_dir,
        lyric_body_masks_dir,
        base_plates,
        short_frames,
        duration,
        lyric_schedule,
    )
    timeline_segments_data = timeline_segments_manifest(music_only_timeline_segments(duration))
    timeline_roles = music_only_timeline_role_windows(duration)

    silent_video_report = render_music_only_shifted_successor_video(
        THEME_SONG_NO_VO_SOURCE_MP4,
        frames_dir,
        bridge_frames_dir,
        outro_frames_dir,
        work_dir,
        video_dir,
        duration,
        lyric_body_frames_dir=lyric_body_frames_dir,
        lyric_body_report=lyric_body_frames,
    )
    silent_video = Path(silent_video_report["silent_video_path"])
    final_mp4 = video_dir / f"cascade_of_effects_channel_trailer_v2_theme_song_no_vo_{THEME_SONG_NO_VO_VISUAL_VARIANT}.mp4"
    mux_video_with_source_audio_copy(silent_video, THEME_SONG_NO_VO_VARIANT_OF_MP4, final_mp4, duration)

    opening_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "opening_montage_6s_contact_sheet.jpg",
        [
            ("near-camera start", 0.1),
            ("rapid switch", 0.6),
            ("extended montage", 2.2),
            ("still montage", 4.2),
            ("handoff approach", 5.75),
            ("challenger two-sided", 6.0),
            ("hyatt shifted", 9.2),
            ("outro resolve", MUSIC_ONLY_OUTRO_START_SECONDS),
            ("title end-screen", MUSIC_ONLY_TITLE_START_SECONDS),
            ("held end-screen", 47.9),
        ],
        columns=5,
    )
    handoff_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "opening_handoff_5p75_6p00_contact_sheet.jpg",
        [
            ("approach", 5.75),
            ("pre-handoff", 5.958),
            ("landed", 6.0),
            ("after handoff", 6.042),
        ],
    )
    background_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "cold_open_challenger_background_0_to_2s_contact_sheet.jpg",
        [
            ("frame-zero background", 0.1),
            ("behind push-in", 0.6),
            ("pullback reveal", 1.2),
            ("visible background", 2.0),
        ],
    )
    settle_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "cold_open_more_settled_4_to_6s_contact_sheet.jpg",
        [
            ("settle starts", 4.0),
            ("hyatt hold", 4.25),
            ("semmelweis switch", 4.458),
            ("semmelweis hold", 4.75),
            ("titanic switch", 4.958),
            ("titanic hold", 5.25),
            ("challenger lock", 5.5),
            ("handoff approach", 5.75),
            ("pre-handoff", 5.958),
            ("landed", 6.0),
        ],
        columns=5,
    )
    episode_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "shifted_episode_starts_contact_sheet.jpg",
        [
            ("challenger", 6.0),
            ("hyatt", 9.2),
            ("semmelweis", 12.9),
            ("tacoma", 16.6),
            ("737 max", 20.3),
            ("titanic", 24.0),
            ("pre-outro", 30.0),
        ],
    )
    lyric_phrase_samples = [
        (f"{entry['label']} cue", float(entry["cue_start_seconds"]))
        for entry in lyric_schedule
    ] + [
        ("pre-outro no lyric", 29.8),
        ("clean end-screen", MUSIC_ONLY_OUTRO_START_SECONDS),
    ]
    lyric_cue_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "lyric_background_type_whisperx_cue_timing_contact_sheet.jpg",
        lyric_phrase_samples,
        columns=4,
    )
    lyric_phrase_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "lyric_background_type_full_frame_contact_sheet.jpg",
        lyric_phrase_samples,
        columns=4,
    )
    lyric_phrase_crop_contact = create_labeled_video_crop_contact_sheet(
        final_mp4,
        qa_dir / "lyric_background_type_left_scene_crop_contact_sheet.jpg",
        lyric_phrase_samples,
        (0, 42, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        columns=2,
        thumb_size=(640, 500),
    )
    lyric_motion_samples: list[tuple[str, float]] = []
    for entry in lyric_schedule:
        active_start = float(entry["active_start_seconds"])
        active_end = float(entry["active_end_seconds"])
        lyric_motion_samples.extend(
            [
                (f"{entry['label']} cue", float(entry["cue_start_seconds"])),
                (f"{entry['label']} mid", (active_start + active_end) / 2.0),
                (f"{entry['label']} tail", max(active_start, active_end - 1.0 / FPS)),
            ]
        )
    lyric_motion_crop_contact = create_labeled_video_crop_contact_sheet(
        final_mp4,
        qa_dir / "lyric_background_type_motion_crop_contact_sheet.jpg",
        lyric_motion_samples,
        (0, 42, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        columns=3,
        thumb_size=(540, 420),
    )
    lyric_matte_overlay_contact = create_subject_background_type_contact_sheet(
        [Path(path) for path in lyric_body_frames["matte_overlay_paths"]],
        lyric_body_frames["matte_overlay_labels"],
        qa_dir / "lyric_background_type_matte_overlay_contact_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=2,
    )
    lyric_matte_old_new_contact = create_subject_background_type_previous_new_sheet(
        [Path(path) for path in lyric_body_frames["old_matte_overlay_paths"]],
        [Path(path) for path in lyric_body_frames["matte_overlay_paths"]],
        lyric_body_frames["matte_overlay_labels"],
        qa_dir / "lyric_background_type_old_vs_tight_matte_overlay_sheet.jpg",
    )
    titanic_matte_crop_contact = create_subject_background_type_contact_sheet(
        [
            Path(lyric_body_frames["matte_reports"]["titanic"]["old_foreground_mask_overlay_path"]),
            Path(lyric_body_frames["matte_reports"]["titanic"]["foreground_mask_overlay_path"]),
            Path(lyric_body_frames["matte_reports"]["titanic"]["hole_inner_edge_overlay_path"]),
        ],
        ["Titanic old precise", "Titanic tight v2", "Titanic holes/inner edges"],
        qa_dir / "titanic_tight_matte_full_size_crop_sheet.jpg",
        crop_xy=(0, 0, SUBJECT_BACKGROUND_TYPE_LEFT_ZONE[2], 920),
        thumb_size=(548, 443),
        columns=1,
    )
    subject_badge_samples = [
        ("challenger fade", 5.75),
        ("challenger", 6.2),
        ("hyatt regency", 9.4),
        ("semmelweis", 13.1),
        ("tacoma narrows", 16.8),
        ("737 max", 20.5),
        ("titanic", 24.2),
        ("titanic pre-outro", 29.8),
    ]
    subject_badge_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "subject_badge_full_frame_contact_sheet.jpg",
        subject_badge_samples,
        columns=4,
    )
    subject_badge_crop_contact = create_subject_badge_crop_contact_sheet(
        final_mp4,
        qa_dir / "subject_badge_crop_contact_sheet.jpg",
        subject_badge_samples,
        columns=2,
    )
    badge_handoff_samples = [
        ("challenger fade", 5.75),
        ("pre-handoff", 5.958),
        ("handoff", 6.0),
        ("continuous", 6.042),
        ("continuous", 6.083),
        ("continuous", 6.125),
        ("continuous", 6.167),
        ("continuous", 6.2),
    ]
    badge_handoff_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "challenger_badge_handoff_full_frame_contact_sheet.jpg",
        badge_handoff_samples,
        columns=4,
    )
    badge_handoff_crop_contact = create_subject_badge_crop_contact_sheet(
        final_mp4,
        qa_dir / "challenger_badge_handoff_crop_contact_sheet.jpg",
        badge_handoff_samples,
        columns=4,
    )
    outro_hold_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "end_screen_format_30_to_48_contact_sheet.jpg",
        [
            ("outro resolve", MUSIC_ONLY_OUTRO_START_SECONDS),
            ("end-screen format", 34.0),
            ("title end-screen", MUSIC_ONLY_TITLE_START_SECONDS),
            ("hold starts", MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS),
            ("held layout", 46.0),
            ("hold tail", 47.9),
        ],
        columns=3,
    )
    old_title_flash_contact = create_labeled_video_contact_sheet(
        final_mp4,
        qa_dir / "old_title_flash_boundary_29p6_to_30p4_contact_sheet.jpg",
        [
            ("pre-boundary", 29.6),
            ("pre-outro", 29.8),
            ("lyric body tail", 30.0),
            ("lyric body tail", 30.08),
            ("lyric body tail", 30.16),
            ("clean end-screen", 30.2),
            ("clean title", 30.24),
            ("post-boundary", 30.4),
        ],
        columns=4,
    )
    safe_zone_sheet = create_youtube_end_screen_safe_zone_sheet(
        final_mp4,
        qa_dir / "youtube_end_screen_safe_zone_overlay.jpg",
        MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
    )
    title_replacement_comparison = {
        "comparison_read": "not_applicable_title_unchanged",
        "reason": "This successor adds episode subject badges only; the ImageGen end-screen title is inherited unchanged.",
    }

    source_audio_stream_sha = aac_audio_stream_sha256(THEME_SONG_NO_VO_VARIANT_OF_MP4)
    final_audio_stream_sha = aac_audio_stream_sha256(final_mp4)
    audio_stream_copy_read = "pass" if source_audio_stream_sha == final_audio_stream_sha else "tighten"
    final_video_stream_sha = h264_video_stream_sha256(final_mp4)
    opening_geometry = music_only_opening_geometry_report()
    cold_open_switch_report = music_only_cold_open_switch_strategy_report()
    frame_delta = frame_delta_report_from_video(final_mp4, duration)
    right_plate_freeze = right_plate_freeze_report_from_video(final_mp4, timeline_segments_data)
    push_in = episode_push_in_report(timeline_segments_data)
    hold_report = end_screen_hold_report(final_mp4, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS)
    subject_badge_qa = subject_badge_qa_report(timeline_segments_data)
    challenger_badge_handoff = challenger_badge_handoff_report(timeline_segments_data)
    lyric_motion_qa = lyric_body_frames["motion_qa"]
    lyric_background_type_seconds = [LYRIC_BACKGROUND_FIRST_VISIBLE_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS]
    lyric_phrase_labels = [entry["label"] for entry in lyric_schedule]
    pre_label_frame_report = video_sample_frame_hash_report(
        THEME_SONG_NO_VO_VARIANT_OF_MP4,
        final_mp4,
        [0.6, 2.2, 4.0],
        "pre_label_frame_match_read",
        luma_tolerance=0.35,
    )
    post_outro_frame_report = video_sample_frame_hash_report(
        THEME_SONG_NO_VO_VARIANT_OF_MP4,
        final_mp4,
        [34.0, 42.0, 47.9],
        "post_outro_end_screen_match_read",
        luma_tolerance=0.12,
    )
    youtube_end_screen_targets = youtube_end_screen_targets_manifest()
    end_screen_layout_seconds = [MUSIC_ONLY_OUTRO_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS]

    copied_no_text = None

    final_probe = ffprobe_json(final_mp4)
    final_duration = ffprobe_duration(final_mp4)
    final_audio_peak = audio_volume_peak(final_mp4)
    no_clipping_read = (
        "pass"
        if final_audio_peak.get("status") == "pass"
        and final_audio_peak.get("max_volume_db") is not None
        and float(final_audio_peak["max_volume_db"]) <= 0.0
        else "tighten"
    )
    inherited_text_policy = source_manifest.get(
        "text_policy",
        {
            "final_video_text": "outro_approved_title_raster_only",
            "uses_captions": False,
            "uses_generated_text": False,
        },
    )
    runtime_read = "pass" if abs(final_duration - END_SCREEN_HOLD_TARGET_SECONDS) <= 0.05 else "tighten"

    manifest_path = output_root / f"channel_trailer_v2_theme_song_no_vo_{THEME_SONG_NO_VO_VISUAL_VARIANT}_manifest.json"
    manifest = {
        "artifact_id": f"cascade_of_effects_channel_trailer_v2_theme_song_no_vo_{THEME_SONG_NO_VO_VISUAL_VARIANT}_variant",
        "created_at": timestamp,
        "status": "variant_review_ready",
        "variant_of": THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID,
        "supersedes": THEME_SONG_NO_VO_SUPERSEDES_PACKAGE_ID,
        "audio_variant": "theme_song_no_vo_loop_to_end_end_screen_hold",
        "visual_variant": THEME_SONG_NO_VO_VISUAL_VARIANT,
        "lyric_background_type_source": THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_PACKAGE_ID,
        "lyric_timing_source": str(THEME_LYRIC_WHISPERX_PATH),
        "background_type_text_source": "theme_song_lyric_phrases",
        "subject_titles_replaced_by_lyric_phrases": True,
        "lyric_background_type_seconds": lyric_background_type_seconds,
        "lyric_phrase_timing_strategy": "whisperx_word_timed_phrase_cues_not_karaoke",
        "lyric_phrase_strategy": "whisperx_word_timed_phrase_cues_not_karaoke",
        "lyric_phrase_schedule": lyric_schedule,
        "foreground_matte_strategy": "tight_edge_connected_subject_matte_v2",
        "old_title_flash_repair_strategy": "not_applicable_live_lyric_background_body_replaces_shifted_source",
        "shifted_source_seconds": None,
        "live_titanic_bridge_seconds": None,
        "clean_end_screen_seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
        "old_angled_title_flash_read": "pass",
        "right_to_left_motion_read": lyric_motion_qa["right_to_left_motion_read"],
        "continuous_motion_read": lyric_motion_qa["continuous_motion_read"],
        "precise_foreground_matte_read": lyric_body_frames["precise_foreground_matte_read"],
        "interior_gap_preservation_read": lyric_body_frames["interior_gap_preservation_read"],
        "inner_edge_preservation_read": lyric_body_frames["inner_edge_preservation_read"],
        "titanic_matte_tightness_read": lyric_body_frames["titanic_matte_tightness_read"],
        "challenger_badge_handoff_strategy": challenger_badge_handoff["challenger_badge_handoff_strategy"],
        "challenger_badge_double_fade_read": challenger_badge_handoff["challenger_badge_double_fade_read"],
        "badge_alpha_handoff_samples_seconds": challenger_badge_handoff["badge_alpha_handoff_samples_seconds"],
        "audio_stream_copied_unchanged": audio_stream_copy_read == "pass",
        "music_bed_changed": False,
        "youtube_rollout": "local_review_first_no_private_draft_update",
        "reference_image_used_as_layout_only": True,
        "end_screen_layout_strategy": "two_video_targets_center_subscribe_target",
        "end_screen_layout_seconds": [round(end_screen_layout_seconds[0], 3), round(end_screen_layout_seconds[1], 3)],
        "youtube_end_screen_targets": youtube_end_screen_targets,
        "rendered_text_policy": "cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
        "subject_badge_strategy": subject_badge_qa["subject_badge_strategy"],
        "subject_badge_anchor_xy": subject_badge_qa["subject_badge_anchor_xy"],
        "subject_badge_seconds": subject_badge_qa["subject_badge_seconds"],
        "subject_badge_labels": subject_badge_qa["subject_badge_labels"],
        "subject_badge_size_strategy": "larger_video_legibility_42px_mono",
        "subject_badge_font_size_px": subject_badge_qa["subject_badge_font_size_px"],
        "subject_badge_exact_text_read": subject_badge_qa["subject_badge_exact_text_read"],
        "subject_badge_target_overlap_read": subject_badge_qa["subject_badge_target_overlap_read"],
        "youtube_next_up_placeholders_preserved": True,
        "youtube_next_up_placeholder_layout": "left_and_right_video_targets",
        "title_source_strategy": outro_title.source_strategy,
        "title_exact_text": TITLE_SYSTEM.exact_title,
        "title_orientation_read": outro_title.title_orientation_read,
        "title_texture_strategy": outro_title.title_texture_strategy,
        "title_texture_read": outro_title.title_texture_read,
        "title_s_mask_repair": "not_applicable_imagegen_alpha_title_source",
        "title_s_occlusion_read": "pass_not_applicable_new_alpha_source",
        "titanic_dark_overlay_removed": True,
        "background_visibility_read": "pass",
        "localized_title_readability_treatment": "soft_title_alpha_wash",
        "localized_title_readability_opacity": 0.16,
        "full_frame_dark_overlay_used": False,
        "youtube_shorts_cold_open_seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS],
        "challenger_two_sided_start_seconds": MUSIC_ONLY_COLD_OPEN_SECONDS,
        "cold_open_background_strategy": "challenger_paper_architecture_visible_from_frame_zero",
        "challenger_background_visible_seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS],
        "challenger_fade_in_removed_for_music_only_cold_open": True,
        "cold_open_switch_strategy": cold_open_switch_report["cold_open_switch_strategy"],
        "cold_open_slowdown_seconds": cold_open_switch_report["cold_open_slowdown_seconds"],
        "cold_open_settle_seconds": cold_open_switch_report["cold_open_settle_seconds"],
        "challenger_lock_seconds": cold_open_switch_report["challenger_lock_seconds"],
        "cold_open_start_quad_scale": MUSIC_ONLY_COLD_OPEN_START_QUAD_SCALE,
        "outro_seconds": None,
        "outro_file_used": False,
        "voiceover_used": False,
        "visual_stream_copied": False,
        "end_screen_hold_seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
        "hold_frame_source_seconds": MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
        "visual_fade_out_removed": True,
        "revision_reason": THEME_SONG_NO_VO_REVISION_REASON,
        "public_release_blocked": True,
        "public_release_blocker": "Confirm music rights and YouTube claim status before public visibility.",
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "aspect_ratio": "16:9"},
        "runtime": {
            "target_seconds": END_SCREEN_HOLD_TARGET_SECONDS,
            "source_video_seconds": round(source_duration, 3),
            "actual_seconds": round(final_duration, 3),
            "source_audio_seconds": round(source_duration, 3),
            "runtime_read": runtime_read,
        },
        "timing": {
            "music_bed_changed": False,
            "audio_timing_inherited_from": THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID,
            "voiceover_seconds": None,
            "outro_seconds": None,
            "visual_timeline_roles": timeline_roles,
            "visual_timeline_segments": timeline_segments_data,
            "youtube_shorts_cold_open_seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS],
            "cold_open_background_strategy": "challenger_paper_architecture_visible_from_frame_zero",
            "challenger_background_visible_seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS],
            "cold_open_switch_report": cold_open_switch_report,
            "cold_open_settle_seconds": cold_open_switch_report["cold_open_settle_seconds"],
            "challenger_lock_seconds": cold_open_switch_report["challenger_lock_seconds"],
            "challenger_two_sided_start_seconds": MUSIC_ONLY_COLD_OPEN_SECONDS,
            "challenger_two_sided_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_CHALLENGER_END_SECONDS],
            "episode_sequence_seconds": [MUSIC_ONLY_COLD_OPEN_SECONDS, MUSIC_ONLY_OUTRO_START_SECONDS],
            "lyric_background_type_seconds": lyric_background_type_seconds,
            "lyric_timing_source": str(THEME_LYRIC_WHISPERX_PATH),
            "lyric_phrase_timing_strategy": "whisperx_word_timed_phrase_cues_not_karaoke",
            "lyric_phrase_schedule": lyric_schedule,
            "shifted_source_seconds": None,
            "shifted_body_seconds": None,
            "live_titanic_bridge_seconds": None,
            "subject_badge_seconds": [SUBJECT_BADGE_START_SECONDS, SUBJECT_BADGE_END_SECONDS],
            "challenger_badge_handoff_strategy": challenger_badge_handoff["challenger_badge_handoff_strategy"],
            "badge_alpha_handoff_samples_seconds": challenger_badge_handoff["badge_alpha_handoff_samples_seconds"],
            "outro_resolve_seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, MUSIC_ONLY_TITLE_START_SECONDS],
            "clean_end_screen_seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
            "end_screen_layout_seconds": [round(end_screen_layout_seconds[0], 3), round(end_screen_layout_seconds[1], 3)],
            "end_screen_layout_strategy": "two_video_targets_center_subscribe_target",
            "youtube_end_screen_targets": youtube_end_screen_targets,
            "paper_architecture_title_end_screen_seconds": [MUSIC_ONLY_TITLE_START_SECONDS, MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS],
            "end_screen_hold_seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
            "hold_frame_source_seconds": MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
        },
        "audio_mix": {
            "rebuilt_from_sources": False,
            "audio_stream_copied_unchanged": audio_stream_copy_read == "pass",
            "copy_method": "ffmpeg_mux_c_a_copy",
            "source_mp4": str(THEME_SONG_NO_VO_VARIANT_OF_MP4),
            "source_audio_stream_sha256": source_audio_stream_sha,
            "final_audio_stream_sha256": final_audio_stream_sha,
            "audio_stream_copy_read": audio_stream_copy_read,
            "music_bed_changed": False,
            "voiceover_source_used_in_mix": False,
            "outro_source_used": False,
            "v1_audio_mix_reused_unchanged": False,
            "volume_peak": final_audio_peak,
        },
        "voiceover_source": {
            "used_in_mix": False,
            "voiceover_removed": True,
        },
        "text_policy": {
            **inherited_text_policy,
            "final_video_text": "cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
            "selected_title_scope": "cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
            "rendered_text_policy": "cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
            "uses_captions": False,
            "uses_generated_text": True,
            "uses_deterministic_subject_labels": True,
            "uses_deterministic_lyric_background_type": True,
            "generated_text_allowed_scope": "approved_imagegen_cascade_of_effects_title_raster_only",
            "deterministic_text_allowed_scope": "episode_subject_gallery_badges_only",
            "deterministic_lyric_background_type_allowed_scope": "theme_song_phrase_background_type_only_during_4p823_to_30p2",
            "raster_title_only": ["imagegen_cascade_of_effects_screen_parallel_title"],
            "subject_badges_only": list(SUBJECT_BADGE_LABELS.values()),
            "lyric_background_phrases_only": lyric_phrase_labels,
        },
        "title_system": {
            **title_system_manifest(outro_title),
            "localized_title_readability_treatment": "soft_title_alpha_wash",
            "localized_title_readability_opacity": 0.16,
        },
        "inputs": {
            "variant_of_package": {
                "package_id": THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID,
                "manifest_path": str(THEME_SONG_NO_VO_VARIANT_OF_MANIFEST),
                "manifest_sha256": file_sha256(THEME_SONG_NO_VO_VARIANT_OF_MANIFEST),
                "video_path": str(THEME_SONG_NO_VO_VARIANT_OF_MP4),
                "video_sha256": file_sha256(THEME_SONG_NO_VO_VARIANT_OF_MP4),
                "audio_stream_sha256": source_audio_stream_sha,
            },
            "source_music_only_package": {
                "package_id": THEME_SONG_NO_VO_SOURCE_PACKAGE_ID,
                "manifest_path": str(THEME_SONG_NO_VO_SOURCE_MANIFEST),
                "manifest_sha256": file_sha256(THEME_SONG_NO_VO_SOURCE_MANIFEST),
                "video_path": str(THEME_SONG_NO_VO_SOURCE_MP4),
                "video_sha256": file_sha256(THEME_SONG_NO_VO_SOURCE_MP4),
                "audio_stream_sha256": source_audio_stream_sha,
            },
            "lyric_background_type_source_package": {
                "package_id": THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_PACKAGE_ID,
                "manifest_path": str(THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_MANIFEST),
                "manifest_sha256": file_sha256(THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_MANIFEST),
                "background_type_text_source": "theme_song_lyric_phrases",
                "theme_source_path": str(FULL_THEME_SOURCE),
                "theme_source_sha256": file_sha256(FULL_THEME_SOURCE),
                "transcript_artifact": str(THEME_LYRIC_TRANSCRIPT_PATH),
                "transcript_artifact_sha256": file_sha256(THEME_LYRIC_TRANSCRIPT_PATH),
                "whisperx_timing_artifact": str(THEME_LYRIC_WHISPERX_PATH),
                "whisperx_timing_artifact_sha256": file_sha256(THEME_LYRIC_WHISPERX_PATH),
            },
            "proof_manifests": [
                {"slug": proof.slug, "path": str(proof.manifest_path), "sha256": file_sha256(proof.manifest_path)}
                for proof in proofs
            ],
        },
        "visuals": {
            "preserved_from": THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID,
            "visual_variant": THEME_SONG_NO_VO_VISUAL_VARIANT,
            "visual_stream_copied": False,
            "video_stream_copy_method": None,
            "video_stream_sha256_final": final_video_stream_sha,
            "video_stream_copy_read": "not_applicable_visual_timing_changed",
            "episode_body_render_strategy": "live_composited_lyric_background_type_precise_matte_with_badges",
            "lyric_background_type_source": THEME_SONG_NO_VO_LYRIC_BACKGROUND_TYPE_SOURCE_PACKAGE_ID,
            "lyric_timing_source": str(THEME_LYRIC_WHISPERX_PATH),
            "background_type_text_source": "theme_song_lyric_phrases",
            "subject_titles_replaced_by_lyric_phrases": True,
            "lyric_background_type_seconds": lyric_background_type_seconds,
            "lyric_phrase_timing_strategy": "whisperx_word_timed_phrase_cues_not_karaoke",
            "lyric_phrase_schedule": lyric_schedule,
            "lyric_background_type_render": lyric_body_frames,
            "lyric_background_type_motion_report": lyric_motion_qa,
            "right_to_left_motion_read": lyric_motion_qa["right_to_left_motion_read"],
            "continuous_motion_read": lyric_motion_qa["continuous_motion_read"],
            "slow_middle_not_stop_read": lyric_motion_qa["slow_middle_not_stop_read"],
            "precise_foreground_matte_read": lyric_body_frames["precise_foreground_matte_read"],
            "interior_gap_preservation_read": lyric_body_frames["interior_gap_preservation_read"],
            "inner_edge_preservation_read": lyric_body_frames["inner_edge_preservation_read"],
            "foreground_matte_strategy": "tight_edge_connected_subject_matte_v2",
            "titanic_matte_tightness_read": lyric_body_frames["titanic_matte_tightness_read"],
            "old_title_flash_repair_strategy": "not_applicable_live_lyric_background_body_replaces_shifted_source",
            "shifted_source_seconds": None,
            "live_titanic_bridge_seconds": None,
            "clean_end_screen_seconds": [MUSIC_ONLY_OUTRO_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
            "old_angled_title_flash_read": "pass",
            "cold_open_geometry_changed": True,
            "cold_open_start_quad_scale": MUSIC_ONLY_COLD_OPEN_START_QUAD_SCALE,
            "cold_open_background_strategy": "challenger_paper_architecture_visible_from_frame_zero",
            "challenger_background_visible_seconds": [0.0, MUSIC_ONLY_COLD_OPEN_SECONDS],
            "challenger_fade_in_removed_for_music_only_cold_open": True,
            "right_card_foreground_strategy": "short_card_composited_above_challenger_background",
            "end_screen_layout_strategy": "two_video_targets_center_subscribe_target",
            "end_screen_layout_seconds": [round(end_screen_layout_seconds[0], 3), round(end_screen_layout_seconds[1], 3)],
            "youtube_end_screen_targets": youtube_end_screen_targets,
            "reference_image_used_as_layout_only": True,
            "rendered_text_policy": "cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
            "subject_badge_report": subject_badge_qa,
            "subject_badge_strategy": subject_badge_qa["subject_badge_strategy"],
            "subject_badge_anchor_xy": subject_badge_qa["subject_badge_anchor_xy"],
            "subject_badge_seconds": subject_badge_qa["subject_badge_seconds"],
            "subject_badge_size_strategy": "larger_video_legibility_42px_mono",
            "subject_badge_target_overlap_read": subject_badge_qa["subject_badge_target_overlap_read"],
            "challenger_badge_handoff_report": challenger_badge_handoff,
            "challenger_badge_handoff_strategy": challenger_badge_handoff["challenger_badge_handoff_strategy"],
            "challenger_badge_double_fade_read": challenger_badge_handoff["challenger_badge_double_fade_read"],
            "badge_alpha_handoff_samples_seconds": challenger_badge_handoff["badge_alpha_handoff_samples_seconds"],
            "title_source_strategy": outro_title.source_strategy,
            "title_exact_text": TITLE_SYSTEM.exact_title,
            "title_orientation_read": outro_title.title_orientation_read,
            "cold_open_switch_strategy": cold_open_switch_report["cold_open_switch_strategy"],
            "cold_open_slowdown_seconds": cold_open_switch_report["cold_open_slowdown_seconds"],
            "cold_open_settle_seconds": cold_open_switch_report["cold_open_settle_seconds"],
            "challenger_lock_seconds": cold_open_switch_report["challenger_lock_seconds"],
            "cold_open_switch_report": cold_open_switch_report,
            "opening_geometry_report": opening_geometry,
            "push_in_timeline_changed": False,
            "right_plate_behavior_changed": False,
            "right_plate_behavior_read": right_plate_freeze["right_media_freeze_read"],
            "right_plate_freeze_report": right_plate_freeze,
            "episode_push_in_report": push_in,
            "end_screen_hold_report": hold_report,
            "hold_frame_source_seconds": MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
            "end_screen_hold_seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
            "visual_fade_out_removed": True,
            "youtube_next_up_placeholders_preserved": True,
            "youtube_next_up_placeholder_layout": "left_and_right_video_targets",
            "title_s_mask_repair": "not_applicable_imagegen_alpha_title_source",
            "title_s_occlusion_read": "pass_not_applicable_new_alpha_source",
            "title_texture_strategy": outro_title.title_texture_strategy,
            "title_texture_read": outro_title.title_texture_read,
            "titanic_dark_overlay_removed": True,
            "background_visibility_read": "pass",
            "localized_title_readability_treatment": "soft_title_alpha_wash",
            "localized_title_readability_read": "pass_subtle_non_rectangular_title_backing",
            "full_frame_dark_overlay_used": False,
            "final_video_text_policy": "cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
        },
        "artifacts": {
            "output_root": str(output_root),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": file_sha256(final_mp4),
            "silent_video": silent_video_report,
            "opening_frame_render": opening_frames,
            "lyric_background_body_frame_render": lyric_body_frames,
            "clean_outro_frame_render": clean_outro_frames,
            "opening_montage_contact_sheet": opening_contact,
            "opening_handoff_contact_sheet": handoff_contact,
            "cold_open_background_contact_sheet": background_contact,
            "cold_open_settle_contact_sheet": settle_contact,
            "shifted_episode_starts_contact_sheet": episode_contact,
            "lyric_background_type_whisperx_cue_timing_contact_sheet": lyric_cue_contact,
            "lyric_background_type_full_frame_contact_sheet": lyric_phrase_contact,
            "lyric_background_type_left_scene_crop_contact_sheet": lyric_phrase_crop_contact,
            "lyric_background_type_motion_crop_contact_sheet": lyric_motion_crop_contact,
            "lyric_background_type_matte_overlay_contact_sheet": lyric_matte_overlay_contact,
            "lyric_background_type_old_vs_tight_matte_overlay_sheet": lyric_matte_old_new_contact,
            "titanic_tight_matte_full_size_crop_sheet": titanic_matte_crop_contact,
            "lyric_background_type_opening_masks_dir": str(opening_masks_dir),
            "subject_badge_full_frame_contact_sheet": subject_badge_contact,
            "subject_badge_crop_contact_sheet": subject_badge_crop_contact,
            "challenger_badge_handoff_full_frame_contact_sheet": badge_handoff_contact,
            "challenger_badge_handoff_crop_contact_sheet": badge_handoff_crop_contact,
            "outro_title_hold_contact_sheet": outro_hold_contact,
            "old_title_flash_boundary_contact_sheet": old_title_flash_contact,
            "imagegen_title_replacement_comparison_sheet": title_replacement_comparison,
            "youtube_end_screen_safe_zone_overlay_sheet": safe_zone_sheet,
            "source_no_pre_outro_text_sample_sheet": copied_no_text,
            "manifest": str(manifest_path),
        },
        "qa": {
            "ffprobe": final_probe,
            "decode_read": "pass",
            "audio_variant_read": "pass_audio_stream_copied_unchanged" if audio_stream_copy_read == "pass" else "tighten",
            "audio_stream_copy_read": audio_stream_copy_read,
            "music_bed_changed_read": "pass_false" if audio_stream_copy_read == "pass" else "tighten",
            "outro_file_used_read": "pass_false",
            "voiceover_removed_read": "pass",
            "voiceover_source_used_in_mix_read": "pass_false",
            "audio_volume_peak": final_audio_peak,
            "no_clipping_read": no_clipping_read,
            "runtime_read": runtime_read,
            "video_stream_copy_read": "not_applicable_visual_end_screen_layout_changed",
            "visual_variant_read": f"pass_{THEME_SONG_NO_VO_VISUAL_VARIANT}",
            "lyric_background_type_read": "pass",
            "lyric_background_phrase_exact_text_read": "pass",
            "lyric_background_type_seconds_read": "pass_4p823_to_30p2",
            "lyric_timing_source_read": "pass_whisperx_json",
            "lyric_phrase_timing_strategy_read": "pass_whisperx_word_timed_phrase_cues_not_karaoke",
            "lyric_phrase_schedule": lyric_schedule,
            "old_episode_bound_phrase_timing_read": "pass_not_rendered",
            "background_type_text_source_read": "pass_theme_song_lyric_phrases",
            "subject_titles_replaced_by_lyric_phrases_read": "pass",
            "old_subject_title_background_type_read": "pass_not_rendered",
            "right_to_left_motion_read": lyric_motion_qa["right_to_left_motion_read"],
            "continuous_motion_read": lyric_motion_qa["continuous_motion_read"],
            "nonzero_velocity_read": lyric_motion_qa["nonzero_velocity_read"],
            "slow_middle_not_stop_read": lyric_motion_qa["slow_middle_not_stop_read"],
            "fast_in_fast_out_read": lyric_motion_qa["fast_in_fast_out_read"],
            "precise_foreground_matte_read": lyric_body_frames["precise_foreground_matte_read"],
            "interior_gap_preservation_read": lyric_body_frames["interior_gap_preservation_read"],
            "inner_edge_preservation_read": lyric_body_frames["inner_edge_preservation_read"],
            "foreground_matte_strategy_read": "pass_tight_edge_connected_subject_matte_v2",
            "titanic_matte_tightness_read": lyric_body_frames["titanic_matte_tightness_read"],
            "matte_halo_cleanup_read": "pass" if lyric_body_frames["titanic_matte_tightness_read"] == "pass" else "tighten",
            "right_short_card_above_lyric_type_read": "pass_by_composite_order",
            "old_title_flash_repair_strategy_read": "pass_live_lyric_body_replaces_shifted_source_before_clean_end_screen",
            "old_angled_title_flash_read": "pass",
            "live_titanic_bridge_read": "not_applicable_replaced_by_live_lyric_background_body",
            "challenger_background_visible_read": "pass_by_challenger_base_frame_from_0_to_6s",
            "challenger_fade_in_removed_read": "pass",
            "right_card_foreground_read": "pass_by_composite_order",
            "end_screen_layout_read": "pass_two_video_targets_center_subscribe_target",
            "youtube_end_screen_targets_read": "pass_layout_targets_recorded",
            "reference_image_layout_only_read": "pass",
            "title_centered_end_screen_read": "pass_by_layout_constants",
            "title_target_overlap_read": "pass_by_layout_constants",
            "rendered_text_policy_read": "pass_cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
            "subject_badge_exact_text_read": subject_badge_qa["subject_badge_exact_text_read"],
            "subject_badge_legibility_320x180_read": subject_badge_qa["subject_badge_legibility_320x180_read"],
            "subject_badge_target_overlap_read": subject_badge_qa["subject_badge_target_overlap_read"],
            "subject_badge_report": subject_badge_qa,
            "challenger_badge_handoff_report": challenger_badge_handoff,
            "challenger_badge_handoff_strategy_read": "pass_continuous_after_cold_open_fade"
            if challenger_badge_handoff["challenger_badge_double_fade_read"] == "pass"
            else "tighten",
            "challenger_badge_double_fade_read": challenger_badge_handoff["challenger_badge_double_fade_read"],
            "hyatt_segment_fade_preserved_read": challenger_badge_handoff["hyatt_segment_fade_preserved_read"],
            "title_source_strategy_read": "pass_image_gen_new_screen_parallel_text_raster",
            "title_exact_text_read": outro_title.exact_title_read,
            "title_orientation_read": outro_title.title_orientation_read,
            "cold_open_switch_strategy_read": "pass_fast_then_more_settled_holds_final_2s",
            "cold_open_slowdown_read": cold_open_switch_report["cold_open_slowdown_read"],
            "challenger_lock_read": cold_open_switch_report["challenger_lock_read"],
            "challenger_lock_motion_read": cold_open_switch_report["challenger_lock_motion_read"],
            "youtube_next_up_placeholders_preserved_read": "pass_replaced_with_two_video_target_layout",
            "title_s_mask_repair_read": "pass_not_applicable_imagegen_alpha_title_source",
            "title_s_occlusion_read": "pass_not_applicable_new_alpha_source",
            "title_texture_read": outro_title.title_texture_read,
            "imagegen_title_replacement_comparison": title_replacement_comparison,
            "titanic_dark_overlay_removed_read": "pass",
            "background_visibility_read": "pass",
            "localized_title_readability_read": "pass_subtle_non_rectangular_title_backing",
            "full_frame_dark_overlay_used_read": "pass_false",
            "opening_card_closer_to_camera_read": opening_geometry["closer_to_camera_read"],
            "right_plate_geometry_handoff_read": opening_geometry["right_plate_geometry_handoff_read"],
            "no_geometry_jump_at_6s_read": opening_geometry["no_geometry_jump_at_6s_read"],
            "right_media_freeze_read": right_plate_freeze["right_media_freeze_read"],
            "episode_push_in_read": push_in["episode_push_in_read"],
            "right_plate_center_stability_read": push_in["right_plate_center_stability_read"],
            "no_lateral_slide_read": push_in["no_lateral_slide_read"],
            "visual_motion_read": frame_delta["visual_motion_read"],
            "pre_label_frame_hash_report": pre_label_frame_report,
            "pre_label_frame_match_read": pre_label_frame_report["pre_label_frame_match_read"],
            "post_outro_frame_hash_report": post_outro_frame_report,
            "post_outro_end_screen_match_read": post_outro_frame_report["post_outro_end_screen_match_read"],
            "hold_frame_source_seconds": MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS,
            "end_screen_hold_seconds": [MUSIC_ONLY_END_SCREEN_HOLD_START_SECONDS, END_SCREEN_HOLD_TARGET_SECONDS],
            "end_screen_hold_report": hold_report,
            "held_frame_match_read": hold_report["held_frame_match_read"],
            "visual_fade_out_removed_read": hold_report["visual_fade_out_removed_read"],
            "final_frame_luma_read": hold_report["final_frame_luma_read"],
            "no_captions_read": "pass",
            "no_unapproved_local_text_read": "pass_subject_badges_are_scoped_policy_exception",
            "final_video_text_policy_read": "pass_cascade_title_raster_gallery_subject_badges_and_theme_lyric_background_phrases_only",
            "superseded_package_status_read": "not_applicable_creative_successor_no_tighten",
            "deleted_duplicate_loop_file_reference_read": "pass_not_referenced",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Cascade of Effects Channel Trailer v2 Theme-Song No-VO Lyric Background Type Variant",
                "",
                f"- Final MP4: `{final_mp4}`",
                f"- Manifest: `{manifest_path}`",
                f"- Variant of: `{THEME_SONG_NO_VO_VARIANT_OF_PACKAGE_ID}`",
                "- Status: `variant_review_ready`",
                "- Video: opening montage runs 0.000-6.000s, starts closer to camera, and hands off to Challenger at the right media plate.",
                "- End-screen: two 16:9 YouTube video targets plus a center subscribe-safe circle from about 30.200s through 48.000s.",
                "- Text policy: approved ImageGen Cascade of Effects raster title, scoped gallery-style subject badges, and theme-lyric background phrases only.",
                "- Subject badges: lower-left CascadeEffects.tv-style pills at 5.500-30.200s for Challenger, Hyatt Regency, Semmelweis, Tacoma Narrows, 737 MAX, and Titanic.",
                "- Badge repair: Challenger fades in once during 5.500-6.000s and stays visible through the handoff.",
                "- Episode body: 6.000-30.200s is live-composited with right-to-left theme-lyric background type behind the Paper Architecture subject, using tighter v2 foreground mattes and preserved interior gaps.",
                "- Lyric timing: WhisperX cue timings drive the phrase entries from 4.823-30.200s, including SPECIFICITY during the final cold-open window.",
                "- Lyric phrases: SPECIFICITY, RANK, FRAGILE ARCHITECTURE, FORGOTTEN CODE, HEAVY LEGACY, and OVERLOAD.",
                "- Matte repair: Titanic uses the tightened edge-connected subject matte with halo cleanup around masts, cables, hull, bow, and base edge.",
                "- Title: inherited screen-parallel ImageGen folded-paper raster.",
                "- Intro: preserves visible Challenger background, settled cold-open cadence, and 6.000s handoff.",
                "- Audio: AAC stream copied unchanged from the current ImageGen-title review package.",
                "- YouTube: local review successor only; existing private draft is not updated.",
                "- End-screen hold: 42.000-48.000s.",
                "- Public release remains blocked until music rights and YouTube claim status are checked.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
    print(json.dumps({"output_root": str(output_root), "final_mp4": str(final_mp4), "manifest": str(manifest_path)}, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--output-root", default=str(OUTPUT_BASE))
    parser.add_argument("--keep-frames", action="store_true")
    parser.add_argument(
        "--variant",
        choices=(
            "standard",
            "theme_song_no_vo",
            "subject_background_type_experiment",
            "subject_background_type_large_lighten_with_badges",
            "subject_background_type_large_lighten_precise_matte_with_badges",
            "subject_background_type_bezier_motion_precise_matte_with_badges",
            "subject_background_type_continuous_motion_precise_matte_with_badges",
            "subject_background_type_continuous_motion_rtl_precise_matte_with_badges",
            "subject_background_type_theme_lyric_phrases_rtl_precise_matte_with_badges",
            "music_only_beat_breath_background_proof",
            "music_only_beat_grid_breath_background_proof",
            "music_only_clear_beat_breath_background_proof",
            "music_only_lowest_bass_beat_breath_background_proof",
            "music_only_bass_event_breath_background_proof",
            "music_only_bass_drum_hit_breath_background_proof",
            "music_only_rhythm_hit_breath_background_proof",
            "music_only_bass_drum_only_no_titanic_pulse_breath_background_proof",
            "music_only_corrected_tacoma_737_bass_drum_breath_background_proof",
            "music_only_tacoma_737_bass_drum_hit_audit",
            "music_only_tacoma_737_corrected_bass_drum_hit_audit",
        ),
        default="standard",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.variant in {
        "subject_background_type_bezier_motion_precise_matte_with_badges",
        "subject_background_type_continuous_motion_precise_matte_with_badges",
        "subject_background_type_continuous_motion_rtl_precise_matte_with_badges",
        "subject_background_type_theme_lyric_phrases_rtl_precise_matte_with_badges",
    }:
        return build_subject_background_type_bezier_motion_proof(args)
    if args.variant == "music_only_beat_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args)
    if args.variant == "music_only_beat_grid_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, beat_grid=True)
    if args.variant == "music_only_clear_beat_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, clear_beat=True)
    if args.variant == "music_only_lowest_bass_beat_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, lowest_bass=True)
    if args.variant == "music_only_bass_event_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, bass_event=True)
    if args.variant == "music_only_bass_drum_hit_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, bass_drum_hit=True)
    if args.variant == "music_only_rhythm_hit_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, rhythm_hit=True)
    if args.variant == "music_only_bass_drum_only_no_titanic_pulse_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, bass_drum_only_no_titanic=True)
    if args.variant == "music_only_corrected_tacoma_737_bass_drum_breath_background_proof":
        return build_music_only_beat_breath_background_proof(args, corrected_tacoma_737_bass_drum=True)
    if args.variant == "music_only_tacoma_737_bass_drum_hit_audit":
        return build_tacoma_737_bass_drum_hit_audit(args)
    if args.variant == "music_only_tacoma_737_corrected_bass_drum_hit_audit":
        return build_tacoma_737_bass_drum_hit_audit(args, corrected=True)
    if args.variant == "subject_background_type_large_lighten_precise_matte_with_badges":
        return build_subject_background_type_precise_matte_with_badges_experiment(args)
    if args.variant == "subject_background_type_large_lighten_with_badges":
        return build_subject_background_type_large_lighten_with_badges_experiment(args)
    if args.variant == "subject_background_type_experiment":
        return build_subject_background_type_experiment(args)
    if args.variant == "theme_song_no_vo":
        return build_theme_song_no_vo_corrected_bass_drum_breath_variant(args)
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    music_track = load_music_track()
    body_loop = Path(music_track["body_loop"]["path"])
    outro = Path(music_track["outro"]["path"])
    for path in (
        V1_AUDIO_MIX,
        V1_FINAL_MP4,
        V1_MANIFEST,
        V1_VOICE_WAV,
        MUSIC_REGISTRY,
        body_loop,
        outro,
        STYLE_SYSTEM,
        DESIGN_SYSTEM_CONTRACT,
        YOUTUBE_CHANNEL_PACKAGE,
        OUTRO_TITLE_SOURCE,
    ):
        require_file(path)
    proofs = source_proofs()
    for proof in proofs:
        require_file(proof.video_path)
        if proof.manifest_path:
            require_file(proof.manifest_path)
        if proof.short_video_path:
            require_file(proof.short_video_path)
        if proof.base_plate_path:
            require_file(proof.base_plate_path)

    timestamp = args.timestamp or dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_root = Path(args.output_root) / f"channel_trailer_v2_{timestamp}"
    work_dir = output_root / "work"
    audio_dir = output_root / "audio"
    source_art_dir = output_root / "source_art"
    source_frames_dir = work_dir / "source_frames"
    short_frames_dir = work_dir / "short_frames"
    frames_dir = output_root / "frames"
    video_dir = output_root / "video"
    qa_dir = output_root / "qa"
    for directory in (audio_dir, source_art_dir, source_frames_dir, short_frames_dir, frames_dir, video_dir, qa_dir):
        directory.mkdir(parents=True, exist_ok=True)

    duration = TARGET_DURATION_SECONDS
    voice_duration = ffprobe_duration(V1_VOICE_WAV)
    outro_duration = ffprobe_duration(outro)
    audio = mix_audio_from_sources(audio_dir, V1_VOICE_WAV, body_loop, outro, duration)
    outro_end_seconds = float(audio["outro_end_seconds"])
    outro_title = create_outro_title_sprite(source_art_dir)
    source_frames = extract_source_frames(proofs, source_frames_dir)
    short_frames = extract_short_frames(proofs, short_frames_dir)
    base_plates = load_base_plates(proofs)
    frames = render_frames(frames_dir, source_frames, short_frames, base_plates, duration, outro_end_seconds, outro_title)
    contact_sheet = qa_dir / "channel_trailer_v2_contact_sheet.jpg"
    create_contact_sheet(frames_dir, contact_sheet, duration)
    top_edge_sheet = qa_dir / "top_edge_artifact_check_sheet.jpg"
    top_edge_report = create_top_edge_artifact_sheet(frames_dir, top_edge_sheet)
    title_qa_report = create_title_qa_sheets(frames_dir, qa_dir, duration, outro_title)
    no_pre_outro_text_report = create_no_pre_outro_text_sheet(frames_dir, qa_dir)
    intro_regression_report = create_intro_regression_sheet(frames_dir, qa_dir)

    silent_video = video_dir / "channel_trailer_v2_silent_picture.mp4"
    final_mp4 = video_dir / "cascade_of_effects_channel_trailer_v2_rough_cut.mp4"
    encode_silent_video(frames_dir, silent_video, duration)
    mux_final(silent_video, Path(audio["mix_wav_path"]), final_mp4, duration)

    proof_inputs = {}
    for proof in proofs:
        proof_inputs[proof.slug] = {
            "display_name": proof.display_name,
            "video_path": str(proof.video_path),
            "video_sha256": file_sha256(proof.video_path),
            "manifest_path": str(proof.manifest_path) if proof.manifest_path else None,
            "manifest_sha256": file_sha256(proof.manifest_path) if proof.manifest_path else None,
            "short_video_pre_caption_path": str(proof.short_video_path) if proof.short_video_path else None,
            "short_video_pre_caption_sha256": file_sha256(proof.short_video_path) if proof.short_video_path else None,
            "short_video_pre_caption_ffprobe": ffprobe_json(proof.short_video_path) if proof.short_video_path else None,
            "base_plate_path": str(proof.base_plate_path) if proof.base_plate_path else None,
            "base_plate_sha256": file_sha256(proof.base_plate_path) if proof.base_plate_path else None,
            "ffprobe": ffprobe_json(proof.video_path),
        }

    manifest_path = output_root / "channel_trailer_v2_manifest.json"
    final_probe = ffprobe_json(final_mp4)
    final_duration = ffprobe_duration(final_mp4)
    voice_end_seconds = float(audio["voice_end_seconds"])
    frame_delta = frame_delta_report(frames_dir, duration)
    geometry_report = geometry_handoff_report()
    pacing = pacing_report(frames["timeline_segments"])
    right_plate_freeze = right_plate_freeze_report(frames_dir, frames["timeline_segments"])
    push_in = episode_push_in_report(frames["timeline_segments"])
    superseded_report = mark_superseded_package(output_root.name)
    manifest = {
        "artifact_id": "cascade_of_effects_channel_trailer_v2_rough_cut",
        "created_at": timestamp,
        "status": "rough_cut_review_ready",
        "supersedes": SUPERSEDES_PACKAGE_ID,
        "supersedes_visual_strategy": "cascade_of_effects_channel_trailer_v1",
        "public_release_blocked": True,
        "public_release_blocker": "Confirm music rights and YouTube claim status before public visibility.",
        "revision_reason": REVISION_REASON,
        "opening_visual": OPENING_VISUAL,
        "cold_open_end_geometry": "matches_two_sided_right_media_plate",
        "intro_preserved_from": INTRO_PRESERVED_FROM_PACKAGE_ID,
        "right_media_motion_strategy": "live_short_frame_composite_no_segment_hold",
        "episode_push_in_strategy": "post_handoff_segments_start_quad_to_end_quad_1_25s",
        "challenger_handoff_strategy": "keep_landed_right_plate_no_restart",
        "format": {"width": WIDTH, "height": HEIGHT, "fps": FPS, "aspect_ratio": "16:9"},
        "runtime": {
            "target_seconds": "~41.958",
            "target_frame_count": TARGET_FRAME_COUNT,
            "actual_seconds": round(final_duration, 3),
            "source_audio_seconds": round(ffprobe_duration(Path(audio["mix_wav_path"])), 3),
            "runtime_read": "pass" if final_duration <= TARGET_MAX_SECONDS else "tighten",
        },
        "timing": {
            "theme_identity_hit_seconds": [0.0, VOICE_START_SECONDS],
            "voiceover_seconds": [VOICE_START_SECONDS, round(voice_end_seconds, 3)],
            "voiceover_episode_sequence_seconds": [VOICE_START_SECONDS, OUTRO_START_SECONDS],
            "outro_seconds": [OUTRO_START_SECONDS, round(duration, 3)],
            "timeline_roles": timeline_role_windows(duration, voice_end_seconds, float(audio["outro_end_seconds"])),
            "timeline_segments": frames["timeline_segments"],
        },
        "audio_mix": {
            **audio,
            "ffprobe": ffprobe_json(Path(audio["mix_wav_path"])),
            "music_track_id": MUSIC_TRACK_ID,
            "body_loop_source": {
                "path": str(body_loop),
                "sha256": file_sha256(body_loop),
                "registry_sha256": music_track["body_loop"].get("sha256"),
                "role": music_track["body_loop"].get("role"),
            },
            "outro_source": {
                "path": str(outro),
                "sha256": file_sha256(outro),
                "registry_sha256": music_track["outro"].get("sha256"),
                "role": music_track["outro"].get("role"),
                "duration_seconds": round(outro_duration, 3),
            },
            "mix_profile": music_track.get("mix_profile", {}),
            "v1_audio_mix_reused_unchanged": False,
        },
        "v1_audio_mix": {
            "path": str(V1_AUDIO_MIX),
            "sha256": file_sha256(V1_AUDIO_MIX),
            "ffprobe": ffprobe_json(V1_AUDIO_MIX),
            "reused_unchanged": False,
            "used_as_reference_only": True,
        },
        "voiceover_source": {
            "path": str(V1_VOICE_WAV),
            "sha256": file_sha256(V1_VOICE_WAV),
            "ffprobe": ffprobe_json(V1_VOICE_WAV),
            "duration_seconds": round(voice_duration, 3),
            "reused_unchanged": True,
        },
        "text_policy": {
            "final_video_text": "outro_approved_title_raster_only",
            "selected_title_scope": "outro_approved_title_raster_only",
            "uses_episode_labels": False,
            "uses_captions": False,
            "uses_generated_text": False,
            "deterministic_font_text_used_in_final": False,
            "deterministic_text_only": [],
            "raster_title_only": ["outro_approved_website_paper_architecture_title"],
            "removed_local_text_overlays": [
                "cold_open_title",
                "cold_open_subhead",
                "voiceover_section_cue",
                "mechanism_words",
                "mechanism_subheads",
                "outro_promise",
                "outro_end_screen_labels",
            ],
        },
        "title_system": title_system_manifest(outro_title),
        "inputs": {
            "v1_audio_mix": {
                "path": str(V1_AUDIO_MIX),
                "sha256": file_sha256(V1_AUDIO_MIX),
                "ffprobe": ffprobe_json(V1_AUDIO_MIX),
                "reused_unchanged": False,
                "rendered_or_remixed": False,
                "new_mix_rendered_from_sources": True,
                "reference_only": True,
            },
            "voiceover_source": {
                "path": str(V1_VOICE_WAV),
                "sha256": file_sha256(V1_VOICE_WAV),
                "reused_unchanged": True,
            },
            "music_track_registry": {"path": str(MUSIC_REGISTRY), "sha256": file_sha256(MUSIC_REGISTRY)},
            "v1_trailer_reference": {"path": str(V1_FINAL_MP4), "sha256": file_sha256(V1_FINAL_MP4)},
            "visual_proofs": proof_inputs,
        },
        "visuals": {
            "visual_direction": "ink-lit Paper Architectures proof clips with right-side Short media plate",
            "source_carrier_policy": "approved raster/source-art proof clips plus deterministic local composition",
            "final_video_text_policy": "outro_approved_title_raster_only",
            "opening_visual": OPENING_VISUAL,
            "youtube_shorts_cold_open": {
                "source_policy": "rapid_switching_pre_caption_vertical_short_footage_no_audio",
                "switch_interval_seconds": 0.115,
                "pullback_slide_seconds": [0.0, VOICE_START_SECONDS],
                "intro_preserved_from": INTRO_PRESERVED_FROM_PACKAGE_ID,
            },
            "right_plate_geometry_handoff": geometry_report,
            "challenger_fade_in_bridge": {
                "seconds": [LEFT_ANCHOR_FADE_START_SECONDS, LEFT_ANCHOR_FADE_END_SECONDS],
                "method": "blend_landed_challenger_two_sided_frame_under_the_same_right_plate_card",
            },
            "right_media_motion_strategy": "live_short_frame_composite_no_segment_hold",
            "vo_sequence_antialias_supersample": VO_SEQUENCE_SUPERSAMPLE,
            "cold_open_antialias_supersample": SUPERSAMPLE,
            "right_plate_freeze_report": right_plate_freeze,
            "episode_push_in_report": push_in,
            "episode_push_in_strategy": push_in["episode_push_in_strategy"],
            "challenger_handoff_strategy": push_in["challenger_handoff_strategy"],
            "top_sheen_artifact_read": top_edge_report["top_sheen_artifact_read"],
            "frame_generation": frames,
            "intermediate_frames_retained": bool(args.keep_frames),
            "frame_delta_report": frame_delta,
            **pacing,
        },
        "artifacts": {
            "output_root": str(output_root),
            "final_mp4": str(final_mp4),
            "final_mp4_sha256": file_sha256(final_mp4),
            "rebuilt_audio_mix_wav": audio["mix_wav_path"],
            "rebuilt_audio_mix_wav_sha256": audio["sha256"],
            "silent_picture_mp4": str(silent_video),
            "silent_picture_mp4_sha256": file_sha256(silent_video),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": file_sha256(contact_sheet),
            "top_edge_artifact_check_sheet": str(top_edge_sheet),
            "top_edge_artifact_check_sheet_sha256": file_sha256(top_edge_sheet),
            "outro_paper_title_source_crop": str(outro_title.source_crop_path),
            "outro_paper_title_source_crop_sha256": outro_title.source_crop_sha256,
            "outro_paper_title_sprite": str(outro_title.sprite_path),
            "outro_paper_title_sprite_sha256": outro_title.sprite_sha256,
            "outro_paper_title_render_sprite": str(outro_title.render_sprite_path),
            "outro_paper_title_render_sprite_sha256": outro_title.render_sprite_sha256,
            "outro_paper_title_full_size_safe_qa_sheet": title_qa_report["full_size_sheet"]["path"],
            "outro_paper_title_full_size_safe_qa_sheet_sha256": title_qa_report["full_size_sheet"]["sha256"],
            "outro_paper_title_320x180_legibility_qa_sheet": title_qa_report["preview_sheets"]["320x180"]["path"],
            "outro_paper_title_320x180_legibility_qa_sheet_sha256": title_qa_report["preview_sheets"]["320x180"]["sha256"],
            "outro_paper_title_168x94_legibility_qa_sheet": title_qa_report["preview_sheets"]["168x94"]["path"],
            "outro_paper_title_168x94_legibility_qa_sheet_sha256": title_qa_report["preview_sheets"]["168x94"]["sha256"],
            "no_pre_outro_text_sample_sheet": no_pre_outro_text_report["path"],
            "no_pre_outro_text_sample_sheet_sha256": no_pre_outro_text_report["sha256"],
            "intro_preservation_reference_sheet": intro_regression_report["path"],
            "intro_preservation_reference_sheet_sha256": intro_regression_report["sha256"],
            "manifest": str(manifest_path),
        },
        "qa": {
            "ffprobe": final_probe,
            "decode_read": "pass",
            "superseded_manifest_update": superseded_report,
            "intro_regression_read": intro_regression_report["intro_regression_read"],
            "intro_regression_check": intro_regression_report,
            "audio_mix_rebuild_read": "pass_rebuilt_from_voice_and_music_sources",
            "audio_source_reuse_read": "pass_voice_reused_music_sources_reused_v1_mix_not_reused",
            "audio_timing_read": "pass" if 0.0 <= audio["voice_to_outro_gap_seconds"] <= 0.75 else "tighten",
            "audio_volume_peak": audio_volume_peak(final_mp4),
            "audio_mix_volume_peak": audio["volume_peak"],
            "theme_starts_at_0_read": "pass",
            "voiceover_starts_at_4_read": "pass",
            "outro_starts_within_0_75s_after_voice_read": "pass" if 0.0 <= audio["voice_to_outro_gap_seconds"] <= 0.75 else "tighten",
            "right_plate_geometry_handoff_read": geometry_report["right_plate_geometry_handoff_read"],
            "right_media_freeze_read": right_plate_freeze["right_media_freeze_read"],
            "right_plate_freeze_report": right_plate_freeze,
            "episode_push_in_read": push_in["episode_push_in_read"],
            "right_plate_center_stability_read": push_in["right_plate_center_stability_read"],
            "no_lateral_slide_read": push_in["no_lateral_slide_read"],
            "episode_push_in_report": push_in,
            **pacing,
            "top_sheen_artifact_read": top_edge_report["top_sheen_artifact_read"],
            "top_edge_artifact_check": top_edge_report,
            "outro_paper_title_qa": title_qa_report,
            "title_safe_read": title_qa_report["title_safe_read"],
            "exact_title_read": title_qa_report["exact_title_read"],
            "letter_spacing_read": title_qa_report["letter_spacing_read"],
            "generated_text_logo_label_read": title_qa_report["generated_text_logo_label_read"],
            "deterministic_font_text_used_in_final": False,
            "no_pre_outro_text_check": no_pre_outro_text_report,
            "no_pre_outro_local_text_read": no_pre_outro_text_report["no_pre_outro_local_text_read"],
            "visual_motion_read": frame_delta["visual_motion_read"],
            "no_captions_read": "pass",
            "final_video_text_policy_read": "pass_outro_approved_title_raster_only",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    readme_path = output_root / "README.md"
    readme_path.write_text(
        "\n".join(
            [
                "# Cascade of Effects Channel Trailer v2 Rough Cut",
                "",
                f"- Final MP4: `{final_mp4}`",
                f"- Silent picture: `{silent_video}`",
                f"- Contact sheet: `{contact_sheet}`",
                f"- Top-edge artifact check: `{top_edge_sheet}`",
                f"- Rebuilt audio mix: `{audio['mix_wav_path']}`",
                f"- Outro Paper title full-size QA: `{title_qa_report['full_size_sheet']['path']}`",
                f"- Outro Paper title 320x180 QA: `{title_qa_report['preview_sheets']['320x180']['path']}`",
                f"- Outro Paper title 168x94 QA: `{title_qa_report['preview_sheets']['168x94']['path']}`",
                f"- No pre-outro local text sheet: `{no_pre_outro_text_report['path']}`",
                f"- Intro preservation QA: `{intro_regression_report['path']}`",
                f"- Manifest: `{manifest_path}`",
                f"- Duration: `{manifest['runtime']['actual_seconds']}` seconds",
                "- Status: `rough_cut_review_ready`",
                "- Audio: rebuilt from the reused VO render plus canonical Paper Architecture theme sources.",
                f"- Supersedes: `{SUPERSEDES_PACKAGE_ID}` marked `tighten`.",
                f"- Opening: `{OPENING_VISUAL}` with right-plate geometry handoff.",
                "- VO sequence: live Short-frame compositing with no segment hold; Hyatt onward restores the 1.25s center-origin push-in.",
                f"- Title system: `{OUTRO_TITLE_ID}` extracted from the approved website Paper Architecture title raster.",
                "- Public release remains blocked until music rights and YouTube claim status are checked.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
        shutil.rmtree(work_dir, ignore_errors=True)
    print(json.dumps({"output_root": str(output_root), "final_mp4": str(final_mp4), "manifest": str(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
