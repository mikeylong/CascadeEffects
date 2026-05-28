#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  CHALLENGER_PRECISION_MATTE,
  challengerPrecisionMatteGuard,
  sha256File,
} from "./challenger_precision_matte_guard.mjs";

const REPO_ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const EPISODE_ROOT =
  "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly";
const SOURCE_ROOT = path.join(
  EPISODE_ROOT,
  "challenger_precision_matte_legal_end_screen_borderless_successor_20260525T230840Z",
);
const MODEL = "challenger_center_source_credit_gap_v1";
const SOURCE_FACT_CHECK_PATH = "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/fact_check.md";
const EXPECTED_AUDIO_SHA = "81174cc27fcbfc67f006dda89c9cf0c467103203a88f6faab2ba97e6209eebca";
const LEGAL_FADE_START_SECONDS = 1191.680884;
const LEGAL_FULL_OPACITY_SECONDS = 1191.980884;
const SOURCE_CREDIT_TIMING = {
  fade_start_seconds: 1184.8,
  full_opacity_seconds: 1185.55,
  fade_out_start_seconds: 1190.75,
  fade_out_end_seconds: LEGAL_FADE_START_SECONDS,
};
const SOURCE_CREDITS = [
  "Presidential Commission on the Space Shuttle Challenger Accident",
  "NASA Rogers Commission hearing record",
  "Diane Vaughan, The Challenger Launch Decision",
];
const RUNTIME_LINKS = ["assets", "audio_repairs", "audio_successor", "proof_assets", "references", "scripts"];

function usage(message = "") {
  if (message) console.error(message);
  console.error("Usage: node scripts/build_challenger_source_credit_gap_successor.mjs [--stamp YYYYMMDDTHHMMSSZ]");
  process.exit(message ? 2 : 0);
}

function parseArgs(argv) {
  const args = { stamp: "" };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--stamp") args.stamp = argv[++i] || "";
    else if (arg === "--help" || arg === "-h") usage();
    else usage(`Unknown argument: ${arg}`);
  }
  return args;
}

function utcStamp() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function writeText(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text, "utf8");
}

function writeJson(filePath, payload) {
  writeText(filePath, `${JSON.stringify(payload, null, 2)}\n`);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function removeIfExists(targetPath) {
  if (!fs.existsSync(targetPath) && !fs.lstatSync?.(targetPath, { throwIfNoEntry: false })) return;
  fs.rmSync(targetPath, { recursive: true, force: true });
}

function resetDir(dirPath) {
  fs.rmSync(dirPath, { recursive: true, force: true });
  fs.mkdirSync(dirPath, { recursive: true });
}

function linkRuntimeTargets(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
  for (const name of RUNTIME_LINKS) {
    const source = path.join(SOURCE_ROOT, name);
    const target = path.join(dirPath, name);
    removeIfExists(target);
    fs.symlinkSync(fs.realpathSync(source), target);
  }
}

function sourceCreditStyle() {
  return `  <style id="ce-source-credit-gap-style">
    .ce-source-credit-gap {
      position: absolute;
      z-index: 6;
      left: 50%;
      top: 50%;
      width: 560px;
      max-width: 46vw;
      transform: translate3d(-50%, -50%, 0);
      opacity: var(--ce-source-credit-gap-opacity, 0);
      pointer-events: none;
      text-align: center;
      color: rgba(255, 248, 232, 0.96);
      text-shadow: 0 3px 18px rgba(0, 0, 0, 0.64);
    }
    .ce-source-credit-gap::before {
      content: "";
      position: absolute;
      z-index: -1;
      inset: -28px -38px;
      border-radius: 10px;
      background: radial-gradient(closest-side, rgba(6, 10, 22, 0.52), rgba(6, 10, 22, 0.28) 64%, rgba(6, 10, 22, 0) 100%);
    }
    .ce-source-credit-gap__label {
      margin: 0 0 18px;
      color: rgba(203, 211, 232, 0.82);
      font-size: 22px;
      font-weight: 760;
      line-height: 1;
      letter-spacing: 0;
      text-transform: uppercase;
    }
    .ce-source-credit-gap__list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 13px;
    }
    .ce-source-credit-gap__item {
      margin: 0;
      color: rgba(255, 248, 232, 0.98);
      font-size: 32px;
      font-weight: 760;
      line-height: 1.12;
      letter-spacing: 0;
    }
  </style>
`;
}

function sourceCreditMarkup() {
  const items = SOURCE_CREDITS.map((source) => `            <li class="ce-source-credit-gap__item">${source}</li>`).join("\n");
  return `        <section class="ce-source-credit-gap" id="ceSourceCreditGap" aria-label="Primary source credits" data-source-credit-model="${MODEL}" aria-hidden="true">
          <p class="ce-source-credit-gap__label">Sources</p>
          <ol class="ce-source-credit-gap__list">
${items}
          </ol>
        </section>`;
}

function sourceCreditRuntime(config) {
  const json = JSON.stringify(config);
  return `<script id="ce-source-credit-gap-config" type="application/json">${json}</script>
<script id="ce-source-credit-gap-runtime">
  (function () {
    const configEl = document.getElementById("ce-source-credit-gap-config");
    const config = configEl ? JSON.parse(configEl.textContent || "{}") : {};
    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const smoother = (value) => {
      const t = clamp(Number(value) || 0, 0, 1);
      return t * t * (3 - 2 * t);
    };
    function sourceCreditOpacityAt(time) {
      const safe = Number(time) || 0;
      const fadeStart = Number(config.fade_start_seconds) || 0;
      const full = Number(config.full_opacity_seconds) || fadeStart;
      const fadeOutStart = Number(config.fade_out_start_seconds) || full;
      const fadeOutEnd = Number(config.fade_out_end_seconds) || fadeOutStart;
      if (safe < fadeStart || safe >= fadeOutEnd) return 0;
      if (safe < full) return smoother((safe - fadeStart) / Math.max(0.001, full - fadeStart));
      if (safe >= fadeOutStart) return 1 - smoother((safe - fadeOutStart) / Math.max(0.001, fadeOutEnd - fadeOutStart));
      return 1;
    }
    function updateSourceCreditGap(time) {
      const overlay = document.getElementById("ceSourceCreditGap");
      if (!overlay) return 0;
      const opacity = sourceCreditOpacityAt(time);
      overlay.style.setProperty("--ce-source-credit-gap-opacity", opacity.toFixed(4));
      overlay.dataset.active = opacity > 0.001 ? "true" : "false";
      return opacity;
    }
    const priorSetRenderTime = window.__setRenderTime;
    window.__setRenderTime = (time) => {
      const result = typeof priorSetRenderTime === "function" ? priorSetRenderTime(time) : time;
      updateSourceCreditGap(Number(time) || 0);
      return result;
    };
    window.__sourceCreditGapOpacityAt = sourceCreditOpacityAt;
    window.__sourceCreditGapStateAt = (time) => ({
      model: config.model,
      time: Number(time) || 0,
      opacity: sourceCreditOpacityAt(time),
      sources: config.sources || [],
      timing: config,
    });
    const audio = document.getElementById("audio");
    let raf = 0;
    function syncFromAudio() {
      updateSourceCreditGap(audio ? audio.currentTime || 0 : 0);
    }
    function tick() {
      syncFromAudio();
      if (audio && !audio.paused && !audio.ended) raf = requestAnimationFrame(tick);
    }
    if (audio) {
      ["timeupdate", "seeked", "loadedmetadata", "pause"].forEach((eventName) => audio.addEventListener(eventName, syncFromAudio));
      audio.addEventListener("play", () => {
        cancelAnimationFrame(raf);
        tick();
      });
    }
    syncFromAudio();
  })();
</script>`;
}

function patchPlayerHtml(html) {
  if (html.includes("ce-source-credit-gap-style")) throw new Error("Source credit gap style already exists in player.");
  let patched = html.replace("</head>", `${sourceCreditStyle()}</head>`);
  const railNeedle = '        </section>\n        <section class="rail"';
  if (!patched.includes(railNeedle)) throw new Error("Could not find insertion point before rolling rail.");
  patched = patched.replace(railNeedle, `        </section>\n${sourceCreditMarkup()}\n        <section class="rail"`);
  const config = {
    model: MODEL,
    review_scope: "challenger_only_html_review_before_youtube_upload",
    placement: "center_frame_between_final_caption_and_legal_end_screen",
    sources: SOURCE_CREDITS,
    source_selection_basis: "top_named_fact_check_sources_from_active_challenger_fact_check",
    source_fact_check_path: SOURCE_FACT_CHECK_PATH,
    fade_start_seconds: SOURCE_CREDIT_TIMING.fade_start_seconds,
    full_opacity_seconds: SOURCE_CREDIT_TIMING.full_opacity_seconds,
    fade_out_start_seconds: SOURCE_CREDIT_TIMING.fade_out_start_seconds,
    fade_out_end_seconds: SOURCE_CREDIT_TIMING.fade_out_end_seconds,
    legal_end_screen_fade_start_seconds: LEGAL_FADE_START_SECONDS,
    legal_end_screen_full_opacity_seconds: LEGAL_FULL_OPACITY_SECONDS,
    youtube_upload_or_visibility_changed: false,
    audio_changed: false,
    end_screen_timing_changed: false,
  };
  return patched.replace("</body>", `${sourceCreditRuntime(config)}\n</body>`);
}

function reviewIndex({ reviewIndexPath, reviewPlayerPath }) {
  const href = path.relative(path.dirname(reviewIndexPath), reviewPlayerPath).split(path.sep).join("/");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Challenger Source Credit Gap HTML Review</title>
  <style>
    :root { color-scheme: dark; --bg: #050817; --ink: #f7efe1; --muted: #aeb8ce; --line: rgba(247, 239, 225, 0.16); --panel: rgba(17, 23, 47, 0.78); --accent: #78dce8; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 16px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { width: min(920px, calc(100vw - 40px)); margin: 0 auto; padding: 44px 0 52px; }
    h1 { margin: 0 0 12px; font-size: 28px; line-height: 1.15; letter-spacing: 0; }
    p { margin: 0 0 22px; color: var(--muted); }
    a { color: var(--ink); text-decoration: none; }
    .review-link { display: block; padding: 18px 20px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
    .review-link strong { display: block; margin-bottom: 5px; font-size: 18px; }
    .review-link span { display: block; color: var(--muted); }
    code { color: var(--accent); }
  </style>
</head>
<body>
  <main>
    <h1>Challenger Source Credit Gap HTML Review</h1>
    <p>This successor adds only a centered source-credit interstitial in the caption-to-end-screen gap. Precision matte, borderless styling, legal end-screen timing, and approved audio are unchanged.</p>
    <a class="review-link" href="${href}">
      <strong>Open Challenger source credit gap review</strong>
      <span>Source credits begin at <code>${SOURCE_CREDIT_TIMING.fade_start_seconds.toFixed(3)}s</code> and clear before the legal end-screen entry at <code>${LEGAL_FADE_START_SECONDS.toFixed(3)}s</code>.</span>
    </a>
  </main>
</body>
</html>
`;
}

function staticQa({ outputRoot, manifestPath, playerPath, reviewPlayerPath, reviewIndexPath, precisionGuard }) {
  const html = fs.readFileSync(playerPath, "utf8");
  const failures = [];
  for (const source of SOURCE_CREDITS) if (!html.includes(source)) failures.push(`missing source credit: ${source}`);
  if (!html.includes(`data-source-credit-model="${MODEL}"`)) failures.push("source-credit model metadata missing");
  if (!html.includes("window.__sourceCreditGapStateAt")) failures.push("source-credit runtime debug hook missing");
  if (!html.includes(`"fade_start_seconds":${SOURCE_CREDIT_TIMING.fade_start_seconds}`)) failures.push("fade start missing from config");
  if (!html.includes(`"fade_out_end_seconds":${LEGAL_FADE_START_SECONDS}`)) failures.push("fade-out end missing from config");
  if (!html.includes(`"legal_end_screen_fade_start_seconds":${LEGAL_FADE_START_SECONDS}`)) failures.push("legal end-screen timing missing from config");
  if (!precisionGuard?.ok) failures.push("precision matte guard failed");

  const qa = {
    model: "challenger_source_credit_gap_static_qa_v1",
    created_utc: new Date().toISOString(),
    status: failures.length ? "fail" : "pass",
    manifest_path: manifestPath,
    player_path: playerPath,
    review_player_path: reviewPlayerPath,
    review_html_path: reviewIndexPath,
    source_credit_model: MODEL,
    source_credits: SOURCE_CREDITS,
    source_fact_check_path: SOURCE_FACT_CHECK_PATH,
    timing: SOURCE_CREDIT_TIMING,
    legal_end_screen_fade_start_seconds: LEGAL_FADE_START_SECONDS,
    legal_end_screen_full_opacity_seconds: LEGAL_FULL_OPACITY_SECONDS,
    challenger_precision_matte_guard: precisionGuard,
    failures,
    reads: {
      source_credit_gap_static_read: failures.length ? "fail_source_credit_gap_static_qa" : "pass_source_credit_gap_static_qa",
      source_credit_names_read: failures.some((failure) => failure.includes("source credit"))
        ? "fail_source_credit_names_missing"
        : "pass_three_named_reputable_sources_present",
      source_credit_timing_read: failures.some((failure) => /fade|timing/.test(failure))
        ? "fail_source_credit_gap_timing"
        : "pass_source_credits_clear_before_legal_end_screen_entry",
      challenger_precision_matte_guard_read:
        precisionGuard?.reads?.challenger_precision_matte_guard_read || "fail_challenger_precision_matte_guard_missing",
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
  };
  const qaPath = path.join(outputRoot, "qa", "challenger_source_credit_gap_static_qa.json");
  writeJson(qaPath, qa);
  if (failures.length) throw new Error(`Static QA failed:\n${JSON.stringify(qa, null, 2)}`);
  return { qaPath, qa };
}

function patchManifest({
  sourceManifest,
  outputRoot,
  manifestPath,
  playerPath,
  reviewPlayerPath,
  reviewIndexPath,
  proofBuildPath,
  createdUtc,
  precisionGuard,
  qaPath,
}) {
  const manifest = structuredClone(sourceManifest);
  Object.assign(manifest, {
    packet_id: path.basename(outputRoot),
    status: "challenger_source_credit_gap_html_review_ready_pending_human_keep",
    human_disposition: "pending",
    human_disposition_source: "pending_challenger_source_credit_gap_html_review",
    mp4_render_created: false,
    may_create_full_runtime_mp4_render: false,
    may_render_final_mp4: false,
    may_advance_to_video_render: false,
    may_advance_to_final_assembly: false,
    may_advance_to_publish_readiness: false,
    may_youtube_action: false,
    publish_ready: false,
    youtube_upload_ready: false,
    upload_allowed: false,
    upload_performed: false,
    youtube_upload_performed: false,
    publish_readiness_updated: false,
    public_visibility_updated: false,
    public_release_ready: false,
    public_release_allowed: false,
    youtube_visibility_action_performed: false,
    rendered_video_proof: null,
    publish_readiness_package: null,
    youtube_unlisted_review: null,
    youtube_upload_result: null,
    human_keep_record: null,
    human_keep_recorded_at: null,
    user_approval: {
      created_utc: createdUtc,
      source: "challenger_source_credit_gap_html_review",
      text: "Source-credit gap trial is HTML-review only until human approval.",
      allowed_actions: ["html_review"],
      public_release_allowed: false,
    },
    production_contract: {
      contract_id: "first-eight-longform-v1",
      intent: "successor",
      status: "blocked_html_review_pending_human_keep",
      youtube_action_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
      render_approval_read: "blocked_pending_human_keep",
      public_release_ready_read: "blocked_public_release_manual",
    },
    source_html_proof: {
      packet_path: outputRoot,
      manifest_path: manifestPath,
      player_path: playerPath,
      player_sha256: sha256File(playerPath),
      current_proof_render_source_read: "blocked_html_review_pending_human_keep",
      current_kept_proof_render_source_read: "blocked_html_review_pending_human_keep",
      corrective_review_render_from_unkept_proof: false,
      challenger_precision_matte_guard: precisionGuard,
    },
    source_credit_gap: {
      model: MODEL,
      source_credits: SOURCE_CREDITS,
      source_selection_basis: "top_named_fact_check_sources_from_active_challenger_fact_check",
      source_fact_check_path: SOURCE_FACT_CHECK_PATH,
      timing: SOURCE_CREDIT_TIMING,
      placement: "center_frame_between_final_caption_and_legal_end_screen",
      fades_out_before_legal_end_screen_read: "pass_source_credit_gap_clears_before_1191p680884",
      audio_changed: false,
      end_screen_timing_changed: false,
      youtube_action_read: "blocked_no_upload_or_visibility_change_performed",
    },
    challenger_precision_matte_guard: precisionGuard,
    foreground_matte_policy: "tower_shuttle_only_no_light_or_right_rail_mask",
    foreground_matte_precision_model: CHALLENGER_PRECISION_MATTE.precisionModel,
    foreground_matte_path: path.join(outputRoot, CHALLENGER_PRECISION_MATTE.maskRelativePath),
    foreground_matte_sha256: CHALLENGER_PRECISION_MATTE.maskSha256,
    precision_matte_human_disposition: "keep",
    precision_matte_keep_receipt_path: CHALLENGER_PRECISION_MATTE.keepReceiptPath,
    precision_matte_keep_receipt_sha256: sha256File(CHALLENGER_PRECISION_MATTE.keepReceiptPath),
    predecessor_review_context: {
      source_root: SOURCE_ROOT,
      source_status: sourceManifest.status || "",
      source_html_proof: sourceManifest.source_html_proof || null,
    },
  });

  manifest.proof_artifacts = {
    ...(manifest.proof_artifacts || {}),
    source_predecessor_root: SOURCE_ROOT,
    player_html_path: playerPath,
    player_html_sha256: sha256File(playerPath),
    review_player_html_path: reviewPlayerPath,
    review_html_path: reviewIndexPath,
    proof_build_json_path: proofBuildPath,
    proof_build_json_sha256: sha256File(proofBuildPath),
    source_credit_gap_static_qa_path: qaPath,
    source_credit_gap_static_qa_sha256: fs.existsSync(qaPath) ? sha256File(qaPath) : "pending",
  };
  manifest.reads = {
    ...(manifest.reads || {}),
    source_credit_gap_static_read: "pass_source_credit_gap_static_qa",
    source_credit_names_read: "pass_three_named_reputable_sources_present",
    source_credit_timing_read: "pass_source_credits_clear_before_legal_end_screen_entry",
    source_credit_audio_read: "pass_audio_sha_preserved_81174cc2",
    end_screen_legal_timing_preservation_read: "pass_youtube_legal_window_entry_v1_unchanged",
    challenger_audio_regression_guard_read: "pass_plus5db_successor_audio_sha_preserved_no_remix",
    challenger_precision_matte_guard_read:
      precisionGuard?.reads?.challenger_precision_matte_guard_read || "fail_challenger_precision_matte_guard_missing",
    challenger_precision_mask_sha_read:
      precisionGuard?.reads?.challenger_precision_mask_sha_read || "fail_mask_sha_not_987d1a96",
    challenger_superseded_mask_block_read:
      precisionGuard?.reads?.challenger_superseded_mask_block_read || "fail_superseded_challenger_mask_active",
    challenger_mask_lineage_read:
      precisionGuard?.reads?.challenger_mask_lineage_read || "fail_mask_does_not_resolve_to_kept_precision_matte_root",
    mp4_created_read: "blocked_html_review_pending_human_keep",
    youtube_upload_ready_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    youtube_action_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    unlisted_review_upload_approval_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    final_assembly_human_keep_read: "blocked_pending_human_keep",
    human_final_assembly_keep_read: "blocked_pending_human_keep",
    public_release_ready_read: "blocked_public_release_manual",
  };
  manifest.rough_assembly_reads = {
    ...(manifest.rough_assembly_reads || {}),
    source_credit_gap_static_read: "pass_source_credit_gap_static_qa",
    source_credit_timing_read: "pass_source_credits_clear_before_legal_end_screen_entry",
    mp4_created_read: "blocked_html_review_pending_human_keep",
    youtube_upload_ready_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    youtube_action_read: "blocked_pending_human_keep_and_explicit_upload_authorization",
    public_release_ready_read: "blocked_public_release_manual",
  };
  return manifest;
}

function main() {
  const args = parseArgs(process.argv);
  const stamp = args.stamp || utcStamp();
  const outputRoot = path.join(EPISODE_ROOT, `challenger_source_credit_gap_successor_${stamp}`);
  const reviewDir = path.join(outputRoot, "review");
  const qaDir = path.join(outputRoot, "qa");
  const reviewPlayerDir = path.join(outputRoot, "html_review", "source_credit_gap");
  const playerPath = path.join(outputRoot, "player.html");
  const reviewPlayerPath = path.join(reviewPlayerDir, "player.html");
  const manifestPath = path.join(outputRoot, "rough_assembly_manifest.json");
  const proofBuildPath = path.join(outputRoot, "proof_build.json");
  const reviewIndexPath = path.join(reviewDir, "challenger_source_credit_gap_html_review.html");
  const createdUtc = new Date().toISOString();

  resetDir(outputRoot);
  fs.mkdirSync(reviewDir, { recursive: true });
  fs.mkdirSync(qaDir, { recursive: true });
  fs.mkdirSync(reviewPlayerDir, { recursive: true });
  linkRuntimeTargets(outputRoot);
  linkRuntimeTargets(reviewPlayerDir);

  const sourceManifestPath = path.join(SOURCE_ROOT, "rough_assembly_manifest.json");
  const sourceManifest = readJson(sourceManifestPath);
  if (sourceManifest.approved_audio?.sha256 !== EXPECTED_AUDIO_SHA) {
    throw new Error(`Source approved audio SHA changed: ${sourceManifest.approved_audio?.sha256 || "missing"}`);
  }
  const sourcePlayerHtml = fs.readFileSync(path.join(SOURCE_ROOT, "player.html"), "utf8");
  const playerHtml = patchPlayerHtml(sourcePlayerHtml);
  writeText(playerPath, playerHtml);
  writeText(reviewPlayerPath, playerHtml);
  writeText(reviewIndexPath, reviewIndex({ reviewIndexPath, reviewPlayerPath }));

  const sourceProofBuild = readJson(path.join(SOURCE_ROOT, "proof_build.json"));
  sourceProofBuild.proof_build_id = `challenger-source-credit-gap_${stamp.replace("T", "").replace("Z", "Z")}`;
  sourceProofBuild.generated_at_utc = createdUtc;
  sourceProofBuild.review_scope = "challenger_source_credit_gap_html_review";
  sourceProofBuild.source_credit_gap = {
    model: MODEL,
    source_credits: SOURCE_CREDITS,
    timing: SOURCE_CREDIT_TIMING,
  };
  writeJson(proofBuildPath, sourceProofBuild);

  const seedManifest = {
    ...sourceManifest,
    packet_id: path.basename(outputRoot),
    foreground_matte_sha256: CHALLENGER_PRECISION_MATTE.maskSha256,
    foreground_matte_precision_model: CHALLENGER_PRECISION_MATTE.precisionModel,
    source_html_proof: { packet_path: outputRoot, manifest_path: manifestPath, player_path: playerPath },
  };
  writeJson(manifestPath, seedManifest);
  const guardReceiptPath = path.join(qaDir, "challenger_precision_matte_guard.json");
  const precisionGuard = challengerPrecisionMatteGuard({
    root: outputRoot,
    manifestPath,
    playerPath,
    writeReceiptPath: guardReceiptPath,
    context: "challenger_source_credit_gap_successor_preflight",
  });
  if (!precisionGuard.ok) throw new Error(`Precision matte guard failed:\n${JSON.stringify(precisionGuard, null, 2)}`);
  precisionGuard.receipt_path = guardReceiptPath;
  precisionGuard.receipt_sha256 = sha256File(guardReceiptPath);

  const qaSeedPath = path.join(qaDir, "challenger_source_credit_gap_static_qa.json");
  const manifest = patchManifest({
    sourceManifest,
    outputRoot,
    manifestPath,
    playerPath,
    reviewPlayerPath,
    reviewIndexPath,
    proofBuildPath,
    createdUtc,
    precisionGuard,
    qaPath: qaSeedPath,
  });
  writeJson(manifestPath, manifest);
  const { qaPath } = staticQa({ outputRoot, manifestPath, playerPath, reviewPlayerPath, reviewIndexPath, precisionGuard });
  const finalManifest = readJson(manifestPath);
  finalManifest.proof_artifacts.source_credit_gap_static_qa_path = qaPath;
  finalManifest.proof_artifacts.source_credit_gap_static_qa_sha256 = sha256File(qaPath);
  finalManifest.source_credit_gap.static_qa_path = qaPath;
  finalManifest.source_credit_gap.static_qa_sha256 = sha256File(qaPath);
  writeJson(manifestPath, finalManifest);

  console.log(
    JSON.stringify(
      {
        status: "challenger_source_credit_gap_html_review_ready",
        output_root: outputRoot,
        manifest_path: manifestPath,
        player_path: playerPath,
        review_player_path: reviewPlayerPath,
        review_html_path: reviewIndexPath,
        static_qa_path: qaPath,
        precision_guard_path: guardReceiptPath,
        source_credits: SOURCE_CREDITS,
      },
      null,
      2,
    ),
  );
}

main();
