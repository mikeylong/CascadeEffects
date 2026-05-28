import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

export const END_SCREEN_PALETTE_CONTRACT_ID = "living_cover_end_screen_palette_contract_v1";
export const END_SCREEN_PALETTE_DERIVATION_MODEL = "backplate_sampled_youtube_end_screen_palette_v1";
export const END_SCREEN_PALETTE_SAMPLE_MODEL = "pillow_downsample_average_rgb_v1";

const REQUIRED_COLOR_KEYS = [
  "video_target_fill_rgba",
  "video_target_border_rgba",
  "video_target_secondary_border_rgba",
  "subscribe_ring_rgba",
  "muted_rail_text_hex",
  "small_accent_hex",
];

const REQUIRED_READ_KEYS = [
  "end_screen_palette_contract_read",
  "end_screen_target_fill_palette_read",
  "end_screen_target_contrast_read",
  "rail_panel_palette_read",
  "source_integrated_panel_color_read",
  "no_cross_episode_default_palette_read",
];

const FORBIDDEN_DEFAULT_COLORS = new Set(
  [
    "rgba(17, 23, 47, 0.42)",
    "rgba(120, 220, 232, 0.76)",
    "rgba(164, 139, 255, 0.70)",
    "rgba(255, 248, 232, 0.88)",
    "rgba(17, 23, 47, 0.28)",
    "rgba(184, 111, 111, 0.720)",
    "rgba(111, 184, 184, 0.720)",
    "rgba(124, 111, 184, 0.860)",
    "rgba(133, 81, 81, 0.120)",
    "rgba(81, 133, 133, 0.120)",
    "rgba(90, 81, 133, 0.130)",
    "#f7efe1",
    "#b9c8d8",
    "#ffe0a6",
  ].map(normalizeColor),
);

function normalizeColor(value) {
  return String(value || "").toLowerCase().replace(/\s+/g, "");
}

function hasNonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0 && !/^(tbd|not_found|missing)$/i.test(value.trim());
}

function readPasses(value) {
  return value === true || (typeof value === "string" && /^pass|approved/i.test(value));
}

function resolveMaybeRelative(filePath, baseDir = process.cwd()) {
  if (!hasNonEmptyString(filePath)) return "";
  return path.isAbsolute(filePath) ? filePath : path.resolve(baseDir, filePath);
}

export function sha256File(filePath) {
  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return "";
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function clamp(value, min = 0, max = 255) {
  return Math.max(min, Math.min(max, Math.round(Number(value) || 0)));
}

function mixRgb(a, b, amount) {
  return [
    clamp(a[0] + (b[0] - a[0]) * amount),
    clamp(a[1] + (b[1] - a[1]) * amount),
    clamp(a[2] + (b[2] - a[2]) * amount),
  ];
}

function rgbToHex(rgb) {
  return `#${rgb.map((channel) => clamp(channel).toString(16).padStart(2, "0")).join("")}`;
}

function rgba(rgb, alpha) {
  return `rgba(${clamp(rgb[0])}, ${clamp(rgb[1])}, ${clamp(rgb[2])}, ${Number(alpha).toFixed(2)})`;
}

function relativeLuminance(rgb) {
  const channels = rgb.map((channel) => {
    const normalized = clamp(channel) / 255;
    return normalized <= 0.03928 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(a, b) {
  const lighter = Math.max(relativeLuminance(a), relativeLuminance(b));
  const darker = Math.min(relativeLuminance(a), relativeLuminance(b));
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(2));
}

function sampleBackplateAverageRgb(sourceArtPath) {
  if (!sourceArtPath || !fs.existsSync(sourceArtPath)) return null;
  const script = `
import json
import sys
from PIL import Image

img = Image.open(sys.argv[1]).convert("RGBA")
img.thumbnail((96, 54))
pixels = []
for r, g, b, a in img.getdata():
    if a >= 16:
        pixels.append((r, g, b))
if not pixels:
    pixels = [(12, 14, 18)]
avg = [round(sum(px[i] for px in pixels) / len(pixels)) for i in range(3)]
print(json.dumps({"average_rgb": avg, "sample_count": len(pixels)}))
`;
  const result = spawnSync("python3", ["-c", script, sourceArtPath], {
    encoding: "utf8",
    maxBuffer: 1024 * 1024,
  });
  if (result.status !== 0) return null;
  try {
    return JSON.parse(result.stdout.trim());
  } catch {
    return null;
  }
}

function deriveColorsFromAverage(averageRgb) {
  const base = Array.isArray(averageRgb) ? averageRgb.map((value) => clamp(value)) : [38, 44, 52];
  const darkInk = [5, 8, 23];
  const warmText = [255, 248, 232];
  const fill = mixRgb(base, darkInk, 0.68);
  const border = mixRgb(base, warmText, 0.62);
  const secondary = mixRgb(base, [220, 230, 244], 0.54);
  const subscribe = mixRgb(border, warmText, 0.45);
  const mutedText = mixRgb(base, warmText, 0.70);
  const accent = mixRgb(base, warmText, 0.80);
  return {
    video_target_fill_rgba: rgba(fill, 0.42),
    video_target_border_rgba: rgba(border, 0.76),
    video_target_secondary_border_rgba: rgba(secondary, 0.70),
    subscribe_ring_rgba: rgba(subscribe, 0.88),
    muted_rail_text_hex: rgbToHex(mutedText),
    small_accent_hex: rgbToHex(accent),
    contrast: {
      muted_text_on_target_fill: contrastRatio(mutedText, fill),
      accent_on_target_fill: contrastRatio(accent, fill),
    },
  };
}

function cssVariablesFromColors(colors) {
  return {
    "--ce-end-screen-target-fill": colors.video_target_fill_rgba,
    "--ce-end-screen-video-border": colors.video_target_border_rgba,
    "--ce-end-screen-video-border-secondary": colors.video_target_secondary_border_rgba,
    "--ce-end-screen-subscribe-ring": colors.subscribe_ring_rgba,
    "--ce-end-screen-muted-text": colors.muted_rail_text_hex,
    "--ce-end-screen-small-accent": colors.small_accent_hex,
  };
}

export function deriveEndScreenPaletteContract({ sourceArtPath, episodeId = "", fallbackPalette = {} } = {}) {
  const resolvedSourceArtPath = sourceArtPath && fs.existsSync(sourceArtPath) ? path.resolve(sourceArtPath) : "";
  const sample = sampleBackplateAverageRgb(resolvedSourceArtPath);
  const averageRgb = sample?.average_rgb || [38, 44, 52];
  const colors = deriveColorsFromAverage(averageRgb);
  if (fallbackPalette.muted && !colors.muted_rail_text_hex) colors.muted_rail_text_hex = fallbackPalette.muted;
  const sourceSha256 = sha256File(resolvedSourceArtPath);
  const status = resolvedSourceArtPath && sourceSha256 && sample ? "pass" : "blocked_missing_sampled_backplate";
  return {
    contract_id: END_SCREEN_PALETTE_CONTRACT_ID,
    status,
    required: true,
    required_for_gates: ["visual_system", "rough_assembly", "final_assembly", "publish_readiness"],
    episode_id: episodeId,
    palette_source: "sampled_episode_backplate",
    derivation_model: END_SCREEN_PALETTE_DERIVATION_MODEL,
    sample_model: END_SCREEN_PALETTE_SAMPLE_MODEL,
    approved_backplate: {
      path: resolvedSourceArtPath || "missing",
      sha256: sourceSha256 || "missing",
      role: "approved_living_cover_source_art_backplate",
    },
    sampled_backplate: {
      path: resolvedSourceArtPath || "missing",
      sha256: sourceSha256 || "missing",
      average_rgb: averageRgb,
      average_hex: rgbToHex(averageRgb),
      sample_count: sample?.sample_count || 0,
    },
    colors: Object.fromEntries(REQUIRED_COLOR_KEYS.map((key) => [key, colors[key]])),
    contrast: colors.contrast,
    css_variables: cssVariablesFromColors(colors),
    reads: {
      end_screen_palette_contract_read: status === "pass" ? "pass_backplate_sampled_palette_contract_present" : status,
      end_screen_target_fill_palette_read: status === "pass" ? "pass_target_fill_harmonized_with_backplate_sample" : status,
      end_screen_target_contrast_read:
        status === "pass" && colors.contrast.muted_text_on_target_fill >= 3
          ? "pass_muted_text_and_accent_contrast_preserved"
          : "blocked_low_or_missing_contrast",
      rail_panel_palette_read: status === "pass" ? "pass_source_aware_end_screen_palette_contract" : status,
      source_integrated_panel_color_read: status === "pass" ? "pass_no_fixed_cross_episode_panel_color" : status,
      no_cross_episode_default_palette_read: status === "pass" ? "pass_no_challenger_default_target_colors" : status,
    },
  };
}

export function endScreenPaletteContractForManifest(manifest) {
  return (
    manifest?.end_screen_palette_contract ||
    manifest?.end_screen_context?.end_screen_palette_contract ||
    manifest?.youtube_end_screen?.end_screen_palette_contract ||
    manifest?.palette_contracts?.end_screen_palette_contract ||
    null
  );
}

export function isHumanApprovedPaletteOverride(contract) {
  return (
    contract?.palette_source === "human_approved_override" ||
    readPasses(contract?.human_approved_override?.approval_read) ||
    readPasses(contract?.override_read)
  );
}

function flattenedColors(contract) {
  const colors = contract?.colors || {};
  const css = contract?.css_variables || {};
  return [...Object.values(colors), ...Object.values(css)].filter((value) => typeof value === "string");
}

export function usesForbiddenCrossEpisodePalette(contract) {
  return flattenedColors(contract).some((value) => FORBIDDEN_DEFAULT_COLORS.has(normalizeColor(value)));
}

export function endScreenPaletteContractFailures(manifest, { manifestPath = "", requireExistingBackplate = true } = {}) {
  const failures = [];
  const manifestDir = manifestPath ? path.dirname(path.resolve(manifestPath)) : process.cwd();
  const contract = endScreenPaletteContractForManifest(manifest);
  if (!contract) {
    return [
      {
        id: "end_screen_palette_contract",
        detail: "missing required end_screen_palette_contract",
      },
    ];
  }

  const override = isHumanApprovedPaletteOverride(contract);
  if (contract.contract_id !== END_SCREEN_PALETTE_CONTRACT_ID) {
    failures.push({ id: "end_screen_palette_contract.contract_id", detail: `expected ${END_SCREEN_PALETTE_CONTRACT_ID}` });
  }
  if (!readPasses(contract.status)) {
    failures.push({ id: "end_screen_palette_contract.status", detail: `status must pass; found ${contract.status || "(missing)"}` });
  }
  if (!["sampled_episode_backplate", "human_approved_override"].includes(contract.palette_source)) {
    failures.push({
      id: "end_screen_palette_contract.palette_source",
      detail: "palette_source must be sampled_episode_backplate or human_approved_override",
    });
  }
  if (contract.palette_source === "sampled_episode_backplate" && contract.derivation_model !== END_SCREEN_PALETTE_DERIVATION_MODEL) {
    failures.push({
      id: "end_screen_palette_contract.derivation_model",
      detail: `sampled contracts must use ${END_SCREEN_PALETTE_DERIVATION_MODEL}`,
    });
  }

  const approved = contract.approved_backplate || {};
  const backplatePath = resolveMaybeRelative(approved.path || contract.source_art_path || "", manifestDir);
  const declaredSha = approved.sha256 || contract.source_art_sha256 || "";
  if (contract.palette_source === "sampled_episode_backplate") {
    if (!hasNonEmptyString(backplatePath)) {
      failures.push({ id: "end_screen_palette_contract.approved_backplate.path", detail: "approved backplate path is required" });
    } else if (requireExistingBackplate && !fs.existsSync(backplatePath)) {
      failures.push({
        id: "end_screen_palette_contract.approved_backplate.exists",
        detail: `approved backplate does not exist: ${backplatePath}`,
      });
    }
    if (!hasNonEmptyString(declaredSha)) {
      failures.push({ id: "end_screen_palette_contract.approved_backplate.sha256", detail: "approved backplate sha256 is required" });
    } else if (requireExistingBackplate && fs.existsSync(backplatePath)) {
      const actualSha = sha256File(backplatePath);
      if (actualSha !== declaredSha) {
        failures.push({
          id: "end_screen_palette_contract.approved_backplate.sha256_match",
          detail: `approved backplate sha256 mismatch: declared ${declaredSha}, actual ${actualSha}`,
        });
      }
    }
  }

  for (const key of REQUIRED_COLOR_KEYS) {
    if (!hasNonEmptyString(contract.colors?.[key])) {
      failures.push({ id: `end_screen_palette_contract.colors.${key}`, detail: `${key} is required` });
    }
  }
  for (const key of REQUIRED_READ_KEYS) {
    if (!readPasses(contract.reads?.[key])) {
      failures.push({
        id: `end_screen_palette_contract.reads.${key}`,
        detail: `${key} must pass; found ${contract.reads?.[key] || "(missing)"}`,
      });
    }
  }
  if (usesForbiddenCrossEpisodePalette(contract) && !override) {
    failures.push({
      id: "end_screen_palette_contract.no_cross_episode_default_palette",
      detail: "contract uses fixed Challenger/default end-screen colors without a human-approved override",
    });
  }
  if (override) {
    const overrideData = contract.human_approved_override || {};
    if (!hasNonEmptyString(overrideData.reason)) {
      failures.push({ id: "end_screen_palette_contract.override.reason", detail: "human-approved override must record a reason" });
    }
    if (!Array.isArray(overrideData.affected_outputs) || overrideData.affected_outputs.length === 0) {
      failures.push({
        id: "end_screen_palette_contract.override.affected_outputs",
        detail: "human-approved override must name affected outputs",
      });
    }
  }
  return failures;
}

export function endScreenPalettePlayerFailures(html, contract = null) {
  const failures = [];
  const override = isHumanApprovedPaletteOverride(contract);
  const injectedRailBlock =
    String(html || "").match(/<!-- ce-rolling-caption-rail-tighten-style:start -->[\s\S]*?<!-- ce-rolling-caption-rail-tighten-script:end -->/)?.[0] ||
    String(html || "");
  const endScreenPaletteSurface = (
    injectedRailBlock.match(/--ce-end-screen[^;]+;|const\s+CE_END_SCREEN_PALETTE\s*=\s*[\s\S]*?;\n|window\.__endScreenPaletteContract\s*=\s*CE_END_SCREEN_PALETTE/gi) ||
    []
  ).join("\n");
  if (!/--ce-end-screen-target-fill|CE_END_SCREEN_PALETTE/i.test(injectedRailBlock)) {
    failures.push({
      id: "player.end_screen_palette_variables",
      detail: "player must expose end-screen palette CSS variables or CE_END_SCREEN_PALETTE",
    });
  }
  if (!override) {
    for (const forbidden of FORBIDDEN_DEFAULT_COLORS) {
      if (normalizeColor(endScreenPaletteSurface).includes(forbidden)) {
        failures.push({
          id: "player.no_fixed_challenger_end_screen_colors",
          detail: "player contains fixed Challenger/default end-screen colors without override",
        });
        break;
      }
    }
  }
  return failures;
}
