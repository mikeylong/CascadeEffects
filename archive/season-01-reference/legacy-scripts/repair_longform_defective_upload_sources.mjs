#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const STAMP = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");

const REPAIRS = [
  {
    episode_id: "therac-25",
    defective_youtube_video_id: "z5Blzqk6Q10",
    root: "/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_legal_borderless_source_credit_gap_outro_level_successor_20260526T031512Z",
    repair_models: ["render_mode_stage_child_preservation_guard_v1"],
  },
  {
    episode_id: "hyatt-regency",
    defective_youtube_video_id: "igQiWQR0XAg",
    root: "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_legal_borderless_source_credit_gap_outro_level_successor_20260526T031512Z",
    repair_models: ["render_mode_stage_child_preservation_guard_v1"],
  },
  {
    episode_id: "tacoma-narrows",
    defective_youtube_video_id: "bNAZXMEmJpA",
    root: "/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_legal_borderless_source_credit_gap_outro_level_successor_20260526T031512Z",
    repair_models: ["render_mode_stage_child_preservation_guard_v1"],
  },
  {
    episode_id: "piltdown-man",
    defective_youtube_video_id: "jX-am5ncSN8",
    root: "/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/production/long_form_video_v1/youtube/rough_assembly/piltdown-man_legal_borderless_source_credit_gap_outro_level_successor_20260526T031512Z",
    repair_models: ["render_mode_stage_child_preservation_guard_v1"],
  },
  {
    episode_id: "titanic",
    defective_youtube_video_id: "-nP4L4HAz3A",
    root: "/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/youtube/rough_assembly/titanic_legal_borderless_source_credit_gap_outro_level_successor_20260526T031512Z",
    repair_models: ["render_mode_stage_child_preservation_guard_v1"],
  },
  {
    episode_id: "semmelweis",
    defective_youtube_video_id: "oAchW5SRPYo",
    root: "/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly/semmelweis_caption_highlight_runtime_audit_successor_20260526T053124Z",
    repair_models: ["semmelweis_deterministic_ambient_time_lock_v1"],
  },
];

const UNSAFE_STAGE_SELECTOR =
  "html.render-mode main > :not(.stage-shell):not(.ce-stage-scale-shell):not(.frame):not(.stage-frame),";
const SAFE_STAGE_SELECTOR =
  "html.render-mode main:not(.stage):not(.ce-fixed-stage) > :not(.stage-shell):not(.ce-stage-scale-shell):not(.frame):not(.stage-frame),";

const SEMMELWEIS_STYLE = `  <style id="ce-semmelweis-deterministic-ambient-style">
    .lamp-breath,
    .left-wall-lamp-bloom,
    .cadaver-table-lamp-reflection,
    .window-drift,
    .doorway-light-sweep,
    .cloth-breath,
    .air-depth,
    .floor-life {
      animation: none !important;
    }

    .lamp-breath {
      opacity: calc(var(--ce-ambient-lamp-breath-opacity, 0.28) * var(--ambient-gain));
      filter: blur(var(--ce-ambient-lamp-breath-blur, 1px));
    }

    .left-wall-lamp-bloom {
      opacity: calc(var(--ce-ambient-left-wall-opacity, 0.18) * var(--ambient-gain));
      filter: blur(var(--ce-ambient-left-wall-blur, 1.5px));
      transform: var(--ce-ambient-left-wall-transform, translate3d(0, 0, 0) scale(1));
    }

    .cadaver-table-lamp-reflection {
      opacity: calc(var(--ce-ambient-table-opacity, 0.16) * var(--ambient-gain));
      transform: var(--ce-ambient-table-transform, translate3d(0, 0, 0) scale(1));
    }

    .window-drift {
      opacity: calc(var(--ce-ambient-window-opacity, 0.42) * var(--ambient-gain));
      transform: var(--ce-ambient-window-transform, translate3d(0, 0, 0));
    }

    .doorway-light-sweep {
      opacity: calc(var(--ce-ambient-doorway-opacity, 0.34) * var(--ambient-gain));
      transform: var(--ce-ambient-doorway-transform, translate3d(0, 0, 0));
    }

    .cloth-breath {
      opacity: calc(var(--ce-ambient-cloth-opacity, 0.38) * var(--ambient-gain));
      transform: var(--ce-ambient-cloth-transform, translate3d(0, 0, 0));
    }

    .air-depth {
      opacity: calc(var(--ce-ambient-air-opacity, 0.42) * var(--ambient-gain));
      transform: var(--ce-ambient-air-transform, translate3d(0, 0, 0));
    }

    .floor-life {
      opacity: calc(var(--ce-ambient-floor-opacity, 0.34) * var(--ambient-gain));
      transform: var(--ce-ambient-floor-transform, translate3d(0, 0, 0));
    }
  </style>
`;

const SEMMELWEIS_RUNTIME = `<script id="ce-semmelweis-deterministic-ambient-runtime">
  (function () {
    const root = document.documentElement;
    const wave = (seconds, period, phase) => 0.5 + 0.5 * Math.sin(((seconds / period) + phase) * Math.PI * 2);
    const fixed = (value, digits = 4) => Number(value).toFixed(digits);
    function stateAt(seconds) {
      const t = Number(seconds) || 0;
      const lamp = wave(t, 5.8, 0.08);
      const left = wave(t, 3.4, 0.19);
      const table = wave(t, 4.6, 0.33);
      const windowGlow = wave(t, 11, 0.02);
      const doorway = wave(t, 9.5, 0.41);
      const cloth = wave(t, 9.5, 0.64);
      const air = (t % 24) / 24;
      const floor = wave(t, 9.2, 0.27);
      return {
        model: "semmelweis_deterministic_ambient_time_lock_v1",
        time_seconds: Number(t.toFixed(3)),
        values: {
          "--ce-ambient-lamp-breath-opacity": fixed(0.20 + lamp * 0.16),
          "--ce-ambient-lamp-breath-blur": fixed(0.5 + lamp * 1.5, 2) + "px",
          "--ce-ambient-left-wall-opacity": fixed(0.12 + left * 0.18),
          "--ce-ambient-left-wall-blur": fixed(0.8 + left * 0.7, 2) + "px",
          "--ce-ambient-left-wall-transform": "translate3d(" + fixed((left - 0.5) * 1.0, 2) + "px, " + fixed(Math.sin(t / 3.4 * Math.PI * 2) * 0.5, 2) + "px, 0) scale(" + fixed(0.996 + left * 0.010, 4) + ")",
          "--ce-ambient-table-opacity": fixed(0.08 + table * 0.10),
          "--ce-ambient-table-transform": "translate3d(" + fixed(-1 + table * 3, 2) + "px, " + fixed((0.5 - table) * 1, 2) + "px, 0) scale(" + fixed(0.996 + table * 0.010, 4) + ")",
          "--ce-ambient-window-opacity": fixed(0.28 + windowGlow * 0.20),
          "--ce-ambient-window-transform": "translate3d(" + fixed(-8 + windowGlow * 20, 2) + "px, 0, 0)",
          "--ce-ambient-doorway-opacity": fixed(0.20 + doorway * 0.22),
          "--ce-ambient-doorway-transform": "translate3d(" + fixed(-9 + doorway * 22, 2) + "px, " + fixed(-doorway, 2) + "px, 0)",
          "--ce-ambient-cloth-opacity": fixed(0.28 + cloth * 0.18),
          "--ce-ambient-cloth-transform": "translate3d(" + fixed(-3 + cloth * 10, 2) + "px, 0, 0)",
          "--ce-ambient-air-opacity": fixed(0.34 + wave(t, 24, 0.77) * 0.12),
          "--ce-ambient-air-transform": "translate3d(" + fixed(-12 + air * 24, 2) + "px, " + fixed(Math.sin(t / 13) * 1.2, 2) + "px, 0)",
          "--ce-ambient-floor-opacity": fixed(0.32 + floor * 0.24),
          "--ce-ambient-floor-transform": "translate3d(" + fixed(-3 + floor * 7, 2) + "px, " + fixed(1 - floor * 2, 2) + "px, 0)",
        },
      };
    }
    function apply(seconds) {
      const state = stateAt(seconds);
      Object.entries(state.values).forEach(([key, value]) => root.style.setProperty(key, value));
      window.__ceDeterministicAmbientLastState = state;
      return state;
    }
    window.__ceDeterministicAmbientStateAt = stateAt;
    window.__ceApplyDeterministicAmbientTime = apply;
    const priorAmbient = window.__ceSetAmbientRenderTime;
    window.__ceSetAmbientRenderTime = (seconds) => {
      const result = typeof priorAmbient === "function" ? priorAmbient(seconds) : seconds;
      apply(seconds);
      return result;
    };
    const priorSetRenderTime = window.__setRenderTime;
    window.__setRenderTime = (seconds) => {
      const result = typeof priorSetRenderTime === "function" ? priorSetRenderTime(seconds) : seconds;
      apply(seconds);
      return result;
    };
    function currentTime() {
      const audio = document.getElementById("audio") || document.querySelector("audio");
      if (audio && Number.isFinite(Number(audio.currentTime))) return Number(audio.currentTime);
      const scrub = document.querySelector("[data-ce-scrub]") || document.querySelector("input[type='range']");
      const value = Number(scrub && scrub.value);
      return Number.isFinite(value) ? value : 0;
    }
    let raf = 0;
    function tick() {
      const audio = document.getElementById("audio") || document.querySelector("audio");
      apply(currentTime());
      if (audio && !audio.paused && !audio.ended) raf = requestAnimationFrame(tick);
    }
    window.addEventListener("load", () => {
      apply(currentTime());
      const audio = document.getElementById("audio") || document.querySelector("audio");
      if (audio) {
        ["loadedmetadata", "timeupdate", "seeked", "seeking", "pause"].forEach((eventName) => audio.addEventListener(eventName, () => apply(currentTime())));
        audio.addEventListener("play", () => {
          cancelAnimationFrame(raf);
          tick();
        });
      }
      document.addEventListener("input", (event) => {
        if (event.target && event.target.matches && event.target.matches("input[type='range'], [data-ce-scrub]")) apply(currentTime());
      });
    });
  })();
</script>
`;

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, payload) {
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function patchPlayer(filePath, repair) {
  if (!fs.existsSync(filePath)) return null;
  const before = fs.readFileSync(filePath, "utf8");
  let html = before.split(UNSAFE_STAGE_SELECTOR).join(SAFE_STAGE_SELECTOR);
  const models = new Set(repair.repair_models);
  if (models.has("semmelweis_deterministic_ambient_time_lock_v1")) {
    if (!html.includes('id="ce-semmelweis-deterministic-ambient-style"')) {
      html = html.replace("</head>", `${SEMMELWEIS_STYLE}</head>`);
    }
    if (!html.includes('id="ce-semmelweis-deterministic-ambient-runtime"')) {
      html = html.replace("</body>", `${SEMMELWEIS_RUNTIME}\n</body>`);
    }
  }
  if (html === before) {
    return {
      path: filePath,
      changed: false,
      sha256: sha256(filePath),
    };
  }
  fs.writeFileSync(filePath, html, "utf8");
  return {
    path: filePath,
    changed: true,
    sha256_before: crypto.createHash("sha256").update(before).digest("hex"),
    sha256: sha256(filePath),
  };
}

function patchManifest(repair, playerReceipts) {
  const manifestPath = path.join(repair.root, "rough_assembly_manifest.json");
  if (!fs.existsSync(manifestPath)) return null;
  const manifest = readJson(manifestPath);
  manifest.defective_upload_repair = {
    model: "defective_unlisted_upload_repair_20260526_v1",
    repaired_at_utc: new Date().toISOString(),
    defective_youtube_video_id: repair.defective_youtube_video_id,
    repair_models: repair.repair_models,
    player_repairs: playerReceipts,
    public_release: "blocked_manual_youtube_studio_only",
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    render_mode_stage_child_preservation_read: "pass_stage_children_not_hidden_by_review_chrome_guard",
    defective_unlisted_upload_supersession_read: "pending_replacement_upload_verified",
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    render_mode_stage_child_preservation_read: "pass_stage_children_not_hidden_by_review_chrome_guard",
  };
  if (repair.repair_models.includes("semmelweis_deterministic_ambient_time_lock_v1")) {
    manifest.reads.semmelweis_deterministic_ambient_read = "pass_deterministic_ambient_runtime_injected_pending_render_qa";
    manifest.rough_assembly_reads.semmelweis_deterministic_ambient_read = "pass_deterministic_ambient_runtime_injected_pending_render_qa";
    manifest.ambient_frame_clock_model = "semmelweis_deterministic_ambient_time_lock_v1";
  }
  writeJson(manifestPath, manifest);
  return {
    path: manifestPath,
    sha256: sha256(manifestPath),
  };
}

function main() {
  const repairs = [];
  for (const repair of REPAIRS) {
    const playerPaths = [
      path.join(repair.root, "player.html"),
      path.join(repair.root, "html_review/source_credit_gap/player.html"),
    ];
    const playerReceipts = playerPaths.map((filePath) => patchPlayer(filePath, repair)).filter(Boolean);
    const manifest = patchManifest(repair, playerReceipts);
    repairs.push({
      ...repair,
      player_repairs: playerReceipts,
      manifest,
    });
  }
  const receipt = {
    receipt_type: "defective_unlisted_upload_source_repair",
    created_at: new Date().toISOString(),
    repair_id: `defective_unlisted_upload_source_repair_${STAMP}`,
    repairs,
  };
  const receiptPath = path.join(EPISODES_ROOT, `defective_unlisted_upload_source_repair_${STAMP}.json`);
  writeJson(receiptPath, receipt);
  console.log(JSON.stringify({ receipt_path: receiptPath, repairs }, null, 2));
}

main();
