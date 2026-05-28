#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const CHALLENGER_PRECISION_MATTE = {
  episodeId: "challenger",
  proofRoot:
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_precise_matte_repair_20260523T044315Z",
  maskRelativePath: "assets/masks/foreground_occlusion_matte.png",
  maskSha256: "987d1a96d51dd5c94acdc94a833a92ad9d9b4866ceb80dda539ed27084d5b857",
  precisionModel: "source_pixel_gap_preserving_tower_shuttle_matte_v3",
  keepReceiptPath:
    "/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_precise_matte_repair_20260523T044315Z/review/precision_matte_keep_receipt_20260523T045650Z.json",
  supersededMaskSha256: [
    "48ebac2e7e4b8737cc56e884d902211ee574781b7363eb24c9799afa3606d208",
    "a184e54cd698b607a2f522c6a11888c4fe55cfaad6585c0a4d249936e97bd9a4",
    "c4e91ecde3dd7ba44b2d5c7f3f3eb2580b142773158db122b4e3861afd9e938e",
  ],
};

export function sha256File(filePath) {
  return createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function readJsonIfExists(filePath) {
  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return null;
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function pickString(...values) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

function resolveMaybe(baseDir, value) {
  const text = String(value || "").trim();
  if (!text) return "";
  return path.isAbsolute(text) ? text : path.resolve(baseDir, text);
}

function inferRootFromManifest(manifestPath, manifest) {
  const manifestDir = manifestPath ? path.dirname(manifestPath) : process.cwd();
  if (manifestPath && fs.existsSync(path.join(manifestDir, "player.html"))) return manifestDir;
  const sourceHtmlProof = manifest?.source_html_proof && typeof manifest.source_html_proof === "object" ? manifest.source_html_proof : {};
  const packetPath = pickString(
    sourceHtmlProof.packet_path,
    sourceHtmlProof.proof_packet_path,
    manifest?.proof_packet_path,
    manifest?.proof_root,
    manifest?.proof_artifacts?.source_predecessor_root,
  );
  if (packetPath) return resolveMaybe(manifestDir, packetPath);
  return manifestPath ? path.dirname(manifestPath) : "";
}

function inferPlayerPath(root, manifestPath, manifest, rootManifest) {
  const manifestDir = manifestPath ? path.dirname(manifestPath) : root;
  const sourceHtmlProof = manifest?.source_html_proof && typeof manifest.source_html_proof === "object" ? manifest.source_html_proof : {};
  return pickString(
    sourceHtmlProof.player_path && resolveMaybe(manifestDir, sourceHtmlProof.player_path),
    rootManifest?.proof_artifacts?.player_html_path,
    rootManifest?.player_path,
    root && path.join(root, "player.html"),
  );
}

function inferRootManifestPath(root, manifestPath, manifest) {
  const manifestDir = manifestPath ? path.dirname(manifestPath) : root;
  const sourceHtmlProof = manifest?.source_html_proof && typeof manifest.source_html_proof === "object" ? manifest.source_html_proof : {};
  return pickString(
    sourceHtmlProof.manifest_path && resolveMaybe(manifestDir, sourceHtmlProof.manifest_path),
    root && path.join(root, "rough_assembly_manifest.json"),
  );
}

function manifestValue(manifests, ...keys) {
  for (const manifest of manifests) {
    if (!manifest || typeof manifest !== "object") continue;
    for (const key of keys) {
      const parts = key.split(".");
      let value = manifest;
      for (const part of parts) value = value && typeof value === "object" ? value[part] : undefined;
      if (value !== undefined && value !== null && String(value).trim() !== "") return value;
    }
  }
  return "";
}

function passFail(condition, pass, fail) {
  return condition ? pass : fail;
}

export function challengerPrecisionMatteGuard({
  root = "",
  manifestPath = "",
  playerPath = "",
  writeReceiptPath = "",
  context = "challenger_precision_matte_preflight",
} = {}) {
  const manifest = readJsonIfExists(manifestPath);
  const inferredRoot = root || inferRootFromManifest(manifestPath, manifest);
  const rootManifestPath = inferRootManifestPath(inferredRoot, manifestPath, manifest);
  const rootManifest = readJsonIfExists(rootManifestPath);
  const resolvedPlayerPath = playerPath || inferPlayerPath(inferredRoot, manifestPath, manifest, rootManifest);
  const manifests = [rootManifest, manifest].filter(Boolean);
  const episodeId = String(manifestValue(manifests, "episode_id") || "").trim();
  const isChallenger = episodeId === CHALLENGER_PRECISION_MATTE.episodeId || /Ep1_Challenger/.test(inferredRoot);
  const receipt = {
    ok: true,
    context,
    created_utc: new Date().toISOString(),
    episode_id: episodeId || (isChallenger ? "challenger" : ""),
    required: isChallenger,
    model: "challenger_precision_matte_guard_v1",
    expected: {
      proof_root: CHALLENGER_PRECISION_MATTE.proofRoot,
      mask_sha256: CHALLENGER_PRECISION_MATTE.maskSha256,
      precision_model: CHALLENGER_PRECISION_MATTE.precisionModel,
      keep_receipt_path: CHALLENGER_PRECISION_MATTE.keepReceiptPath,
      superseded_mask_sha256: CHALLENGER_PRECISION_MATTE.supersededMaskSha256,
    },
    observed: {
      proof_root: inferredRoot,
      root_manifest_path: rootManifestPath || "",
      manifest_path: manifestPath || "",
      player_path: resolvedPlayerPath || "",
      assets_path: inferredRoot ? path.join(inferredRoot, "assets") : "",
      assets_realpath: "",
      mask_path: inferredRoot ? path.join(inferredRoot, CHALLENGER_PRECISION_MATTE.maskRelativePath) : "",
      mask_realpath: "",
      mask_sha256: "",
      manifest_mask_sha256: "",
      manifest_precision_model: "",
      player_has_mask_cache_bust: false,
      player_has_data_mask_sha256: false,
      player_has_precision_model: false,
      keep_receipt_sha256: "",
    },
    failures: [],
    reads: {},
  };

  if (!isChallenger) {
    receipt.ok = true;
    receipt.reads.challenger_precision_matte_guard_read = "not_applicable_non_challenger_episode";
    if (writeReceiptPath) writeJson(writeReceiptPath, receipt);
    return receipt;
  }

  const fail = (message) => receipt.failures.push(message);
  const maskPath = receipt.observed.mask_path;
  const assetsPath = receipt.observed.assets_path;
  try {
    receipt.observed.assets_realpath = fs.realpathSync(assetsPath);
  } catch {
    fail(`assets path is missing or has broken symlink lineage: ${assetsPath}`);
  }
  if (!fs.existsSync(maskPath)) {
    fail(`foreground occlusion matte is missing: ${maskPath}`);
  } else {
    try {
      receipt.observed.mask_realpath = fs.realpathSync(maskPath);
    } catch {
      fail(`foreground occlusion matte has broken symlink lineage: ${maskPath}`);
    }
    receipt.observed.mask_sha256 = sha256File(maskPath);
  }

  const keepReceipt = readJsonIfExists(CHALLENGER_PRECISION_MATTE.keepReceiptPath);
  if (!keepReceipt) {
    fail(`precision matte keep receipt missing: ${CHALLENGER_PRECISION_MATTE.keepReceiptPath}`);
  } else {
    receipt.observed.keep_receipt_sha256 = sha256File(CHALLENGER_PRECISION_MATTE.keepReceiptPath);
  }

  receipt.observed.manifest_mask_sha256 = String(
    manifestValue(
      manifests,
      "foreground_matte_sha256",
      "matte_precision_repair.mask_sha256",
      "challenger_precision_matte_guard.expected.mask_sha256",
      "challenger_precision_matte_guard.observed.mask_sha256",
    ) || "",
  );
  receipt.observed.manifest_precision_model = String(
    manifestValue(
      manifests,
      "foreground_matte_precision_model",
      "matte_precision_repair.model_id",
      "challenger_precision_matte_guard.expected.precision_model",
    ) || "",
  );

  const playerHtml =
    resolvedPlayerPath && fs.existsSync(resolvedPlayerPath) && fs.statSync(resolvedPlayerPath).isFile()
      ? fs.readFileSync(resolvedPlayerPath, "utf8")
      : "";
  if (!playerHtml) {
    fail(`player.html missing for precision matte guard: ${resolvedPlayerPath || "(empty)"}`);
  } else {
    receipt.observed.player_has_mask_cache_bust = playerHtml.includes(`foreground_occlusion_matte.png?v=${CHALLENGER_PRECISION_MATTE.maskSha256}`);
    receipt.observed.player_has_data_mask_sha256 = playerHtml.includes(`data-mask-sha256="${CHALLENGER_PRECISION_MATTE.maskSha256}"`);
    receipt.observed.player_has_precision_model = playerHtml.includes(`foregroundMattePrecisionModel = "${CHALLENGER_PRECISION_MATTE.precisionModel}"`);
  }

  if (receipt.observed.mask_sha256 !== CHALLENGER_PRECISION_MATTE.maskSha256) {
    const stale = CHALLENGER_PRECISION_MATTE.supersededMaskSha256.includes(receipt.observed.mask_sha256);
    fail(
      stale
        ? `stale superseded Challenger mask is active: ${receipt.observed.mask_sha256}`
        : `Challenger mask SHA mismatch: ${receipt.observed.mask_sha256 || "missing"}`,
    );
  }
  if (receipt.observed.manifest_mask_sha256 && receipt.observed.manifest_mask_sha256 !== CHALLENGER_PRECISION_MATTE.maskSha256) {
    fail(`manifest records non-canonical Challenger mask SHA: ${receipt.observed.manifest_mask_sha256}`);
  }
  if (receipt.observed.manifest_precision_model && receipt.observed.manifest_precision_model !== CHALLENGER_PRECISION_MATTE.precisionModel) {
    fail(`manifest records non-canonical Challenger precision model: ${receipt.observed.manifest_precision_model}`);
  }
  if (receipt.observed.mask_realpath && !receipt.observed.mask_realpath.startsWith(CHALLENGER_PRECISION_MATTE.proofRoot + path.sep)) {
    fail(`active mask does not resolve to kept precision proof root: ${receipt.observed.mask_realpath}`);
  }
  if (!receipt.observed.player_has_mask_cache_bust) fail("player.html does not cache-bust the mask with the canonical SHA");
  if (!receipt.observed.player_has_data_mask_sha256) fail("player.html does not expose data-mask-sha256 for the canonical mask");
  if (!receipt.observed.player_has_precision_model) fail("player.html does not expose the canonical foregroundMattePrecisionModel");
  if (keepReceipt && keepReceipt?.mask?.sha256 && keepReceipt.mask.sha256 !== CHALLENGER_PRECISION_MATTE.maskSha256) {
    fail(`precision matte keep receipt mask SHA mismatch: ${keepReceipt.mask.sha256}`);
  }

  receipt.ok = receipt.failures.length === 0;
  receipt.reads = {
    challenger_precision_matte_guard_read: passFail(
      receipt.ok,
      "pass_challenger_precision_matte_v3_sha_model_receipt_and_player_metadata",
      "fail_challenger_precision_matte_guard",
    ),
    challenger_precision_mask_sha_read: passFail(
      receipt.observed.mask_sha256 === CHALLENGER_PRECISION_MATTE.maskSha256,
      "pass_mask_sha_987d1a96",
      "fail_mask_sha_not_987d1a96",
    ),
    challenger_superseded_mask_block_read: passFail(
      !CHALLENGER_PRECISION_MATTE.supersededMaskSha256.includes(receipt.observed.mask_sha256),
      "pass_no_superseded_challenger_mask_active",
      "fail_superseded_challenger_mask_active",
    ),
    challenger_mask_lineage_read: passFail(
      Boolean(receipt.observed.mask_realpath && receipt.observed.mask_realpath.startsWith(CHALLENGER_PRECISION_MATTE.proofRoot + path.sep)),
      "pass_mask_resolves_to_kept_precision_matte_root",
      "fail_mask_does_not_resolve_to_kept_precision_matte_root",
    ),
    challenger_precision_player_metadata_read: passFail(
      receipt.observed.player_has_mask_cache_bust &&
        receipt.observed.player_has_data_mask_sha256 &&
        receipt.observed.player_has_precision_model,
      "pass_player_cache_bust_data_sha_and_precision_model_present",
      "fail_player_precision_matte_metadata_missing",
    ),
    challenger_precision_keep_receipt_read: passFail(
      Boolean(receipt.observed.keep_receipt_sha256),
      "pass_precision_matte_human_keep_receipt_present",
      "fail_precision_matte_human_keep_receipt_missing",
    ),
  };

  if (writeReceiptPath) {
    receipt.receipt_path = writeReceiptPath;
    writeJson(writeReceiptPath, receipt);
    receipt.receipt_sha256 = sha256File(writeReceiptPath);
    writeJson(writeReceiptPath, receipt);
  }
  if (!receipt.ok) {
    const error = new Error(`Challenger precision matte guard failed:\n${receipt.failures.join("\n")}`);
    error.receipt = receipt;
    throw error;
  }
  return receipt;
}

function parseArgs(argv) {
  const args = { root: "", manifest: "", player: "", writeReceipt: "", context: "cli" };
  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      index += 1;
      if (index >= argv.length) throw new Error(`Missing value for ${arg}`);
      return argv[index];
    };
    if (arg === "--root") args.root = next();
    else if (arg === "--manifest") args.manifest = next();
    else if (arg === "--player") args.player = next();
    else if (arg === "--write-receipt") args.writeReceipt = next();
    else if (arg === "--context") args.context = next();
    else if (arg === "--help" || arg === "-h") {
      console.log("Usage: node scripts/challenger_precision_matte_guard.mjs [--root ROOT] [--manifest MANIFEST] [--player PLAYER] [--write-receipt PATH]");
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

const invokedPath = process.argv[1] ? pathToFileURL(path.resolve(process.argv[1])).href : "";
if (import.meta.url === invokedPath) {
  try {
    const args = parseArgs(process.argv);
    const receipt = challengerPrecisionMatteGuard({
      root: args.root,
      manifestPath: args.manifest,
      playerPath: args.player,
      writeReceiptPath: args.writeReceipt,
      context: args.context,
    });
    console.log(JSON.stringify(receipt, null, 2));
  } catch (error) {
    if (error.receipt) console.error(JSON.stringify(error.receipt, null, 2));
    console.error(error.stack || error.message || String(error));
    process.exit(1);
  }
}
