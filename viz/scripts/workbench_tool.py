#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import io
import json
import math
import mimetypes
import os
import random
import re
import shutil
import subprocess
import tempfile
import threading
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
import urllib.error
import urllib.request

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat
from workbench_model_source import (
    BUILTIN_MODEL_CHALLENGER_ORBITER,
    BUILTIN_MODEL_CHALLENGER_STACK,
    MODEL_SOURCE_PROVIDER_SKETCHFAB,
    MODEL_SOURCE_STATUS_CLEARED,
    MODEL_SOURCE_STATUS_SELECTED,
    PARTICLE_MOTION_ANCHOR_ATTACHMENT,
    PARTICLE_MOTION_ANCHOR_SHELL,
    PARTICLE_MOTION_EMISSION_PLUME,
    ModelSourceError,
    build_model_particles_from_cache,
    canonical_subject_view_vectors,
    default_model_source_query,
    external_model_source_resources,
    fetch_model_candidate,
    load_subject_frame_from_point_cache,
    materialize_builtin_model_candidate,
    model_emitter_direction_from_point_cache,
    model_source_defaults,
    normalize_model_source_transform,
    normalize_fetched_model_candidate,
    pygltflib,
    rotate_model_source_vector,
    search_model_candidates,
    transform_model_source_points,
    trimesh,
)


SCHEMA_VERSION = 1
DEFAULT_WIDTH = 3840
DEFAULT_HEIGHT = 2160
DEFAULT_FPS = 60
DEFAULT_SERVE_HOST = "127.0.0.1"
DEFAULT_SERVE_PORT = 8765
PROJECT_TYPE = "particle_workbench_phase0"
STATIC_DIRNAME = "workbench_static"
MASK_STATUS_APPROVED = "approved"
MASK_STATUS_REVIEW_REQUIRED = "mask_review_required"
MASK_STATUS_NOT_APPLICABLE = "not_applicable"
MASK_SOURCE_ALPHA = "alpha"
MASK_SOURCE_IMPORTED = "imported"
MASK_SOURCE_AUTO = "auto_model"
MASK_SOURCE_MANUAL = "manual_refine"
SOURCE_ORIGIN_INIT = "init"
SOURCE_ORIGIN_UPLOAD = "upload"
WORKFLOW_MODE_IMAGE_SOURCE = "image_source"
WORKFLOW_MODE_MODEL_ONLY = "model_only"
EMITTER_DIRECTION_SPACE_CAMERA = "camera"
EMITTER_DIRECTION_SPACE_SUBJECT = "subject"
APPROVAL_STATUS_DRAFT = "draft"
APPROVAL_STATUS_APPROVED = "approved"
DEFAULT_CAMERA_FOV = 34.0
DEFAULT_CAMERA_YAW = 0.28
DEFAULT_CAMERA_PITCH = 0.12
CAMERA_PITCH_LIMIT = (math.pi * 0.5) - 1.0e-4
DEFAULT_EFFECT_MODEL = "volumetric_shell_v2"
EFFECT_MODEL_BACKUP_LABEL = f"Auto backup before {DEFAULT_EFFECT_MODEL}"
VISIBLE_DRIFT_DEFAULT_HARNESS_PROJECT_PATH = Path("/Users/mike/ParticleWorkbench/ad-hoc/challenger-default-model/project.json")
VOLUME_BACKEND_ACQUIRED_SHELL = "acquired_shell"
VOLUME_BACKEND_MODEL_SOURCE = "model_source_spike"
PRIOR_ASSIST_STATUS_INACTIVE = "inactive"
PRIOR_ASSIST_STATUS_ACTIVE = "active"
PRIOR_ASSIST_STATUS_REJECTED = "rejected"
PRIOR_ASSIST_SOURCE_CURATED = "curated_local_prior"
PRIOR_ASSIST_SUBJECT_SHUTTLE = "space_shuttle"
PRIOR_ASSIST_REASON_NOT_ELIGIBLE = "subject_not_eligible"
PRIOR_ASSIST_REASON_MASK_NOT_APPROVED = "mask_not_approved"
PRIOR_ASSIST_REASON_NO_PRIOR = "no_curated_prior"
PRIOR_ASSIST_REASON_LOW_FIT = "fit_below_threshold"
PRIOR_ASSIST_REASON_EXACT_MATCH = "exact_match_fit"
PRIOR_ASSIST_MIN_FIT_SCORE = 0.70
SKETCHFAB_ME_URL = "https://api.sketchfab.com/v3/me"
PARTICLE_MOTION_LEGACY_DYNAMIC = 3
LEGACY_SHELL_VOLUME = {
    "depth_scale": 0.38,
    "depth_curve": 1.05,
    "thickness_jitter": 0.26,
}

_SKETCHFAB_AUTH_LOCK = threading.Lock()

PRESET_DEFAULTS: dict[str, dict[str, Any]] = {
    "default": {
        "label": "Default",
        "surface": {
            "density": 0.92,
            "size": 0.22,
            "jitter": 0.08,
            "luminance_floor": 0.16,
            "edge_boost": 0.56,
            "opacity": 0.98,
        },
        "breakup": {
            "amount": 0.24,
            "tail": 0.52,
            "drift_x": -0.28,
            "drift_y": -0.02,
            "turbulence": 0.18,
            "swirl": 0.12,
            "retain": 0.88,
        },
        "framing": {
            "scale": 0.74,
            "center_x": 0.55,
            "center_y": 0.56,
        },
        "volume": {
            "depth_scale": 0.58,
            "depth_curve": 1.22,
            "thickness_jitter": 0.12,
        },
        "render": {
            "background": 0.035,
            "glow": 0.22,
            "contrast": 1.14,
        },
    },
    "vigil": {
        "label": "Vigil",
        "surface": {
            "density": 0.92,
            "size": 0.22,
            "jitter": 0.08,
            "luminance_floor": 0.16,
            "edge_boost": 0.56,
            "opacity": 0.98,
        },
        "breakup": {
            "amount": 0.24,
            "tail": 0.52,
            "drift_x": -0.28,
            "drift_y": -0.02,
            "turbulence": 0.18,
            "swirl": 0.12,
            "retain": 0.88,
        },
        "framing": {
            "scale": 0.74,
            "center_x": 0.55,
            "center_y": 0.56,
        },
        "volume": {
            "depth_scale": 0.58,
            "depth_curve": 1.22,
            "thickness_jitter": 0.12,
        },
        "render": {
            "background": 0.035,
            "glow": 0.22,
            "contrast": 1.14,
        },
    },
    "momentum": {
        "label": "Momentum",
        "surface": {
            "density": 1.00,
            "size": 0.24,
            "jitter": 0.10,
            "luminance_floor": 0.18,
            "edge_boost": 0.50,
            "opacity": 0.96,
        },
        "breakup": {
            "amount": 0.48,
            "tail": 0.62,
            "drift_x": -0.38,
            "drift_y": -0.04,
            "turbulence": 0.28,
            "swirl": 0.20,
            "retain": 0.74,
        },
        "framing": {
            "scale": 0.78,
            "center_x": 0.54,
            "center_y": 0.56,
        },
        "volume": {
            "depth_scale": 0.64,
            "depth_curve": 1.10,
            "thickness_jitter": 0.18,
        },
        "render": {
            "background": 0.03,
            "glow": 0.18,
            "contrast": 1.18,
        },
    },
    "fragility": {
        "label": "Fragility",
        "surface": {
            "density": 0.78,
            "size": 0.20,
            "jitter": 0.06,
            "luminance_floor": 0.14,
            "edge_boost": 0.60,
            "opacity": 0.94,
        },
        "breakup": {
            "amount": 0.20,
            "tail": 0.38,
            "drift_x": -0.22,
            "drift_y": -0.03,
            "turbulence": 0.16,
            "swirl": 0.10,
            "retain": 0.92,
        },
        "framing": {
            "scale": 0.70,
            "center_x": 0.56,
            "center_y": 0.58,
        },
        "volume": {
            "depth_scale": 0.46,
            "depth_curve": 1.34,
            "thickness_jitter": 0.10,
        },
        "render": {
            "background": 0.04,
            "glow": 0.18,
            "contrast": 1.12,
        },
    },
    "memory": {
        "label": "Memory",
        "surface": {
            "density": 0.90,
            "size": 0.23,
            "jitter": 0.09,
            "luminance_floor": 0.16,
            "edge_boost": 0.54,
            "opacity": 0.97,
        },
        "breakup": {
            "amount": 0.34,
            "tail": 0.56,
            "drift_x": -0.34,
            "drift_y": -0.02,
            "turbulence": 0.22,
            "swirl": 0.16,
            "retain": 0.82,
        },
        "framing": {
            "scale": 0.76,
            "center_x": 0.55,
            "center_y": 0.57,
        },
        "volume": {
            "depth_scale": 0.54,
            "depth_curve": 1.28,
            "thickness_jitter": 0.16,
        },
        "render": {
            "background": 0.032,
            "glow": 0.24,
            "contrast": 1.16,
        },
    },
    "collision": {
        "label": "Collision",
        "surface": {
            "density": 1.04,
            "size": 0.25,
            "jitter": 0.12,
            "luminance_floor": 0.16,
            "edge_boost": 0.46,
            "opacity": 0.97,
        },
        "breakup": {
            "amount": 0.62,
            "tail": 0.72,
            "drift_x": -0.48,
            "drift_y": -0.06,
            "turbulence": 0.34,
            "swirl": 0.24,
            "retain": 0.66,
        },
        "framing": {
            "scale": 0.82,
            "center_x": 0.53,
            "center_y": 0.56,
        },
        "volume": {
            "depth_scale": 0.72,
            "depth_curve": 1.02,
            "thickness_jitter": 0.22,
        },
        "render": {
            "background": 0.028,
            "glow": 0.18,
            "contrast": 1.20,
        },
    },
}

DEFAULT_PRESET_ID = "default"
VISIBLE_PRESET_IDS = (DEFAULT_PRESET_ID,)
LEGACY_PRESET_IDS = tuple(sorted(set(PRESET_DEFAULTS.keys()) - set(VISIBLE_PRESET_IDS)))
EFFECT_PRESET_SECTION_KEYS = ("surface", "breakup", "emitter", "volume", "render")
SNAPSHOT_KIND_INITIAL = "initial"
SNAPSHOT_KIND_SAVED = "snapshot"
SNAPSHOT_KIND_APPROVED = "approved"

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Particle Workbench</title>
  <style>
    :root {
      --bg: #080a0d;
      --panel: #12161b;
      --line: rgba(255,255,255,0.12);
      --text: #edf1f6;
      --muted: #8d98a8;
      --accent: #f2f4f6;
      --danger: #ff7373;
      --success: #92d7a8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Avenir Next", "Gill Sans", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.05), transparent 24%),
        linear-gradient(160deg, #050607 0%, #090b0f 48%, #0d1014 100%);
      color: var(--text);
      min-height: 100vh;
    }
    .shell {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: 100vh;
    }
    .sidebar, .content {
      padding: 24px;
    }
    .sidebar {
      border-right: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(18,22,27,0.95), rgba(12,15,19,0.95));
      overflow: auto;
    }
    .sidebar-stack {
      display: grid;
      gap: 16px;
    }
    .content {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      gap: 18px;
    }
    h1, h2, h3, p { margin: 0; }
    h1 { font-size: 28px; letter-spacing: 0.02em; }
    h2 { font-size: 12px; text-transform: uppercase; letter-spacing: 0.16em; color: var(--muted); margin-bottom: 10px; }
    .meta { color: var(--muted); font-size: 14px; line-height: 1.5; }
    .panel {
      border: 1px solid var(--line);
      background: rgba(14,18,24,0.92);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 24px 70px rgba(0,0,0,0.28);
    }
    .workflow-rail {
      display: grid;
      gap: 16px;
      padding: 18px;
      border-radius: 28px;
      background:
        linear-gradient(180deg, rgba(17,20,26,0.96), rgba(13,16,21,0.94)),
        radial-gradient(circle at top left, rgba(255,255,255,0.04), transparent 32%);
    }
    .workflow-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }
    .tab-panel {
      display: none;
      min-height: 0;
    }
    .tab-panel.active {
      display: block;
      animation: panel-enter 180ms ease;
    }
    .workflow-step {
      appearance: none;
      width: 100%;
      text-align: left;
      display: grid;
      grid-template-columns: 44px minmax(0, 1fr);
      gap: 14px;
      align-items: start;
      padding: 18px 20px;
      border-radius: 22px;
      border: 1px solid rgba(255,255,255,0.07);
      background: linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0.015));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
      color: var(--text);
      transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
    }
    .workflow-step span {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 44px;
      height: 44px;
      border-radius: 999px;
      background: rgba(255,255,255,0.05);
      color: var(--text);
      font-size: 18px;
      font-weight: 700;
    }
    .workflow-step strong {
      display: block;
      font-size: 24px;
      line-height: 1.05;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
      color: var(--text);
    }
    .workflow-step p {
      color: var(--muted);
      font-size: 15px;
      line-height: 1.35;
    }
    .workflow-step.active {
      border-color: rgba(255,255,255,0.16);
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
      transform: translateY(-1px);
      box-shadow: 0 16px 30px rgba(0,0,0,0.22);
    }
    .workflow-step.complete span {
      background: rgba(146,215,168,0.16);
      color: var(--success);
    }
    .workflow-step.locked {
      opacity: 0.6;
    }
    .workflow-step:hover {
      border-color: rgba(255,255,255,0.14);
      transform: translateY(-1px);
    }
    .workflow-status {
      display: flex;
      justify-content: flex-start;
    }
    .source-panel,
    .effect-grid {
      display: grid;
      gap: 18px;
    }
    .effect-grid {
      grid-template-columns: minmax(0, 1fr) 360px;
    }
    .section-head {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 14px;
    }
    .section-head .meta {
      max-width: 720px;
    }
    .viewport {
      background: #040506;
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.06);
      min-height: 360px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }
    .viewport img, .viewport canvas {
      width: 100%;
      display: block;
      background: #090b0f;
    }
    .viewport img {
      object-fit: contain;
    }
    .viewport canvas {
      cursor: crosshair;
    }
    .control-group { margin-bottom: 18px; }
    .control {
      display: grid;
      grid-template-columns: 1fr 74px;
      gap: 12px;
      align-items: center;
      margin: 10px 0;
    }
    .control label { color: var(--muted); font-size: 13px; }
    .control output {
      font-variant-numeric: tabular-nums;
      text-align: right;
      color: var(--text);
    }
    input[type="range"], select {
      width: 100%;
      accent-color: #f1f4f8;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 10px 16px;
      cursor: pointer;
      background: linear-gradient(135deg, var(--accent), #cfd5db);
      color: #0d1116;
      font-weight: 700;
    }
    button.secondary {
      background: rgba(255,255,255,0.06);
      color: var(--text);
      border: 1px solid var(--line);
    }
    button.danger {
      background: rgba(255,115,115,0.14);
      color: #ffd5d5;
      border: 1px solid rgba(255,115,115,0.24);
    }
    button:disabled, select:disabled, input:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }
    .snapshot-list {
      display: grid;
      gap: 8px;
      margin-top: 14px;
      max-height: 180px;
      overflow: auto;
    }
    .snapshot-item {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.03);
      font-size: 13px;
    }
    .snapshot-item.active {
      border-color: rgba(255,255,255,0.18);
      background: rgba(255,255,255,0.06);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .stat span,
    .detail span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .stat strong {
      display: block;
      font-size: 20px;
      margin-top: 4px;
    }
    .detail-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 16px;
    }
    .detail {
      padding: 12px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.06);
      background: rgba(255,255,255,0.03);
    }
    .detail strong {
      display: block;
      margin-top: 6px;
      font-size: 14px;
      line-height: 1.45;
      word-break: break-word;
    }
    .log {
      font-size: 13px;
      color: var(--muted);
      min-height: 18px;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      border: 1px solid var(--line);
      margin-top: 10px;
    }
    .status-pill.review {
      color: #ffe5a5;
      border-color: rgba(255,229,165,0.24);
      background: rgba(255,229,165,0.08);
    }
    .status-pill.approved {
      color: var(--success);
      border-color: rgba(146,215,168,0.24);
      background: rgba(146,215,168,0.08);
    }
    .tool-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 12px;
    }
    .tool-row label {
      font-size: 13px;
      color: var(--muted);
    }
    .mode-toggle {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 999px;
      overflow: hidden;
    }
    .mode-toggle button {
      border-radius: 0;
      background: transparent;
      border: 0;
      color: var(--text);
    }
    .mode-toggle button.active {
      background: rgba(255,255,255,0.10);
    }
    .scrub {
      margin-top: 12px;
      display: grid;
      grid-template-columns: 1fr 64px;
      gap: 10px;
      align-items: center;
    }
    .locked-note {
      margin-top: 12px;
      font-size: 13px;
      color: var(--muted);
    }
    .controls-panel {
      display: grid;
      align-content: start;
      gap: 16px;
    }
    .behavior-card {
      margin-bottom: 4px;
    }
    @media (max-width: 1100px) {
      .shell, .effect-grid { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid var(--line); }
      .workflow-strip { grid-template-columns: 1fr; }
    }
    @media (max-width: 720px) {
      .detail-grid,
      .stats {
        grid-template-columns: 1fr;
      }
      .workflow-step strong {
        font-size: 22px;
      }
      .workflow-step p {
        font-size: 14px;
      }
    }
    @keyframes panel-enter {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="sidebar-stack">
        <div>
          <h2>Particle Workbench</h2>
          <h1 id="project-title">Loading…</h1>
          <p class="meta" id="project-meta"></p>
        </div>
        <div class="panel">
          <h2>Analysis</h2>
          <div class="stats">
            <div class="stat"><span>Coverage</span><strong id="coverage-stat">--</strong></div>
            <div class="stat"><span>Contrast</span><strong id="contrast-stat">0%</strong></div>
            <div class="stat"><span>Seed</span><strong id="seed-stat">0</strong></div>
          </div>
          <div class="detail-grid">
            <div class="detail"><span>Mask Source</span><strong id="mask-source-stat">--</strong></div>
            <div class="detail"><span>Preset</span><strong id="preset-stat">--</strong></div>
          </div>
        </div>
        <div class="panel">
          <h2>Snapshots</h2>
          <div class="snapshot-list" id="snapshot-list"></div>
        </div>
      </div>
    </aside>
    <main class="content">
      <header class="panel workflow-rail">
        <div class="workflow-strip" role="tablist" aria-label="Workbench stages">
          <button class="workflow-step active" id="workflow-source" data-tab="source" role="tab" aria-selected="true" type="button">
            <span>1</span>
            <div>
              <strong>Source</strong>
              <p>Inspect the input image and confirm the subject framing.</p>
            </div>
          </button>
          <button class="workflow-step" id="workflow-mask" data-tab="mask" role="tab" aria-selected="false" type="button">
            <span>2</span>
            <div>
              <strong>Mask</strong>
              <p>Keep only the hero subject, then approve the mask.</p>
            </div>
          </button>
          <button class="workflow-step" id="workflow-effect" data-tab="effect" role="tab" aria-selected="false" type="button">
            <span>3</span>
            <div>
              <strong>Effect</strong>
              <p>Tune the stipple breakup, preview, save, and export.</p>
            </div>
          </button>
        </div>
        <div class="workflow-status">
          <div id="mask-status-pill" class="status-pill review">Mask Review Required</div>
        </div>
      </header>
      <section class="tab-panel active" data-tab-panel="source">
        <div class="panel source-panel">
          <div class="viewport"><img id="source-image" alt="source" /></div>
          <div class="detail-grid">
            <div class="detail"><span>Path</span><strong id="source-path">--</strong></div>
            <div class="detail"><span>Resolution</span><strong id="source-resolution">--</strong></div>
            <div class="detail"><span>Behavior</span><strong id="source-behavior">--</strong></div>
            <div class="detail"><span>Mask Source</span><strong id="source-mask-source">--</strong></div>
          </div>
        </div>
      </section>
      <section class="tab-panel" data-tab-panel="mask">
        <div class="panel">
          <div class="viewport"><canvas id="mask-canvas"></canvas></div>
          <div class="tool-row">
            <div class="mode-toggle">
              <button id="brush-add" type="button" class="active">Add</button>
              <button id="brush-remove" type="button">Remove</button>
            </div>
            <label>Brush Size</label>
            <input id="brush-size" type="range" min="0.01" max="0.12" step="0.005" value="0.035" />
            <output id="brush-size-output">0.04</output>
          </div>
          <div class="button-row">
            <button id="repropose-button" class="secondary">Re-Propose</button>
            <button id="reset-mask-button" class="secondary">Reset To Proposal</button>
            <button id="approve-mask-button">Approve Mask</button>
          </div>
          <div class="log" id="mask-log"></div>
        </div>
      </section>
      <section class="tab-panel" data-tab-panel="effect">
        <div class="effect-grid">
          <div class="panel">
            <div class="viewport"><img id="preview-image" alt="preview" /></div>
            <div class="scrub">
              <input id="preview-progress" type="range" min="0" max="1" step="0.01" value="0.65" />
              <output id="preview-progress-output">0.65</output>
            </div>
            <div class="locked-note" id="effect-lock-note">Approve the mask to unlock effect preview and export.</div>
            <div class="log" id="preview-log"></div>
          </div>
          <div class="panel controls-panel">
            <div class="detail behavior-card">
              <span>Behavior</span>
              <strong id="behavior-text">--</strong>
            </div>
            <div class="control-group">
              <h2>Preset</h2>
              <select id="preset-family"></select>
            </div>
            <div class="control-group">
              <h2>Surface</h2>
              <div id="surface-controls"></div>
            </div>
            <div class="control-group">
              <h2>Breakup</h2>
              <div id="breakup-controls"></div>
            </div>
            <div class="control-group">
              <h2>Framing</h2>
              <div id="framing-controls"></div>
            </div>
            <div class="button-row">
              <button id="save-button">Save Scene</button>
              <button id="snapshot-button" class="secondary">Snapshot</button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const effectFieldSpecs = {
      surface: [
        ['scene.surface.density', 'Density', 0.20, 1.50, 0.01],
        ['scene.surface.size', 'Point Size', 0.10, 0.80, 0.01],
        ['scene.surface.jitter', 'Jitter', 0.00, 1.00, 0.01],
        ['scene.surface.luminance_floor', 'Shadow Fill', 0.00, 1.00, 0.01],
        ['scene.surface.edge_boost', 'Edge Boost', 0.00, 1.00, 0.01],
        ['scene.surface.opacity', 'Opacity', 0.10, 1.00, 0.01],
        ['scene.render.glow', 'Glow', 0.00, 0.80, 0.01],
        ['scene.render.contrast', 'Contrast', 0.60, 1.60, 0.01]
      ],
      breakup: [
        ['scene.breakup.amount', 'Breakup', 0.00, 1.00, 0.01],
        ['scene.breakup.tail', 'Tail', 0.00, 1.00, 0.01],
        ['scene.breakup.drift_x', 'Drift X', -1.00, 1.00, 0.01],
        ['scene.breakup.drift_y', 'Drift Y', -1.00, 1.00, 0.01],
        ['scene.breakup.turbulence', 'Turbulence', 0.00, 1.00, 0.01],
        ['scene.breakup.swirl', 'Swirl', 0.00, 1.00, 0.01],
        ['scene.breakup.retain', 'Retention', 0.00, 1.00, 0.01]
      ],
      framing: [
        ['scene.framing.scale', 'Scale', 0.35, 1.15, 0.01],
        ['scene.framing.center_x', 'Center X', 0.15, 0.85, 0.01],
        ['scene.framing.center_y', 'Center Y', 0.20, 0.85, 0.01],
        ['scene.render.background', 'Background', 0.00, 0.18, 0.01]
      ]
    };

    let project = null;
    let sourceImage = null;
    let approvedMaskImage = null;
    let proposalMaskImage = null;
    let previewProgress = 0.65;
    let previewUrl = null;
    let brushMode = 'add';
    let drawing = false;
    let strokePoints = [];
    let previewToken = 0;
    let currentTab = 'source';

    const maskCanvas = document.getElementById('mask-canvas');
    const maskCtx = maskCanvas.getContext('2d');

    function titleCase(value) {
      return String(value || '')
        .split('_')
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
    }

    function basename(path) {
      const value = String(path || '');
      const parts = value.split('/');
      return parts[parts.length - 1] || value;
    }

    function setActiveTab(tabId) {
      currentTab = tabId;
      for (const button of document.querySelectorAll('.workflow-step[data-tab]')) {
        const active = button.dataset.tab === tabId;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', active ? 'true' : 'false');
      }
      for (const panel of document.querySelectorAll('[data-tab-panel]')) {
        panel.classList.toggle('active', panel.dataset.tabPanel === tabId);
      }
      if (project) {
        updateWorkflowState();
      }
    }

    function updateWorkflowState() {
      const approved = project?.mask?.status === 'approved';
      const workflowState = {
        source: document.getElementById('workflow-source'),
        mask: document.getElementById('workflow-mask'),
        effect: document.getElementById('workflow-effect'),
      };
      for (const [name, element] of Object.entries(workflowState)) {
        element.classList.remove('active', 'complete', 'locked');
        if (name === currentTab) {
          element.classList.add('active');
        }
      }
      workflowState.source.classList.add('complete');
      if (approved) {
        workflowState.mask.classList.add('complete');
      }
      if (!approved) {
        workflowState.effect.classList.add('locked');
      }
    }

    function getValue(path) {
      return path.split('.').reduce((current, part) => current?.[part], project);
    }

    function setValue(path, value) {
      const parts = path.split('.');
      let current = project;
      for (let index = 0; index < parts.length - 1; index += 1) {
        current = current[parts[index]];
      }
      current[parts[parts.length - 1]] = value;
    }

    function formatNumber(value) {
      return Number(value).toFixed(2);
    }

    function brushSizeValue() {
      return Number(document.getElementById('brush-size').value);
    }

    function setMaskLog(text) {
      document.getElementById('mask-log').textContent = text;
    }

    function setPreviewLog(text) {
      document.getElementById('preview-log').textContent = text;
    }

    function renderControls(targetId, specs) {
      const host = document.getElementById(targetId);
      host.innerHTML = '';
      for (const [path, label, min, max, step] of specs) {
        const wrapper = document.createElement('div');
        wrapper.className = 'control';
        const controlWrap = document.createElement('div');
        const controlLabel = document.createElement('label');
        controlLabel.textContent = label;
        const input = document.createElement('input');
        input.type = 'range';
        input.min = min;
        input.max = max;
        input.step = step;
        input.value = String(getValue(path));
        const output = document.createElement('output');
        output.textContent = formatNumber(input.value);
        input.addEventListener('input', () => {
          const value = Number(input.value);
          setValue(path, value);
          output.textContent = formatNumber(value);
          if (project.mask.status === 'approved') {
            renderPreview();
          }
        });
        controlWrap.appendChild(controlLabel);
        controlWrap.appendChild(input);
        wrapper.appendChild(controlWrap);
        wrapper.appendChild(output);
        host.appendChild(wrapper);
      }
    }

    async function loadImage(url) {
      const image = new Image();
      image.src = url;
      await new Promise((resolve, reject) => {
        image.onload = resolve;
        image.onerror = reject;
      });
      return image;
    }

    async function refreshMaskImages() {
      const stamp = Date.now();
      approvedMaskImage = await loadImage(`/mask/approved.png?ts=${stamp}`);
      proposalMaskImage = await loadImage(`/mask/proposal.png?ts=${stamp}`);
      drawMaskCanvas();
    }

    function normalizedPoint(event) {
      const rect = maskCanvas.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width;
      const y = (event.clientY - rect.top) / rect.height;
      return {
        x: Math.max(0, Math.min(1, x)),
        y: Math.max(0, Math.min(1, y)),
      };
    }

    function drawMaskCanvas(extraPoints = []) {
      if (!sourceImage || !approvedMaskImage) {
        return;
      }
      maskCanvas.width = sourceImage.naturalWidth || sourceImage.width;
      maskCanvas.height = sourceImage.naturalHeight || sourceImage.height;
      maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
      maskCtx.drawImage(sourceImage, 0, 0, maskCanvas.width, maskCanvas.height);

      maskCtx.save();
      maskCtx.globalAlpha = 0.38;
      maskCtx.drawImage(approvedMaskImage, 0, 0, maskCanvas.width, maskCanvas.height);
      maskCtx.restore();

      if (proposalMaskImage && project.mask.status !== 'approved') {
        maskCtx.save();
        maskCtx.globalAlpha = 0.18;
        maskCtx.drawImage(proposalMaskImage, 0, 0, maskCanvas.width, maskCanvas.height);
        maskCtx.restore();
      }

      if (extraPoints.length > 0) {
        maskCtx.save();
        maskCtx.globalAlpha = 0.52;
        maskCtx.fillStyle = brushMode === 'add' ? '#7ae59b' : '#ff7a7a';
        const radius = brushSizeValue() * Math.max(maskCanvas.width, maskCanvas.height);
        for (const point of extraPoints) {
          maskCtx.beginPath();
          maskCtx.arc(point.x * maskCanvas.width, point.y * maskCanvas.height, radius, 0, Math.PI * 2);
          maskCtx.fill();
        }
        maskCtx.restore();
      }
    }

    function refreshStats() {
      document.getElementById('project-title').textContent = `${project.episode_id} / ${project.motion_item_id}`;
      document.getElementById('project-meta').textContent = `${project.scene.preset_family} preset · ${project.motion_contract.width}x${project.motion_contract.height} · ${project.motion_contract.frames} frames`;
      document.getElementById('coverage-stat').textContent = project.subject_analysis.coverage_ratio == null ? '--' : `${Math.round(project.subject_analysis.coverage_ratio * 100)}%`;
      document.getElementById('contrast-stat').textContent = `${Math.round(project.subject_analysis.contrast_score * 100)}%`;
      document.getElementById('seed-stat').textContent = String(project.scene.seed);
      document.getElementById('behavior-text').textContent = project.motion_contract.behavior || 'No behavior recorded.';
      document.getElementById('mask-source-stat').textContent = titleCase(project.mask.source || 'unknown');
      document.getElementById('preset-stat').textContent = titleCase(project.scene.preset_family);
      document.getElementById('source-path').textContent = basename(project.source_image.path);
      document.getElementById('source-path').title = project.source_image.path;
      document.getElementById('source-resolution').textContent = `${project.source_image.width}x${project.source_image.height}`;
      document.getElementById('source-behavior').textContent = project.motion_contract.behavior || 'No behavior recorded.';
      document.getElementById('source-mask-source').textContent = titleCase(project.mask.source || 'unknown');

      const statusPill = document.getElementById('mask-status-pill');
      const approved = project.mask.status === 'approved';
      statusPill.textContent = approved ? 'Mask Approved' : 'Mask Review Required';
      statusPill.className = `status-pill ${approved ? 'approved' : 'review'}`;

      const effectLocked = !approved;
      for (const input of document.querySelectorAll('#surface-controls input, #breakup-controls input, #framing-controls input, #preset-family, #save-button, #snapshot-button, #preview-progress')) {
        input.disabled = effectLocked;
      }
      document.getElementById('effect-lock-note').textContent = approved
        ? 'Effect controls are live. Save scene changes before snapshotting or export.'
        : 'Approve the mask to unlock effect preview and export.';

      const snapshotHost = document.getElementById('snapshot-list');
      snapshotHost.innerHTML = '';
      for (const snapshot of project.snapshots) {
        const item = document.createElement('div');
        item.className = `snapshot-item ${snapshot.id === project.active_snapshot_id ? 'active' : ''}`;
        item.textContent = `${snapshot.label} · ${snapshot.id}`;
        snapshotHost.appendChild(item);
      }
      updateWorkflowState();
    }

    async function renderPreview() {
      if (!project || project.mask.status !== 'approved') {
        revokePreviewUrl();
        document.getElementById('preview-image').removeAttribute('src');
        setPreviewLog('Approve the mask to preview the effect.');
        return;
      }
      const token = ++previewToken;
      setPreviewLog('Rendering preview…');
      const response = await fetch('/api/preview', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({scene: project.scene, progress: previewProgress})
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({error: 'Preview failed.'}));
        setPreviewLog(payload.error || 'Preview failed.');
        return;
      }
      const blob = await response.blob();
      if (token !== previewToken) {
        return;
      }
      revokePreviewUrl();
      previewUrl = URL.createObjectURL(blob);
      document.getElementById('preview-image').src = previewUrl;
      setPreviewLog(`Preview ${formatNumber(previewProgress)}`);
    }

    function revokePreviewUrl() {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        previewUrl = null;
      }
    }

    async function saveProject(updatePreview = true) {
      const response = await fetch('/api/project', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({scene: project.scene})
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({error: 'Save failed.'}));
        setPreviewLog(payload.error || 'Save failed.');
        return;
      }
      project = await response.json();
      refreshStats();
      if (updatePreview) {
        await renderPreview();
      }
      setPreviewLog(`Saved ${project.metadata.updated_at}`);
    }

    async function snapshotProject() {
      const label = window.prompt('Snapshot label', 'Manual snapshot');
      if (!label) {
        return;
      }
      await saveProject(false);
      const response = await fetch('/api/snapshot', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({label})
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({error: 'Snapshot failed.'}));
        setPreviewLog(payload.error || 'Snapshot failed.');
        return;
      }
      project = await response.json();
      refreshStats();
      setPreviewLog(`Snapshot saved ${project.active_snapshot_id}`);
    }

    async function postMaskAction(path, body, logText) {
      setMaskLog(logText);
      const response = await fetch(path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body || {})
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({error: 'Mask update failed.'}));
        setMaskLog(payload.error || 'Mask update failed.');
        return;
      }
      project = await response.json();
      await refreshMaskImages();
      refreshStats();
      await renderPreview();
      setMaskLog(`Mask ${project.mask.status}`);
      if (path === '/api/mask/approve' && project.mask.status === 'approved') {
        setActiveTab('effect');
      }
    }

    async function applyStroke(points) {
      if (points.length === 0) {
        return;
      }
      await postMaskAction('/api/mask/brush', {
        mode: brushMode,
        radius: brushSizeValue(),
        points
      }, 'Applying brush…');
    }

    function wireMaskCanvas() {
      maskCanvas.addEventListener('pointerdown', (event) => {
        drawing = true;
        strokePoints = [normalizedPoint(event)];
        drawMaskCanvas(strokePoints);
      });
      maskCanvas.addEventListener('pointermove', (event) => {
        if (!drawing) {
          return;
        }
        strokePoints.push(normalizedPoint(event));
        drawMaskCanvas(strokePoints);
      });
      const finish = async () => {
        if (!drawing) {
          return;
        }
        drawing = false;
        const points = strokePoints.slice();
        strokePoints = [];
        drawMaskCanvas();
        await applyStroke(points);
      };
      maskCanvas.addEventListener('pointerup', finish);
      maskCanvas.addEventListener('pointerleave', finish);
    }

    async function loadProject() {
      const response = await fetch('/api/project');
      project = await response.json();
      sourceImage = await loadImage('/source-image');
      await refreshMaskImages();
      setActiveTab(project.mask.status === 'approved' ? 'effect' : 'mask');

      const presetSelect = document.getElementById('preset-family');
      presetSelect.innerHTML = '';
      for (const option of Object.keys(project.available_presets)) {
        const node = document.createElement('option');
        node.value = option;
        node.textContent = project.available_presets[option].label;
        if (option === project.scene.preset_family) {
          node.selected = true;
        }
        presetSelect.appendChild(node);
      }
      presetSelect.addEventListener('change', async () => {
        const response = await fetch('/api/project', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({scene: {preset_family: presetSelect.value}})
        });
        project = await response.json();
        renderControls('surface-controls', effectFieldSpecs.surface);
        renderControls('breakup-controls', effectFieldSpecs.breakup);
        renderControls('framing-controls', effectFieldSpecs.framing);
        refreshStats();
        await renderPreview();
      });

      renderControls('surface-controls', effectFieldSpecs.surface);
      renderControls('breakup-controls', effectFieldSpecs.breakup);
      renderControls('framing-controls', effectFieldSpecs.framing);

      document.getElementById('source-image').src = '/source-image';
      document.getElementById('preview-progress-output').textContent = formatNumber(previewProgress);
      document.getElementById('brush-size-output').textContent = formatNumber(brushSizeValue());
      refreshStats();
      await renderPreview();
    }

    document.getElementById('save-button').addEventListener('click', () => saveProject());
    document.getElementById('snapshot-button').addEventListener('click', snapshotProject);
    for (const button of document.querySelectorAll('.workflow-step[data-tab]')) {
      button.addEventListener('click', () => setActiveTab(button.dataset.tab));
    }
    document.getElementById('preview-progress').addEventListener('input', (event) => {
      previewProgress = Number(event.target.value);
      document.getElementById('preview-progress-output').textContent = formatNumber(previewProgress);
      renderPreview();
    });
    document.getElementById('brush-size').addEventListener('input', (event) => {
      document.getElementById('brush-size-output').textContent = formatNumber(event.target.value);
    });
    document.getElementById('brush-add').addEventListener('click', () => {
      brushMode = 'add';
      document.getElementById('brush-add').classList.add('active');
      document.getElementById('brush-remove').classList.remove('active');
    });
    document.getElementById('brush-remove').addEventListener('click', () => {
      brushMode = 'remove';
      document.getElementById('brush-remove').classList.add('active');
      document.getElementById('brush-add').classList.remove('active');
    });
    document.getElementById('repropose-button').addEventListener('click', () => postMaskAction('/api/mask/propose', {}, 'Re-generating mask proposal…'));
    document.getElementById('reset-mask-button').addEventListener('click', () => postMaskAction('/api/mask/reset', {}, 'Resetting to proposal…'));
    document.getElementById('approve-mask-button').addEventListener('click', () => postMaskAction('/api/mask/approve', {}, 'Approving mask…'));

    window.addEventListener('beforeunload', revokePreviewUrl);
    wireMaskCanvas();
    loadProject();
  </script>
</body>
</html>
"""


class WorkbenchError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExportRequest:
    project_path: Path
    output_path: Path
    master_output_path: Path | None
    manifest_path: Path
    poster_path: Path
    still_path: Path
    width: int
    height: int
    frames: int
    fps: int
    duration_seconds: float
    snapshot_id: str
    min_duration_seconds: float
    alpha: bool


@dataclass(frozen=True)
class MaskPaths:
    root: Path
    proposal: Path
    approved: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def deep_merge(base: Any, patch: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(patch, dict):
        return copy.deepcopy(patch)
    merged = copy.deepcopy(base)
    for key, value in patch.items():
        if key in merged:
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged

def _user_cache_root() -> Path:
    xdg_cache_home = str(os.environ.get("XDG_CACHE_HOME", "")).strip()
    if xdg_cache_home:
        return Path(xdg_cache_home).expanduser() / "cascade-effects"
    return Path.home() / ".cache" / "cascade-effects"


def _oauth_cache_root() -> Path:
    return _user_cache_root() / "model-sources" / "oauth"


def _sketchfab_token_path() -> Path:
    return _oauth_cache_root() / "sketchfab.json"


def _sketchfab_state_path() -> Path:
    return _oauth_cache_root() / "sketchfab-state.json"


def _write_private_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    temp_path.chmod(0o600)
    temp_path.replace(path)
    path.chmod(0o600)


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkbenchError(f"Corrupt auth state: {path.name}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorkbenchError(f"Invalid auth state payload: {path.name}")
    return payload


def _sketchfab_api_request(url: str, access_token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Token {access_token}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "ignore").strip()
        raise WorkbenchError(f"Sketchfab API request failed: HTTP {exc.code} {body}".strip()) from exc
    except urllib.error.URLError as exc:
        raise WorkbenchError(f"Sketchfab API request failed: {exc.reason}") from exc
    if not isinstance(payload, dict):
        raise WorkbenchError("Sketchfab API returned an unexpected response.")
    return payload


def _sketchfab_profile_summary(access_token: str) -> dict[str, str]:
    profile = _sketchfab_api_request(SKETCHFAB_ME_URL, access_token)
    return {
        "uid": str(profile.get("uid", "")).strip(),
        "username": str(profile.get("username", "")).strip(),
        "display_name": str(profile.get("displayName") or profile.get("username") or "").strip(),
        "profile_url": str(profile.get("profileUrl", "")).strip(),
    }


def _normalize_sketchfab_access_token(value: str) -> str:
    token = str(value or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if token.lower().startswith("token "):
        token = token[6:].strip()
    return token


def _sketchfab_env_access_token() -> str:
    return _normalize_sketchfab_access_token(os.environ.get("CE_SKETCHFAB_API_TOKEN", ""))


def _sketchfab_cached_token_payload() -> dict[str, Any]:
    payload = _read_optional_json(_sketchfab_token_path())
    access_token = _normalize_sketchfab_access_token(payload.get("access_token") or payload.get("token") or "")
    if not access_token:
        return {}
    profile = payload.get("me", {}) if isinstance(payload.get("me", {}), dict) else {}
    return {
        "access_token": access_token,
        "token_source": "cache",
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
        "me": {
            "uid": str(profile.get("uid", "")).strip(),
            "username": str(profile.get("username", "")).strip(),
            "display_name": str(profile.get("display_name") or profile.get("displayName") or profile.get("username") or "").strip(),
            "profile_url": str(profile.get("profile_url") or profile.get("profileUrl") or "").strip(),
        },
    }


def _persist_sketchfab_cached_token(access_token: str, profile: dict[str, str], *, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    normalized = {
        "access_token": _normalize_sketchfab_access_token(access_token),
        "token_source": "cache",
        "created_at": str((previous or {}).get("created_at", "")).strip() or utc_now_iso(),
        "updated_at": utc_now_iso(),
        "me": {
            "uid": str(profile.get("uid", "")).strip(),
            "username": str(profile.get("username", "")).strip(),
            "display_name": str(profile.get("display_name", "")).strip(),
            "profile_url": str(profile.get("profile_url", "")).strip(),
        },
    }
    _write_private_json(_sketchfab_token_path(), normalized)
    return normalized


def _build_sketchfab_auth_status(
    *,
    token_source: str,
    configured: bool,
    connected: bool,
    profile: dict[str, Any] | None = None,
    message: str = "",
) -> dict[str, Any]:
    resolved_profile = profile if isinstance(profile, dict) else {}
    return {
        "provider": MODEL_SOURCE_PROVIDER_SKETCHFAB,
        "configured": bool(configured),
        "connected": bool(connected),
        "token_source": str(token_source or "none").strip() or "none",
        "display_name": str(resolved_profile.get("display_name", "")).strip(),
        "username": str(resolved_profile.get("username", "")).strip(),
        "profile_url": str(resolved_profile.get("profile_url", "")).strip(),
        "message": str(message).strip(),
    }


def _clear_sketchfab_auth_files() -> None:
    for path in (_sketchfab_token_path(), _sketchfab_state_path()):
        if path.exists():
            path.unlink()


def _sketchfab_token_mode_page(message: str) -> str:
    body_copy = str(message).strip() or "Sketchfab now uses local token mode in Particle Workbench."
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Sketchfab Token Mode</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: #0b1014;
        color: #f3f6f7;
        font: 15px/1.5 system-ui, sans-serif;
      }}
      main {{
        max-width: 460px;
        padding: 32px 28px;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.04);
      }}
      p {{ margin: 0; color: rgba(243,246,247,0.82); }}
    </style>
  </head>
  <body>
    <main>
      <h1 style="margin:0 0 12px;font-size:20px;">Sketchfab Token Mode</h1>
      <p>{body_copy}</p>
    </main>
  </body>
</html>
"""


def sketchfab_auth_status() -> dict[str, Any]:
    env_token = _sketchfab_env_access_token()
    if env_token:
        try:
            profile = _sketchfab_profile_summary(env_token)
        except WorkbenchError as exc:
            return _build_sketchfab_auth_status(
                token_source="env",
                configured=True,
                connected=False,
                message=f"CE_SKETCHFAB_API_TOKEN is configured but could not be validated: {exc}",
            )
        label = str(profile.get("display_name", "")).strip() or str(profile.get("username", "")).strip() or "your account"
        return _build_sketchfab_auth_status(
            token_source="env",
            configured=True,
            connected=True,
            profile=profile,
            message=f"Sketchfab connected as {label}. Token is managed by CE_SKETCHFAB_API_TOKEN.",
        )

    with _SKETCHFAB_AUTH_LOCK:
        payload = _sketchfab_cached_token_payload()
    if not payload:
        return _build_sketchfab_auth_status(
            token_source="none",
            configured=False,
            connected=False,
            message="Paste a Sketchfab personal token to fetch downloadable CC0 and CC BY models.",
        )
    try:
        profile = _sketchfab_profile_summary(str(payload.get("access_token", "")).strip())
    except WorkbenchError:
        with _SKETCHFAB_AUTH_LOCK:
            _clear_sketchfab_auth_files()
        return _build_sketchfab_auth_status(
            token_source="none",
            configured=False,
            connected=False,
            message="Stored Sketchfab token is no longer valid. Paste a fresh token to reconnect.",
        )
    with _SKETCHFAB_AUTH_LOCK:
        _persist_sketchfab_cached_token(str(payload.get("access_token", "")).strip(), profile, previous=payload)
    label = str(profile.get("display_name", "")).strip() or str(profile.get("username", "")).strip() or "your account"
    return _build_sketchfab_auth_status(
        token_source="cache",
        configured=True,
        connected=True,
        profile=profile,
        message=f"Sketchfab connected as {label}. Downloadable CC0 and CC BY results can be fetched.",
    )


def connect_sketchfab_token(raw_token: str) -> dict[str, Any]:
    if _sketchfab_env_access_token():
        raise WorkbenchError(
            "Sketchfab is managed by CE_SKETCHFAB_API_TOKEN. Remove that env var and restart the server before connecting a different token."
        )
    access_token = _normalize_sketchfab_access_token(raw_token)
    if not access_token:
        raise WorkbenchError("Paste a Sketchfab personal token before connecting.")
    profile = _sketchfab_profile_summary(access_token)
    with _SKETCHFAB_AUTH_LOCK:
        previous = _sketchfab_cached_token_payload()
        _persist_sketchfab_cached_token(access_token, profile, previous=previous)
    return sketchfab_auth_status()


def resolve_sketchfab_access_token() -> str:
    env_token = _sketchfab_env_access_token()
    if env_token:
        return env_token
    with _SKETCHFAB_AUTH_LOCK:
        payload = _sketchfab_cached_token_payload()
    access_token = str(payload.get("access_token", "")).strip()
    if not access_token:
        raise WorkbenchError("Connect Sketchfab with a personal token before fetching this asset.")
    return access_token


def disconnect_sketchfab_auth() -> dict[str, Any]:
    if _sketchfab_env_access_token():
        status = sketchfab_auth_status()
        status["message"] = (
            "Sketchfab is managed by CE_SKETCHFAB_API_TOKEN. Remove that env var and restart the server to disconnect it."
        )
        return status
    with _SKETCHFAB_AUTH_LOCK:
        _clear_sketchfab_auth_files()
    return _build_sketchfab_auth_status(
        token_source="none",
        configured=False,
        connected=False,
        message="Sketchfab disconnected. Paste a token to reconnect.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/ce workbench")
    parser.add_argument("--repo-root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--project", required=True)
    init_parser.add_argument("--source-image")
    init_parser.add_argument("--mask-image")
    init_parser.add_argument("--episode-id", required=True)
    init_parser.add_argument("--motion-item-id", required=True)
    init_parser.add_argument("--behavior", default="")
    init_parser.add_argument("--preset", choices=sorted(PRESET_DEFAULTS.keys()), default=DEFAULT_PRESET_ID)
    init_parser.add_argument("--frames", type=int, default=33)
    init_parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    init_parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    init_parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    init_parser.add_argument("--pipeline", default="particle_workbench")
    init_parser.add_argument("--min-duration-seconds", type=float, default=0.0)
    init_parser.add_argument("--seed", type=int)
    init_parser.add_argument("--force", action="store_true")

    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--project", required=True)
    serve_parser.add_argument("--host", default=DEFAULT_SERVE_HOST)
    serve_parser.add_argument("--port", type=int, default=DEFAULT_SERVE_PORT)
    serve_parser.add_argument("--open-browser", action="store_true")

    export_parser = subparsers.add_parser("export-shot")
    export_parser.add_argument("--project", required=True)
    export_parser.add_argument("--output")
    export_parser.add_argument("--manifest-output")
    export_parser.add_argument("--poster-output")
    export_parser.add_argument("--still-output")
    export_parser.add_argument("--snapshot-id")
    export_parser.add_argument("--width", type=int)
    export_parser.add_argument("--height", type=int)
    export_parser.add_argument("--frames", type=int)
    export_parser.add_argument("--fps", type=int)
    export_parser.add_argument("--min-duration-seconds", type=float)
    export_parser.add_argument("--alpha", action="store_true")

    return parser.parse_args()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def stable_seed(*parts: str) -> int:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big")


def project_sources_root(project_path: Path) -> Path:
    return project_path.parent / "sources"


def project_static_root(repo_root: Path) -> Path:
    return repo_root / "scripts" / STATIC_DIRNAME


def source_candidate_id(index: int) -> str:
    return f"source_{index:02d}"


def next_source_candidate_id(project: dict[str, Any]) -> str:
    existing = {
        str(candidate.get("id", "")).strip()
        for candidate in project.get("source_candidates", [])
        if isinstance(candidate, dict)
    }
    index = 1
    while True:
        candidate_id = source_candidate_id(index)
        if candidate_id not in existing:
            return candidate_id
        index += 1


def project_mask_paths(project_path: Path, source_id: str | None = None) -> MaskPaths:
    root = project_path.parent / "mask"
    resolved_source_id = str(source_id or "").strip()
    if not resolved_source_id and project_path.exists():
        try:
            project = read_json(project_path)
        except (OSError, json.JSONDecodeError):
            project = None
        if isinstance(project, dict):
            resolved_source_id = str(project.get("active_source_id", "")).strip()
            if not resolved_source_id:
                candidates = project.get("source_candidates", [])
                if isinstance(candidates, list) and candidates:
                    first_candidate = candidates[0]
                    if isinstance(first_candidate, dict):
                        resolved_source_id = str(first_candidate.get("id", "")).strip()
    if resolved_source_id:
        root = root / resolved_source_id
    return MaskPaths(root=root, proposal=root / "proposal.png", approved=root / "approved.png")


def camera_defaults() -> dict[str, float]:
    return {
        "target_x": 0.0,
        "target_y": 0.0,
        "target_z": 0.0,
        "yaw": DEFAULT_CAMERA_YAW,
        "pitch": DEFAULT_CAMERA_PITCH,
        "roll": 0.0,
        "distance": 3.0,
        "fov": DEFAULT_CAMERA_FOV,
    }


def volume_defaults() -> dict[str, float]:
    return {
        "depth_scale": 0.58,
        "depth_curve": 1.18,
        "thickness_jitter": 0.16,
    }


def emitter_defaults(*, breakup: dict[str, Any] | None = None) -> dict[str, float | bool | str]:
    breakup_patch = breakup if isinstance(breakup, dict) else {}
    drift_x = float(breakup_patch.get("drift_x", -0.34) or -0.34)
    drift_y = float(breakup_patch.get("drift_y", -0.04) or -0.04)
    direction_x = drift_x
    direction_y = drift_y
    direction_z = 0.42
    direction_length = math.sqrt((direction_x * direction_x) + (direction_y * direction_y) + (direction_z * direction_z))
    if direction_length <= 1.0e-8:
        direction_x, direction_y, direction_z, direction_length = -1.0, 0.0, 0.28, math.sqrt(1.0 + (0.28 * 0.28))
    return {
        "anchored_shell": True,
        "direction_space": EMITTER_DIRECTION_SPACE_CAMERA,
        "direction_x": round(direction_x / direction_length, 4),
        "direction_y": round(direction_y / direction_length, 4),
        "direction_z": round(direction_z / direction_length, 4),
        "strength": 0.74,
        "decay": 0.56,
        "rate": 0.82,
    }


def available_presets_payload() -> dict[str, dict[str, Any]]:
    return {preset_id: copy.deepcopy(PRESET_DEFAULTS[preset_id]) for preset_id in VISIBLE_PRESET_IDS}


def _effect_payload(effect: Any) -> dict[str, Any]:
    effect_dict = effect if isinstance(effect, dict) else {}
    breakup = deep_merge(copy.deepcopy(PRESET_DEFAULTS[DEFAULT_PRESET_ID]["breakup"]), effect_dict.get("breakup", {}))
    return {
        "surface": deep_merge(copy.deepcopy(PRESET_DEFAULTS[DEFAULT_PRESET_ID]["surface"]), effect_dict.get("surface", {})),
        "breakup": breakup,
        "emitter": deep_merge(emitter_defaults(breakup=breakup), effect_dict.get("emitter", {})),
        "volume": deep_merge(volume_defaults(), effect_dict.get("volume", {})),
        "render": deep_merge(copy.deepcopy(PRESET_DEFAULTS[DEFAULT_PRESET_ID]["render"]), effect_dict.get("render", {})),
    }


def preset_effect_payload(preset_family: str) -> dict[str, Any]:
    preset_key = str(preset_family).strip().lower() or DEFAULT_PRESET_ID
    if preset_key not in PRESET_DEFAULTS:
        raise WorkbenchError(f"Unknown preset family: {preset_family}")
    preset = PRESET_DEFAULTS[preset_key]
    return _effect_payload(
        {
            "surface": preset["surface"],
            "breakup": preset["breakup"],
            "emitter": emitter_defaults(breakup=preset["breakup"]),
            "volume": preset.get("volume", {}),
            "render": preset["render"],
        }
    )


def effect_payload_from_scene(scene: Any) -> dict[str, Any]:
    scene_dict = scene if isinstance(scene, dict) else {}
    return _effect_payload({key: scene_dict.get(key, {}) for key in EFFECT_PRESET_SECTION_KEYS})


def apply_effect_payload_to_scene(scene: dict[str, Any], effect: Any) -> dict[str, Any]:
    updated = copy.deepcopy(scene)
    effect_payload = _effect_payload(effect)
    for key, value in effect_payload.items():
        updated[key] = copy.deepcopy(value)
    updated["preset_family"] = DEFAULT_PRESET_ID
    return updated


def _casefold_label(value: str) -> str:
    return str(value).strip().casefold()


def _preset_id_for_index(index: int) -> str:
    return f"preset_{index:02d}"


def next_saved_preset_id(saved_presets: list[dict[str, Any]]) -> str:
    existing_ids = {str(preset.get("id", "")).strip() for preset in saved_presets if isinstance(preset, dict)}
    index = 1
    while True:
        preset_id = _preset_id_for_index(index)
        if preset_id not in existing_ids:
            return preset_id
        index += 1


def find_saved_preset(project: dict[str, Any], preset_id: str) -> dict[str, Any]:
    target_id = str(preset_id).strip()
    for preset in project.get("saved_presets", []):
        if str(preset.get("id", "")).strip() == target_id:
            return preset
    raise WorkbenchError(f"Unknown preset: {preset_id}")


def upsert_saved_preset_record(
    saved_presets: list[dict[str, Any]],
    *,
    label: str,
    effect: Any,
    preferred_id: str = "",
    created_at: str = "",
) -> str:
    normalized_label = str(label).strip() or "Preset"
    effect_payload = _effect_payload(effect)
    timestamp = utc_now_iso()
    for preset in saved_presets:
        if _casefold_label(preset.get("label", "")) == _casefold_label(normalized_label):
            preset["label"] = normalized_label
            preset["updated_at"] = timestamp
            preset["effect"] = effect_payload
            return str(preset.get("id", "")).strip()
    preset_id = str(preferred_id).strip()
    if not preset_id or any(str(preset.get("id", "")).strip() == preset_id for preset in saved_presets):
        preset_id = next_saved_preset_id(saved_presets)
    created_value = str(created_at).strip() or timestamp
    saved_presets.append(
        {
            "id": preset_id,
            "label": normalized_label,
            "created_at": created_value,
            "updated_at": timestamp,
            "effect": effect_payload,
        }
    )
    return preset_id


def _snapshot_kind(project: dict[str, Any], snapshot: dict[str, Any]) -> str:
    existing_kind = str(snapshot.get("kind", "")).strip().lower()
    if existing_kind in {SNAPSHOT_KIND_INITIAL, SNAPSHOT_KIND_SAVED, SNAPSHOT_KIND_APPROVED}:
        return existing_kind
    snapshot_id = str(snapshot.get("id", "")).strip()
    label = str(snapshot.get("label", "")).strip().lower()
    approval_snapshot_id = str(project.get("approval", {}).get("snapshot_id", "")).strip()
    if snapshot_id == "snapshot_initial" or label == "initial import":
        return SNAPSHOT_KIND_INITIAL
    if snapshot_id and snapshot_id == approval_snapshot_id:
        return SNAPSHOT_KIND_APPROVED
    if label == "approved look":
        return SNAPSHOT_KIND_APPROVED
    return SNAPSHOT_KIND_SAVED


def normalize_snapshot_records(project: dict[str, Any]) -> bool:
    raw_snapshots = project.get("snapshots")
    normalized: list[dict[str, Any]] = []
    changed = not isinstance(raw_snapshots, list)
    active_preset_id = str(project.get("active_preset_id", DEFAULT_PRESET_ID)).strip() or DEFAULT_PRESET_ID
    approval_snapshot_id = str(project.get("approval", {}).get("snapshot_id", "")).strip()
    for index, snapshot in enumerate(raw_snapshots if isinstance(raw_snapshots, list) else [], start=1):
        if not isinstance(snapshot, dict):
            changed = True
            continue
        snapshot_id = str(snapshot.get("id", "")).strip()
        if not snapshot_id:
            snapshot_id = "snapshot_initial" if index == 1 else _snapshot_id_for_index(index)
        label = str(snapshot.get("label", "")).strip() or ("Initial import" if snapshot_id == "snapshot_initial" else "Snapshot")
        created_at = str(snapshot.get("created_at", "")).strip() or utc_now_iso()
        scene = copy.deepcopy(snapshot.get("scene", project.get("scene", {})))
        kind = _snapshot_kind(project, {**snapshot, "id": snapshot_id, "label": label})
        preset_id = str(snapshot.get("preset_id", "")).strip()
        if not preset_id:
            if kind == SNAPSHOT_KIND_INITIAL:
                preset_id = DEFAULT_PRESET_ID
            elif snapshot_id == approval_snapshot_id or snapshot_id == str(project.get("active_snapshot_id", "")).strip():
                preset_id = active_preset_id
        normalized_snapshot = {
            "id": snapshot_id,
            "label": label,
            "created_at": created_at,
            "kind": kind,
            "scene": scene,
        }
        if preset_id:
            normalized_snapshot["preset_id"] = preset_id
        normalized.append(normalized_snapshot)
    valid_snapshot_ids = {str(snapshot.get("id", "")).strip() for snapshot in normalized}
    active_snapshot_id = str(project.get("active_snapshot_id", "")).strip()
    if active_snapshot_id not in valid_snapshot_ids:
        fallback_snapshot_id = approval_snapshot_id if approval_snapshot_id in valid_snapshot_ids else ""
        if not fallback_snapshot_id and normalized:
            fallback_snapshot_id = str(normalized[0]["id"])
        project["active_snapshot_id"] = fallback_snapshot_id
        changed = True
    if project.get("snapshots") != normalized:
        project["snapshots"] = normalized
        changed = True
    return changed


def migrate_project_presets(project: dict[str, Any]) -> bool:
    changed = False
    raw_saved_presets = project.get("saved_presets")
    normalized_saved_presets: list[dict[str, Any]] = []
    for index, preset in enumerate(raw_saved_presets if isinstance(raw_saved_presets, list) else [], start=1):
        if not isinstance(preset, dict):
            changed = True
            continue
        preset_id = str(preset.get("id", "")).strip()
        if not preset_id or any(str(existing.get("id", "")).strip() == preset_id for existing in normalized_saved_presets):
            preset_id = next_saved_preset_id(normalized_saved_presets)
            changed = True
        label = str(preset.get("label", "")).strip() or f"Preset {index}"
        created_at = str(preset.get("created_at", "")).strip() or utc_now_iso()
        updated_at = str(preset.get("updated_at", "")).strip() or created_at
        normalized_saved_presets.append(
            {
                "id": preset_id,
                "label": label,
                "created_at": created_at,
                "updated_at": updated_at,
                "effect": _effect_payload(preset.get("effect", {})),
            }
        )
    if project.get("saved_presets") != normalized_saved_presets:
        project["saved_presets"] = normalized_saved_presets
        changed = True
    scene = project.get("scene", {}) if isinstance(project.get("scene"), dict) else {}
    current_preset_id = str(scene.get("preset_family", DEFAULT_PRESET_ID)).strip().lower() or DEFAULT_PRESET_ID
    active_preset_id = str(project.get("active_preset_id", "")).strip()
    if current_preset_id in LEGACY_PRESET_IDS:
        active_preset_id = upsert_saved_preset_record(
            project["saved_presets"],
            label=str(PRESET_DEFAULTS[current_preset_id]["label"]),
            effect=effect_payload_from_scene(scene),
            created_at=str(project.get("metadata", {}).get("created_at", "")).strip(),
        )
        scene["preset_family"] = DEFAULT_PRESET_ID
        changed = True
    valid_preset_ids = {DEFAULT_PRESET_ID, *(str(preset.get("id", "")).strip() for preset in project.get("saved_presets", []))}
    if active_preset_id not in valid_preset_ids:
        active_preset_id = DEFAULT_PRESET_ID
        changed = True
    if str(project.get("active_preset_id", "")).strip() != active_preset_id:
        project["active_preset_id"] = active_preset_id
        changed = True
    available_presets = available_presets_payload()
    if project.get("available_presets") != available_presets:
        project["available_presets"] = available_presets
        changed = True
    if normalize_snapshot_records(project):
        changed = True
    return changed


def _matches_legacy_shell_volume(volume: Any) -> bool:
    if not isinstance(volume, dict):
        return False
    for key, legacy_value in LEGACY_SHELL_VOLUME.items():
        try:
            current = float(volume.get(key, legacy_value))
        except (TypeError, ValueError):
            return False
        if abs(current - legacy_value) > 1.0e-6:
            return False
    return True


def _project_model_point_cache_path(project: dict[str, Any]) -> Path | None:
    scene = project.get("scene", {}) if isinstance(project.get("scene"), dict) else {}
    if str(scene.get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)).strip() != VOLUME_BACKEND_MODEL_SOURCE:
        return None
    model_source = project.get("model_source", {}) if isinstance(project.get("model_source"), dict) else {}
    if str(model_source.get("status", "")).strip() != MODEL_SOURCE_STATUS_SELECTED:
        return None
    point_cache_path = Path(str(model_source.get("point_cache_path", "")).strip()).expanduser()
    return point_cache_path if point_cache_path.exists() else None


def _model_subject_emitter_defaults(
    point_cache_path: Path,
    *,
    breakup: dict[str, Any] | None = None,
    model_transform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    defaults = dict(emitter_defaults(breakup=breakup))
    defaults.update(model_emitter_direction_from_point_cache(point_cache_path, model_transform=model_transform))
    defaults["direction_space"] = EMITTER_DIRECTION_SPACE_SUBJECT
    return defaults


def _camera_reference_up(forward: tuple[float, float, float]) -> tuple[float, float, float]:
    reference_up = (0.0, 1.0, 0.0)
    if abs(_vector_dot(forward, reference_up)) > 0.98:
        reference_up = (0.0, 0.0, 1.0)
    return reference_up


def _camera_state_from_forward_up(
    *,
    target: tuple[float, float, float],
    distance: float,
    fov: float,
    forward: tuple[float, float, float],
    up: tuple[float, float, float],
) -> dict[str, float]:
    forward = _vector_normalize(forward)
    reference_up = _camera_reference_up(forward)
    projected_up = _vector_sub(up, _vector_scale(forward, _vector_dot(up, forward)))
    if _vector_length(projected_up) <= 1.0e-6:
        projected_up = _vector_sub(reference_up, _vector_scale(forward, _vector_dot(reference_up, forward)))
    projected_up = _vector_normalize(projected_up)
    base_right = _vector_normalize(_vector_cross(forward, reference_up))
    base_up = _vector_normalize(_vector_cross(base_right, forward))
    roll = math.atan2(
        _vector_dot(_vector_cross(base_up, projected_up), forward),
        clamp(_vector_dot(base_up, projected_up), -1.0, 1.0),
    )
    distance = max(0.2, float(distance))
    offset = _vector_scale(forward, -distance)
    horizontal = math.sqrt(max((offset[0] * offset[0]) + (offset[2] * offset[2]), 1.0e-12))
    return {
        "target_x": round(float(target[0]), 4),
        "target_y": round(float(target[1]), 4),
        "target_z": round(float(target[2]), 4),
        "yaw": round(math.atan2(offset[0], offset[2]), 4),
        "pitch": round(clamp(math.atan2(offset[1], horizontal), -CAMERA_PITCH_LIMIT, CAMERA_PITCH_LIMIT), 4),
        "roll": round(roll, 4),
        "distance": round(distance, 4),
        "fov": round(clamp(float(fov), 18.0, 70.0), 4),
    }


def _canonical_reset_camera_from_point_cache(
    point_cache_path: Path | None,
    *,
    fit_camera: dict[str, Any],
    model_transform: Any = None,
) -> dict[str, float]:
    if point_cache_path is None:
        return copy.deepcopy(fit_camera)
    try:
        subject_frame = load_subject_frame_from_point_cache(point_cache_path)
        vectors = canonical_subject_view_vectors(subject_frame, raw_transform=model_transform)
    except ModelSourceError:
        return copy.deepcopy(fit_camera)
    return _camera_state_from_forward_up(
        target=(
            float(fit_camera.get("target_x", 0.0) or 0.0),
            float(fit_camera.get("target_y", 0.0) or 0.0),
            float(fit_camera.get("target_z", 0.0) or 0.0),
        ),
        distance=float(fit_camera.get("distance", 3.0) or 3.0),
        fov=float(fit_camera.get("fov", DEFAULT_CAMERA_FOV) or DEFAULT_CAMERA_FOV),
        forward=vectors["forward"],
        up=vectors["up"],
    )


def _emitter_direction_matches_defaults(emitter: dict[str, Any], defaults: dict[str, Any]) -> bool:
    for key in ("direction_x", "direction_y", "direction_z"):
        try:
            current_value = float(emitter.get(key, defaults[key]) or 0.0)
            default_value = float(defaults[key] or 0.0)
        except (TypeError, ValueError, KeyError):
            return False
        if abs(current_value - default_value) > 1.0e-4:
            return False
    return True


def _resolve_scene_emitter(
    scene: dict[str, Any],
    *,
    model_point_cache_path: Path | None = None,
    prefer_model_subject_defaults: bool = False,
    model_transform: dict[str, Any] | None = None,
    previous_model_transform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    breakup = scene.get("breakup", {}) if isinstance(scene.get("breakup"), dict) else {}
    generic_defaults = dict(emitter_defaults(breakup=breakup))
    emitter_patch = scene.get("emitter", {}) if isinstance(scene.get("emitter"), dict) else {}
    merged_emitter = deep_merge(generic_defaults, emitter_patch)
    if model_point_cache_path is None:
        merged_emitter["direction_space"] = EMITTER_DIRECTION_SPACE_CAMERA
        return merged_emitter

    requested_space = str(emitter_patch.get("direction_space", "")).strip().lower()
    subject_defaults = _model_subject_emitter_defaults(
        model_point_cache_path,
        breakup=breakup,
        model_transform=model_transform,
    )
    if prefer_model_subject_defaults:
        resolved = dict(subject_defaults)
        for key in ("anchored_shell", "strength", "decay", "rate"):
            if key in merged_emitter:
                resolved[key] = merged_emitter[key]
        return resolved
    if requested_space == EMITTER_DIRECTION_SPACE_CAMERA:
        merged_emitter["direction_space"] = EMITTER_DIRECTION_SPACE_CAMERA
        return merged_emitter

    if requested_space == EMITTER_DIRECTION_SPACE_SUBJECT:
        previous_subject_defaults = None
        if previous_model_transform is not None:
            previous_subject_defaults = _model_subject_emitter_defaults(
                model_point_cache_path,
                breakup=breakup,
                model_transform=previous_model_transform,
            )
        if previous_subject_defaults and _emitter_direction_matches_defaults(emitter_patch, previous_subject_defaults):
            resolved = dict(subject_defaults)
            for key in ("anchored_shell", "strength", "decay", "rate"):
                if key in merged_emitter:
                    resolved[key] = merged_emitter[key]
            return resolved
        resolved = deep_merge(subject_defaults, emitter_patch)
        resolved["direction_space"] = EMITTER_DIRECTION_SPACE_SUBJECT
        return resolved

    if prefer_model_subject_defaults or _emitter_direction_matches_defaults(merged_emitter, generic_defaults):
        resolved = dict(subject_defaults)
        for key in ("anchored_shell", "strength", "decay", "rate"):
            if key in merged_emitter:
                resolved[key] = merged_emitter[key]
        return resolved

    merged_emitter["direction_space"] = EMITTER_DIRECTION_SPACE_CAMERA
    return merged_emitter


def _sync_model_backed_emitter(
    project: dict[str, Any],
    *,
    raw_emitter_patch: dict[str, Any] | None = None,
    previous_model_transform: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    scene = project.setdefault("scene", {})
    emitter_source = copy.deepcopy(scene)
    if isinstance(raw_emitter_patch, dict):
        emitter_source["emitter"] = copy.deepcopy(raw_emitter_patch)
    resolved = _resolve_scene_emitter(
        emitter_source,
        model_point_cache_path=_project_model_point_cache_path(project),
        model_transform=_project_model_source_transform(project),
        previous_model_transform=previous_model_transform,
    )
    if scene.get("emitter") == resolved:
        return project, False
    scene["emitter"] = resolved
    return project, True


def _snapshot_id_for_index(index: int) -> str:
    return f"snapshot_{index:02d}"


def append_snapshot_record(
    project: dict[str, Any],
    label: str,
    *,
    scene: dict[str, Any] | None = None,
    kind: str = SNAPSHOT_KIND_SAVED,
    preset_id: str = "",
) -> str:
    snapshot_id = _snapshot_id_for_index(len(project.get("snapshots", [])) + 1)
    resolved_preset_id = str(preset_id).strip() or str(project.get("active_preset_id", DEFAULT_PRESET_ID)).strip() or DEFAULT_PRESET_ID
    project.setdefault("snapshots", []).append(
        {
            "id": snapshot_id,
            "label": str(label).strip() or "Snapshot",
            "created_at": utc_now_iso(),
            "kind": kind,
            "preset_id": resolved_preset_id,
            "scene": copy.deepcopy(scene or project.get("scene", {})),
        }
    )
    return snapshot_id


def repo_root_for_project(project: dict[str, Any]) -> Path:
    if project.get("repo_root"):
        return Path(str(project["repo_root"])).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def model_source_project_root(project_path: Path) -> Path:
    return project_path.parent / "model_source"


def uploaded_model_root(project_path: Path) -> Path:
    return project_path.parent / "model_uploads"


def prior_assist_defaults(
    *,
    subject_class: str = "",
    reason: str = PRIOR_ASSIST_REASON_NOT_ELIGIBLE,
) -> dict[str, Any]:
    return {
        "status": PRIOR_ASSIST_STATUS_INACTIVE,
        "subject_class": str(subject_class).strip(),
        "prior_id": "",
        "fit_score": 0.0,
        "source": PRIOR_ASSIST_SOURCE_CURATED,
        "reason": str(reason).strip() or PRIOR_ASSIST_REASON_NOT_ELIGIBLE,
    }


def prior_pack_root(repo_root: Path) -> Path:
    return repo_root / "config" / "workbench_priors"


def _prior_catalog_path(repo_root: Path) -> Path:
    return prior_pack_root(repo_root) / "catalog.json"


def _load_prior_catalog(repo_root: Path) -> list[dict[str, Any]]:
    catalog_path = _prior_catalog_path(repo_root)
    if not catalog_path.exists():
        return []
    try:
        payload = read_json(catalog_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkbenchError(f"Curated prior catalog is invalid: {catalog_path}: {exc}") from exc
    priors = payload.get("priors") if isinstance(payload, dict) else None
    return [copy.deepcopy(prior) for prior in priors] if isinstance(priors, list) else []


def _load_curated_prior(repo_root: Path, prior_entry: dict[str, Any]) -> dict[str, Any]:
    points_rel = str(prior_entry.get("points_path", "")).strip()
    if not points_rel:
        raise WorkbenchError(f"Curated prior entry is missing points_path: {prior_entry.get('id', 'prior')}")
    points_path = prior_pack_root(repo_root) / points_rel
    if not points_path.exists():
        raise WorkbenchError(f"Curated prior points are missing: {points_path}")
    try:
        payload = read_json(points_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkbenchError(f"Curated prior points are invalid: {points_path}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("points"), list):
        raise WorkbenchError(f"Curated prior points are invalid: {points_path}")
    return payload


def _prior_support_query_radius(subject_bounds: dict[str, float], image_size: tuple[int, int]) -> float:
    left, top, right, bottom = _subject_box_pixels(subject_bounds, image_size)
    min_dim = max(8.0, min(right - left, bottom - top))
    return max(14.0, min_dim * 0.12)


def _shuttle_subject_class(label: str, behavior: str) -> str:
    combined = f"{label} {behavior}".lower()
    if re.search(r"\b(space\s+shuttle|shuttle|orbiter)\b", combined):
        return PRIOR_ASSIST_SUBJECT_SHUTTLE
    return ""


def _default_builtin_model_id_for_init(args: argparse.Namespace) -> str:
    combined = " ".join(
        str(part).strip().lower()
        for part in (args.episode_id, args.motion_item_id, args.behavior)
        if str(part).strip()
    )
    if "challenger" not in combined and not re.search(r"\b(space\s+shuttle|shuttle|orbiter)\b", combined):
        return ""
    if re.search(r"\borbiter\b", combined):
        return BUILTIN_MODEL_CHALLENGER_ORBITER
    return BUILTIN_MODEL_CHALLENGER_STACK


def _default_builtin_model_id_for_project(project: dict[str, Any]) -> str:
    combined = " ".join(
        str(part).strip().lower()
        for part in (
            project.get("episode_id", ""),
            project.get("motion_item_id", ""),
            project.get("motion_contract", {}).get("behavior", ""),
        )
        if str(part).strip()
    )
    if "challenger" not in combined and not re.search(r"\b(space\s+shuttle|shuttle|orbiter)\b", combined):
        return ""
    if re.search(r"\borbiter\b", combined):
        return BUILTIN_MODEL_CHALLENGER_ORBITER
    return BUILTIN_MODEL_CHALLENGER_STACK


def _visible_drift_default_harness_path() -> Path:
    return VISIBLE_DRIFT_DEFAULT_HARNESS_PROJECT_PATH.expanduser().resolve()


def _matches_suppressed_emission_pattern(project: dict[str, Any]) -> bool:
    breakup = project.get("scene", {}).get("breakup", {})
    amount = float(breakup.get("amount", 0.0) or 0.0)
    retain = float(breakup.get("retain", 0.0) or 0.0)
    return amount < 0.05 or retain > 0.96


def _binary_histogram_count(mask: Image.Image) -> int:
    histogram = mask.histogram()
    return int(histogram[255]) if histogram else 0


def _float_round_dict(data: dict[str, float]) -> dict[str, float]:
    return {key: round(float(value), 4) for key, value in data.items()}


def _transform_prior_points(
    prior_points: list[list[float]],
    *,
    scale: float,
    translate_x: float,
    translate_y: float,
    mirror_x: float,
    rotate_radians: float,
) -> list[dict[str, float]]:
    cosine = math.cos(rotate_radians)
    sine = math.sin(rotate_radians)
    transformed: list[dict[str, float]] = []
    for entry in prior_points:
        if len(entry) < 7:
            continue
        x, y, z, nx, ny, nz, weight = [float(value) for value in entry[:7]]
        mirrored_x = x * mirror_x
        mirrored_nx = nx * mirror_x
        rotated_x = (mirrored_x * cosine) - (y * sine)
        rotated_y = (mirrored_x * sine) + (y * cosine)
        rotated_nx = (mirrored_nx * cosine) - (ny * sine)
        rotated_ny = (mirrored_nx * sine) + (ny * cosine)
        normal_x, normal_y, normal_z = _normalize_shell_vector(rotated_nx, rotated_ny, nz)
        transformed.append(
            {
                "x_px": (rotated_x * scale) + translate_x,
                "y_px": (rotated_y * scale) + translate_y,
                "z": z,
                "normal_x": normal_x,
                "normal_y": normal_y,
                "normal_z": normal_z,
                "weight": max(weight, 0.01),
            }
        )
    return transformed


def _rasterize_prior_samples(
    image_size: tuple[int, int],
    samples: list[dict[str, float]],
    *,
    radius_px: float,
) -> Image.Image:
    raster = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(raster)
    for sample in samples:
        x_px = float(sample["x_px"])
        y_px = float(sample["y_px"])
        draw.ellipse(
            (x_px - radius_px, y_px - radius_px, x_px + radius_px, y_px + radius_px),
            fill=255,
        )
    return raster


def _fit_curated_prior_to_mask(
    *,
    mask_image: Image.Image,
    subject_bounds: dict[str, float],
    prior_entry: dict[str, Any],
    prior_payload: dict[str, Any],
) -> dict[str, Any] | None:
    prior_points = prior_payload.get("points") or []
    if not isinstance(prior_points, list) or not prior_points:
        return None

    bounds = prior_payload.get("bounds") or {}
    prior_min_x = float(bounds.get("min_x", min(float(point[0]) for point in prior_points)))
    prior_max_x = float(bounds.get("max_x", max(float(point[0]) for point in prior_points)))
    prior_min_y = float(bounds.get("min_y", min(float(point[1]) for point in prior_points)))
    prior_max_y = float(bounds.get("max_y", max(float(point[1]) for point in prior_points)))
    prior_width = max(prior_max_x - prior_min_x, 1.0e-4)
    prior_height = max(prior_max_y - prior_min_y, 1.0e-4)
    prior_center_x = (prior_min_x + prior_max_x) * 0.5
    prior_center_y = (prior_min_y + prior_max_y) * 0.5

    left, top, right, bottom = _subject_box_pixels(subject_bounds, mask_image.size)
    bbox_width = max(1.0, right - left)
    bbox_height = max(1.0, bottom - top)
    scale = min((bbox_width * 0.96) / prior_width, (bbox_height * 0.96) / prior_height)
    translate_x = (left + (bbox_width * 0.5)) - (prior_center_x * scale)
    translate_y = (top + (bbox_height * 0.5)) - (prior_center_y * scale)
    mask_binary = binary_mask(mask_image)
    mask_pixels = max(_binary_histogram_count(mask_binary), 1)
    mask_aspect = bbox_width / max(bbox_height, 1.0)
    prior_aspect = prior_width / max(prior_height, 1.0)
    aspect_ratio_error = abs(math.log(max(mask_aspect, 1.0e-4) / max(prior_aspect, 1.0e-4)))
    aspect_score = clamp(1.0 - (aspect_ratio_error / 0.55), 0.0, 1.0)
    # Use a broader silhouette stamp so curated priors score against the
    # subject outline they represent rather than only their sparse support samples.
    radius_px = max(2.0, min(bbox_width, bbox_height) * 0.048)

    best_fit: dict[str, Any] | None = None
    rotations = prior_entry.get("orientation_search_deg") or [0.0]
    mirrors = prior_entry.get("mirror_x") or [1.0]
    for raw_mirror in mirrors:
        mirror_x = -1.0 if float(raw_mirror) < 0.0 else 1.0
        for raw_rotation in rotations:
            transformed = _transform_prior_points(
                prior_points,
                scale=scale,
                translate_x=translate_x,
                translate_y=translate_y,
                mirror_x=mirror_x,
                rotate_radians=math.radians(float(raw_rotation)),
            )
            if not transformed:
                continue
            raster = _rasterize_prior_samples(mask_image.size, transformed, radius_px=radius_px)
            intersection = ImageChops.multiply(mask_binary, raster).point(lambda value: 255 if value else 0)
            union = ImageChops.lighter(mask_binary, raster).point(lambda value: 255 if value else 0)
            intersection_pixels = _binary_histogram_count(intersection)
            union_pixels = max(_binary_histogram_count(union), 1)
            raster_pixels = max(_binary_histogram_count(raster), 1)
            inside_points = 0
            for sample in transformed:
                px = int(clamp(sample["x_px"], 0.0, mask_image.width - 1.0))
                py = int(clamp(sample["y_px"], 0.0, mask_image.height - 1.0))
                if mask_binary.getpixel((px, py)) >= 24:
                    inside_points += 1
            inside_ratio = inside_points / max(len(transformed), 1)
            iou = intersection_pixels / union_pixels
            raster_precision = intersection_pixels / raster_pixels
            mask_recall = intersection_pixels / mask_pixels
            fit_score = (
                (iou * 0.42)
                + (raster_precision * 0.22)
                + (mask_recall * 0.18)
                + (inside_ratio * 0.10)
                + (aspect_score * 0.08)
            )
            candidate_fit = {
                "prior_id": str(prior_entry.get("id", "")),
                "fit_score": round(fit_score, 4),
                "samples": transformed,
                "query_radius_px": round(_prior_support_query_radius(subject_bounds, mask_image.size), 4),
                "metrics": {
                    "iou": round(iou, 4),
                    "raster_precision": round(raster_precision, 4),
                    "mask_recall": round(mask_recall, 4),
                    "inside_ratio": round(inside_ratio, 4),
                    "aspect_score": round(aspect_score, 4),
                    "rotation_deg": round(float(raw_rotation), 4),
                    "mirror_x": mirror_x,
                },
            }
            if best_fit is None or candidate_fit["fit_score"] > best_fit["fit_score"]:
                best_fit = candidate_fit
    return best_fit


def _resolve_prior_assist_support(
    project_path: Path,
    project: dict[str, Any],
    candidate: dict[str, Any],
    source_image: Image.Image,
    mask_image: Image.Image,
    subject_analysis: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    label = str(candidate.get("label", "")).strip()
    behavior = str(project.get("motion_contract", {}).get("behavior", "")).strip()
    subject_class = _shuttle_subject_class(label, behavior)
    if not subject_class:
        return prior_assist_defaults(reason=PRIOR_ASSIST_REASON_NOT_ELIGIBLE), None
    if str(candidate.get("mask", {}).get("status", "")).strip() != MASK_STATUS_APPROVED:
        metadata = prior_assist_defaults(subject_class=subject_class, reason=PRIOR_ASSIST_REASON_MASK_NOT_APPROVED)
        return metadata, None

    subject_bounds = subject_analysis.get("subject_bounds")
    if not isinstance(subject_bounds, dict):
        metadata = prior_assist_defaults(subject_class=subject_class, reason=PRIOR_ASSIST_REASON_MASK_NOT_APPROVED)
        return metadata, None

    repo_root = repo_root_for_project(project)
    priors = [prior for prior in _load_prior_catalog(repo_root) if str(prior.get("subject_class", "")).strip() == subject_class]
    if not priors:
        metadata = prior_assist_defaults(subject_class=subject_class, reason=PRIOR_ASSIST_REASON_NO_PRIOR)
        metadata["status"] = PRIOR_ASSIST_STATUS_REJECTED
        return metadata, None

    best_fit: dict[str, Any] | None = None
    for prior_entry in priors:
        prior_payload = _load_curated_prior(repo_root, prior_entry)
        fit = _fit_curated_prior_to_mask(
            mask_image=mask_image,
            subject_bounds=subject_bounds,
            prior_entry=prior_entry,
            prior_payload=prior_payload,
        )
        if fit is None:
            continue
        if best_fit is None or fit["fit_score"] > best_fit["fit_score"]:
            best_fit = fit

    if best_fit is None:
        metadata = prior_assist_defaults(subject_class=subject_class, reason=PRIOR_ASSIST_REASON_NO_PRIOR)
        metadata["status"] = PRIOR_ASSIST_STATUS_REJECTED
        return metadata, None
    if float(best_fit["fit_score"]) < PRIOR_ASSIST_MIN_FIT_SCORE:
        metadata = prior_assist_defaults(subject_class=subject_class, reason=PRIOR_ASSIST_REASON_LOW_FIT)
        metadata["status"] = PRIOR_ASSIST_STATUS_REJECTED
        metadata["prior_id"] = str(best_fit["prior_id"])
        metadata["fit_score"] = round(float(best_fit["fit_score"]), 4)
        return metadata, None

    metadata = prior_assist_defaults(subject_class=subject_class, reason=PRIOR_ASSIST_REASON_EXACT_MATCH)
    metadata["status"] = PRIOR_ASSIST_STATUS_ACTIVE
    metadata["prior_id"] = str(best_fit["prior_id"])
    metadata["fit_score"] = round(float(best_fit["fit_score"]), 4)
    return metadata, best_fit


def refresh_active_source_prior_assist(project_path: Path, project: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if not project.get("source_candidates"):
        metadata = prior_assist_defaults(reason=PRIOR_ASSIST_REASON_NOT_ELIGIBLE)
        existing = copy.deepcopy(project.get("prior_assist", prior_assist_defaults()))
        project["prior_assist"] = copy.deepcopy(metadata)
        return project, metadata != existing
    candidate = active_source_candidate(project)
    existing = copy.deepcopy(candidate.get("prior_assist", prior_assist_defaults()))
    source_path = Path(str(candidate.get("path", ""))).expanduser().resolve()
    if not source_path.exists():
        metadata = prior_assist_defaults(reason=PRIOR_ASSIST_REASON_NOT_ELIGIBLE)
    else:
        with Image.open(source_path) as opened:
            source_image = opened.convert("RGBA")
            approved_path = project_mask_paths(project_path, str(candidate.get("id", ""))).approved
            if approved_path.exists():
                mask_image = read_mask_file(approved_path, source_image.size)
            else:
                mask_image = Image.new("L", source_image.size, 0)
            metadata, _support = _resolve_prior_assist_support(
                project_path,
                project,
                candidate,
                source_image,
                mask_image,
                candidate.get("subject_analysis", {}) or {},
            )
    candidate["prior_assist"] = metadata
    project["prior_assist"] = copy.deepcopy(metadata)
    return project, metadata != existing


def _default_model_source_query_for_project(project: dict[str, Any]) -> str:
    candidate = None
    try:
        candidate = active_source_candidate(project)
    except WorkbenchError:
        candidate = None
    behavior = str(project.get("motion_contract", {}).get("behavior", "")).strip()
    return default_model_source_query(str((candidate or {}).get("label", "")), behavior)


def _project_model_source_transform(project: dict[str, Any]) -> dict[str, float]:
    model_source = project.get("model_source", {})
    if not isinstance(model_source, dict):
        return normalize_model_source_transform(None)
    return normalize_model_source_transform(model_source.get("transform"))


def select_builtin_project_model_source(project_path: Path, model_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    project = load_project(project_path)
    resolved_repo_root = repo_root or repo_root_for_project(project)
    try:
        selected = materialize_builtin_model_candidate(
            model_id,
            repo_root=resolved_repo_root,
            project_root=project_path.parent,
            seed=int(project.get("scene", {}).get("seed", 42)),
        )
    except ModelSourceError as exc:
        raise WorkbenchError(str(exc)) from exc
    project = _apply_selected_model_source(project_path, project, selected, refit_camera=True)
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def _apply_selected_model_source(
    project_path: Path,
    project: dict[str, Any],
    selected: dict[str, Any],
    *,
    refit_camera: bool,
) -> dict[str, Any]:
    selected_query = str(selected.get("query", "")).strip() or _default_model_source_query_for_project(project)
    project["model_source"] = deep_merge(model_source_defaults(query=selected_query), selected)
    project["model_source"]["transform"] = normalize_model_source_transform(project["model_source"].get("transform"))
    project["scene"]["volume_backend"] = VOLUME_BACKEND_MODEL_SOURCE
    point_cache_path = Path(str(project["model_source"]["point_cache_path"])).expanduser()
    project["scene"]["emitter"] = _resolve_scene_emitter(
        project["scene"],
        model_point_cache_path=point_cache_path if point_cache_path.exists() else None,
        prefer_model_subject_defaults=True,
        model_transform=project["model_source"].get("transform"),
    )
    if refit_camera:
        try:
            build_model_particles_from_cache(
                Path(project["model_source"]["point_cache_path"]),
                project["scene"],
                model_transform=project["model_source"].get("transform"),
            )
        except ModelSourceError as exc:
            raise WorkbenchError(str(exc)) from exc
        project["scene"]["camera"] = reset_camera_for_subject(project)
    return project


def _sync_model_source_state(project: dict[str, Any], *, reset: bool = False) -> dict[str, Any]:
    defaults = model_source_defaults(query=_default_model_source_query_for_project(project))
    current = project.get("model_source", {})
    if not isinstance(current, dict) or reset:
        current = {}
    merged = deep_merge(defaults, current)
    if not str(merged.get("query", "")).strip():
        merged["query"] = defaults["query"]
    merged["transform"] = normalize_model_source_transform(merged.get("transform"))
    project["model_source"] = merged
    scene = project.setdefault("scene", {})
    backend = str(scene.get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)).strip()
    if not project.get("source_candidates"):
        backend = VOLUME_BACKEND_MODEL_SOURCE
    if backend not in {VOLUME_BACKEND_ACQUIRED_SHELL, VOLUME_BACKEND_MODEL_SOURCE}:
        backend = VOLUME_BACKEND_ACQUIRED_SHELL
    scene["volume_backend"] = backend
    if backend != VOLUME_BACKEND_MODEL_SOURCE and str(project["model_source"].get("status", "")).strip() == MODEL_SOURCE_STATUS_SELECTED:
        project["model_source"]["status"] = MODEL_SOURCE_STATUS_CLEARED
    return project


def active_source_candidate(project: dict[str, Any]) -> dict[str, Any]:
    active_source_id = str(project.get("active_source_id", "")).strip()
    candidates = project.get("source_candidates", [])
    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, dict) and str(candidate.get("id", "")).strip() == active_source_id:
                return candidate
        for candidate in candidates:
            if isinstance(candidate, dict):
                return candidate
    raise WorkbenchError("Workbench project does not define any source candidates.")


def find_source_candidate(project: dict[str, Any], source_id: str) -> dict[str, Any]:
    for candidate in project.get("source_candidates", []):
        if isinstance(candidate, dict) and str(candidate.get("id", "")).strip() == str(source_id).strip():
            return candidate
    raise WorkbenchError(f"Unknown source candidate: {source_id}")


def sync_active_source_views(project: dict[str, Any]) -> dict[str, Any]:
    candidates = project.get("source_candidates", [])
    if not isinstance(candidates, list) or not candidates:
        project["active_source_id"] = ""
        project["source_image"] = {
            "id": "",
            "label": "",
            "path": "",
            "width": 0,
            "height": 0,
            "sha256": "",
            "origin": "",
        }
        project["mask"] = empty_mask_metadata()
        project["subject_analysis"] = empty_subject_analysis()
        project["prior_assist"] = prior_assist_defaults()
        return _sync_model_source_state(project)
    candidate = active_source_candidate(project)
    project["active_source_id"] = str(candidate.get("id", "")).strip()
    project["source_image"] = {
        "id": project["active_source_id"],
        "label": str(candidate.get("label", "")),
        "path": str(candidate.get("path", "")),
        "width": int(candidate.get("width", 0) or 0),
        "height": int(candidate.get("height", 0) or 0),
        "sha256": str(candidate.get("sha256", "")),
        "origin": str(candidate.get("origin", "")),
    }
    project["mask"] = copy.deepcopy(candidate.get("mask", {}))
    project["subject_analysis"] = copy.deepcopy(candidate.get("subject_analysis", {}))
    project["prior_assist"] = copy.deepcopy(candidate.get("prior_assist", prior_assist_defaults()))
    return _sync_model_source_state(project)


def run_checked_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part).strip()
        raise WorkbenchError(combined or f"Command failed with exit code {result.returncode}: {' '.join(args)}")
    return result


@contextmanager
def serve_export_session(project_path: Path, export_project: dict[str, Any]) -> Any:
    server = ThreadingHTTPServer(
        (DEFAULT_SERVE_HOST, 0),
        create_request_handler(project_path, project_override=export_project, readonly=True),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5.0)
        server.server_close()


def _is_meaningful_alpha(image: Image.Image) -> bool:
    if image.mode != "RGBA":
        return False
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return False
    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    return area < (image.width * image.height * 0.98)


def _corner_color(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width = rgb.width - 1
    height = rgb.height - 1
    samples = [
        rgb.getpixel((0, 0)),
        rgb.getpixel((width, 0)),
        rgb.getpixel((0, height)),
        rgb.getpixel((width, height)),
    ]
    return tuple(int(round(sum(channel) / len(samples))) for channel in zip(*samples))


def heuristic_mask(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    if _is_meaningful_alpha(rgba):
        return ImageOps.autocontrast(rgba.getchannel("A"))

    background = _corner_color(rgba)
    difference = ImageChops.difference(rgba.convert("RGB"), Image.new("RGB", rgba.size, background)).convert("L")
    difference = ImageOps.autocontrast(difference, cutoff=1)
    softened = difference.filter(ImageFilter.GaussianBlur(radius=max(2, int(min(rgba.size) * 0.01))))
    mask = softened.point(lambda value: 255 if value >= 18 else 0)
    if mask.getbbox():
        return mask.filter(ImageFilter.GaussianBlur(radius=max(1, int(min(rgba.size) * 0.004))))

    grayscale = ImageOps.autocontrast(rgba.convert("L"), cutoff=2)
    blurred = grayscale.filter(ImageFilter.GaussianBlur(radius=max(6, int(min(rgba.size) * 0.03))))
    contrast_mask = ImageChops.difference(grayscale, blurred).point(lambda value: 255 if value >= 12 else 0)
    if contrast_mask.getbbox():
        return contrast_mask.filter(ImageFilter.GaussianBlur(radius=max(1, int(min(rgba.size) * 0.004))))

    fallback = Image.new("L", rgba.size, 0)
    draw = ImageDraw.Draw(fallback)
    draw.ellipse(
        (
            int(rgba.width * 0.2),
            int(rgba.height * 0.12),
            int(rgba.width * 0.8),
            int(rgba.height * 0.9),
        ),
        fill=255,
    )
    return fallback


def canonicalize_mask(mask_image: Image.Image, size: tuple[int, int]) -> Image.Image:
    grayscale = mask_image.convert("L")
    if grayscale.size != size:
        grayscale = grayscale.resize(size, Image.Resampling.LANCZOS)
    grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
    grayscale = grayscale.point(lambda value: 0 if value < 6 else min(255, value))
    return grayscale


def binary_mask(mask_image: Image.Image) -> Image.Image:
    return mask_image.convert("L").point(lambda value: 255 if value >= 24 else 0)


def compute_subject_bounds(mask_image: Image.Image) -> dict[str, float]:
    binary = binary_mask(mask_image)
    bbox = binary.getbbox()
    if bbox is None:
        raise WorkbenchError("Mask does not contain any subject pixels.")
    left, top, right, bottom = bbox
    width = max(1, right - left)
    height = max(1, bottom - top)
    return {
        "x": round(left / binary.width, 4),
        "y": round(top / binary.height, 4),
        "width": round(width / binary.width, 4),
        "height": round(height / binary.height, 4),
    }


def infer_focus_point(bounds: dict[str, float]) -> dict[str, float]:
    return {
        "x": round(bounds["x"] + (bounds["width"] * 0.52), 4),
        "y": round(bounds["y"] + (bounds["height"] * 0.46), 4),
    }


def base_subject_analysis(source_image: Image.Image, *, mask_mode: str) -> dict[str, Any]:
    grayscale = ImageOps.autocontrast(source_image.convert("L"), cutoff=1)
    stats = ImageStat.Stat(grayscale)
    contrast = float(stats.stddev[0]) / 128.0 if stats.stddev else 0.0
    return {
        "subject_bounds": None,
        "focus_point": None,
        "coverage_ratio": None,
        "contrast_score": round(clamp(contrast, 0.0, 1.0), 4),
        "alpha_present": _is_meaningful_alpha(source_image),
        "mask_mode": mask_mode,
    }


def empty_subject_analysis() -> dict[str, Any]:
    return {
        "subject_bounds": None,
        "focus_point": None,
        "coverage_ratio": None,
        "contrast_score": 0.0,
        "alpha_present": False,
        "mask_mode": "not_applicable",
    }


def empty_mask_metadata() -> dict[str, Any]:
    return {
        "status": MASK_STATUS_NOT_APPLICABLE,
        "source": "",
        "proposal_engine": "",
        "proposal_path": "",
        "approved_path": "",
        "mask_sha256": "",
        "subject_bounds": None,
    }


def approval_defaults() -> dict[str, Any]:
    return {
        "status": APPROVAL_STATUS_DRAFT,
        "approved_at": "",
        "snapshot_id": "",
        "output_path": "",
        "master_output_path": "",
        "master_codec": "",
        "master_container": "",
        "master_lossless": False,
        "manifest_path": "",
        "poster_path": "",
        "still_path": "",
    }


def subject_analysis_from_mask(source_image: Image.Image, mask_image: Image.Image, *, mask_mode: str) -> dict[str, Any]:
    analysis = base_subject_analysis(source_image, mask_mode=mask_mode)
    bounds = compute_subject_bounds(mask_image)
    mask_stats = ImageStat.Stat(binary_mask(mask_image))
    coverage_ratio = (mask_stats.mean[0] / 255.0) if mask_stats.mean else 0.0
    analysis.update(
        {
            "subject_bounds": bounds,
            "focus_point": infer_focus_point(bounds),
            "coverage_ratio": round(coverage_ratio, 4),
        }
    )
    return analysis


def write_mask_file(path: Path, mask_image: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mask_image.convert("L").save(path)


def read_mask_file(path: Path, size: tuple[int, int]) -> Image.Image:
    if not path.exists():
        raise WorkbenchError(f"Mask is missing: {path}")
    with Image.open(path) as opened:
        return canonicalize_mask(opened, size)


def _normalized_image_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".png"


def copy_source_candidate_file(project_path: Path, source_id: str, source_path: Path, *, filename: str | None = None) -> Path:
    if not source_path.exists():
        raise WorkbenchError(f"Source image is missing: {source_path}")
    suffix = _normalized_image_extension(filename or source_path.name)
    destination = project_sources_root(project_path) / f"{source_id}{suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)
    return destination


def decode_uploaded_source(content_base64: str) -> bytes:
    payload = str(content_base64).strip()
    if "," in payload:
        payload = payload.split(",", 1)[1]
    try:
        return base64.b64decode(payload, validate=True)
    except ValueError as exc:
        raise WorkbenchError(f"Invalid uploaded source payload: {exc}") from exc


def _normalized_model_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".obj", ".glb", ".gltf"}:
        return suffix
    raise WorkbenchError(f"Unsupported 3D model format: {suffix or 'unknown'}")


def write_uploaded_source_file(project_path: Path, source_id: str, filename: str, content_base64: str) -> Path:
    suffix = _normalized_image_extension(filename)
    destination = project_sources_root(project_path) / f"{source_id}{suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decode_uploaded_source(content_base64))
    return destination


def write_uploaded_model_file(project_path: Path, filename: str, content_base64: str) -> Path:
    suffix = _normalized_model_extension(filename)
    destination = uploaded_model_root(project_path) / f"upload_{utc_now_iso().replace(':', '').replace('-', '')}{suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(decode_uploaded_source(content_base64))
    return destination


def build_scene(
    *,
    preset_family: str,
    seed: int,
    frames: int,
    fps: int,
    min_duration_seconds: float,
) -> dict[str, Any]:
    preset = PRESET_DEFAULTS[preset_family]
    duration_seconds = max(float(frames) / max(fps, 1), min_duration_seconds, 1.0)
    return {
        "effect_model": DEFAULT_EFFECT_MODEL,
        "volume_backend": VOLUME_BACKEND_ACQUIRED_SHELL,
        "preset_family": preset_family,
        "seed": seed,
        "seed_locked": True,
        "surface": copy.deepcopy(preset["surface"]),
        "breakup": copy.deepcopy(preset["breakup"]),
        "emitter": emitter_defaults(breakup=preset["breakup"]),
        "framing": copy.deepcopy(preset["framing"]),
        "render": copy.deepcopy(preset["render"]),
        "volume": deep_merge(volume_defaults(), preset.get("volume", {})),
        "camera": camera_defaults(),
        "shot": {
            "frames": frames,
            "fps": fps,
            "duration_seconds": round(duration_seconds, 3),
            "ease": "ease_in_out",
        },
    }


def vision_helper_path(repo_root: Path) -> Path:
    return repo_root / "scripts" / "workbench_mask_vision.swift"


def refine_saliency_proposal(source_image: Image.Image, model_mask: Image.Image, boxes: list[list[float]], size: tuple[int, int]) -> Image.Image:
    proposal = canonicalize_mask(model_mask, size)
    if (ImageStat.Stat(proposal).mean or [0.0])[0] > 140.0:
        proposal = ImageOps.invert(proposal)
    if not boxes:
        return proposal

    combined = Image.new("L", size, 0)
    width, height = size
    for raw_box in boxes:
        if len(raw_box) != 4:
            continue
        x, y, box_width, box_height = [float(value) for value in raw_box]
        pad_x = box_width * 0.12
        pad_y = box_height * 0.12
        left = int(clamp(x - pad_x, 0.0, 1.0) * width)
        top = int(clamp(1.0 - (y + box_height + pad_y), 0.0, 1.0) * height)
        right = int(clamp(x + box_width + pad_x, 0.0, 1.0) * width)
        bottom = int(clamp(1.0 - (y - pad_y), 0.0, 1.0) * height)
        if right - left < 4 or bottom - top < 4:
            continue
        crop_box = (left, top, right, bottom)
        source_crop = source_image.crop(crop_box).convert("RGBA")
        heuristic_crop = canonicalize_mask(heuristic_mask(source_crop), source_crop.size)
        proposal_crop = proposal.crop(crop_box)
        multiplied = ImageChops.multiply(heuristic_crop, proposal_crop)
        refined_crop = ImageOps.autocontrast(multiplied, cutoff=2).filter(ImageFilter.GaussianBlur(radius=1.0))
        refined_crop = refined_crop.point(lambda value: 0 if value < 18 else value)
        region = Image.new("L", size, 0)
        region.paste(refined_crop, crop_box)
        combined = ImageChops.lighter(combined, region)

    combined_mean = (ImageStat.Stat(combined).mean or [0.0])[0]
    if combined.getbbox() and combined_mean >= 6.0:
        return combined
    return proposal


def generate_auto_proposal_mask(repo_root: Path, source_image_path: Path, size: tuple[int, int]) -> tuple[Image.Image, str]:
    helper_path = vision_helper_path(repo_root)
    if helper_path.exists() and shutil.which("swift"):
        with tempfile.TemporaryDirectory(prefix="particle-workbench-mask-") as temp_dir:
            output_path = Path(temp_dir) / "proposal.png"
            try:
                result = run_checked_command(
                    [
                        "swift",
                        str(helper_path),
                        "--input",
                        str(source_image_path),
                        "--output",
                        str(output_path),
                    ]
                )
                payload = json.loads(result.stdout.strip() or "{}")
                with Image.open(output_path) as opened:
                    mode = str(payload.get("mode", "vision")).strip() or "vision"
                    boxes = payload.get("boxes") or []
                    if mode == "vision_saliency":
                        with Image.open(source_image_path) as source_opened:
                            return refine_saliency_proposal(source_opened.convert("RGBA"), opened, boxes, size), mode
                    return canonicalize_mask(opened, size), mode
            except (WorkbenchError, json.JSONDecodeError):
                pass

    with Image.open(source_image_path) as opened:
        return canonicalize_mask(heuristic_mask(opened.convert("RGBA")), size), "heuristic_fallback"


def build_mask_metadata(
    project_path: Path,
    source_id: str,
    proposal_mask: Image.Image,
    approved_mask: Image.Image,
    *,
    status: str,
    source: str,
    proposal_engine: str,
    subject_analysis: dict[str, Any],
) -> dict[str, Any]:
    paths = project_mask_paths(project_path, source_id)
    write_mask_file(paths.proposal, proposal_mask)
    write_mask_file(paths.approved, approved_mask)
    approved_sha = sha256_path(paths.approved)
    return {
        "status": status,
        "source": source,
        "proposal_engine": proposal_engine,
        "proposal_path": str(paths.proposal),
        "approved_path": str(paths.approved),
        "mask_sha256": approved_sha,
        "subject_bounds": subject_analysis.get("subject_bounds"),
    }


def _candidate_label(default_label: str, label: str | None) -> str:
    normalized = str(label or "").strip()
    return normalized or default_label


def build_source_candidate(
    *,
    project_path: Path,
    repo_root: Path,
    source_id: str,
    label: str,
    source_path: Path,
    origin: str,
    mask_path: Path | None = None,
) -> dict[str, Any]:
    with Image.open(source_path) as opened:
        source_image = opened.convert("RGBA")
        image_width = source_image.width
        image_height = source_image.height
        size = source_image.size

        if mask_path is not None:
            if not mask_path.exists():
                raise WorkbenchError(f"Mask image is missing: {mask_path}")
            with Image.open(mask_path) as opened_mask:
                canonical_mask = canonicalize_mask(
                    opened_mask
                    if opened_mask.mode == "L"
                    else (opened_mask.getchannel("A") if _is_meaningful_alpha(opened_mask.convert("RGBA")) else opened_mask.convert("L")),
                    size,
                )
            subject_analysis = subject_analysis_from_mask(source_image, canonical_mask, mask_mode="imported")
            mask_metadata = build_mask_metadata(
                project_path,
                source_id,
                canonical_mask,
                canonical_mask,
                status=MASK_STATUS_APPROVED,
                source=MASK_SOURCE_IMPORTED,
                proposal_engine="imported",
                subject_analysis=subject_analysis,
            )
        elif _is_meaningful_alpha(source_image):
            alpha_mask = canonicalize_mask(source_image.getchannel("A"), size)
            subject_analysis = subject_analysis_from_mask(source_image, alpha_mask, mask_mode="alpha")
            mask_metadata = build_mask_metadata(
                project_path,
                source_id,
                alpha_mask,
                alpha_mask,
                status=MASK_STATUS_APPROVED,
                source=MASK_SOURCE_ALPHA,
                proposal_engine="alpha_channel",
                subject_analysis=subject_analysis,
            )
        else:
            proposal_mask, proposal_engine = generate_auto_proposal_mask(repo_root, source_path, size)
            subject_analysis = base_subject_analysis(source_image, mask_mode=proposal_engine)
            mask_metadata = build_mask_metadata(
                project_path,
                source_id,
                proposal_mask,
                proposal_mask,
                status=MASK_STATUS_REVIEW_REQUIRED,
                source=MASK_SOURCE_AUTO,
                proposal_engine=proposal_engine,
                subject_analysis=subject_analysis,
            )

    return {
        "id": source_id,
        "label": _candidate_label(source_path.stem.replace("_", " ").title(), label),
        "path": str(source_path),
        "width": image_width,
        "height": image_height,
        "sha256": sha256_path(source_path),
        "imported_at": utc_now_iso(),
        "origin": origin,
        "mask": mask_metadata,
        "subject_analysis": subject_analysis,
        "prior_assist": prior_assist_defaults(reason=PRIOR_ASSIST_REASON_MASK_NOT_APPROVED),
    }


def init_project_bundle(args: argparse.Namespace) -> dict[str, Any]:
    project_path = Path(args.project).expanduser().resolve()
    if project_path.exists() and not args.force:
        raise WorkbenchError(f"Workbench project already exists: {project_path}")

    repo_root = Path(args.repo_root).expanduser().resolve()
    source_image_path = Path(args.source_image).expanduser().resolve() if args.source_image else None
    if source_image_path is not None and not source_image_path.exists():
        raise WorkbenchError(f"Source image is missing: {source_image_path}")

    seed_basis = str(source_image_path) if source_image_path is not None else "model_only"
    seed = int(args.seed) if args.seed is not None else stable_seed(args.episode_id, args.motion_item_id, seed_basis)
    scene = build_scene(
        preset_family=args.preset,
        seed=seed,
        frames=args.frames,
        fps=args.fps,
        min_duration_seconds=max(float(args.min_duration_seconds), 0.0),
    )
    workflow_mode = WORKFLOW_MODE_IMAGE_SOURCE if source_image_path is not None else WORKFLOW_MODE_MODEL_ONLY
    first_source_id = ""
    source_candidates: list[dict[str, Any]] = []
    first_candidate: dict[str, Any] | None = None
    if source_image_path is not None:
        first_source_id = source_candidate_id(1)
        stored_source_path = copy_source_candidate_file(project_path, first_source_id, source_image_path)
        first_mask_path = Path(args.mask_image).expanduser().resolve() if args.mask_image else None
        first_candidate = build_source_candidate(
            project_path=project_path,
            repo_root=repo_root,
            source_id=first_source_id,
            label=source_image_path.stem.replace("_", " ").title(),
            source_path=stored_source_path,
            origin=SOURCE_ORIGIN_INIT,
            mask_path=first_mask_path,
        )
        source_candidates = [first_candidate]
    else:
        scene["volume_backend"] = VOLUME_BACKEND_MODEL_SOURCE
    builtin_model_id = _default_builtin_model_id_for_init(args) if workflow_mode == WORKFLOW_MODE_MODEL_ONLY else ""

    project = {
        "schema_version": SCHEMA_VERSION,
        "project_type": PROJECT_TYPE,
        "project_id": f"{args.episode_id}_{args.motion_item_id}",
        "workflow_mode": workflow_mode,
        "repo_root": str(repo_root),
        "episode_id": args.episode_id,
        "motion_item_id": args.motion_item_id,
        "available_presets": available_presets_payload(),
        "saved_presets": [],
        "active_preset_id": DEFAULT_PRESET_ID,
        "source_candidates": source_candidates,
        "active_source_id": first_source_id,
        "motion_contract": {
            "behavior": str(args.behavior).strip(),
            "frames": int(args.frames),
            "width": int(args.width),
            "height": int(args.height),
            "fps": int(args.fps),
            "pipeline": str(args.pipeline).strip() or "particle_workbench",
            "min_duration_seconds": round(max(float(args.min_duration_seconds), 0.0), 3),
        },
        "scene": scene,
        "model_source": model_source_defaults(query=default_model_source_query(str((first_candidate or {}).get("label", "")), str(args.behavior).strip())),
        "prior_assist": prior_assist_defaults(reason=PRIOR_ASSIST_REASON_MASK_NOT_APPROVED if first_candidate else PRIOR_ASSIST_REASON_NOT_ELIGIBLE),
        "approval": approval_defaults(),
        "snapshots": [],
        "active_snapshot_id": "snapshot_initial",
        "metadata": {
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        },
    }
    project = sync_active_source_views(project)
    project, _changed = refresh_active_source_prior_assist(project_path, project)
    project = reset_scene_for_active_source(project)
    write_json(project_path, project)
    if builtin_model_id:
        project = select_builtin_project_model_source(project_path, builtin_model_id, repo_root=repo_root)
    return project


def migrate_legacy_project_schema(project_path: Path, project: dict[str, Any]) -> dict[str, Any]:
    if project.get("source_candidates"):
        return sync_active_source_views(project)

    source_image = project.get("source_image")
    if not isinstance(source_image, dict):
        raise WorkbenchError("Legacy workbench project is missing source_image.")
    source_path = Path(str(source_image.get("path", ""))).expanduser().resolve()
    if not source_path.exists():
        raise WorkbenchError(f"Legacy workbench source image is missing: {source_path}")

    first_source_id = source_candidate_id(1)
    stored_source_path = copy_source_candidate_file(project_path, first_source_id, source_path)
    candidate = {
        "id": first_source_id,
        "label": source_path.stem.replace("_", " ").title(),
        "path": str(stored_source_path),
        "width": int(source_image.get("width", 0) or 0),
        "height": int(source_image.get("height", 0) or 0),
        "sha256": sha256_path(stored_source_path),
        "imported_at": str(project.get("metadata", {}).get("created_at", utc_now_iso())),
        "origin": SOURCE_ORIGIN_INIT,
        "mask": copy.deepcopy(project.get("mask", {})),
        "subject_analysis": copy.deepcopy(project.get("subject_analysis", {})),
        "prior_assist": copy.deepcopy(project.get("prior_assist", prior_assist_defaults())),
    }

    legacy_mask = project.get("mask", {})
    if isinstance(legacy_mask, dict):
        legacy_proposal = Path(str(legacy_mask.get("proposal_path", ""))).expanduser()
        legacy_approved = Path(str(legacy_mask.get("approved_path", ""))).expanduser()
        new_paths = project_mask_paths(project_path, first_source_id)
        new_paths.root.mkdir(parents=True, exist_ok=True)
        if legacy_proposal.exists():
            shutil.copy2(legacy_proposal, new_paths.proposal)
        if legacy_approved.exists():
            shutil.copy2(legacy_approved, new_paths.approved)
        if new_paths.proposal.exists():
            candidate["mask"]["proposal_path"] = str(new_paths.proposal)
        if new_paths.approved.exists():
            candidate["mask"]["approved_path"] = str(new_paths.approved)
            candidate["mask"]["mask_sha256"] = sha256_path(new_paths.approved)

    project["source_candidates"] = [candidate]
    project["active_source_id"] = first_source_id
    return sync_active_source_views(project)


def load_project(project_path: Path) -> dict[str, Any]:
    if not project_path.exists():
        raise WorkbenchError(f"Workbench project is missing: {project_path}")
    try:
        project = read_json(project_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkbenchError(f"Workbench project is invalid: {project_path}: {exc}") from exc
    if not isinstance(project, dict):
        raise WorkbenchError(f"Workbench project is invalid: {project_path}")
    if project.get("project_type") != PROJECT_TYPE:
        raise WorkbenchError(f"Unsupported workbench project type: {project.get('project_type')!r}")
    if "workflow_mode" not in project:
        project["workflow_mode"] = WORKFLOW_MODE_IMAGE_SOURCE if project.get("source_image") else WORKFLOW_MODE_MODEL_ONLY
    project["approval"] = deep_merge(approval_defaults(), project.get("approval", {}))
    raw_scene = project.get("scene") if isinstance(project.get("scene"), dict) else {}
    raw_effect_model = str(raw_scene.get("effect_model", "")).strip() if isinstance(raw_scene, dict) else ""
    raw_emitter = copy.deepcopy(raw_scene.get("emitter", {})) if isinstance(raw_scene, dict) and isinstance(raw_scene.get("emitter"), dict) else None
    project.setdefault("available_presets", available_presets_payload())
    project.setdefault("repo_root", str(Path(__file__).resolve().parent.parent))
    project["scene"] = resolve_preset_scene(project.get("scene", {}), project.get("scene", {}).get("preset_family", DEFAULT_PRESET_ID))
    if not project.get("source_candidates"):
        if str(project.get("workflow_mode", "")).strip() == WORKFLOW_MODE_MODEL_ONLY:
            project = sync_active_source_views(project)
        else:
            project = migrate_legacy_project_schema(project_path, project)
            persist_project(project_path, project)
    else:
        project = sync_active_source_views(project)
    project, prior_changed = refresh_active_source_prior_assist(project_path, project)
    project, _migrated = migrate_project_effect_model(project_path, project, raw_effect_model)
    project, visible_drift_recovered = recover_visible_drift_project(project_path, project)
    project, emitter_changed = _sync_model_backed_emitter(project, raw_emitter_patch=raw_emitter)
    preset_changed = migrate_project_presets(project)
    if prior_changed or visible_drift_recovered or emitter_changed or preset_changed:
        project = persist_project(project_path, project)
    return project


def resolve_preset_scene(scene: dict[str, Any], preset_family: str) -> dict[str, Any]:
    preset_key = str(preset_family).strip().lower()
    if preset_key not in PRESET_DEFAULTS:
        raise WorkbenchError(f"Unknown preset family: {preset_family}")
    preset = PRESET_DEFAULTS[preset_key]
    updated = copy.deepcopy(scene)
    updated["effect_model"] = str(updated.get("effect_model") or DEFAULT_EFFECT_MODEL).strip() or DEFAULT_EFFECT_MODEL
    updated["preset_family"] = preset_key
    updated["surface"] = deep_merge(preset["surface"], updated.get("surface", {}))
    updated["breakup"] = deep_merge(preset["breakup"], updated.get("breakup", {}))
    updated["emitter"] = deep_merge(emitter_defaults(breakup=updated["breakup"]), updated.get("emitter", {}))
    updated["framing"] = deep_merge(preset["framing"], updated.get("framing", {}))
    updated["render"] = deep_merge(preset["render"], updated.get("render", {}))
    volume_patch = updated.get("volume", {})
    if updated["effect_model"] in {DEFAULT_EFFECT_MODEL, "volumetric_shell_v1"} and _matches_legacy_shell_volume(volume_patch):
        volume_patch = {}
    updated["volume"] = deep_merge(deep_merge(volume_defaults(), preset.get("volume", {})), volume_patch)
    updated["camera"] = deep_merge(camera_defaults(), updated.get("camera", {}))
    volume_backend = str(updated.get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)).strip()
    if volume_backend not in {VOLUME_BACKEND_ACQUIRED_SHELL, VOLUME_BACKEND_MODEL_SOURCE}:
        volume_backend = VOLUME_BACKEND_ACQUIRED_SHELL
    updated["volume_backend"] = volume_backend
    return updated


def persist_project(project_path: Path, project: dict[str, Any]) -> dict[str, Any]:
    project.setdefault("workflow_mode", WORKFLOW_MODE_IMAGE_SOURCE if project.get("source_candidates") else WORKFLOW_MODE_MODEL_ONLY)
    project["approval"] = deep_merge(approval_defaults(), project.get("approval", {}))
    project = sync_active_source_views(project)
    project["metadata"]["updated_at"] = utc_now_iso()
    write_json(project_path, project)
    return project


def reset_camera_for_subject(project: dict[str, Any]) -> dict[str, float]:
    model_point_cache_path = _project_model_point_cache_path(project)
    if model_point_cache_path is not None:
        try:
            fit_camera = fit_camera_for_particles(
                project.get("scene", {}),
                build_model_particles_from_cache(
                    model_point_cache_path,
                    project.get("scene", {}),
                    model_transform=_project_model_source_transform(project),
                ),
            )
            return _canonical_reset_camera_from_point_cache(
                model_point_cache_path,
                fit_camera=fit_camera,
                model_transform=_project_model_source_transform(project),
            )
        except ModelSourceError:
            pass
    camera = camera_defaults()
    framing = project.get("scene", {}).get("framing", {})
    analysis = project.get("subject_analysis", {})
    bounds = analysis.get("subject_bounds") or {}
    focus = analysis.get("focus_point") or {"x": 0.5, "y": 0.5}
    coverage = float(analysis.get("coverage_ratio") or 0.34)
    camera["yaw"] = DEFAULT_CAMERA_YAW
    camera["pitch"] = DEFAULT_CAMERA_PITCH
    camera["fov"] = float(project.get("scene", {}).get("camera", {}).get("fov", DEFAULT_CAMERA_FOV) or DEFAULT_CAMERA_FOV)
    camera["target_x"] = round((((float(focus.get("x", 0.5)) - 0.5) * 1.25) + ((float(framing.get("center_x", 0.5)) - 0.5) * 0.35)), 4)
    camera["target_y"] = round(((((0.5 - float(focus.get("y", 0.5))) * 1.25) + ((0.5 - float(framing.get("center_y", 0.5))) * 0.35))), 4)
    camera["target_z"] = round((((float(bounds.get("height", 0.5)) - 0.5) * 0.18) if bounds else 0.0), 4)
    scale = clamp(float(framing.get("scale", 0.75)), 0.35, 1.15)
    camera["distance"] = round(clamp((2.55 - (coverage * 0.85)) / scale, 1.4, 4.8), 4)
    return camera


def build_active_scene_baseline(project: dict[str, Any]) -> dict[str, Any]:
    contract = project.get("motion_contract", {})
    current_scene = project.get("scene", {})
    scene = build_scene(
        preset_family=str(current_scene.get("preset_family", DEFAULT_PRESET_ID)).strip().lower() or DEFAULT_PRESET_ID,
        seed=int(current_scene.get("seed", stable_seed(project.get("episode_id", ""), project.get("motion_item_id", ""), project.get("active_source_id", "")))),
        frames=int(contract.get("frames", current_scene.get("shot", {}).get("frames", 33)) or 33),
        fps=int(contract.get("fps", current_scene.get("shot", {}).get("fps", DEFAULT_FPS)) or DEFAULT_FPS),
        min_duration_seconds=float(contract.get("min_duration_seconds", 0.0) or 0.0),
    )
    scene = resolve_preset_scene(scene, scene.get("preset_family", DEFAULT_PRESET_ID))
    project_with_scene = copy.deepcopy(project)
    project_with_scene["scene"] = scene
    scene["camera"] = reset_camera_for_subject(project_with_scene)
    return scene


def reset_scene_to_preset_baseline(
    project_path: Path,
    project: dict[str, Any],
    preset_family: str,
    *,
    preserve_camera: bool,
    builtin_model_id: str = "",
) -> dict[str, Any]:
    current_scene = copy.deepcopy(project.get("scene", {}))
    project_for_baseline = copy.deepcopy(project)
    project_for_baseline.setdefault("scene", {})
    project_for_baseline["scene"]["preset_family"] = preset_family
    project_for_baseline["scene"]["seed"] = int(current_scene.get("seed", project_for_baseline["scene"].get("seed", 42)) or 42)
    baseline_scene = build_active_scene_baseline(project_for_baseline)
    if preserve_camera and isinstance(current_scene.get("camera"), dict):
        baseline_scene["camera"] = deep_merge(baseline_scene.get("camera", {}), current_scene["camera"])
    project["scene"] = baseline_scene
    if project.get("workflow_mode") == WORKFLOW_MODE_MODEL_ONLY:
        project["scene"]["volume_backend"] = VOLUME_BACKEND_MODEL_SOURCE
        selected_model = project.get("model_source", {}) if isinstance(project.get("model_source"), dict) else {}
        if builtin_model_id:
            resolved_repo_root = repo_root_for_project(project)
            try:
                selected_model = materialize_builtin_model_candidate(
                    builtin_model_id,
                    repo_root=resolved_repo_root,
                    project_root=project_path.parent,
                    seed=int(project["scene"].get("seed", 42)),
                )
            except ModelSourceError as exc:
                raise WorkbenchError(str(exc)) from exc
        if str(selected_model.get("status", "")).strip() == MODEL_SOURCE_STATUS_SELECTED:
            project = _apply_selected_model_source(project_path, project, selected_model, refit_camera=not preserve_camera)
    return project


def recover_visible_drift_project(project_path: Path, project: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if str(project.get("workflow_mode", "")).strip() != WORKFLOW_MODE_MODEL_ONLY:
        return project, False
    if str(project.get("approval", {}).get("status", "")).strip() == APPROVAL_STATUS_APPROVED:
        return project, False
    default_harness = project_path.resolve() == _visible_drift_default_harness_path()
    suppressed = _matches_suppressed_emission_pattern(project)
    if not default_harness and not suppressed:
        return project, False

    builtin_model_id = _default_builtin_model_id_for_project(project) if default_harness else ""
    current_model = project.get("model_source", {}) if isinstance(project.get("model_source"), dict) else {}
    current_model_id = str(current_model.get("remote_id", "")).strip()
    current_provider = str(current_model.get("provider", "")).strip()
    if default_harness and current_provider and current_provider != "builtin_curated" and str(current_model.get("status", "")).strip() == MODEL_SOURCE_STATUS_SELECTED and not suppressed:
        return project, False
    if default_harness and builtin_model_id and current_provider == "builtin_curated" and current_model_id == builtin_model_id and not suppressed:
        return project, False

    preset_family = str(project.get("scene", {}).get("preset_family", DEFAULT_PRESET_ID)).strip().lower() or DEFAULT_PRESET_ID
    recovered = reset_scene_to_preset_baseline(
        project_path,
        project,
        preset_family,
        preserve_camera=False,
        builtin_model_id=builtin_model_id,
    )
    recovered = mark_project_draft(recovered)
    return recovered, True


def migrate_project_effect_model(project_path: Path, project: dict[str, Any], raw_effect_model: str) -> tuple[dict[str, Any], bool]:
    incoming_effect_model = str(raw_effect_model or "").strip()
    if incoming_effect_model == DEFAULT_EFFECT_MODEL:
        return project, False
    append_snapshot_record(project, EFFECT_MODEL_BACKUP_LABEL, scene=project.get("scene", {}))
    project["scene"] = build_active_scene_baseline(project)
    return persist_project(project_path, project), True


def reset_scene_for_active_source(project: dict[str, Any]) -> dict[str, Any]:
    project["scene"] = build_active_scene_baseline(project)
    project["scene"]["volume_backend"] = VOLUME_BACKEND_ACQUIRED_SHELL if project.get("source_candidates") else VOLUME_BACKEND_MODEL_SOURCE
    project["model_source"] = model_source_defaults(query=_default_model_source_query_for_project(project))
    project["active_preset_id"] = DEFAULT_PRESET_ID
    project["active_snapshot_id"] = "snapshot_initial"
    project["snapshots"] = [
        {
            "id": "snapshot_initial",
            "label": "Initial import",
            "created_at": utc_now_iso(),
            "kind": SNAPSHOT_KIND_INITIAL,
            "preset_id": DEFAULT_PRESET_ID,
            "scene": copy.deepcopy(project["scene"]),
        }
    ]
    return project


def add_source_candidate(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    source_id = next_source_candidate_id(project)
    filename = str(payload.get("filename", "")).strip()
    if not filename:
        raise WorkbenchError("Uploaded source is missing a filename.")
    content_base64 = str(payload.get("content_base64", "")).strip()
    if not content_base64:
        raise WorkbenchError("Uploaded source is missing image data.")
    label = str(payload.get("label", "")).strip() or Path(filename).stem.replace("_", " ").title()
    stored_source_path = write_uploaded_source_file(project_path, source_id, filename, content_base64)
    candidate = build_source_candidate(
        project_path=project_path,
        repo_root=repo_root_for_project(project),
        source_id=source_id,
        label=label,
        source_path=stored_source_path,
        origin=SOURCE_ORIGIN_UPLOAD,
    )
    project.setdefault("source_candidates", []).append(candidate)
    project["active_source_id"] = source_id
    project = sync_active_source_views(project)
    project, _changed = refresh_active_source_prior_assist(project_path, project)
    project = reset_scene_for_active_source(project)
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def select_source_candidate(project_path: Path, source_id: str) -> dict[str, Any]:
    project = load_project(project_path)
    find_source_candidate(project, source_id)
    project["active_source_id"] = str(source_id).strip()
    project = sync_active_source_views(project)
    project, _changed = refresh_active_source_prior_assist(project_path, project)
    project = reset_scene_for_active_source(project)
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def remove_source_candidate(project_path: Path, source_id: str) -> dict[str, Any]:
    project = load_project(project_path)
    active_source_id = str(project.get("active_source_id", "")).strip()
    if str(source_id).strip() == active_source_id:
        raise WorkbenchError("Cannot remove the active source candidate.")
    remaining: list[dict[str, Any]] = []
    removed_candidate: dict[str, Any] | None = None
    for candidate in project.get("source_candidates", []):
        if isinstance(candidate, dict) and str(candidate.get("id", "")).strip() == str(source_id).strip():
            removed_candidate = candidate
            continue
        if isinstance(candidate, dict):
            remaining.append(candidate)
    if removed_candidate is None:
        raise WorkbenchError(f"Unknown source candidate: {source_id}")
    source_path = Path(str(removed_candidate.get("path", ""))).expanduser()
    if source_path.exists():
        source_path.unlink()
    mask_root = project_mask_paths(project_path, str(removed_candidate.get("id", "")).strip()).root
    if mask_root.exists():
        shutil.rmtree(mask_root)
    project["source_candidates"] = remaining
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def _candidate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = payload.get("candidate", payload)
    if not isinstance(candidate, dict):
        raise WorkbenchError("Model-source request is missing a candidate payload.")
    return copy.deepcopy(candidate)


def _selection_phase(label: str, status: str, detail: str) -> dict[str, str]:
    return {
        "label": str(label).strip(),
        "status": str(status).strip(),
        "detail": str(detail).strip(),
    }


def search_project_model_sources(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    query = str(payload.get("query", "")).strip() or _default_model_source_query_for_project(project)
    category_hints = [str(project.get("motion_contract", {}).get("behavior", "")).strip()]
    try:
        results = search_model_candidates(query, category_hints=category_hints)
    except ModelSourceError as exc:
        raise WorkbenchError(str(exc)) from exc
    return {
        "query": query,
        "results": results,
        "resources": external_model_source_resources(query),
    }


def fetch_project_model_source(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    del project_path
    candidate = _candidate_payload(payload)
    try:
        fetch_kwargs: dict[str, Any] = {}
        if str(candidate.get("provider", "")).strip() == MODEL_SOURCE_PROVIDER_SKETCHFAB:
            fetch_kwargs["sketchfab_access_token"] = resolve_sketchfab_access_token()
        fetched = fetch_model_candidate(candidate, **fetch_kwargs)
    except ModelSourceError as exc:
        raise WorkbenchError(str(exc)) from exc
    return {"candidate": fetched}


def select_project_model_source(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    candidate = _candidate_payload(payload)
    phases = [
        _selection_phase("fetching", "pending", "Fetching source asset."),
        _selection_phase("decoding", "pending", "Decoding compressed geometry when required."),
        _selection_phase("normalizing", "pending", "Normalizing mesh bounds."),
        _selection_phase("point_cache", "pending", "Generating model point cache."),
        _selection_phase("effect_reload", "pending", "Refreshing the viewer payload."),
    ]
    try:
        phases[0]["status"] = "in_progress"
        fetch_kwargs: dict[str, Any] = {}
        if (
            not str(candidate.get("raw_asset_path", "")).strip()
            and str(candidate.get("provider", "")).strip() == MODEL_SOURCE_PROVIDER_SKETCHFAB
        ):
            fetch_kwargs["sketchfab_access_token"] = resolve_sketchfab_access_token()
        fetched = fetch_model_candidate(candidate, **fetch_kwargs) if not str(candidate.get("raw_asset_path", "")).strip() else candidate
        phases[0]["status"] = "completed"
        phases[0]["detail"] = f"Fetched {fetched.get('title') or fetched.get('remote_id') or 'model'}."
        phases[1]["status"] = "completed"
        phases[1]["detail"] = "Decoded Draco-compressed asset." if str(fetched.get("decoded_asset_path", "")).strip() else "No decode needed."
        phases[2]["status"] = "in_progress"
        selected = normalize_fetched_model_candidate(
            fetched,
            project_root=project_path.parent,
            seed=int(project.get("scene", {}).get("seed", 42)),
        )
    except ModelSourceError as exc:
        for phase in phases:
            if phase["status"] == "in_progress":
                phase["status"] = "failed"
                phase["detail"] = str(exc)
                break
        raise WorkbenchError(str(exc)) from exc
    phases[2]["status"] = "completed"
    phases[2]["detail"] = "Mesh normalized for workbench playback."
    phases[3]["status"] = "completed"
    phases[3]["detail"] = "Point cache generated."
    project = _apply_selected_model_source(project_path, project, selected, refit_camera=True)
    project = mark_project_draft(project)
    persisted = persist_project(project_path, project)
    phases[4]["status"] = "completed"
    phases[4]["detail"] = "Viewer payload ready."
    return {
        "project": persisted,
        "selection_status": {
            "status": "selected",
            "title": str(persisted.get("model_source", {}).get("title") or persisted.get("model_source", {}).get("remote_id") or ""),
            "phases": phases,
        },
    }


def clear_project_model_source(project_path: Path) -> dict[str, Any]:
    project = load_project(project_path)
    query = _default_model_source_query_for_project(project)
    if project.get("source_candidates"):
        project["scene"]["volume_backend"] = VOLUME_BACKEND_ACQUIRED_SHELL
    else:
        project["scene"]["volume_backend"] = VOLUME_BACKEND_MODEL_SOURCE
    cleared = model_source_defaults(query=query)
    cleared["status"] = MODEL_SOURCE_STATUS_CLEARED
    project["model_source"] = cleared
    project["scene"]["camera"] = reset_camera_for_subject(project)
    project["scene"]["emitter"] = _resolve_scene_emitter(project["scene"])
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def upload_project_model_source(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    filename = str(payload.get("filename", "")).strip()
    if not filename:
        raise WorkbenchError("Uploaded model is missing a filename.")
    content_base64 = str(payload.get("content_base64", "")).strip()
    if not content_base64:
        raise WorkbenchError("Uploaded model is missing file data.")
    title = str(payload.get("label", "")).strip() or Path(filename).stem.replace("_", " ").title()
    uploaded_path = write_uploaded_model_file(project_path, filename, content_base64)
    local_candidate = {
        "query": str(payload.get("query", "")).strip() or _default_model_source_query_for_project(project),
        "provider": "local_upload",
        "provider_label": "Local Upload",
        "provider_kind": "user_supplied",
        "provider_capability": "enabled",
        "subject_fit": "exact",
        "license_class": "user_supplied",
        "license_summary": "User Supplied",
        "eligibility_note": "Direct project-local upload.",
        "remote_id": uploaded_path.stem,
        "remote_url": "",
        "title": title,
        "status": MODEL_SOURCE_STATUS_SELECTED,
        "fetched_at": utc_now_iso(),
        "raw_asset_path": str(uploaded_path),
        "source_format": uploaded_path.suffix.lstrip("."),
    }
    try:
        selected = normalize_fetched_model_candidate(
            local_candidate,
            project_root=project_path.parent,
            seed=int(project.get("scene", {}).get("seed", 42)),
        )
    except ModelSourceError as exc:
        raise WorkbenchError(str(exc)) from exc
    project = _apply_selected_model_source(project_path, project, selected, refit_camera=True)
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def update_mask_metadata(project_path: Path, project: dict[str, Any], approved_mask: Image.Image, *, status: str, source: str | None = None, subject_analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    candidate = active_source_candidate(project)
    source_id = str(candidate.get("id", "")).strip()
    paths = project_mask_paths(project_path, source_id)
    write_mask_file(paths.approved, approved_mask)
    candidate.setdefault("mask", {})
    candidate["mask"]["status"] = status
    if source:
        candidate["mask"]["source"] = source
    candidate["mask"]["approved_path"] = str(paths.approved)
    candidate["mask"]["proposal_path"] = str(paths.proposal)
    candidate["mask"]["mask_sha256"] = sha256_path(paths.approved)
    if subject_analysis is not None:
        candidate["subject_analysis"] = subject_analysis
        candidate["mask"]["subject_bounds"] = subject_analysis.get("subject_bounds")
    project, _changed = refresh_active_source_prior_assist(project_path, project)
    return persist_project(project_path, project)


def apply_project_patch(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    project_changed = False
    scene_patch = payload.get("scene")
    if isinstance(scene_patch, dict):
        reset_to_preset = bool(payload.get("reset_to_preset"))
        merged_scene = deep_merge(project.get("scene", {}), scene_patch)
        preset_family = str(merged_scene.get("preset_family", project["scene"].get("preset_family", DEFAULT_PRESET_ID))).strip().lower()
        if reset_to_preset:
            project = reset_scene_to_preset_baseline(
                project_path,
                project,
                preset_family,
                preserve_camera=True,
            )
            if preset_family in VISIBLE_PRESET_IDS:
                project["active_preset_id"] = preset_family
        else:
            project["scene"] = resolve_preset_scene(merged_scene, preset_family)
        project_changed = True
    model_source_patch = payload.get("model_source")
    if isinstance(model_source_patch, dict):
        previous_model_transform = _project_model_source_transform(project)
        project = _sync_model_source_state(project)
        project["model_source"] = deep_merge(project["model_source"], model_source_patch)
        project["model_source"]["transform"] = normalize_model_source_transform(project["model_source"].get("transform"))
        project, _emitter_changed = _sync_model_backed_emitter(
            project,
            previous_model_transform=previous_model_transform,
        )
        project_changed = True
    if project_changed:
        project = mark_project_draft(project)
    return persist_project(project_path, project)


def save_project_preset(project_path: Path, label: str) -> dict[str, Any]:
    project = load_project(project_path)
    ensure_effect_ready(project)
    normalized_label = str(label).strip()
    if not normalized_label:
        raise WorkbenchError("Preset label is required.")
    preset_id = upsert_saved_preset_record(
        project.setdefault("saved_presets", []),
        label=normalized_label,
        effect=effect_payload_from_scene(project.get("scene", {})),
    )
    project["active_preset_id"] = preset_id
    project["scene"]["preset_family"] = DEFAULT_PRESET_ID
    return persist_project(project_path, project)


def apply_project_preset(project_path: Path, preset_id: str) -> dict[str, Any]:
    project = load_project(project_path)
    ensure_effect_ready(project)
    resolved_preset_id = str(preset_id).strip() or DEFAULT_PRESET_ID
    if resolved_preset_id == DEFAULT_PRESET_ID:
        effect = preset_effect_payload(DEFAULT_PRESET_ID)
    else:
        effect = copy.deepcopy(find_saved_preset(project, resolved_preset_id).get("effect", {}))
    project["scene"] = apply_effect_payload_to_scene(project.get("scene", {}), effect)
    project["active_preset_id"] = resolved_preset_id
    project = mark_project_draft(project)
    return persist_project(project_path, project)


def append_snapshot(project_path: Path, label: str) -> dict[str, Any]:
    project = load_project(project_path)
    snapshot_id = append_snapshot_record(project, label, scene=project["scene"], kind=SNAPSHOT_KIND_SAVED)
    project["active_snapshot_id"] = snapshot_id
    return persist_project(project_path, project)


def select_project_snapshot(project_path: Path, snapshot_id: str) -> dict[str, Any]:
    project = load_project(project_path)
    target_snapshot_id = str(snapshot_id).strip()
    snapshot = next(
        (item for item in project.get("snapshots", []) if str(item.get("id", "")).strip() == target_snapshot_id),
        None,
    )
    if snapshot is None:
        raise WorkbenchError(f"Unknown snapshot: {snapshot_id}")
    selected_scene = copy.deepcopy(snapshot.get("scene", {}))
    project["scene"] = resolve_preset_scene(selected_scene, selected_scene.get("preset_family", DEFAULT_PRESET_ID))
    project["scene"]["preset_family"] = DEFAULT_PRESET_ID
    project["active_snapshot_id"] = target_snapshot_id
    snapshot_preset_id = str(snapshot.get("preset_id", "")).strip()
    if snapshot_preset_id == DEFAULT_PRESET_ID or any(
        str(preset.get("id", "")).strip() == snapshot_preset_id for preset in project.get("saved_presets", [])
    ):
        project["active_preset_id"] = snapshot_preset_id
    approved_snapshot_id = str(project.get("approval", {}).get("snapshot_id", "")).strip()
    if approved_snapshot_id and target_snapshot_id == approved_snapshot_id:
        project["approval"] = deep_merge(approval_defaults(), project.get("approval", {}))
        project["approval"]["status"] = APPROVAL_STATUS_APPROVED
    else:
        project = mark_project_draft(project)
    return persist_project(project_path, project)


def mark_project_draft(project: dict[str, Any]) -> dict[str, Any]:
    project["approval"] = deep_merge(approval_defaults(), project.get("approval", {}))
    project["approval"]["status"] = APPROVAL_STATUS_DRAFT
    return project


def approve_project_look(project_path: Path) -> dict[str, Any]:
    project = load_project(project_path)
    ensure_effect_ready(project)
    snapshot_id = append_snapshot_record(project, "Approved look", scene=project["scene"], kind=SNAPSHOT_KIND_APPROVED)
    project["active_snapshot_id"] = snapshot_id
    project["approval"] = deep_merge(
        approval_defaults(),
        {
            "status": APPROVAL_STATUS_APPROVED,
            "approved_at": utc_now_iso(),
            "snapshot_id": snapshot_id,
        },
    )
    return persist_project(project_path, project)


def repropose_mask(project_path: Path) -> dict[str, Any]:
    project = load_project(project_path)
    candidate = active_source_candidate(project)
    source_id = str(candidate.get("id", "")).strip()
    source_path = Path(project["source_image"]["path"]).expanduser().resolve()
    with Image.open(source_path) as opened:
        source_image = opened.convert("RGBA")
        proposal_mask, proposal_engine = generate_auto_proposal_mask(repo_root_for_project(project), source_path, source_image.size)
        paths = project_mask_paths(project_path, source_id)
        write_mask_file(paths.proposal, proposal_mask)
        write_mask_file(paths.approved, proposal_mask)
        candidate["mask"]["status"] = MASK_STATUS_REVIEW_REQUIRED
        candidate["mask"]["source"] = MASK_SOURCE_AUTO
        candidate["mask"]["proposal_engine"] = proposal_engine
        candidate["mask"]["proposal_path"] = str(paths.proposal)
        candidate["mask"]["approved_path"] = str(paths.approved)
        candidate["mask"]["mask_sha256"] = sha256_path(paths.approved)
        candidate["mask"]["subject_bounds"] = None
        candidate["subject_analysis"] = base_subject_analysis(source_image, mask_mode=proposal_engine)
        project, _changed = refresh_active_source_prior_assist(project_path, project)
    return persist_project(project_path, project)


def reset_mask_to_proposal(project_path: Path) -> dict[str, Any]:
    project = load_project(project_path)
    source_path = Path(project["source_image"]["path"]).expanduser().resolve()
    with Image.open(source_path) as opened:
        source_image = opened.convert("RGBA")
        proposal_mask = read_mask_file(project_mask_paths(project_path, str(project["active_source_id"])).proposal, source_image.size)
        return update_mask_metadata(
            project_path,
            project,
            proposal_mask,
            status=MASK_STATUS_REVIEW_REQUIRED,
            source=MASK_SOURCE_AUTO,
            subject_analysis=base_subject_analysis(source_image, mask_mode=str(project["mask"].get("proposal_engine", "proposal"))),
        )


def apply_mask_brush(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    source_path = Path(project["source_image"]["path"]).expanduser().resolve()
    with Image.open(source_path) as opened:
        source_image = opened.convert("RGBA")
        approved_mask = read_mask_file(project_mask_paths(project_path, str(project["active_source_id"])).approved, source_image.size)
        draw = ImageDraw.Draw(approved_mask)
        fill_value = 255 if str(payload.get("mode", "add")).strip().lower() != "remove" else 0
        radius = max(1.0, float(payload.get("radius", 0.03)) * max(approved_mask.size))
        raw_points = payload.get("points") or []
        if not raw_points and {"x", "y"} <= set(payload):
            raw_points = [{"x": payload.get("x"), "y": payload.get("y")}]
        for point in raw_points:
            x = clamp(float(point.get("x", 0.0)), 0.0, 1.0) * approved_mask.width
            y = clamp(float(point.get("y", 0.0)), 0.0, 1.0) * approved_mask.height
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill_value)
        approved_mask = approved_mask.filter(ImageFilter.GaussianBlur(radius=0.8))
        return update_mask_metadata(
            project_path,
            project,
            approved_mask,
            status=MASK_STATUS_REVIEW_REQUIRED,
            source=MASK_SOURCE_MANUAL,
            subject_analysis=base_subject_analysis(source_image, mask_mode=str(project["mask"].get("proposal_engine", "manual_refine"))),
        )


def approve_mask(project_path: Path) -> dict[str, Any]:
    project = load_project(project_path)
    source_path = Path(project["source_image"]["path"]).expanduser().resolve()
    with Image.open(source_path) as opened:
        source_image = opened.convert("RGBA")
        approved_mask = read_mask_file(project_mask_paths(project_path, str(project["active_source_id"])).approved, source_image.size)
        analysis = subject_analysis_from_mask(source_image, approved_mask, mask_mode=str(project["mask"].get("proposal_engine", "approved")))
        return update_mask_metadata(
            project_path,
            project,
            approved_mask,
            status=MASK_STATUS_APPROVED,
            subject_analysis=analysis,
        )


def ensure_mask_approved(project: dict[str, Any]) -> None:
    if str(project.get("mask", {}).get("status", "")).strip() != MASK_STATUS_APPROVED:
        raise WorkbenchError("Approve the hero-subject mask before preview or export.")


def effect_ready_message(project: dict[str, Any]) -> str | None:
    volume_backend = str(project.get("scene", {}).get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)).strip()
    if volume_backend == VOLUME_BACKEND_MODEL_SOURCE:
        model_source = project.get("model_source", {})
        if str(model_source.get("status", "")).strip() != MODEL_SOURCE_STATUS_SELECTED:
            return "Load a 3D model before authoring the effect."
        point_cache_path = Path(str(model_source.get("point_cache_path", ""))).expanduser()
        if not point_cache_path.exists():
            return "The selected 3D model is missing its normalized point cache."
        return None
    if str(project.get("mask", {}).get("status", "")).strip() != MASK_STATUS_APPROVED:
        return "Approve the hero-subject mask before preview or export."
    return None


def ensure_effect_ready(project: dict[str, Any]) -> None:
    message = effect_ready_message(project)
    if message:
        raise WorkbenchError(message)


def _subject_box_pixels(bounds: dict[str, float], image_size: tuple[int, int]) -> tuple[float, float, float, float]:
    image_width, image_height = image_size
    left = float(bounds["x"]) * image_width
    top = float(bounds["y"]) * image_height
    right = (float(bounds["x"]) + float(bounds["width"])) * image_width
    bottom = (float(bounds["y"]) + float(bounds["height"])) * image_height
    return left, top, right, bottom


def _ease_in_out(value: float) -> float:
    return value * value * (3.0 - (2.0 * value))


def _wrap01(value: float) -> float:
    wrapped = math.fmod(float(value), 1.0)
    return wrapped + 1.0 if wrapped < 0.0 else wrapped


def plume_emission_envelope(progress: float, point_phase: float, drift_scale: float, emitter_rate: float) -> float:
    cycles = 1.0 + (clamp(float(emitter_rate), 0.0, 1.5) * 2.4)
    phase_offset = _wrap01(float(point_phase) / (math.pi * 2.0))
    drift_offset = float(drift_scale) * 0.37
    cycle_progress = _wrap01((float(progress) * cycles) + phase_offset + drift_offset)
    outward = _ease_in_out(cycle_progress)
    return clamp((outward * 0.92) + 0.08, 0.0, 1.0)


def _trailing_weight(x_norm: float, y_norm: float, drift_x: float, drift_y: float) -> float:
    if abs(drift_x) >= abs(drift_y):
        return 1.0 - x_norm if drift_x < 0.0 else x_norm
    return 1.0 - y_norm if drift_y < 0.0 else y_norm


def _default_particle_motion_context() -> dict[str, Any]:
    return {
        "center": (0.0, 0.0, 0.0),
        "radius": 1.0,
        "forward": (0.0, 0.0, 1.0),
        "right": (1.0, 0.0, 0.0),
        "up": (0.0, 1.0, 0.0),
        "direction_space": EMITTER_DIRECTION_SPACE_CAMERA,
        "drift_direction": (0.0, 0.0, 0.0),
        "lateral_direction": (1.0, 0.0, 0.0),
        "drift_magnitude": 0.0,
    }


def _vector_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def _vector_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def _vector_scale(vector: tuple[float, float, float], scalar: float) -> tuple[float, float, float]:
    return vector[0] * scalar, vector[1] * scalar, vector[2] * scalar


def _vector_dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2])


def _vector_cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        (a[1] * b[2]) - (a[2] * b[1]),
        (a[2] * b[0]) - (a[0] * b[2]),
        (a[0] * b[1]) - (a[1] * b[0]),
    )


def _vector_length(vector: tuple[float, float, float]) -> float:
    return math.sqrt(max((_vector_dot(vector, vector)), 1.0e-12))


def _vector_normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = _vector_length(vector)
    return vector[0] / length, vector[1] / length, vector[2] / length


def _rotate_around_axis(
    vector: tuple[float, float, float],
    axis: tuple[float, float, float],
    angle: float,
) -> tuple[float, float, float]:
    if abs(angle) < 1.0e-9:
        return vector
    axis = _vector_normalize(axis)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    term1 = _vector_scale(vector, cosine)
    term2 = _vector_scale(_vector_cross(axis, vector), sine)
    term3 = _vector_scale(axis, _vector_dot(axis, vector) * (1.0 - cosine))
    return _vector_add(_vector_add(term1, term2), term3)


def camera_vectors(camera: dict[str, Any]) -> dict[str, tuple[float, float, float] | float]:
    target = (
        float(camera.get("target_x", 0.0)),
        float(camera.get("target_y", 0.0)),
        float(camera.get("target_z", 0.0)),
    )
    yaw = float(camera.get("yaw", DEFAULT_CAMERA_YAW))
    pitch = clamp(float(camera.get("pitch", DEFAULT_CAMERA_PITCH)), -CAMERA_PITCH_LIMIT, CAMERA_PITCH_LIMIT)
    distance = max(0.2, float(camera.get("distance", 3.0)))
    roll = float(camera.get("roll", 0.0))
    eye = (
        target[0] + (distance * math.cos(pitch) * math.sin(yaw)),
        target[1] + (distance * math.sin(pitch)),
        target[2] + (distance * math.cos(pitch) * math.cos(yaw)),
    )
    forward = _vector_normalize(_vector_sub(target, eye))
    reference_up = (0.0, 1.0, 0.0)
    if abs(_vector_dot(forward, reference_up)) > 0.98:
        reference_up = (0.0, 0.0, 1.0)
    right = _vector_normalize(_vector_cross(forward, reference_up))
    up = _vector_normalize(_vector_cross(right, forward))
    if abs(roll) > 1.0e-9:
        right = _rotate_around_axis(right, forward, roll)
        up = _rotate_around_axis(up, forward, roll)
    return {
        "target": target,
        "eye": eye,
        "forward": forward,
        "right": right,
        "up": up,
        "fov": clamp(float(camera.get("fov", DEFAULT_CAMERA_FOV)), 18.0, 70.0),
    }


def project_point(
    point: tuple[float, float, float],
    camera: dict[str, tuple[float, float, float] | float],
    width: int,
    height: int,
) -> tuple[float, float, float] | None:
    eye = camera["eye"]
    right = camera["right"]
    up = camera["up"]
    forward = camera["forward"]
    if not isinstance(eye, tuple) or not isinstance(right, tuple) or not isinstance(up, tuple) or not isinstance(forward, tuple):
        return None
    relative = _vector_sub(point, eye)
    cam_x = _vector_dot(relative, right)
    cam_y = _vector_dot(relative, up)
    cam_z = _vector_dot(relative, forward)
    if cam_z <= 0.05:
        return None
    fov = float(camera["fov"])
    focal = (height * 0.5) / math.tan(math.radians(fov * 0.5))
    screen_x = (width * 0.5) + ((cam_x * focal) / cam_z)
    screen_y = (height * 0.5) - ((cam_y * focal) / cam_z)
    return screen_x, screen_y, cam_z


def particle_cloud_bounds(particles: list[dict[str, float]]) -> dict[str, Any]:
    min_x = min(particle["world_x"] for particle in particles)
    max_x = max(particle["world_x"] for particle in particles)
    min_y = min(particle["world_y"] for particle in particles)
    max_y = max(particle["world_y"] for particle in particles)
    min_z = min(particle["world_z"] for particle in particles)
    max_z = max(particle["world_z"] for particle in particles)
    center = (
        (min_x + max_x) * 0.5,
        (min_y + max_y) * 0.5,
        (min_z + max_z) * 0.5,
    )
    radius = 0.0
    for particle in particles:
        radius = max(
            radius,
            _vector_length(
                (
                    particle["world_x"] - center[0],
                    particle["world_y"] - center[1],
                    particle["world_z"] - center[2],
                )
            ),
        )
    return {
        "center": {"x": round(center[0], 4), "y": round(center[1], 4), "z": round(center[2], 4)},
        "radius": round(max(radius, 0.001), 4),
        "extents": {
            "min_x": round(min_x, 4),
            "max_x": round(max_x, 4),
            "min_y": round(min_y, 4),
            "max_y": round(max_y, 4),
            "min_z": round(min_z, 4),
            "max_z": round(max_z, 4),
        },
    }


def fit_camera_for_particles(scene: dict[str, Any], particles: list[dict[str, float]]) -> dict[str, float]:
    primary_particles = [particle for particle in particles if str(particle.get("layer", "")) != "halo"] or particles
    bounds = particle_cloud_bounds(primary_particles)
    radius = float(bounds["radius"])
    framing = scene.get("framing", {})
    camera = camera_defaults()
    camera["yaw"] = DEFAULT_CAMERA_YAW
    camera["pitch"] = DEFAULT_CAMERA_PITCH
    camera["fov"] = float(scene.get("camera", {}).get("fov", DEFAULT_CAMERA_FOV) or DEFAULT_CAMERA_FOV)
    camera["target_x"] = round(float(bounds["center"]["x"]) + ((float(framing.get("center_x", 0.5)) - 0.5) * radius * 0.7), 4)
    camera["target_y"] = round(float(bounds["center"]["y"]) - ((float(framing.get("center_y", 0.5)) - 0.5) * radius * 0.7), 4)
    camera["target_z"] = round(float(bounds["center"]["z"]), 4)
    scale = clamp(float(framing.get("scale", 0.75)), 0.35, 1.15)
    camera["distance"] = round(clamp((radius * 2.6) / scale, 1.2, 5.0), 4)
    return camera


def particle_motion_context(scene: dict[str, Any], particles: list[dict[str, float]]) -> dict[str, Any]:
    primary_particles = [particle for particle in particles if str(particle.get("layer", "")) != "halo"] or particles
    bounds = particle_cloud_bounds(primary_particles)
    breakup = scene.get("breakup", {})
    emitter = deep_merge(emitter_defaults(breakup=breakup), scene.get("emitter", {}))
    direction_space = str(emitter.get("direction_space", EMITTER_DIRECTION_SPACE_CAMERA)).strip().lower()
    if direction_space == EMITTER_DIRECTION_SPACE_SUBJECT:
        right = (1.0, 0.0, 0.0)
        up = (0.0, 1.0, 0.0)
        forward = (0.0, 0.0, 1.0)
    else:
        direction_space = EMITTER_DIRECTION_SPACE_CAMERA
        camera = camera_vectors(scene.get("camera", {}))
        right = camera["right"]
        up = camera["up"]
        forward = camera["forward"]
    if not isinstance(right, tuple) or not isinstance(up, tuple) or not isinstance(forward, tuple):
        return _default_particle_motion_context()
    direction_x = float(emitter.get("direction_x", 0.0) or 0.0)
    direction_y = float(emitter.get("direction_y", 0.0) or 0.0)
    direction_z = float(emitter.get("direction_z", 0.0) or 0.0)
    emitter_direction = _vector_add(
        _vector_add(_vector_scale(right, direction_x), _vector_scale(up, direction_y)),
        _vector_scale(forward, direction_z),
    )
    emitter_strength = clamp(float(emitter.get("strength", 0.74) or 0.74), 0.0, 1.5)
    drift_magnitude = clamp(_vector_length(emitter_direction) * emitter_strength, 0.0, 1.5)
    drift_direction = (0.0, 0.0, 0.0)
    lateral_direction = right
    if drift_magnitude >= 0.05:
        drift_direction = _vector_normalize(emitter_direction)
        lateral_direction = _vector_add(
            _vector_scale(right, -direction_y),
            _vector_scale(up, direction_x),
        )
        if _vector_length(lateral_direction) <= 1.0e-8:
            lateral_direction = right
        else:
            lateral_direction = _vector_normalize(lateral_direction)
    return {
        "center": (
            float(bounds["center"]["x"]),
            float(bounds["center"]["y"]),
            float(bounds["center"]["z"]),
        ),
        "radius": max(float(bounds["radius"]), 1.0e-3),
        "direction_space": direction_space,
        "forward": forward,
        "right": right,
        "up": up,
        "drift_direction": drift_direction,
        "lateral_direction": lateral_direction,
        "drift_magnitude": drift_magnitude,
        "emitter_strength": emitter_strength,
        "emitter_decay": clamp(float(emitter.get("decay", 0.56) or 0.56), 0.0, 1.0),
        "emitter_rate": clamp(float(emitter.get("rate", 0.82) or 0.82), 0.0, 1.5),
    }


def particle_directional_release_bias(particle: dict[str, float], motion_context: dict[str, Any] | None) -> float:
    if not motion_context:
        return 1.0
    drift_magnitude = float(motion_context.get("drift_magnitude", 0.0) or 0.0)
    if drift_magnitude < 0.05:
        return 1.0
    center = motion_context.get("center") or (0.0, 0.0, 0.0)
    radius = max(float(motion_context.get("radius", 1.0) or 1.0), 1.0e-3)
    drift_direction = motion_context.get("drift_direction") or (0.0, 0.0, 0.0)
    if not isinstance(center, tuple) or not isinstance(drift_direction, tuple):
        return 1.0
    projected = _vector_dot(
        (
            float(particle["world_x"]) - float(center[0]),
            float(particle["world_y"]) - float(center[1]),
            float(particle["world_z"]) - float(center[2]),
        ),
        drift_direction,
    ) / radius
    normalized = clamp(projected, -1.25, 1.25)
    bias_strength = clamp(drift_magnitude * 0.72, 0.0, 0.92)
    return clamp(1.0 + (normalized * bias_strength), 0.24, 1.78)


def particle_motion_mode_value(particle: dict[str, float]) -> int:
    raw_value = particle.get("motion_mode", PARTICLE_MOTION_LEGACY_DYNAMIC)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return PARTICLE_MOTION_LEGACY_DYNAMIC


def _odd_kernel_size(radius_px: int) -> int:
    return max(3, (max(1, int(radius_px)) * 2) + 1)


def _build_shell_fields(
    mask_image: Image.Image,
    subject_bounds: dict[str, float],
    subject_analysis: dict[str, Any],
    volume: dict[str, Any],
) -> dict[str, Any]:
    binary = binary_mask(mask_image)
    left, top, right, bottom = _subject_box_pixels(subject_bounds, mask_image.size)
    bbox_width = max(1.0, right - left)
    bbox_height = max(1.0, bottom - top)
    min_dim = max(8.0, min(bbox_width, bbox_height))
    depth_scale = clamp(float(volume.get("depth_scale", 0.58)), 0.0, 1.5)
    thickness_jitter = clamp(float(volume.get("thickness_jitter", 0.16)), 0.0, 1.0)
    shell_radius_px = max(2, int(round(min_dim * (0.010 + (depth_scale * 0.016)))))
    attachment_radius_px = max(shell_radius_px + 1, int(round(min_dim * (0.024 + (thickness_jitter * 0.020)))))
    halo_radius_px = max(attachment_radius_px + 2, int(round(min_dim * (0.030 + (thickness_jitter * 0.030)))))

    eroded_shell = binary.filter(ImageFilter.MinFilter(_odd_kernel_size(shell_radius_px)))
    eroded_attachment = binary.filter(ImageFilter.MinFilter(_odd_kernel_size(attachment_radius_px)))
    dilated_halo = binary.filter(ImageFilter.MaxFilter(_odd_kernel_size(halo_radius_px)))

    shell_band = ImageChops.subtract(binary, eroded_shell).filter(ImageFilter.GaussianBlur(radius=max(1.0, shell_radius_px * 0.35)))
    attachment_band = ImageChops.subtract(eroded_shell, eroded_attachment).filter(ImageFilter.GaussianBlur(radius=max(1.0, shell_radius_px * 0.45)))
    halo_band = ImageChops.subtract(dilated_halo, binary).filter(ImageFilter.GaussianBlur(radius=max(1.0, halo_radius_px * 0.35)))
    core_mask = eroded_attachment.filter(ImageFilter.GaussianBlur(radius=max(1.0, shell_radius_px * 0.5)))

    focus_point = subject_analysis.get("focus_point") or {"x": 0.5, "y": 0.5}
    focus_px = (
        float(focus_point.get("x", 0.5)) * mask_image.width,
        float(focus_point.get("y", 0.5)) * mask_image.height,
    )
    center_x = left + (bbox_width * 0.5)
    center_y = top + (bbox_height * 0.5)
    sample_bounds = (
        max(0, int(math.floor(left - halo_radius_px))),
        max(0, int(math.floor(top - halo_radius_px))),
        min(mask_image.width, int(math.ceil(right + halo_radius_px))),
        min(mask_image.height, int(math.ceil(bottom + halo_radius_px))),
    )
    return {
        "binary": binary,
        "shell_band": shell_band,
        "attachment_band": attachment_band,
        "halo_band": halo_band,
        "core_mask": core_mask,
        "focus_px": focus_px,
        "center_px": (center_x, center_y),
        "bbox_width": bbox_width,
        "bbox_height": bbox_height,
        "sample_bounds": sample_bounds,
        "shell_radius_px": shell_radius_px,
        "attachment_radius_px": attachment_radius_px,
        "halo_radius_px": halo_radius_px,
    }


def _normalize_shell_vector(normal_x: float, normal_y: float, normal_z: float) -> tuple[float, float, float]:
    length = math.sqrt(max((normal_x * normal_x) + (normal_y * normal_y) + (normal_z * normal_z), 1.0e-8))
    return normal_x / length, normal_y / length, normal_z / length


def _sample_prior_support(
    prior_support: dict[str, Any],
    px: float,
    py: float,
) -> dict[str, float] | None:
    samples = prior_support.get("samples") or []
    query_radius = max(float(prior_support.get("query_radius_px", 0.0)), 1.0)
    query_radius_sq = query_radius * query_radius
    total_weight = 0.0
    weighted_z = 0.0
    weighted_nx = 0.0
    weighted_ny = 0.0
    weighted_nz = 0.0
    for sample in samples:
        dx = float(sample["x_px"]) - px
        dy = float(sample["y_px"]) - py
        distance_sq = (dx * dx) + (dy * dy)
        if distance_sq > query_radius_sq:
            continue
        falloff = 1.0 - (distance_sq / query_radius_sq)
        weight = max(float(sample.get("weight", 1.0)) * (falloff * falloff), 0.0)
        if weight <= 0.0:
            continue
        total_weight += weight
        weighted_z += float(sample["z"]) * weight
        weighted_nx += float(sample["normal_x"]) * weight
        weighted_ny += float(sample["normal_y"]) * weight
        weighted_nz += float(sample["normal_z"]) * weight
    if total_weight <= 1.0e-8:
        return None
    normal_x, normal_y, normal_z = _normalize_shell_vector(weighted_nx, weighted_ny, weighted_nz)
    return {
        "z": weighted_z / total_weight,
        "normal_x": normal_x,
        "normal_y": normal_y,
        "normal_z": normal_z,
        "confidence": clamp(total_weight / 2.5, 0.0, 1.0),
    }


def _blend_particle_with_prior_support(
    particle: dict[str, float],
    *,
    px: float,
    py: float,
    prior_support: dict[str, Any] | None,
    depth_scale: float,
) -> dict[str, float]:
    if not prior_support:
        return particle
    if str(particle.get("layer", "")) == "halo":
        return particle
    support = _sample_prior_support(prior_support, px, py)
    if support is None:
        return particle

    layer = str(particle.get("layer", "attachment"))
    layer_blend = 1.0 if layer == "shell" else 0.70
    blend = clamp(support["confidence"] * layer_blend * (0.75 + (particle.get("shell_weight", 0.0) * 0.20)), 0.0, 0.92)
    if blend <= 0.0:
        return particle

    shell_side = -1.0 if float(particle.get("world_z", 0.0)) < 0.0 else 1.0
    base_world_z = float(particle["world_z"])
    support_magnitude = float(support["z"]) * depth_scale * (2.35 if layer == "shell" else 1.28)
    supported_z = shell_side * max(abs(base_world_z), support_magnitude)
    particle["world_z"] = ((1.0 - blend) * base_world_z) + (blend * supported_z)
    normal_x, normal_y, normal_z = _normalize_shell_vector(
        ((1.0 - blend) * particle["normal_x"]) + (blend * support["normal_x"]),
        ((1.0 - blend) * particle["normal_y"]) + (blend * support["normal_y"]),
        ((1.0 - blend) * particle["normal_z"]) + (blend * support["normal_z"] * shell_side),
    )
    particle["normal_x"] = float(normal_x)
    particle["normal_y"] = float(normal_y)
    particle["normal_z"] = float(normal_z)
    particle["depth"] = float(
        clamp(
            ((1.0 - blend) * particle["depth"]) + (blend * clamp(0.5 + (shell_side * support["z"] * 0.38), 0.0, 1.0)),
            0.0,
            1.0,
        )
    )
    return particle


def _world_position_from_pixel(
    px: float,
    py: float,
    *,
    world_center_x: float,
    world_center_y: float,
    world_scale: float,
) -> tuple[float, float]:
    return (
        (px - world_center_x) * world_scale,
        (world_center_y - py) * world_scale,
    )


def generate_particle_specs(
    *,
    scene: dict[str, Any],
    source_image: Image.Image,
    mask_image: Image.Image,
    subject_analysis: dict[str, Any],
    prior_support: dict[str, Any] | None = None,
) -> list[dict[str, float]]:
    luma = ImageOps.autocontrast(source_image.convert("L"), cutoff=1)
    edge = ImageOps.autocontrast(binary_mask(mask_image).filter(ImageFilter.FIND_EDGES), cutoff=1)
    subject_bounds = subject_analysis.get("subject_bounds")
    if not subject_bounds:
        raise WorkbenchError("Approve a mask before generating particles.")
    coverage = float(subject_analysis.get("coverage_ratio") or 0.3)
    surface = scene["surface"]
    breakup = scene["breakup"]
    volume = scene.get("volume", volume_defaults())
    depth_scale = clamp(float(volume.get("depth_scale", 0.58)), 0.0, 1.5)
    depth_curve = clamp(float(volume.get("depth_curve", 1.18)), 0.25, 2.5)
    thickness_jitter = clamp(float(volume.get("thickness_jitter", 0.16)), 0.0, 1.0)
    shell_focus = clamp(depth_curve / 1.18, 0.45, 1.9)
    support_bias = clamp(1.18 - ((shell_focus - 1.0) * 0.34), 0.58, 1.18)
    shell_depth_gain = clamp(0.88 + (shell_focus * 0.24), 0.72, 1.42)
    support_depth_gain = clamp(0.94 - ((shell_focus - 1.0) * 0.22), 0.54, 1.08)
    fields = _build_shell_fields(mask_image, subject_bounds, subject_analysis, volume)
    left, top, right, bottom = fields["sample_bounds"]
    bbox_width = float(fields["bbox_width"])
    bbox_height = float(fields["bbox_height"])
    focus_x, focus_y = fields["focus_px"]
    center_px_x, center_px_y = fields["center_px"]

    target_points = int((5600 + (surface["density"] * 18000)) * clamp(coverage * 1.7, 0.36, 1.10))
    cell = max(2, int(round(math.sqrt((bbox_width * bbox_height) / max(target_points, 1)))))
    rng = random.Random(int(scene.get("seed", 42)))
    particles: list[dict[str, float]] = []
    world_center_x = center_px_x
    world_center_y = center_px_y
    world_scale = 2.0 / max(bbox_width, bbox_height)

    for y in range(int(top), int(bottom), cell):
        for x in range(int(left), int(right), cell):
            jitter_x = ((rng.random() * 2.0) - 1.0) * cell * surface["jitter"] * 0.5
            jitter_y = ((rng.random() * 2.0) - 1.0) * cell * surface["jitter"] * 0.5
            px = clamp(x + (cell * 0.5) + jitter_x, left, right - 1.0)
            py = clamp(y + (cell * 0.5) + jitter_y, top, bottom - 1.0)
            pixel = (int(px), int(py))
            mask_strength = fields["binary"].getpixel(pixel) / 255.0
            shell_strength = fields["shell_band"].getpixel(pixel) / 255.0
            attachment_strength = fields["attachment_band"].getpixel(pixel) / 255.0
            halo_strength = fields["halo_band"].getpixel(pixel) / 255.0
            core_strength = fields["core_mask"].getpixel(pixel) / 255.0
            if max(mask_strength, shell_strength, attachment_strength, halo_strength) < 0.035:
                continue
            luminance = luma.getpixel(pixel) / 255.0
            edge_strength = edge.getpixel(pixel) / 255.0
            focus_dx = (px - focus_x) / max(bbox_width * 0.58, 1.0)
            focus_dy = (py - focus_y) / max(bbox_height * 0.58, 1.0)
            radial_distance = clamp(math.hypot(focus_dx, focus_dy), 0.0, 1.6)
            radial_focus = clamp(1.0 - radial_distance, 0.0, 1.0)
            x_norm = clamp((px - center_px_x) / max(bbox_width * 0.5, 1.0), -1.4, 1.4)
            y_norm = clamp((py - center_px_y) / max(bbox_height * 0.5, 1.0), -1.4, 1.4)
            trailing = _trailing_weight((x_norm * 0.5) + 0.5, (y_norm * 0.5) + 0.5, breakup["drift_x"], breakup["drift_y"])
            shell_presence = clamp(shell_strength + (edge_strength * 0.24) + (halo_strength * 0.04), 0.0, 1.0)
            attachment_presence = clamp(attachment_strength + (core_strength * 0.06), 0.0, 1.0)

            layer = "attachment"
            if shell_presence >= max(attachment_presence * (0.54 + (0.06 * shell_focus)), halo_strength * 1.06, 0.05):
                layer = "shell"
            elif halo_strength > max(shell_presence, attachment_presence * 0.86) and halo_strength > 0.05:
                layer = "halo"

            if layer == "shell":
                keep_probability = clamp(
                    (0.54 + (surface["density"] * 0.24))
                    + (shell_presence * (0.44 + (0.22 * shell_focus)))
                    + (edge_strength * surface["edge_boost"] * (0.20 + (0.12 * shell_focus))),
                    0.0,
                    0.995,
                )
            elif layer == "attachment":
                keep_probability = clamp(
                    (
                        (0.004 + (surface["density"] * 0.018))
                        + (attachment_presence * 0.036 * support_bias)
                        + (radial_focus * 0.010 * support_bias)
                    ),
                    0.0,
                    0.085,
                )
            else:
                keep_probability = clamp(
                    (0.01 + (surface["density"] * 0.028))
                    + (halo_strength * 0.10)
                    + (trailing * (0.08 + (0.04 * shell_focus))),
                    0.0,
                    0.16,
                )
            if rng.random() > keep_probability:
                continue

            normal_2d_x = px - focus_x
            normal_2d_y = py - focus_y
            if abs(normal_2d_x) + abs(normal_2d_y) < 2.0:
                normal_2d_x = px - center_px_x
                normal_2d_y = py - center_px_y
            normal_2d_length = math.hypot(normal_2d_x, normal_2d_y)
            if normal_2d_length < 1.0:
                normal_2d_x, normal_2d_y, normal_2d_length = 0.0, -1.0, 1.0
            normal_2d_x /= normal_2d_length
            normal_2d_y /= normal_2d_length

            front_bias = clamp(0.56 + ((luminance - 0.5) * 0.18) + ((0.5 - clamp((py - top) / max(bbox_height, 1.0), 0.0, 1.0)) * 0.06), 0.34, 0.74)
            shell_side = 1.0 if rng.random() <= front_bias else -1.0

            shell_weight = shell_presence
            attachment_weight = attachment_presence
            depth_jitter = ((rng.random() * 2.0) - 1.0) * thickness_jitter * 0.12
            halo_offset_px = 0.0
            world_depth = depth_scale * (0.30 + (attachment_weight * 0.16)) * support_depth_gain
            alpha_factor = 0.42
            release_weight = clamp(0.16 + (trailing * 0.18) + (attachment_weight * 0.12), 0.0, 1.0)
            retain_weight = clamp(breakup["retain"] * (0.64 + (attachment_weight * 0.12)), 0.0, 1.0)
            drift_scale = 0.82 + (rng.random() * 0.18)
            if layer == "shell":
                world_depth = depth_scale * (0.44 + (shell_weight * (0.26 + (0.10 * shell_focus))) + ((1.0 - radial_focus) * 0.06)) * shell_depth_gain
                alpha_factor = 0.78 + (shell_weight * 0.06)
                release_weight = clamp(0.08 + (trailing * 0.12) + (shell_weight * 0.10) + (edge_strength * 0.08), 0.0, 1.0)
                retain_weight = clamp(breakup["retain"] * (0.88 + (shell_weight * 0.08)), 0.0, 1.0)
                drift_scale = 0.76 + (rng.random() * 0.18)
            elif layer == "halo":
                halo_offset_px = fields["halo_radius_px"] * (0.20 + (halo_strength * 0.85))
                world_depth = depth_scale * (0.72 + (halo_strength * 0.28)) * clamp(0.92 + (shell_focus * 0.10), 0.78, 1.18)
                alpha_factor = 0.16 + (halo_strength * 0.08)
                release_weight = clamp(0.52 + (trailing * 0.16) + (halo_strength * 0.12), 0.0, 1.0)
                retain_weight = clamp(breakup["retain"] * 0.24, 0.0, 1.0)
                drift_scale = 1.08 + (rng.random() * 0.34)

            sample_px = px + (normal_2d_x * halo_offset_px)
            sample_py = py + (normal_2d_y * halo_offset_px)
            world_x, world_y = _world_position_from_pixel(
                sample_px,
                sample_py,
                world_center_x=world_center_x,
                world_center_y=world_center_y,
                world_scale=world_scale,
            )
            normal_x, normal_y, normal_z = _normalize_shell_vector(
                normal_2d_x,
                -normal_2d_y,
                shell_side * (0.78 if layer == "shell" else (0.56 if layer == "attachment" else 0.92)),
            )
            world_z = (shell_side * world_depth) + depth_jitter
            radius_factor = 0.065 + (surface["size"] * 0.16)
            base_radius = max(0.52, cell * radius_factor * (0.92 + (shell_weight * 0.12) + (halo_strength * 0.06)))
            if layer == "halo":
                base_radius *= 0.72
            elif layer == "attachment":
                base_radius *= 0.86
            intensity = clamp((0.30 + (luminance * 0.40) + (edge_strength * 0.18) + (shell_weight * 0.14)) if layer != "halo" else (0.18 + (luminance * 0.24) + (halo_strength * 0.08)), 0.0, 1.0)
            particle = {
                "source_x": float(px),
                "source_y": float(py),
                "world_x": float(world_x),
                "world_y": float(world_y),
                "world_z": float(world_z),
                "world_radius": float(max(base_radius * world_scale * 0.86, 0.0030)),
                "luminance": float(luminance),
                "edge": float(edge_strength),
                "alpha": float(clamp(alpha_factor, 0.12, 1.0)),
                "intensity": float(intensity),
                "release_weight": float(release_weight),
                "retain_weight": float(retain_weight),
                "phase": float(rng.random() * math.pi * 2.0),
                "drift_scale": float(drift_scale),
                "depth": float(clamp(0.5 + (shell_side * 0.28) + (halo_strength * 0.12), 0.0, 1.0)),
                "normal_x": float(normal_x),
                "normal_y": float(normal_y),
                "normal_z": float(normal_z),
                "halo_factor": float(clamp(halo_strength, 0.0, 1.0)),
                "shell_weight": float(clamp(shell_weight, 0.0, 1.0)),
                "layer": layer,
            }
            particles.append(
                _blend_particle_with_prior_support(
                    particle,
                    px=px,
                    py=py,
                    prior_support=prior_support,
                    depth_scale=depth_scale,
                )
            )

    if not particles:
        raise WorkbenchError("Unable to generate particles from the approved mask.")
    return particles


def animated_particle_position(
    particle: dict[str, float],
    breakup: dict[str, float],
    progress: float,
    *,
    motion_context: dict[str, Any] | None = None,
) -> tuple[tuple[float, float, float], float, float]:
    resolved_motion = motion_context or _default_particle_motion_context()
    eased = _ease_in_out(progress)
    settle_envelope = max(0.0, math.sin(eased * math.pi))
    emitter_strength = float(resolved_motion.get("emitter_strength", 0.74) or 0.74)
    emitter_decay = float(resolved_motion.get("emitter_decay", 0.56) or 0.56)
    emitter_rate = float(resolved_motion.get("emitter_rate", 0.82) or 0.82)
    release_bias = particle_directional_release_bias(particle, resolved_motion)
    emission_weight = float(particle.get("emission_weight", particle.get("halo_factor", 0.0)) or 0.0)
    travel_weight = float(particle.get("travel_weight", (0.22 + (emission_weight * 1.1))) or 0.22)
    release_gate = clamp(0.32 + (particle["release_weight"] * release_bias * 1.04), 0.0, 1.85)
    retain_factor = 1.0 - (particle["retain_weight"] * 0.22)
    emission_gain = 0.78 + (emission_weight * 0.94)
    motion_mode = particle_motion_mode_value(particle)
    rate_release_gain = 0.34 + (emitter_rate * (1.24 if motion_mode == PARTICLE_MOTION_EMISSION_PLUME else 0.28))
    strength_release_gain = 0.92 + (emitter_strength * (0.34 if motion_mode == PARTICLE_MOTION_EMISSION_PLUME else 0.08))
    plume_envelope = plume_emission_envelope(progress, particle["phase"], particle["drift_scale"], emitter_rate) if motion_mode == PARTICLE_MOTION_EMISSION_PLUME else eased
    release = (
        (breakup["amount"] ** 0.72)
        * plume_envelope
        * release_gate
        * retain_factor
        * emission_gain
        * rate_release_gain
        * strength_release_gain
    ) if breakup["amount"] > 0.0 else 0.0
    drift_magnitude = float(resolved_motion.get("drift_magnitude", 0.0) or 0.0)
    normal = (
        float(particle["normal_x"]),
        float(particle["normal_y"]),
        float(particle["normal_z"]),
    )
    drift_direction = resolved_motion.get("drift_direction") or (0.0, 0.0, 0.0)
    lateral_direction = resolved_motion.get("lateral_direction") or (1.0, 0.0, 0.0)
    forward = resolved_motion.get("forward") or (0.0, 0.0, 1.0)
    if not isinstance(drift_direction, tuple) or not isinstance(lateral_direction, tuple) or not isinstance(forward, tuple):
        drift_direction = (0.0, 0.0, 0.0)
        lateral_direction = (1.0, 0.0, 0.0)
        forward = (0.0, 0.0, 1.0)
    if motion_mode in {PARTICLE_MOTION_ANCHOR_SHELL, PARTICLE_MOTION_ANCHOR_ATTACHMENT}:
        anchored_release = min(release * (0.10 if motion_mode == PARTICLE_MOTION_ANCHOR_SHELL else 0.14), 0.09)
        settle_distance = min(
            0.0024 if motion_mode == PARTICLE_MOTION_ANCHOR_SHELL else 0.0034,
            breakup["tail"]
            * (0.0012 + (particle.get("shell_weight", 0.0) * 0.0009) + ((1.0 - particle["retain_weight"]) * 0.0007))
            * (0.30 + (breakup["amount"] * 0.34))
            * settle_envelope,
        )
        settle_offset = _vector_scale(normal, settle_distance)
        return (
            (
                particle["world_x"] + settle_offset[0],
                particle["world_y"] + settle_offset[1],
                particle["world_z"] + settle_offset[2],
            ),
            anchored_release,
            0.0,
        )

    release *= 0.92 + (emitter_strength * 0.22)
    decay_tail_gain = 0.86 + ((1.0 - emitter_decay) * 0.68)
    tail_distance = breakup["tail"] * release * decay_tail_gain * (0.72 + (travel_weight * (1.42 + (emitter_strength * 1.36) + (emitter_rate * 0.28))) + (drift_magnitude * 1.02) + (particle["halo_factor"] * 0.22))
    phase = particle["phase"] + (eased * math.pi * 2.0 * particle["drift_scale"])
    normal_lift = 0.30 + (particle["depth"] * 0.24)
    halo_lift = 0.18 + (particle["halo_factor"] * 0.36)
    normal_offset = _vector_scale(normal, tail_distance * normal_lift * (0.72 + (emission_weight * 0.14)))
    drift_weight = 0.36 + halo_lift + (particle["drift_scale"] * 0.14) + (emission_weight * 0.34) + (emitter_strength * 0.52) + (emitter_rate * 0.18)
    directional_offset = _vector_scale(
        drift_direction,
        tail_distance * drift_weight * (0.46 + (drift_magnitude * 1.28) + (travel_weight * 0.28) + (emitter_strength * 0.24)),
    ) if drift_magnitude >= 0.05 else (0.0, 0.0, 0.0)
    depth_offset = _vector_scale(forward, (particle["depth"] - 0.5) * tail_distance * (0.12 + (emission_weight * 0.08)))
    turbulence = breakup["turbulence"] * release * (0.34 + (emission_weight * 0.26) + (emitter_rate * 0.08)) * (0.82 + ((1.0 - emitter_decay) * 0.40))
    swirl = breakup["swirl"] * release * (0.28 + (emission_weight * 0.18)) * (0.78 + ((1.0 - emitter_decay) * 0.32))
    turbulence_offset = _vector_add(
        _vector_scale(lateral_direction, math.cos(phase) * turbulence * (0.16 + (particle["halo_factor"] * 0.08) + (travel_weight * 0.04))),
        _vector_scale(forward, math.sin(phase * 0.73) * turbulence * (0.10 + (particle["depth"] * 0.05) + (emission_weight * 0.04))),
    )
    swirl_axis = _vector_cross(drift_direction if drift_magnitude >= 0.05 else lateral_direction, normal)
    if _vector_length(swirl_axis) <= 1.0e-8:
        swirl_axis = lateral_direction
    else:
        swirl_axis = _vector_normalize(swirl_axis)
    swirl_offset = _vector_add(
        _vector_scale(swirl_axis, math.sin(phase * 0.81) * swirl * (0.10 + (particle["halo_factor"] * 0.07) + (emission_weight * 0.05))),
        _vector_add(
            _vector_scale(lateral_direction, math.cos(phase * 0.93) * swirl * (0.07 + (travel_weight * 0.015))),
            _vector_scale(forward, math.cos(phase * 0.61) * swirl * (0.05 + (emission_weight * 0.02)) * abs(particle["normal_z"])),
        ),
    )
    offset = _vector_add(
        _vector_add(normal_offset, directional_offset),
        _vector_add(depth_offset, _vector_add(turbulence_offset, swirl_offset)),
    )
    return (
        (
            particle["world_x"] + offset[0],
            particle["world_y"] + offset[1],
            particle["world_z"] + offset[2],
        ),
        release,
        tail_distance,
    )


def projected_particle_radius(world_radius: float, focal: float, camera_z: float) -> float:
    return max(0.34, (world_radius * focal) / max(camera_z, 0.001))


def particle_display_brightness(scene: dict[str, Any], particle: dict[str, float]) -> float:
    surface = scene["surface"]
    contrast = clamp(float(scene["render"]["contrast"]), 0.4, 1.8)
    emitter = deep_merge(emitter_defaults(breakup=scene.get("breakup", {})), scene.get("emitter", {}))
    emitter_strength = clamp(float(emitter.get("strength", 0.74) or 0.74), 0.0, 1.5)
    emitter_rate = clamp(float(emitter.get("rate", 0.82) or 0.82), 0.0, 1.5)
    brightness = clamp(
        (surface["luminance_floor"] * 0.28)
        + ((particle["intensity"] ** (1.0 / contrast)) * 1.02)
        + (particle["edge"] * 0.24)
        + (particle.get("shell_weight", 0.0) * 0.30)
        - (particle.get("halo_factor", 0.0) * 0.04),
        0.0,
        1.0,
    )
    layer = str(particle.get("layer", "attachment"))
    if layer == "attachment":
        brightness *= 0.94
    elif layer == "halo":
        brightness *= 0.78
    elif layer == "emission":
        brightness = clamp(
            (brightness * 1.32)
            + 0.22
            + (float(particle.get("emission_weight", 0.0) or 0.0) * 0.18)
            + (emitter_strength * 0.06)
            + (emitter_rate * 0.08),
            0.0,
            1.0,
        )
    return clamp(brightness, 0.0, 1.0)


def particle_display_alpha_terms(scene: dict[str, Any], particle: dict[str, float], brightness: float) -> tuple[float, float]:
    layer = str(particle.get("layer", "attachment"))
    emitter = deep_merge(emitter_defaults(breakup=scene.get("breakup", {})), scene.get("emitter", {}))
    emitter_strength = clamp(float(emitter.get("strength", 0.74) or 0.74), 0.0, 1.5)
    emitter_decay = clamp(float(emitter.get("decay", 0.56) or 0.56), 0.0, 1.0)
    emitter_rate = clamp(float(emitter.get("rate", 0.82) or 0.82), 0.0, 1.5)
    layer_gain = 2.20 if layer == "shell" else (0.78 if layer == "attachment" else (0.42 if layer == "emission" else 0.32))
    surface_opacity = float(scene["surface"]["opacity"])
    base_alpha = ((72.0 + (brightness * 206.0)) * particle["alpha"] * surface_opacity * layer_gain) / 255.0
    alpha_decay = ((18.0 + (particle["release_weight"] * 28.0) + (float(particle.get("emission_weight", 0.0) or 0.0) * 12.0)) * particle["alpha"] * surface_opacity * layer_gain) / 255.0
    if layer == "emission":
        base_alpha *= 3.8 + (emitter_rate * 0.34) + (emitter_strength * 0.12)
        alpha_decay *= 0.16 + (emitter_decay * 1.04)
    min_alpha = 0.06 if layer == "emission" else 0.025
    return clamp(base_alpha, min_alpha, 1.0), clamp(alpha_decay, 0.008 if layer == "emission" else 0.01, 0.45)


def particle_display_alpha(scene: dict[str, Any], particle: dict[str, float], brightness: float, release: float) -> float:
    base_alpha, alpha_decay = particle_display_alpha_terms(scene, particle, brightness)
    return clamp(base_alpha - (release * alpha_decay), 0.025, 1.0)


def _draw_dot(draw: ImageDraw.ImageDraw, x: float, y: float, radius: float, alpha: int, intensity: int) -> None:
    if alpha <= 0 or radius <= 0.0:
        return
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=(intensity, intensity, intensity, alpha),
    )


def render_frame(
    *,
    project: dict[str, Any],
    source_image: Image.Image,
    mask_image: Image.Image,
    particles: list[dict[str, float]],
    width: int,
    height: int,
    frame_index: int,
    total_frames: int,
    transparent_background: bool = False,
) -> Image.Image:
    scene = project["scene"]
    breakup = scene["breakup"]
    render_settings = scene["render"]
    progress = frame_index / max(total_frames - 1, 1)
    eased = _ease_in_out(progress)
    camera = camera_vectors(scene.get("camera", {}))
    motion_context = particle_motion_context(scene, particles)

    bg_value = int(clamp(render_settings["background"], 0.0, 1.0) * 255.0)
    if transparent_background:
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    else:
        canvas = Image.new("RGBA", (width, height), (bg_value, bg_value, bg_value, 255))
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dot_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer, "RGBA")
    dot_draw = ImageDraw.Draw(dot_layer, "RGBA")

    glow_strength = clamp(render_settings["glow"], 0.0, 1.0)
    projected_particles: list[dict[str, Any]] = []

    for particle in particles:
        anchor = (particle["world_x"], particle["world_y"], particle["world_z"])
        world, release, tail_distance = animated_particle_position(
            particle,
            breakup,
            progress,
            motion_context=motion_context,
        )
        projected = project_point(world, camera, width, height)
        anchor_projected = project_point(anchor, camera, width, height)
        if projected is None or anchor_projected is None:
            continue
        projected_particles.append(
            {
                "screen_x": projected[0],
                "screen_y": projected[1],
                "camera_z": projected[2],
                "anchor_x": anchor_projected[0],
                "anchor_y": anchor_projected[1],
                "anchor_z": anchor_projected[2],
                "release": release,
                "tail_distance": tail_distance,
                "particle": particle,
            }
        )

    projected_particles.sort(key=lambda item: item["camera_z"], reverse=True)

    focal = (height * 0.5) / math.tan(math.radians(float(camera["fov"]) * 0.5))
    for item in projected_particles:
        particle = item["particle"]
        layer = str(particle.get("layer", "attachment"))
        emitter = scene.get("emitter", {})
        emitter_rate = clamp(float(emitter.get("rate", 0.82) or 0.82), 0.0, 1.5)
        radius = projected_particle_radius(particle["world_radius"], focal, item["camera_z"])
        if layer == "emission":
            radius *= 1.24 + (emitter_rate * 0.10)
        brightness = particle_display_brightness(scene, particle)
        alpha_factor = particle_display_alpha(scene, particle, brightness, item["release"])
        intensity = int(clamp(110.0 + (brightness * 145.0), 0.0, 255.0))
        alpha = int(clamp(alpha_factor * 255.0, 6.0, 255.0))
        _draw_dot(dot_draw, item["screen_x"], item["screen_y"], radius, alpha, intensity)

        if glow_strength > 0.0:
            glow_alpha = int(alpha * ((0.22 + (float(particle.get("emission_weight", 0.0) or 0.0) * 0.10)) if layer == "emission" else (0.12 + (particle.get("shell_weight", 0.0) * 0.06))) * glow_strength)
            glow_radius = radius * ((2.2 + (glow_strength * 1.5)) if layer == "emission" else (1.8 + (glow_strength * 1.2)))
            _draw_dot(glow_draw, item["screen_x"], item["screen_y"], glow_radius, glow_alpha, intensity)

        if layer == "emission" and item["tail_distance"] > 0.05 and (particle["release_weight"] > 0.24 or float(particle.get("emission_weight", 0.0) or 0.0) > 0.30):
            trail_steps = 3 + int(round(float(particle.get("emission_weight", 0.0) or 0.0) * 4.0) + round(emitter_rate * 2.0))
            for trail_index in range(1, trail_steps + 1):
                trail_ratio = trail_index / (trail_steps + 1)
                trail_x = item["anchor_x"] + ((item["screen_x"] - item["anchor_x"]) * trail_ratio * 0.96)
                trail_y = item["anchor_y"] + ((item["screen_y"] - item["anchor_y"]) * trail_ratio * 0.96)
                trail_alpha = int(alpha * (0.62 - (trail_ratio * 0.22)))
                trail_radius = radius * (1.06 - (trail_ratio * 0.24))
                _draw_dot(dot_draw, trail_x, trail_y, trail_radius, trail_alpha, intensity)

    if glow_strength > 0.0:
        blur_radius = max(1, int(round(1 + (glow_strength * 4))))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        canvas.alpha_composite(glow_layer)
    canvas.alpha_composite(dot_layer)
    return canvas


def generate_active_particle_specs(project_path: Path, project: dict[str, Any]) -> list[dict[str, float]]:
    volume_backend = str(project.get("scene", {}).get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)).strip()
    if volume_backend == VOLUME_BACKEND_MODEL_SOURCE:
        point_cache_path = Path(str(project.get("model_source", {}).get("point_cache_path", ""))).expanduser()
        if not point_cache_path.exists():
            raise WorkbenchError("Selected model source is missing its point cache.")
        try:
            return build_model_particles_from_cache(
                point_cache_path,
                project["scene"],
                model_transform=_project_model_source_transform(project),
            )
        except ModelSourceError as exc:
            raise WorkbenchError(str(exc)) from exc

    source_image_path = Path(project["source_image"]["path"]).expanduser().resolve()
    if not source_image_path.exists():
        raise WorkbenchError(f"Source image is missing: {source_image_path}")
    with Image.open(source_image_path) as opened:
        source_image = opened.convert("RGBA")
        mask_image = read_mask_file(project_mask_paths(project_path, str(project["active_source_id"])).approved, source_image.size)
        prior_support = None
        candidate = active_source_candidate(project)
        prior_metadata, support = _resolve_prior_assist_support(
            project_path,
            project,
            candidate,
            source_image,
            mask_image,
            project.get("subject_analysis", {}) or {},
        )
        if str(prior_metadata.get("status", "")).strip() == PRIOR_ASSIST_STATUS_ACTIVE:
            prior_support = support
        return generate_particle_specs(
            scene=project["scene"],
            source_image=source_image,
            mask_image=mask_image,
            subject_analysis=project["subject_analysis"],
            prior_support=prior_support,
        )


def build_raw_model_preview_payload(
    point_cache_path: Path,
    scene: dict[str, Any],
    model_transform: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        point_cache = json.loads(point_cache_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ModelSourceError(f"Model point cache is invalid: {point_cache_path}: {exc}") from exc
    base_points = point_cache.get("points") or []
    if not isinstance(base_points, list) or not base_points:
        raise ModelSourceError(f"Model point cache is missing or empty: {point_cache_path}")
    transformed_points = transform_model_source_points(base_points, model_transform)
    surface = scene.get("surface", {}) if isinstance(scene.get("surface"), dict) else {}
    base_radius = 0.0032 + (float(surface.get("size", 0.22)) * 0.0075)
    encoded_points: list[list[float]] = []
    for entry in transformed_points:
        if not isinstance(entry, list) or len(entry) < 7:
            continue
        x, y, z, _normal_x, _normal_y, normal_z, curvature = [float(value) for value in entry[:7]]
        brightness = clamp(0.42 + (curvature * 0.22) + (max(normal_z, 0.0) * 0.26), 0.18, 0.98)
        alpha = clamp(0.82 + (curvature * 0.10), 0.72, 0.96)
        radius = max(base_radius * (0.92 + (curvature * 0.16)), 0.0022)
        encoded_points.append([
            round(x, 5),
            round(y, 5),
            round(z, 5),
            round(radius, 5),
            round(brightness, 5),
            round(alpha, 5),
        ])
    if not encoded_points:
        raise ModelSourceError(f"Model point cache did not contain any valid preview samples: {point_cache_path}")
    return {
        "schema": ["x", "y", "z", "radius", "brightness", "alpha"],
        "points": encoded_points,
    }


def _project_model_raw_asset_path(project: dict[str, Any]) -> Path | None:
    model_source = project.get("model_source", {})
    if not isinstance(model_source, dict):
        return None
    for key in ("raw_asset_path", "decoded_asset_path", "normalized_asset_path"):
        candidate = Path(str(model_source.get(key, "")).strip()).expanduser()
        if candidate.exists():
            return candidate
    return None


def _image_data_url(image: Any, *, default_mime_type: str = "image/png") -> str:
    if image is None:
        return ""
    if isinstance(image, Image.Image):
        buffer = io.BytesIO()
        image_format = "PNG"
        mime_type = default_mime_type
        if image.format:
            candidate_format = str(image.format).upper()
            if candidate_format in {"PNG", "JPEG", "WEBP"}:
                image_format = candidate_format
                mime_type = Image.MIME.get(image_format, default_mime_type)
        image.save(buffer, format=image_format)
        return f"data:{mime_type};base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}"
    if isinstance(image, (bytes, bytearray)):
        return f"data:{default_mime_type};base64,{base64.b64encode(bytes(image)).decode('ascii')}"
    return ""


def _decode_data_uri_bytes(uri: str) -> tuple[bytes, str]:
    match = re.match(r"^data:(?P<mime>[^;,]+)?(?:;charset=[^;,]+)?;base64,(?P<data>.+)$", uri, re.IGNORECASE)
    if not match:
        raise ModelSourceError("Unsupported embedded data URI in model asset.")
    mime_type = str(match.group("mime") or "application/octet-stream").strip() or "application/octet-stream"
    return base64.b64decode(match.group("data")), mime_type


def _gltf_buffer_bytes(gltf: Any, asset_path: Path, buffer_index: int) -> bytes:
    if buffer_index < 0 or buffer_index >= len(gltf.buffers or []):
        raise ModelSourceError("glTF buffer index is out of range.")
    buffer = gltf.buffers[buffer_index]
    uri = str(getattr(buffer, "uri", "") or "").strip()
    if uri:
        if uri.startswith("data:"):
            data, _mime_type = _decode_data_uri_bytes(uri)
            return data
        return (asset_path.parent / unquote(uri)).read_bytes()
    blob = gltf.binary_blob()
    if blob is None:
        raise ModelSourceError("glTF buffer payload is missing.")
    return bytes(blob)


def _gltf_image_data_url(gltf: Any, asset_path: Path, image_index: int) -> str:
    if image_index < 0 or image_index >= len(gltf.images or []):
        return ""
    image = gltf.images[image_index]
    uri = str(getattr(image, "uri", "") or "").strip()
    if uri:
        if uri.startswith("data:"):
            return uri
        image_path = asset_path.parent / unquote(uri)
        mime_type = str(getattr(image, "mimeType", "") or mimetypes.guess_type(str(image_path))[0] or "application/octet-stream")
        return f"data:{mime_type};base64,{base64.b64encode(image_path.read_bytes()).decode('ascii')}"
    buffer_view_index = getattr(image, "bufferView", None)
    if buffer_view_index is None or buffer_view_index >= len(gltf.bufferViews or []):
        return ""
    buffer_view = gltf.bufferViews[buffer_view_index]
    buffer_bytes = _gltf_buffer_bytes(gltf, asset_path, int(buffer_view.buffer))
    start = int(getattr(buffer_view, "byteOffset", 0) or 0)
    end = start + int(getattr(buffer_view, "byteLength", 0) or 0)
    mime_type = str(getattr(image, "mimeType", "") or "application/octet-stream")
    return f"data:{mime_type};base64,{base64.b64encode(buffer_bytes[start:end]).decode('ascii')}"


def _gltf_material_texture_map(asset_path: Path) -> dict[str, dict[str, str]]:
    if pygltflib is None or asset_path.suffix.lower() not in {".glb", ".gltf"}:
        return {}
    try:
        gltf = pygltflib.GLTF2()
        if asset_path.suffix.lower() == ".glb":
            gltf.load_binary(str(asset_path))
        else:
            gltf.load(str(asset_path))
    except Exception:
        return {}
    textures = gltf.textures or []
    image_urls = [
        _gltf_image_data_url(gltf, asset_path, int(texture.source))
        if getattr(texture, "source", None) is not None
        else ""
        for texture in textures
    ]
    payload_by_name: dict[str, dict[str, str]] = {}
    for index, material in enumerate(gltf.materials or []):
        material_name = str(getattr(material, "name", "") or f"material_{index}")
        pbr = getattr(material, "pbrMetallicRoughness", None)
        base_color_texture = getattr(getattr(pbr, "baseColorTexture", None), "index", None)
        metallic_roughness_texture = getattr(getattr(pbr, "metallicRoughnessTexture", None), "index", None)
        normal_texture = getattr(getattr(material, "normalTexture", None), "index", None)
        emissive_texture = getattr(getattr(material, "emissiveTexture", None), "index", None)
        payload_by_name[material_name] = {
            "map": image_urls[int(base_color_texture)] if base_color_texture is not None and int(base_color_texture) < len(image_urls) else "",
            "metallic_roughness_map": image_urls[int(metallic_roughness_texture)] if metallic_roughness_texture is not None and int(metallic_roughness_texture) < len(image_urls) else "",
            "normal_map": image_urls[int(normal_texture)] if normal_texture is not None and int(normal_texture) < len(image_urls) else "",
            "emissive_map": image_urls[int(emissive_texture)] if emissive_texture is not None and int(emissive_texture) < len(image_urls) else "",
        }
    return payload_by_name


def _material_color_components(value: Any, *, default: tuple[float, float, float, float]) -> list[float]:
    if value is None:
        return [round(component, 5) for component in default]
    try:
        components = [float(component) for component in value]
    except TypeError:
        return [round(component, 5) for component in default]
    if len(components) == 3:
        components.append(default[3])
    if len(components) < 4:
        components.extend(default[len(components):4])
    scale = 255.0 if max(abs(component) for component in components[:4]) > 1.0001 else 1.0
    return [
        round(clamp(components[0] / scale, 0.0, 1.0), 5),
        round(clamp(components[1] / scale, 0.0, 1.0), 5),
        round(clamp(components[2] / scale, 0.0, 1.0), 5),
        round(clamp(components[3] / scale, 0.0, 1.0), 5),
    ]


def _mesh_material_payload(mesh: Any, asset_path: Path, gltf_textures: dict[str, dict[str, str]]) -> dict[str, Any]:
    visual = getattr(mesh, "visual", None)
    material = getattr(visual, "material", None) if visual is not None else None
    base_color = _material_color_components(
        getattr(material, "baseColorFactor", None) if material is not None else None,
        default=(0.82, 0.82, 0.82, 1.0),
    )
    if material is not None and base_color == [0.82, 0.82, 0.82, 1.0]:
        base_color = _material_color_components(getattr(material, "main_color", None), default=(0.82, 0.82, 0.82, 1.0))
    emissive = _material_color_components(getattr(material, "emissiveFactor", None), default=(0.0, 0.0, 0.0, 1.0))[:3]
    material_name = str(getattr(material, "name", "") or "")
    texture_payload = copy.deepcopy(gltf_textures.get(material_name, {}))
    if material is not None:
        if not texture_payload.get("map"):
            texture_payload["map"] = (
                _image_data_url(getattr(material, "baseColorTexture", None))
                or _image_data_url(getattr(material, "image", None))
                or _image_data_url(getattr(getattr(material, "to_simple", lambda: None)(), "image", None))
            )
        if not texture_payload.get("normal_map"):
            texture_payload["normal_map"] = _image_data_url(getattr(material, "normalTexture", None))
        if not texture_payload.get("metallic_roughness_map"):
            texture_payload["metallic_roughness_map"] = _image_data_url(getattr(material, "metallicRoughnessTexture", None))
        if not texture_payload.get("emissive_map"):
            texture_payload["emissive_map"] = _image_data_url(getattr(material, "emissiveTexture", None))
    opacity = round(base_color[3], 5)
    alpha_mode = str(getattr(material, "alphaMode", "") or "").strip().upper() if material is not None else ""
    return {
        "name": material_name,
        "base_color": base_color,
        "emissive": emissive,
        "opacity": opacity,
        "metalness": round(clamp(float(getattr(material, "metallicFactor", 0.0) or 0.0), 0.0, 1.0), 5) if material is not None else 0.0,
        "roughness": round(clamp(float(getattr(material, "roughnessFactor", 1.0) or 1.0), 0.0, 1.0), 5) if material is not None else 1.0,
        "double_sided": bool(getattr(material, "doubleSided", False)) if material is not None else False,
        "alpha_mode": alpha_mode or ("BLEND" if opacity < 0.999 else "OPAQUE"),
        "alpha_cutoff": round(clamp(float(getattr(material, "alphaCutoff", 0.5) or 0.5), 0.0, 1.0), 5) if material is not None else 0.5,
        "map": str(texture_payload.get("map", "") or ""),
        "normal_map": str(texture_payload.get("normal_map", "") or ""),
        "metallic_roughness_map": str(texture_payload.get("metallic_roughness_map", "") or ""),
        "emissive_map": str(texture_payload.get("emissive_map", "") or ""),
        "flip_y": asset_path.suffix.lower() == ".obj",
    }


def _mesh_vertex_normals(mesh: Any) -> list[tuple[float, float, float]] | None:
    vertices = getattr(mesh, "vertices", None)
    faces = getattr(mesh, "faces", None)
    face_normals = getattr(mesh, "face_normals", None)
    if vertices is None or faces is None or face_normals is None:
        return None
    if not len(vertices) or not len(faces) or len(face_normals) != len(faces):
        return None
    accum = [[0.0, 0.0, 0.0] for _ in range(len(vertices))]
    for face, normal in zip(faces, face_normals):
        nx, ny, nz = [float(component) for component in normal]
        for vertex_index in face:
            target = accum[int(vertex_index)]
            target[0] += nx
            target[1] += ny
            target[2] += nz
    normals: list[tuple[float, float, float]] = []
    for nx, ny, nz in accum:
        length = math.sqrt(max((nx * nx) + (ny * ny) + (nz * nz), 1.0e-12))
        normals.append((nx / length, ny / length, nz / length))
    return normals


def build_raw_model_mesh_payload(raw_asset_path: Path, model_transform: dict[str, Any] | None = None) -> dict[str, Any]:
    if trimesh is None:
        raise ModelSourceError("Mesh preview runtime is unavailable.")
    suffix = raw_asset_path.suffix.lower()
    if suffix not in {".glb", ".gltf", ".obj"}:
        raise ModelSourceError(f"Unsupported raw-model preview format: {raw_asset_path.suffix}")
    loaded = trimesh.load(str(raw_asset_path), force="scene")
    meshes: list[tuple[str, Any]] = []
    if isinstance(loaded, trimesh.Trimesh):
        meshes = [(raw_asset_path.stem, loaded.copy())]
    elif isinstance(loaded, trimesh.Scene):
        for node_name in loaded.graph.nodes_geometry:
            transform, geometry_name = loaded.graph[node_name]
            geometry = loaded.geometry.get(geometry_name)
            if not isinstance(geometry, trimesh.Trimesh) or not len(geometry.vertices) or not len(geometry.faces):
                continue
            transformed = geometry.copy()
            transformed.apply_transform(transform)
            meshes.append((str(node_name or geometry_name), transformed))
        if not meshes:
            for geometry_name, geometry in loaded.geometry.items():
                if isinstance(geometry, trimesh.Trimesh) and len(geometry.vertices) and len(geometry.faces):
                    meshes.append((str(geometry_name), geometry.copy()))
    if not meshes:
        raise ModelSourceError(f"Raw model preview is empty: {raw_asset_path}")

    min_corner: list[float] | None = None
    max_corner: list[float] | None = None
    for _name, mesh in meshes:
        bounds = mesh.bounds
        if bounds is None or len(bounds) != 2:
            continue
        if min_corner is None:
            min_corner = [float(value) for value in bounds[0]]
            max_corner = [float(value) for value in bounds[1]]
        else:
            min_corner = [min(min_corner[index], float(bounds[0][index])) for index in range(3)]
            max_corner = [max(max_corner[index], float(bounds[1][index])) for index in range(3)]
    if min_corner is None or max_corner is None:
        raise ModelSourceError(f"Raw model preview is missing usable bounds: {raw_asset_path}")

    center = [(min_corner[index] + max_corner[index]) / 2.0 for index in range(3)]
    extents = [max_corner[index] - min_corner[index] for index in range(3)]
    max_extent = float(max(float(extent) for extent in extents))
    if max_extent <= 1.0e-8:
        raise ModelSourceError(f"Raw model preview has zero usable bounds: {raw_asset_path}")
    normalization_scale = 2.0 / max_extent
    gltf_textures = _gltf_material_texture_map(raw_asset_path)

    encoded_meshes: list[dict[str, Any]] = []
    visibility_points: list[list[float]] = []
    total_vertices = sum(len(mesh.vertices) for _name, mesh in meshes)
    visibility_step = max(1, total_vertices // 320)
    visibility_counter = 0
    for mesh_name, mesh in meshes:
        normalized_vertices = mesh.vertices.copy()
        normalized_vertices[:, 0] = (normalized_vertices[:, 0] - center[0]) * normalization_scale
        normalized_vertices[:, 1] = (normalized_vertices[:, 1] - center[1]) * normalization_scale
        normalized_vertices[:, 2] = (normalized_vertices[:, 2] - center[2]) * normalization_scale
        faces = getattr(mesh, "faces", None)
        if faces is None or not len(faces):
            continue
        normals = _mesh_vertex_normals(mesh)
        if normals is not None and len(normals) != len(normalized_vertices):
            normals = None
        uv = getattr(getattr(mesh, "visual", None), "uv", None)
        if uv is not None and len(uv) != len(normalized_vertices):
            uv = None
        positions_payload: list[float] = []
        normals_payload: list[float] = []
        uvs_payload: list[float] = []
        for vertex_index, vertex in enumerate(normalized_vertices):
            x, y, z = rotate_model_source_vector(
                (float(vertex[0]), float(vertex[1]), float(vertex[2])),
                model_transform,
            )
            x, y, z = [round(float(component), 6) for component in (x, y, z)]
            positions_payload.extend((x, y, z))
            if visibility_counter % visibility_step == 0 and len(visibility_points) < 512:
                visibility_points.append([x, y, z])
            visibility_counter += 1
            if normals is not None:
                nx, ny, nz = rotate_model_source_vector(
                    (
                        float(normals[vertex_index][0]),
                        float(normals[vertex_index][1]),
                        float(normals[vertex_index][2]),
                    ),
                    model_transform,
                )
                nx, ny, nz = _vector_normalize((nx, ny, nz))
                nx, ny, nz = [round(float(component), 6) for component in (nx, ny, nz)]
                normals_payload.extend((nx, ny, nz))
            if uv is not None:
                u, v = uv[vertex_index]
                uvs_payload.extend((round(float(u), 6), round(float(v), 6)))
        encoded_meshes.append(
            {
                "name": mesh_name,
                "positions": positions_payload,
                "normals": normals_payload,
                "uvs": uvs_payload,
                "indices": [int(index) for face in faces for index in face],
                "material": _mesh_material_payload(mesh, raw_asset_path, gltf_textures),
            }
        )
    if not visibility_points:
        visibility_points = [
            [0.0, 0.0, 0.0],
        ]
    return {
        "format": "mesh_v1",
        "meshes": encoded_meshes,
        "visibility_points": visibility_points,
    }


def build_effect_scene_payload(project_path: Path, project: dict[str, Any]) -> dict[str, Any]:
    ensure_effect_ready(project)
    particles = generate_active_particle_specs(project_path, project)
    model_transform = _project_model_source_transform(project)
    resolved_emitter = _resolve_scene_emitter(
        project["scene"],
        model_point_cache_path=_project_model_point_cache_path(project),
        model_transform=model_transform,
    )
    model_source_payload = copy.deepcopy(project.get("model_source", {}))
    model_point_cache_path = _project_model_point_cache_path(project)
    raw_model_asset_path = _project_model_raw_asset_path(project)
    raw_model_preview = {
        "schema": ["x", "y", "z", "radius", "brightness", "alpha"],
        "points": [],
    }
    raw_model_mesh = {
        "format": "mesh_v1",
        "meshes": [],
        "visibility_points": [],
    }
    if model_point_cache_path is not None:
        try:
            model_source_payload["subject_frame"] = load_subject_frame_from_point_cache(
                model_point_cache_path,
                model_transform=model_transform,
            )
        except ModelSourceError:
            pass
        raw_model_preview = build_raw_model_preview_payload(
            model_point_cache_path,
            project["scene"],
            model_transform=model_transform,
        )
    if raw_model_asset_path is not None:
        try:
            raw_model_mesh = build_raw_model_mesh_payload(raw_model_asset_path, model_transform=model_transform)
        except Exception:
            raw_model_mesh = {
                "format": "mesh_v1",
                "meshes": [],
                "visibility_points": [],
            }
    point_schema = ["x", "y", "z", "radius", "release", "retain", "normal_x", "normal_y", "normal_z", "phase", "drift", "depth", "halo", "edge", "shell", "travel", "emit", "brightness", "alpha_base", "alpha_decay", "motion_mode"]

    def encode_particle(particle: dict[str, float]) -> list[float]:
        brightness = particle_display_brightness(project["scene"], particle)
        alpha_base, alpha_decay = particle_display_alpha_terms(project["scene"], particle, brightness)
        return [
            round(particle["world_x"], 5),
            round(particle["world_y"], 5),
            round(particle["world_z"], 5),
            round(particle["world_radius"], 5),
            round(particle["release_weight"], 5),
            round(particle["retain_weight"], 5),
            round(particle["normal_x"], 5),
            round(particle["normal_y"], 5),
            round(particle["normal_z"], 5),
            round(particle["phase"], 5),
            round(particle["drift_scale"], 5),
            round(particle["depth"], 5),
            round(particle["halo_factor"], 5),
            round(particle["edge"], 5),
            round(particle["shell_weight"], 5),
            round(float(particle.get("travel_weight", 0.22) or 0.22), 5),
            round(float(particle.get("emission_weight", particle.get("halo_factor", 0.0)) or 0.0), 5),
            round(brightness, 5),
            round(alpha_base, 5),
            round(alpha_decay, 5),
            particle_motion_mode_value(particle),
        ]

    anchored_particles = [
        particle for particle in particles
        if particle_motion_mode_value(particle) in {PARTICLE_MOTION_ANCHOR_SHELL, PARTICLE_MOTION_ANCHOR_ATTACHMENT}
    ]
    emitter_particles = [
        particle for particle in particles
        if particle_motion_mode_value(particle) not in {PARTICLE_MOTION_ANCHOR_SHELL, PARTICLE_MOTION_ANCHOR_ATTACHMENT}
    ]
    raw_model_fit_samples = [
        {
            "world_x": float(point[0]),
            "world_y": float(point[1]),
            "world_z": float(point[2]),
            "layer": "shell",
        }
        for point in raw_model_mesh.get("visibility_points", [])
    ]
    if not raw_model_fit_samples:
        raw_model_fit_samples = [
            {
                "world_x": float(point[0]),
                "world_y": float(point[1]),
                "world_z": float(point[2]),
                "layer": "shell",
            }
            for point in raw_model_preview["points"]
        ]
    fit_camera = fit_camera_for_particles(project["scene"], particles)
    raw_model_fit_camera = fit_camera_for_particles(project["scene"], raw_model_fit_samples) if raw_model_fit_samples else copy.deepcopy(project["scene"]["camera"])
    reset_camera = _canonical_reset_camera_from_point_cache(
        model_point_cache_path,
        fit_camera=fit_camera,
        model_transform=model_transform,
    )
    raw_model_reset_camera = _canonical_reset_camera_from_point_cache(
        model_point_cache_path,
        fit_camera=raw_model_fit_camera,
        model_transform=model_transform,
    )
    return {
        "source_id": str(project["active_source_id"]),
        "camera": copy.deepcopy(project["scene"]["camera"]),
        "fit_camera": fit_camera,
        "reset_camera": reset_camera,
        "raw_model_fit_camera": raw_model_fit_camera,
        "raw_model_reset_camera": raw_model_reset_camera,
        "scene": {
            "effect_model": str(project["scene"].get("effect_model", DEFAULT_EFFECT_MODEL)),
            "volume_backend": str(project["scene"].get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)),
            "preset_family": str(project["scene"]["preset_family"]),
            "surface": copy.deepcopy(project["scene"]["surface"]),
            "breakup": copy.deepcopy(project["scene"]["breakup"]),
            "emitter": copy.deepcopy(resolved_emitter),
            "framing": copy.deepcopy(project["scene"]["framing"]),
            "render": copy.deepcopy(project["scene"]["render"]),
            "volume": copy.deepcopy(project["scene"]["volume"]),
            "shot": copy.deepcopy(project["scene"].get("shot", {})),
        },
        "model_source": model_source_payload,
        "prior_assist": copy.deepcopy(project.get("prior_assist", prior_assist_defaults())),
        "approval": copy.deepcopy(project.get("approval", approval_defaults())),
        "appearance": {
            "min_radius_px": 0.34,
            "background": float(project["scene"]["render"]["background"]),
        },
        "bounds": particle_cloud_bounds(particles),
        "raw_model_mesh": raw_model_mesh,
        "raw_model_schema": raw_model_preview["schema"],
        "raw_model_points": raw_model_preview["points"],
        "point_schema": point_schema,
        "points": [encode_particle(particle) for particle in particles],
        "anchored_points": [encode_particle(particle) for particle in anchored_particles],
        "emitter_points": [encode_particle(particle) for particle in emitter_particles],
    }


def encode_frames_to_video(frames_dir: Path, fps: int, output_path: Path, *, alpha: bool = False) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise WorkbenchError("ffmpeg is required for workbench export-shot.")
    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.png"),
    ]
    if alpha:
        if output_path.suffix.lower() != ".mov":
            raise WorkbenchError("Alpha workbench exports currently require a `.mov` output path.")
        command.extend(
            [
                "-c:v",
                "prores_ks",
                "-profile:v",
                "4444",
                "-pix_fmt",
                "yuva444p10le",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
    else:
        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "veryslow",
                "-profile:v",
                "high",
                "-crf",
                "10",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
    run_checked_command(command)


def encode_frames_to_lossless_master_video(frames_dir: Path, fps: int, output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise WorkbenchError("ffmpeg is required for workbench export-shot.")
    if output_path.suffix.lower() != ".mkv":
        raise WorkbenchError("Opaque workbench master exports require a `.mkv` output path.")
    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.png"),
        "-c:v",
        "ffv1",
        "-pix_fmt",
        "bgra",
        str(output_path),
    ]
    run_checked_command(command)


def export_frames_with_webgl(
    repo_root: Path,
    session_url: str,
    frames_dir: Path,
    export_request: ExportRequest,
) -> None:
    node = shutil.which("node")
    if not node:
        raise WorkbenchError("Node.js is required for workbench export-shot.")
    capture_script = repo_root / "scripts" / "workbench_chrome_capture.mjs"
    if not capture_script.exists():
        raise WorkbenchError(f"Workbench Chrome capture helper is missing: {capture_script}")
    frames_dir.mkdir(parents=True, exist_ok=True)
    timeout_ms = max(
        30_000,
        int((max(export_request.duration_seconds, 1.0) * 12_000) + 30_000),
    )
    command = [
        node,
        str(capture_script),
        "--url",
        session_url,
        "--output-dir",
        str(frames_dir),
        "--frames",
        str(export_request.frames),
        "--width",
        str(export_request.width),
        "--height",
        str(export_request.height),
        "--timeout-ms",
        str(timeout_ms),
        "--headless",
    ]
    if export_request.alpha:
        command.append("--alpha")
    run_checked_command(command)


def copy_export_reference_frames(frames_dir: Path, export_request: ExportRequest) -> None:
    poster_frame_path = frames_dir / f"frame_{export_request.frames // 2:05d}.png"
    still_frame_path = frames_dir / f"frame_{export_request.frames - 1:05d}.png"
    if not poster_frame_path.exists():
        raise WorkbenchError(f"Poster frame is missing: {poster_frame_path}")
    if not still_frame_path.exists():
        raise WorkbenchError(f"Still frame is missing: {still_frame_path}")
    shutil.copy2(poster_frame_path, export_request.poster_path)
    shutil.copy2(still_frame_path, export_request.still_path)


def sync_export_project_contract(export_project: dict[str, Any], export_request: ExportRequest) -> None:
    contract = export_project.setdefault("motion_contract", {})
    contract["width"] = export_request.width
    contract["height"] = export_request.height
    contract["frames"] = export_request.frames
    contract["fps"] = export_request.fps
    contract["min_duration_seconds"] = export_request.min_duration_seconds

    scene = export_project.setdefault("scene", {})
    shot = scene.setdefault("shot", {})
    shot["frames"] = export_request.frames
    shot["fps"] = export_request.fps
    shot["duration_seconds"] = export_request.duration_seconds


def build_export_request(project: dict[str, Any], args: argparse.Namespace) -> ExportRequest:
    project_path = Path(args.project).expanduser().resolve()
    output_root = project_path.parent / "exports"
    snapshot_id = str(args.snapshot_id or project.get("active_snapshot_id") or "snapshot_initial").strip()
    shot = project["scene"].get("shot", {})
    contract = project.get("motion_contract", {})
    width = int(args.width or contract.get("width") or DEFAULT_WIDTH)
    height = int(args.height or contract.get("height") or DEFAULT_HEIGHT)
    requested_frames = int(args.frames or contract.get("frames") or shot.get("frames") or 33)
    fps = int(args.fps or contract.get("fps") or shot.get("fps") or DEFAULT_FPS)
    min_duration_seconds = float(args.min_duration_seconds if args.min_duration_seconds is not None else contract.get("min_duration_seconds", 0.0) or 0.0)
    duration_seconds = max(float(shot.get("duration_seconds", 0.0) or 0.0), min_duration_seconds, requested_frames / max(fps, 1), 1.0)
    rendered_frames = max(requested_frames, int(math.ceil(duration_seconds * fps)))
    timestamp = utc_now_iso().replace(":", "").replace("-", "")
    alpha = bool(getattr(args, "alpha", False))
    output_suffix = ".mov" if alpha else ".mp4"
    output_path = Path(args.output).expanduser().resolve() if args.output else (output_root / f"{timestamp}_{snapshot_id}{output_suffix}")
    if alpha and output_path.suffix.lower() != ".mov":
        raise WorkbenchError("Alpha workbench exports require a `.mov` output path.")
    if not alpha and output_path.suffix.lower() != ".mp4":
        raise WorkbenchError("Opaque workbench exports require a `.mp4` output path. The lossless master is written automatically as `*.master.mkv`.")
    master_output_path = None if alpha else output_path.with_suffix(".master.mkv")
    manifest_path = Path(args.manifest_output).expanduser().resolve() if args.manifest_output else Path(f"{output_path}.json")
    poster_path = Path(args.poster_output).expanduser().resolve() if args.poster_output else output_path.with_suffix(".poster.png")
    still_path = Path(args.still_output).expanduser().resolve() if args.still_output else output_path.with_suffix(".still.png")
    return ExportRequest(
        project_path=project_path,
        output_path=output_path,
        master_output_path=master_output_path,
        manifest_path=manifest_path,
        poster_path=poster_path,
        still_path=still_path,
        width=width,
        height=height,
        frames=rendered_frames,
        fps=fps,
        duration_seconds=round(duration_seconds, 3),
        snapshot_id=snapshot_id,
        min_duration_seconds=round(min_duration_seconds, 3),
        alpha=alpha,
    )


def _scene_for_snapshot(project: dict[str, Any], snapshot_id: str) -> dict[str, Any]:
    approval_status = str(project.get("approval", {}).get("status", "")).strip()
    if approval_status != APPROVAL_STATUS_APPROVED and snapshot_id in {"", "snapshot_initial"}:
        preset_family = project.get("scene", {}).get("preset_family", DEFAULT_PRESET_ID)
        return resolve_preset_scene(copy.deepcopy(project["scene"]), preset_family)
    selected_scene = copy.deepcopy(project["scene"])
    for snapshot in project.get("snapshots", []):
        if str(snapshot.get("id", "")).strip() == snapshot_id:
            selected_scene = copy.deepcopy(snapshot.get("scene", selected_scene))
            break
    selected_scene["volume_backend"] = str(project.get("scene", {}).get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL))
    preset_family = selected_scene.get("preset_family", project["scene"].get("preset_family", DEFAULT_PRESET_ID))
    return resolve_preset_scene(selected_scene, preset_family)


def export_project_shot(args: argparse.Namespace) -> dict[str, Any]:
    project_path = Path(args.project).expanduser().resolve()
    project = load_project(project_path)
    ensure_effect_ready(project)
    export_request = build_export_request(project, args)
    repo_root = repo_root_for_project(project)
    volume_backend = str(project.get("scene", {}).get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)).strip()
    source_image_path: Path | None = None
    if volume_backend != VOLUME_BACKEND_MODEL_SOURCE:
        source_image_path = Path(project["source_image"]["path"]).expanduser().resolve()
        if not source_image_path.exists():
            raise WorkbenchError(f"Source image is missing: {source_image_path}")

    export_project = copy.deepcopy(project)
    export_project["scene"] = _scene_for_snapshot(project, export_request.snapshot_id)
    export_project["active_snapshot_id"] = export_request.snapshot_id
    sync_export_project_contract(export_project, export_request)
    export_request.output_path.parent.mkdir(parents=True, exist_ok=True)
    if export_request.master_output_path is not None:
        export_request.master_output_path.parent.mkdir(parents=True, exist_ok=True)
    export_request.poster_path.parent.mkdir(parents=True, exist_ok=True)
    export_request.still_path.parent.mkdir(parents=True, exist_ok=True)
    export_request.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="particle-workbench-frames-") as temp_dir:
        frames_dir = Path(temp_dir)
        with serve_export_session(project_path, export_project) as session_url:
            export_frames_with_webgl(repo_root, session_url, frames_dir, export_request)
        copy_export_reference_frames(frames_dir, export_request)
        if export_request.master_output_path is not None:
            encode_frames_to_lossless_master_video(frames_dir, export_request.fps, export_request.master_output_path)
        encode_frames_to_video(frames_dir, export_request.fps, export_request.output_path, alpha=export_request.alpha)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "invocation": "workbench export-shot",
        "project_path": str(project_path),
        "manifest_path": str(export_request.manifest_path),
        "project_id": str(project.get("project_id", "")),
        "episode_id": str(project.get("episode_id", "")),
        "motion_item_id": str(project.get("motion_item_id", "")),
        "snapshot_id": export_request.snapshot_id,
        "source_id": str(project["active_source_id"]),
        "output_path": str(export_request.output_path),
        "master_output_path": str(export_request.master_output_path) if export_request.master_output_path is not None else "",
        "master_codec": "ffv1" if export_request.master_output_path is not None else "",
        "master_container": "mkv" if export_request.master_output_path is not None else "",
        "master_lossless": export_request.master_output_path is not None,
        "poster_path": str(export_request.poster_path),
        "still_path": str(export_request.still_path),
        "width": export_request.width,
        "height": export_request.height,
        "fps": export_request.fps,
        "alpha": export_request.alpha,
        "rendered_frames": export_request.frames,
        "duration_seconds": export_request.duration_seconds,
        "min_duration_seconds": export_request.min_duration_seconds,
        "seed": int(export_project["scene"]["seed"]),
        "effect_model": str(export_project["scene"].get("effect_model", DEFAULT_EFFECT_MODEL)),
        "volume_backend": str(export_project["scene"].get("volume_backend", VOLUME_BACKEND_ACQUIRED_SHELL)),
        "preset_family": str(export_project["scene"]["preset_family"]),
        "behavior": str(export_project.get("motion_contract", {}).get("behavior", "")),
        "pipeline": str(export_project.get("motion_contract", {}).get("pipeline", "particle_workbench")),
        "generated_at": utc_now_iso(),
        "approval": copy.deepcopy(export_project.get("approval", approval_defaults())),
    }
    if source_image_path is not None:
        manifest["source_image_path"] = str(source_image_path)
        manifest["source_image_sha256"] = export_project["source_image"]["sha256"]
        manifest["mask_source"] = str(export_project["mask"]["source"])
        manifest["mask_sha256"] = str(export_project["mask"]["mask_sha256"])
    if str(export_project["scene"].get("volume_backend", "")).strip() == VOLUME_BACKEND_MODEL_SOURCE:
        manifest["model_source"] = {
            "provider": str(export_project.get("model_source", {}).get("provider", "")),
            "remote_id": str(export_project.get("model_source", {}).get("remote_id", "")),
            "remote_url": str(export_project.get("model_source", {}).get("remote_url", "")),
            "license_class": str(export_project.get("model_source", {}).get("license_class", "")),
            "author_name": str(export_project.get("model_source", {}).get("author_name", "")),
            "author_url": str(export_project.get("model_source", {}).get("author_url", "")),
            "license_url": str(export_project.get("model_source", {}).get("license_url", "")),
            "attribution_text": str(export_project.get("model_source", {}).get("attribution_text", "")),
        }
    if (
        str(export_project["scene"].get("volume_backend", "")).strip() == VOLUME_BACKEND_ACQUIRED_SHELL
        and str(export_project.get("prior_assist", {}).get("status", "")).strip() == PRIOR_ASSIST_STATUS_ACTIVE
    ):
        manifest["prior_assist"] = copy.deepcopy(export_project.get("prior_assist", {}))
    write_json(export_request.manifest_path, manifest)
    return manifest


def _preview_size(project: dict[str, Any]) -> tuple[int, int]:
    contract = project.get("motion_contract", {})
    width = int(contract.get("width", DEFAULT_WIDTH))
    height = int(contract.get("height", DEFAULT_HEIGHT))
    scale = min(1.0, 960.0 / max(width, height))
    return max(1, int(round(width * scale))), max(1, int(round(height * scale)))


def render_preview_png(project_path: Path, project: dict[str, Any], progress: float) -> bytes:
    ensure_effect_ready(project)
    width, height = _preview_size(project)
    frames = max(int(project["motion_contract"].get("frames", project["scene"]["shot"].get("frames", 33))), 1)
    frame_index = int(round(clamp(progress, 0.0, 1.0) * max(frames - 1, 0)))
    particles = generate_active_particle_specs(project_path, project)
    frame = render_frame(
        project=project,
        source_image=Image.new("RGBA", (4, 4), (0, 0, 0, 0)),
        mask_image=Image.new("L", (4, 4), 255),
        particles=particles,
        width=width,
        height=height,
        frame_index=frame_index,
        total_frames=frames,
    )
    buffer = io.BytesIO()
    frame.save(buffer, format="PNG")
    return buffer.getvalue()


def burn_project_video(project_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    project = load_project(project_path)
    approval = project.get("approval", {})
    if str(approval.get("status", "")).strip() != APPROVAL_STATUS_APPROVED:
        raise WorkbenchError("Approve the particle effect before burning a video.")
    snapshot_id = str(approval.get("snapshot_id", "")).strip() or str(project.get("active_snapshot_id", "")).strip()
    args = argparse.Namespace(
        project=str(project_path),
        output=payload.get("output"),
        manifest_output=payload.get("manifest_output"),
        poster_output=payload.get("poster_output"),
        still_output=payload.get("still_output"),
        snapshot_id=snapshot_id,
        width=payload.get("width"),
        height=payload.get("height"),
        frames=payload.get("frames"),
        fps=payload.get("fps"),
        min_duration_seconds=payload.get("min_duration_seconds"),
    )
    manifest = export_project_shot(args)
    project = load_project(project_path)
    project["approval"]["output_path"] = str(manifest.get("output_path", ""))
    project["approval"]["master_output_path"] = str(manifest.get("master_output_path", ""))
    project["approval"]["master_codec"] = str(manifest.get("master_codec", ""))
    project["approval"]["master_container"] = str(manifest.get("master_container", ""))
    project["approval"]["master_lossless"] = bool(manifest.get("master_lossless", False))
    project["approval"]["manifest_path"] = str(manifest.get("manifest_path", ""))
    project["approval"]["poster_path"] = str(manifest.get("poster_path", ""))
    project["approval"]["still_path"] = str(manifest.get("still_path", ""))
    persist_project(project_path, project)
    return manifest


def _read_request_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    payload = handler.rfile.read(length)
    if not payload:
        return {}
    return json.loads(payload.decode("utf-8"))


def _send_json(handler: BaseHTTPRequestHandler, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
    encoded = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(encoded)


def _send_bytes(handler: BaseHTTPRequestHandler, payload: bytes, *, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(payload)


def _send_redirect(handler: BaseHTTPRequestHandler, location: str, *, status: HTTPStatus = HTTPStatus.FOUND) -> None:
    handler.send_response(status)
    handler.send_header("Location", location)
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()


def static_asset_bytes(repo_root: Path, relative_path: str) -> tuple[bytes, str]:
    asset_path = (project_static_root(repo_root) / relative_path).resolve()
    static_root = project_static_root(repo_root).resolve()
    try:
        asset_path.relative_to(static_root)
    except ValueError as exc:
        raise WorkbenchError(f"Invalid static asset path: {relative_path}") from exc
    if not asset_path.exists():
        raise WorkbenchError(f"Static asset is missing: {asset_path}")
    content_type = mimetypes.guess_type(str(asset_path))[0] or "application/octet-stream"
    return asset_path.read_bytes(), content_type


def project_file_bytes(project_path: Path, relative_path: str) -> tuple[bytes, str]:
    if not relative_path:
        raise WorkbenchError("Project file path is missing.")
    root = project_path.parent.resolve()
    asset_path = (root / relative_path).resolve()
    try:
        asset_path.relative_to(root)
    except ValueError as exc:
        raise WorkbenchError(f"Invalid project file path: {relative_path}") from exc
    if not asset_path.exists():
        raise WorkbenchError(f"Project file is missing: {asset_path}")
    content_type = mimetypes.guess_type(str(asset_path))[0] or "application/octet-stream"
    return asset_path.read_bytes(), content_type


def create_request_handler(
    project_path: Path,
    *,
    project_override: dict[str, Any] | None = None,
    readonly: bool = False,
) -> type[BaseHTTPRequestHandler]:
    def request_project() -> dict[str, Any]:
        if project_override is not None:
            return copy.deepcopy(project_override)
        return load_project(project_path)

    class WorkbenchHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            route = parsed.path
            query = parse_qs(parsed.query)
            try:
                project = request_project()
                repo_root = repo_root_for_project(project)
                if route == "/":
                    body, content_type = static_asset_bytes(repo_root, "index.html")
                    _send_bytes(self, body, content_type=content_type)
                    return
                if route.startswith("/assets/"):
                    body, content_type = static_asset_bytes(repo_root, route.removeprefix("/assets/"))
                    _send_bytes(self, body, content_type=content_type)
                    return
                if route.startswith("/vendor/"):
                    body, content_type = static_asset_bytes(repo_root, f"vendor/{route.removeprefix('/vendor/')}")
                    _send_bytes(self, body, content_type=content_type)
                    return
                if route == "/api/model-source/sketchfab/auth/status":
                    _send_json(self, sketchfab_auth_status())
                    return
                if route == "/api/model-source/sketchfab/auth/start":
                    body = _sketchfab_token_mode_page(
                        "Sketchfab OAuth is no longer used here. Close this window and paste your personal token into Particle Workbench."
                    )
                    _send_bytes(self, body.encode("utf-8"), content_type="text/html; charset=utf-8")
                    return
                if route == "/api/model-source/sketchfab/callback":
                    del query
                    body = _sketchfab_token_mode_page(
                        "Sketchfab now uses local token mode. Return to Particle Workbench and paste your personal token there."
                    )
                    _send_bytes(self, body.encode("utf-8"), content_type="text/html; charset=utf-8")
                    return
                if route == "/api/project":
                    _send_json(self, project)
                    return
                if route == "/project-file":
                    relative_path = str((query.get("path") or [""])[0]).strip()
                    body, content_type = project_file_bytes(project_path, relative_path)
                    _send_bytes(self, body, content_type=content_type)
                    return
                if route == "/api/effect-scene":
                    _send_json(self, build_effect_scene_payload(project_path, project))
                    return
                if route == "/source-image":
                    source_id = str((query.get("source_id") or [project["active_source_id"]])[0])
                    candidate = find_source_candidate(project, source_id)
                    source_path = Path(candidate["path"]).expanduser().resolve()
                    if not source_path.exists():
                        self.send_error(HTTPStatus.NOT_FOUND, "Source image missing.")
                        return
                    data = source_path.read_bytes()
                    content_type = mimetypes.guess_type(str(source_path))[0] or "application/octet-stream"
                    _send_bytes(self, data, content_type=content_type)
                    return
                if route in {"/mask/proposal.png", "/mask/approved.png"}:
                    source_id = str((query.get("source_id") or [project["active_source_id"]])[0])
                    mask_paths = project_mask_paths(project_path, source_id)
                    mask_path = mask_paths.proposal if route.endswith("proposal.png") else mask_paths.approved
                    if not mask_path.exists():
                        self.send_error(HTTPStatus.NOT_FOUND, "Mask missing.")
                        return
                    _send_bytes(self, mask_path.read_bytes(), content_type="image/png")
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown route.")
            except WorkbenchError as exc:
                _send_json(self, {"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        def do_POST(self) -> None:  # noqa: N802
            try:
                route = urlparse(self.path).path
                payload = _read_request_json(self)
                if route == "/api/model-source/sketchfab/token/connect":
                    token = str(payload.get("token", "")).strip()
                    _send_json(self, connect_sketchfab_token(token))
                    return
                if route == "/api/model-source/sketchfab/auth/disconnect":
                    _send_json(self, disconnect_sketchfab_auth())
                    return
                if readonly:
                    _send_json(self, {"error": "This workbench session is read-only."}, status=HTTPStatus.METHOD_NOT_ALLOWED)
                    return
                if route == "/api/project":
                    _send_json(self, apply_project_patch(project_path, payload))
                    return
                if route == "/api/approve":
                    _send_json(self, approve_project_look(project_path))
                    return
                if route == "/api/export-shot":
                    _send_json(self, burn_project_video(project_path, payload))
                    return
                if route == "/api/source/upload":
                    _send_json(self, add_source_candidate(project_path, payload))
                    return
                if route == "/api/source/select":
                    _send_json(self, select_source_candidate(project_path, str(payload.get("source_id", "")).strip()))
                    return
                if route == "/api/source/remove":
                    _send_json(self, remove_source_candidate(project_path, str(payload.get("source_id", "")).strip()))
                    return
                if route == "/api/model-source/search":
                    _send_json(self, search_project_model_sources(project_path, payload))
                    return
                if route == "/api/model-source/fetch":
                    _send_json(self, fetch_project_model_source(project_path, payload))
                    return
                if route == "/api/model-source/upload":
                    _send_json(self, upload_project_model_source(project_path, payload))
                    return
                if route == "/api/model-source/select":
                    _send_json(self, select_project_model_source(project_path, payload))
                    return
                if route == "/api/model-source/clear":
                    _send_json(self, clear_project_model_source(project_path))
                    return
                if route == "/api/snapshot":
                    _send_json(self, append_snapshot(project_path, str(payload.get("label", "")).strip()))
                    return
                if route == "/api/snapshot/select":
                    _send_json(self, select_project_snapshot(project_path, str(payload.get("snapshot_id", "")).strip()))
                    return
                if route == "/api/preset/save":
                    _send_json(self, save_project_preset(project_path, str(payload.get("label", "")).strip()))
                    return
                if route == "/api/preset/apply":
                    _send_json(self, apply_project_preset(project_path, str(payload.get("preset_id", "")).strip()))
                    return
                if route == "/api/mask/propose":
                    _send_json(self, repropose_mask(project_path))
                    return
                if route == "/api/mask/reset":
                    _send_json(self, reset_mask_to_proposal(project_path))
                    return
                if route == "/api/mask/brush":
                    _send_json(self, apply_mask_brush(project_path, payload))
                    return
                if route == "/api/mask/approve":
                    _send_json(self, approve_mask(project_path))
                    return
                if route == "/api/preview":
                    project = load_project(project_path)
                    scene_patch = payload.get("scene", {})
                    if isinstance(scene_patch, dict):
                        merged_scene = deep_merge(project.get("scene", {}), scene_patch)
                        preset_family = str(merged_scene.get("preset_family", project["scene"].get("preset_family", DEFAULT_PRESET_ID))).strip().lower()
                        project["scene"] = resolve_preset_scene(merged_scene, preset_family)
                    progress = float(payload.get("progress", 0.65))
                    _send_bytes(self, render_preview_png(project_path, project, progress), content_type="image/png")
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown route.")
            except WorkbenchError as exc:
                _send_json(self, {"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError as exc:
                _send_json(self, {"error": f"Invalid JSON payload: {exc}"}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return WorkbenchHandler


def serve_project(args: argparse.Namespace) -> int:
    project_path = Path(args.project).expanduser().resolve()
    load_project(project_path)
    server = ThreadingHTTPServer((args.host, args.port), create_request_handler(project_path))
    url = f"http://{args.host}:{args.port}"
    print(url)
    if args.open_browser:
        webbrowser.open(url, new=1, autoraise=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def command_init(args: argparse.Namespace) -> int:
    project = init_project_bundle(args)
    print(json.dumps({"project_path": str(Path(args.project).expanduser().resolve()), "project_id": project["project_id"]}, indent=2))
    return 0


def command_export(args: argparse.Namespace) -> int:
    manifest = export_project_shot(args)
    print(json.dumps(manifest, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            return command_init(args)
        if args.command == "serve":
            return serve_project(args)
        if args.command == "export-shot":
            return command_export(args)
        raise WorkbenchError(f"Unknown command: {args.command}")
    except WorkbenchError as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
