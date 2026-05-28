#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const requireFromHere = createRequire(import.meta.url);
const REPO_ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const EPISODES_ROOT = "/Users/mike/Episodes_CascadeEffects";
const REVIEW_SERVER_BASE_URL = "http://127.0.0.1:8766";
const MODEL = "other_seven_source_credit_gap_browser_qa_v1";
const REVIEW_START_MODEL = "challenger_contextual_source_credit_review_start_v1";

function formatReviewTime(seconds) {
  return Number(seconds).toFixed(3);
}

function usage(message = "") {
  if (message) console.error(message);
  console.error("Usage: node scripts/qa_other_seven_source_credit_gap_runtime.mjs --rollout-manifest PATH [--json]");
  process.exit(message ? 2 : 0);
}

function parseArgs(argv) {
  const args = { rolloutManifest: "", json: false };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--rollout-manifest") args.rolloutManifest = argv[++i] || "";
    else if (arg === "--json") args.json = true;
    else if (arg === "--help" || arg === "-h") usage();
    else usage(`Unknown argument: ${arg}`);
  }
  if (!args.rolloutManifest) usage("--rollout-manifest is required");
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function sha256File(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return "missing";
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function reviewUrlForPath(filePath, params = {}) {
  const rel = path.relative(EPISODES_ROOT, filePath).split(path.sep).map(encodeURIComponent).join("/");
  const url = new URL(`/${rel}`, REVIEW_SERVER_BASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }
  return url.toString();
}

function findPlaywright() {
  const candidates = [];
  try {
    candidates.push({ modulePath: null, playwright: requireFromHere("playwright") });
  } catch {}
  const npxRoot = path.join(process.env.HOME || "/Users/mike", ".npm/_npx");
  if (fs.existsSync(npxRoot)) {
    for (const entry of fs.readdirSync(npxRoot)) {
      const modulePath = path.join(npxRoot, entry, "node_modules/playwright");
      if (fs.existsSync(modulePath)) {
        try {
          candidates.push({ modulePath, playwright: requireFromHere(modulePath) });
        } catch {}
      }
    }
  }
  for (const candidate of candidates) {
    try {
      const executablePath = candidate.playwright.chromium.executablePath();
      if (fs.existsSync(executablePath)) return candidate.playwright;
    } catch {}
  }
  throw new Error("No Playwright Chromium executable was found.");
}

async function sampleEpisode(page, episode) {
  const timing = episode.source_credit_timing;
  const reviewStartSeconds = Number(episode.review_start_seconds);
  const legalFadeStart = Number(episode.fade_start_seconds);
  const legalFullOpacity = Number(episode.full_opacity_seconds);
  const samples = [
    { name: "review_start", time: reviewStartSeconds },
    { name: "before_source_credit", time: Math.max(0, timing.fade_start_seconds - 0.05) },
    { name: "source_credit_fade_start", time: timing.fade_start_seconds },
    { name: "source_credit_full", time: timing.full_opacity_seconds + 0.05 },
    { name: "source_credit_fade_out", time: timing.fade_out_start_seconds + 0.15 },
    { name: "legal_entry_minus", time: Math.max(0, legalFadeStart - 0.05) },
    { name: "legal_entry", time: legalFadeStart },
    { name: "legal_entry_mid_ramp", time: legalFadeStart + 0.15 },
    { name: "legal_entry_full", time: legalFullOpacity + 0.05 },
  ];
  const url = reviewUrlForPath(episode.review_player_path, {
    t: formatReviewTime(reviewStartSeconds),
    range_guard: episode.review_proof_build_id || `source_credit_${Date.now()}`,
  });
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => typeof window.__setRenderTime === "function", null, { timeout: 15000 });
  await page.waitForFunction(() => typeof window.__sourceCreditGapStateAt === "function", null, { timeout: 15000 });
  const domMeta = await page.evaluate(async () => {
    const params = new URL(window.location.href).searchParams;
    const freshness =
      typeof window.__ceRunProofFreshnessCheck === "function"
        ? await window.__ceRunProofFreshnessCheck()
        : window.__ceProofFreshnessState || null;
    const warning = document.querySelector(".ce-proof-freshness-warning");
    const warningStyle = warning ? getComputedStyle(warning) : null;
    const warningVisible =
      Boolean(warning) &&
      warning.hidden === false &&
      warningStyle &&
      warningStyle.display !== "none" &&
      warningStyle.visibility !== "hidden" &&
      Number.parseFloat(warningStyle.opacity || "1") > 0;
    const overlay = document.getElementById("ceSourceCreditGap");
    const overlayStyle = overlay ? getComputedStyle(overlay) : null;
    const sourceCreditContainerStyle = overlayStyle
      ? {
          backgroundColor: overlayStyle.backgroundColor,
          borderWidth: overlayStyle.borderWidth,
          borderStyle: overlayStyle.borderStyle,
          boxShadow: overlayStyle.boxShadow,
          paddingTop: overlayStyle.paddingTop,
          paddingRight: overlayStyle.paddingRight,
          paddingBottom: overlayStyle.paddingBottom,
          paddingLeft: overlayStyle.paddingLeft,
          backdropFilter: overlayStyle.backdropFilter || overlayStyle.webkitBackdropFilter || "",
        }
      : null;
    const labels = Array.from(document.querySelectorAll(".ce-source-credit-gap__item")).map((node) =>
      node.textContent.trim(),
    );
    const targetSelectors = {
      left: ".target.left, .youtube-target.left-video, .ce-youtube-end-screen-target.left-video",
      right: ".target.right, .youtube-target.right-video, .ce-youtube-end-screen-target.right-video",
      subscribe: ".target.subscribe, .youtube-target.subscribe-target, .ce-youtube-end-screen-target.subscribe-target",
    };
    const targetStyles = Object.fromEntries(
      Object.entries(targetSelectors).map(([key, selector]) => {
        const node = document.querySelector(selector);
        if (!node) return [key, null];
        const style = getComputedStyle(node);
        const after = getComputedStyle(node, "::after");
        return [
          key,
          {
            selector,
            borderWidth: style.borderWidth,
            boxShadow: style.boxShadow,
            afterContent: after.content,
            afterDisplay: after.display,
            afterBorderWidth: after.borderWidth,
            afterBoxShadow: after.boxShadow,
          },
        ];
      }),
    );
    return {
      hasOverlay: Boolean(overlay),
      model: overlay?.dataset?.sourceCreditModel || "",
      initialSourceCreditComputedOpacity: overlayStyle ? Number.parseFloat(overlayStyle.opacity || "0") : null,
      initialSourceCreditActive: overlay?.dataset?.active || "",
      sourceCreditContainerStyle,
      labels,
      visibleUrlsInLabels: labels.filter((label) => /https?:\/\//i.test(label)),
      targetStyles,
      urlTimeParam: params.get("t") || "",
      urlRangeGuard: params.get("range_guard") || "",
      proofFreshness: {
        hasCheckHook: typeof window.__ceRunProofFreshnessCheck === "function",
        state: freshness,
        warningVisible,
        warningText: warning ? (warning.textContent || "").replace(/\s+/g, " ").trim() : "",
      },
    };
  });
  const reviewChrome = await page.evaluate(() => {
    const selectors = [
      ".review-header",
      ".audio-review",
      ".controls",
      ".review-grid",
      ".review-note",
      ".review-meta",
      ".machine-reads",
      "main > header",
    ];
    const reads = selectors.flatMap((selector) =>
      Array.from(document.querySelectorAll(selector)).map((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        const visible =
          style.display !== "none" &&
          style.visibility !== "hidden" &&
          Number.parseFloat(style.opacity || "1") > 0 &&
          rect.width > 0 &&
          rect.height > 0;
        return {
          selector,
          text: (node.textContent || "").replace(/\s+/g, " ").trim().slice(0, 160),
          display: style.display,
          visibility: style.visibility,
          opacity: Number.parseFloat(style.opacity || "1"),
          rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
          visible,
        };
      }),
    );
    return {
      guardStylePresent: Boolean(document.getElementById("ce-source-credit-review-chrome-guard-style")),
      visibleNodes: reads.filter((read) => read.visible),
      reads,
    };
  });
  const renderChrome = await page.evaluate(async (sampleTime) => {
    const previousRenderMode = document.documentElement.classList.contains("render-mode");
    document.documentElement.classList.add("render-mode");
    if (typeof window.__setRenderTime === "function") window.__setRenderTime(sampleTime);
    await new Promise((resolve) => requestAnimationFrame(() => resolve()));
    const forbiddenText = /Ambient\/effects visual review|Review-only browser sample|Sample cue states|Current Gate|Viewer Stage Policy/i;
    const selectors = [
      ".review-header",
      ".audio-review",
      ".controls",
      ".review-grid",
      ".review-note",
      ".review-meta",
      ".machine-reads",
      ".ce-review-transport",
      "main > header",
      "audio",
      "input",
      "output",
    ];
    const reads = selectors.flatMap((selector) =>
      Array.from(document.querySelectorAll(selector)).map((node) => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        const visible =
          style.display !== "none" &&
          style.visibility !== "hidden" &&
          Number.parseFloat(style.opacity || "1") > 0 &&
          rect.width > 0 &&
          rect.height > 0;
        return {
          selector,
          text: (node.textContent || "").replace(/\s+/g, " ").trim().slice(0, 160),
          display: style.display,
          visibility: style.visibility,
          opacity: Number.parseFloat(style.opacity || "1"),
          rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
          visible,
          forbiddenText: forbiddenText.test(node.textContent || ""),
        };
      }),
    );
    if (!previousRenderMode) document.documentElement.classList.remove("render-mode");
    return {
      sampleTime,
      visibleForbiddenNodes: reads.filter((read) => read.visible || read.forbiddenText),
      reads,
    };
  }, timing.full_opacity_seconds + 0.05);
  const mediaEventSync = await page.evaluate(
    async ({ reviewStartSeconds: startTime, fullTime }) => {
      const audio = document.getElementById("audio") || document.querySelector("audio");
      const overlay = document.getElementById("ceSourceCreditGap");
      const waitFrame = () => new Promise((resolve) => requestAnimationFrame(() => resolve()));
      if (!audio || !overlay) return { hasAudio: Boolean(audio), hasOverlay: Boolean(overlay), passed: false };
      try {
        audio.pause();
        audio.currentTime = Number(startTime) || 0;
      } catch {}
      audio.dispatchEvent(new Event("timeupdate"));
      audio.dispatchEvent(new Event("seeked"));
      await waitFrame();
      const reviewStartOpacity = Number(getComputedStyle(overlay).opacity || 0);
      try {
        audio.currentTime = Number(fullTime) || 0;
      } catch {}
      audio.dispatchEvent(new Event("timeupdate"));
      audio.dispatchEvent(new Event("seeked"));
      await waitFrame();
      const sourceCreditFullOpacity = Number(getComputedStyle(overlay).opacity || 0);
      try {
        audio.currentTime = Number(startTime) || 0;
      } catch {}
      audio.dispatchEvent(new Event("timeupdate"));
      await waitFrame();
      return {
        hasAudio: true,
        hasOverlay: true,
        review_start_seconds: Number(startTime) || 0,
        source_credit_full_sample_seconds: Number(fullTime) || 0,
        review_start_computed_opacity: reviewStartOpacity,
        source_credit_full_computed_opacity: sourceCreditFullOpacity,
        passed: reviewStartOpacity <= 0.001 && sourceCreditFullOpacity >= 0.95,
      };
    },
    { reviewStartSeconds, fullTime: timing.full_opacity_seconds + 0.05 },
  );
  const fullUrl = reviewUrlForPath(episode.review_player_path, {
    t: formatReviewTime(timing.full_opacity_seconds + 0.05),
    range_guard: `${episode.review_proof_build_id || "source_credit"}_url_time_sync`,
  });
  await page.goto(fullUrl, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => typeof window.__setRenderTime === "function", null, { timeout: 15000 });
  await page.waitForFunction(() => typeof window.__sourceCreditGapStateAt === "function", null, { timeout: 15000 });
  const urlTimeSourceCreditSync = await page.evaluate((fullTime) => {
    const overlay = document.getElementById("ceSourceCreditGap");
    const style = overlay ? getComputedStyle(overlay) : null;
    const state = typeof window.__sourceCreditGapStateAt === "function" ? window.__sourceCreditGapStateAt(fullTime) : null;
    const computedOpacity = style ? Number.parseFloat(style.opacity || "0") : null;
    return {
      url: window.location.href,
      full_sample_seconds: Number(fullTime) || 0,
      hasOverlay: Boolean(overlay),
      active: overlay?.dataset?.active || "",
      computedOpacity,
      state,
      passed: Boolean(overlay) && computedOpacity >= 0.95,
    };
  }, timing.full_opacity_seconds + 0.05);
  const sampleReads = [];
  for (const sample of samples) {
    const read = await page.evaluate((time) => {
      window.__setRenderTime(time);
      const sourceCredit = window.__sourceCreditGapStateAt(time);
      const endScreen = typeof window.__outroDebugAt === "function" ? window.__outroDebugAt(time) : null;
      const overlay = document.getElementById("ceSourceCreditGap");
      const computedOpacity = overlay ? Number(getComputedStyle(overlay).opacity || 0) : null;
      return {
        source_credit: sourceCredit,
        source_credit_computed_opacity: computedOpacity,
        end_screen: endScreen,
      };
    }, sample.time);
    sampleReads.push({ ...sample, ...read });
  }
  const failures = [];
  if (!domMeta.hasOverlay) failures.push("source credit overlay missing");
  if (!reviewChrome.guardStylePresent) failures.push("source-credit review chrome guard style missing");
  if (reviewChrome.visibleNodes.length) {
    failures.push(`legacy review chrome visible in review mode: ${reviewChrome.visibleNodes.map((node) => node.selector).join(", ")}`);
  }
  if (renderChrome.visibleForbiddenNodes.some((node) => node.visible)) {
    failures.push(
      `legacy review chrome visible in render mode: ${renderChrome.visibleForbiddenNodes
        .filter((node) => node.visible)
        .map((node) => node.selector)
        .join(", ")}`,
    );
  }
  if (!Number.isFinite(reviewStartSeconds)) failures.push("review start seconds missing or invalid");
  if (!(reviewStartSeconds < timing.fade_start_seconds)) failures.push("review start is not before source-credit fade start");
  if (Math.abs(Number(domMeta.urlTimeParam) - reviewStartSeconds) > 0.001) {
    failures.push(`review URL t param mismatch: ${domMeta.urlTimeParam} !== ${formatReviewTime(reviewStartSeconds)}`);
  }
  if (episode.review_start_model !== REVIEW_START_MODEL) failures.push(`review start model mismatch: ${episode.review_start_model}`);
  if (!domMeta.proofFreshness?.hasCheckHook) failures.push("proof freshness check hook missing");
  if (domMeta.proofFreshness?.state?.stale) {
    failures.push(
      `proof freshness stale: loaded ${domMeta.proofFreshness.state.loaded_proof_build_id}, latest ${domMeta.proofFreshness.state.latest_proof_build_id}`,
    );
  }
  if (domMeta.proofFreshness?.warningVisible) failures.push(`proof freshness warning visible: ${domMeta.proofFreshness.warningText}`);
  if (domMeta.model !== "center_source_credit_gap_v1") failures.push(`source credit model mismatch: ${domMeta.model}`);
  const sourceCreditPanel = domMeta.sourceCreditContainerStyle || {};
  const sourceCreditPadding = [
    sourceCreditPanel.paddingTop,
    sourceCreditPanel.paddingRight,
    sourceCreditPanel.paddingBottom,
    sourceCreditPanel.paddingLeft,
  ].map((value) => Number.parseFloat(value || "0"));
  if (Number.parseFloat(sourceCreditPanel.borderWidth || "0") !== 0) {
    failures.push(`source credit container border is not zero: ${sourceCreditPanel.borderWidth}`);
  }
  if (String(sourceCreditPanel.boxShadow || "none") !== "none") {
    failures.push(`source credit container box shadow is not none: ${sourceCreditPanel.boxShadow}`);
  }
  if (sourceCreditPadding.some((value) => value !== 0)) {
    failures.push(`source credit container padding is not zero: ${sourceCreditPadding.join(",")}`);
  }
  if (!/rgba?\(0,\s*0,\s*0,\s*0\)|transparent/i.test(String(sourceCreditPanel.backgroundColor || ""))) {
    failures.push(`source credit container background is not transparent: ${sourceCreditPanel.backgroundColor}`);
  }
  if (!mediaEventSync.hasAudio) failures.push("audio element missing for source-credit media-event sync");
  if (!mediaEventSync.passed) {
    failures.push(
      `source-credit media-event sync failed: review_start_opacity=${mediaEventSync.review_start_computed_opacity}, full_opacity=${mediaEventSync.source_credit_full_computed_opacity}`,
    );
  }
  if ((domMeta.initialSourceCreditComputedOpacity ?? 1) > 0.001) {
    failures.push(`source credit visible on initial review-start URL load: ${domMeta.initialSourceCreditComputedOpacity}`);
  }
  if (!urlTimeSourceCreditSync.passed) {
    failures.push(
      `source-credit URL time sync failed: full_url_opacity=${urlTimeSourceCreditSync.computedOpacity}, active=${urlTimeSourceCreditSync.active}`,
    );
  }
  if (domMeta.labels.length !== 3) failures.push(`expected 3 source labels, found ${domMeta.labels.length}`);
  if (domMeta.visibleUrlsInLabels.length) failures.push("visible source label URL found");
  for (const label of episode.source_labels || []) {
    if (!domMeta.labels.includes(label)) failures.push(`source label missing in DOM: ${label}`);
  }
  const before = sampleReads.find((sample) => sample.name === "before_source_credit");
  const reviewStart = sampleReads.find((sample) => sample.name === "review_start");
  const full = sampleReads.find((sample) => sample.name === "source_credit_full");
  const legalMinus = sampleReads.find((sample) => sample.name === "legal_entry_minus");
  const legalEntry = sampleReads.find((sample) => sample.name === "legal_entry");
  const legalMid = sampleReads.find((sample) => sample.name === "legal_entry_mid_ramp");
  const legalFull = sampleReads.find((sample) => sample.name === "legal_entry_full");
  if ((reviewStart?.source_credit?.opacity ?? 1) > 0.001) failures.push("source credit visible at contextual review start");
  if ((before?.source_credit?.opacity ?? 1) > 0.001) failures.push("source credit visible before fade start");
  if ((full?.source_credit?.opacity ?? 0) < 0.95) failures.push("source credit not full after fade-in");
  if ((legalEntry?.source_credit?.opacity ?? 1) > 0.001) failures.push("source credit not cleared at legal entry");
  const endBefore = Number(legalMinus?.end_screen?.endScreenOpacity ?? legalMinus?.end_screen?.overlayOpacity ?? 0);
  const endMid = Number(legalMid?.end_screen?.endScreenOpacity ?? legalMid?.end_screen?.overlayOpacity ?? 0);
  const endFull = Number(legalFull?.end_screen?.endScreenOpacity ?? legalFull?.end_screen?.overlayOpacity ?? 0);
  if (endBefore > 0.001) failures.push("end-screen visible before legal entry");
  if (endMid <= 0) failures.push("end-screen did not begin during legal ramp");
  if (endFull < 0.95) failures.push("end-screen not full after legal ramp");
  for (const [targetKey, style] of Object.entries(domMeta.targetStyles)) {
    if (!style) {
      failures.push(`end-screen target missing: ${targetKey}`);
      continue;
    }
    if (parseFloat(style.borderWidth || "0") !== 0) failures.push(`${targetKey} border width is not zero`);
    if (String(style.boxShadow || "none") !== "none") failures.push(`${targetKey} box shadow is not none`);
    if (targetKey === "subscribe" && style.afterDisplay !== "none" && style.afterContent !== "none") {
      failures.push("subscribe pseudo-element is still visible");
    }
  }
  return {
    episode_id: episode.episode_id,
    title: episode.title,
    review_player_url: url,
    review_start_model: episode.review_start_model,
    review_start_seconds: reviewStartSeconds,
    source_credit_timing: timing,
    legal_end_screen_fade_start_seconds: legalFadeStart,
    legal_end_screen_full_opacity_seconds: legalFullOpacity,
    dom: domMeta,
    review_chrome: reviewChrome,
    render_chrome: renderChrome,
    media_event_sync: mediaEventSync,
    url_time_source_credit_sync: urlTimeSourceCreditSync,
    samples: sampleReads,
    failures,
    passed: failures.length === 0,
    reads: {
      source_credit_gap_browser_read: failures.length
        ? "fail_source_credit_gap_browser_qa"
        : "pass_source_credit_gap_browser_qa",
      source_credit_opacity_browser_read: failures.some((failure) => /source credit/.test(failure))
        ? "fail_source_credit_opacity_timing"
        : "pass_source_credit_opacity_zero_visible_and_clear",
      legal_end_screen_opacity_browser_read: failures.some((failure) => /end-screen/.test(failure))
        ? "fail_legal_end_screen_opacity_timing"
        : "pass_legal_end_screen_opacity_zero_before_entry_and_full_after_ramp",
      borderless_placeholder_computed_read: failures.some((failure) => /border|shadow|pseudo/.test(failure))
        ? "fail_borderless_placeholder_computed_styles"
        : "pass_borderless_placeholder_computed_styles",
      proof_freshness_browser_read: failures.some((failure) => /proof freshness/.test(failure))
        ? "fail_stale_proof_warning_visible"
        : "pass_no_stale_proof_warning_visible",
      source_credit_review_start_browser_read: failures.some((failure) => /review start|URL t param/.test(failure))
        ? "fail_source_credit_review_start_not_contextual"
        : "pass_source_credit_review_starts_before_fade_like_challenger",
      source_credit_media_event_sync_read: failures.some((failure) => /media-event sync|audio element/.test(failure))
        ? "fail_source_credit_not_synced_to_audio_events"
        : "pass_source_credit_synced_to_audio_timeupdate_seeked_events",
      source_credit_url_time_sync_read: failures.some((failure) => /URL time sync|initial review-start URL/.test(failure))
        ? "fail_source_credit_not_synced_to_url_time"
        : "pass_source_credit_synced_to_url_time_on_initial_load",
      source_credit_container_chrome_read: failures.some((failure) => /source credit container/.test(failure))
        ? "fail_source_credit_container_has_panel_chrome"
        : "pass_source_credit_container_has_no_panel_chrome",
      legacy_review_chrome_suppression_read: failures.some((failure) => /legacy review chrome|chrome guard/.test(failure))
        ? "fail_legacy_review_chrome_visible"
        : "pass_legacy_review_chrome_hidden_in_review_and_render_modes",
    },
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const rollout = readJson(args.rolloutManifest);
  const playwright = findPlaywright();
  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const results = [];
  try {
    for (const episode of rollout.episodes || []) {
      const qa = await sampleEpisode(page, episode);
      const qaPath = path.join(episode.output_root, "qa", "source_credit_gap_browser_qa.json");
      writeJson(qaPath, {
        model: MODEL,
        created_utc: new Date().toISOString(),
        ...qa,
      });
      const manifest = readJson(episode.manifest_path);
      manifest.source_credit_gap = {
        ...(manifest.source_credit_gap || {}),
        browser_qa_path: qaPath,
        browser_qa_sha256: sha256File(qaPath),
        browser_qa_passed: qa.passed,
      };
      manifest.proof_artifacts = {
        ...(manifest.proof_artifacts || {}),
        source_credit_gap_browser_qa_path: qaPath,
        source_credit_gap_browser_qa_sha256: sha256File(qaPath),
      };
      manifest.qa = {
        ...(manifest.qa || {}),
        source_credit_gap_browser_pass: qa.passed,
      };
      manifest.reads = {
        ...(manifest.reads || {}),
        ...qa.reads,
      };
      if (!qa.passed) {
        manifest.blocked_prerequisite = "source_credit_gap_browser_qa_failed";
        manifest.may_render_final_mp4 = false;
        manifest.may_youtube_action = false;
      }
      writeJson(episode.manifest_path, manifest);
      qa.manifest_sha256_after_update = sha256File(episode.manifest_path);
      writeJson(qaPath, {
        model: MODEL,
        created_utc: new Date().toISOString(),
        ...qa,
      });
      results.push({ ...qa, qa_path: qaPath });
    }
  } finally {
    await browser.close();
  }
  rollout.browser_qa = {
    model: MODEL,
    created_utc: new Date().toISOString(),
    passed: results.every((result) => result.passed),
    episodes: results.map((result) => ({
      episode_id: result.episode_id,
      qa_path: result.qa_path,
      passed: result.passed,
      failure_count: result.failures.length,
    })),
  };
  rollout.browser_qa_passed = rollout.browser_qa.passed;
  rollout.updated_browser_qa_utc = new Date().toISOString();
  writeJson(args.rolloutManifest, rollout);
  const output = {
    rollout_manifest_path: args.rolloutManifest,
    passed: rollout.browser_qa.passed,
    episodes: rollout.browser_qa.episodes,
  };
  if (args.json) console.log(JSON.stringify(output, null, 2));
  else console.log(`source credit browser QA ${output.passed ? "passed" : "failed"}: ${args.rolloutManifest}`);
  if (!output.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
