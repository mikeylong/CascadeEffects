#!/usr/bin/env node
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const restartRoot = "/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516";
const proofRoot = path.join(
  restartRoot,
  "youtube/rough_assembly/hyatt_living_cover_html_rough_proof_n6_subtle_tail_outro_20260519T040128Z",
);
const finalRenderRoot = path.join(proofRoot, "video_render/hyatt_longform_final_mp4_20260519T040222Z");
const proofManifestPath = path.join(proofRoot, "rough_assembly_manifest.json");
const finalRenderManifestPath = path.join(finalRenderRoot, "render_manifest.json");
const finalMp4Path = path.join(finalRenderRoot, "hyatt_regency_living_cover_final_review_1080p24.mp4");
const finalAssemblyReviewPath = path.join(finalRenderRoot, "review/final_assembly_review_packet.md");
const metadataManifestPath = path.join(
  restartRoot,
  "youtube/metadata/hyatt_metadata_copy_20260517T_upload_readiness/youtube_metadata_copy_manifest.json",
);
const metadataPacketPath = path.join(
  restartRoot,
  "youtube/metadata/hyatt_metadata_copy_20260517T_upload_readiness/youtube_metadata_copy_packet.md",
);
const sourceFactcheckManifestPath = path.join(
  restartRoot,
  "youtube/source_factcheck/hyatt_source_factcheck_packet_20260517T_upload_readiness/source_factcheck_manifest.json",
);
const sourceFactcheckReviewPath = path.join(
  restartRoot,
  "youtube/source_factcheck/hyatt_source_factcheck_packet_20260517T_upload_readiness/source_factcheck_review_packet.md",
);
const sourceArtManifestPath = path.join(
  restartRoot,
  "youtube/source_art/hyatt_living_cover_n6_architecture_crowd_density_20260517T083750Z/source_art_manifest.json",
);
const audioMixManifestPath = path.join(proofRoot, "references/audio_mix_manifest.json");
const transitionSamplePath = path.join(proofRoot, "qa/audio/vo_outro_subtle_tail_transition_20260519T040128Z.mp3");
const historicalInvalidatedPublishPath = path.join(
  restartRoot,
  "youtube/publish_readiness/hyatt_publish_readiness_20260519T031327Z/publish_readiness_manifest.json",
);

const REQUIRED_MUSIC_READS = [
  "vo_outro_blend_plan_read",
  "vo_outro_music_blend_read",
  "vo_outro_perceptual_review_read",
  "outro_transition_review_sample_read",
  "outro_entry_level_match_read",
  "outro_under_vo_masking_read",
  "outro_target_after_voice_read",
  "outro_prelap_source_read",
  "outro_prelap_start_read",
  "outro_no_restart_at_voice_end_read",
  "outro_source_continuity_read",
  "music_contract_regression_read",
];

function utcStamp(date = new Date()) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function parseArgs(argv) {
  const args = { mode: "lifecycle" };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (key === "--mode") {
      args.mode = argv[index + 1];
      index += 1;
      continue;
    }
    if (key === "--help" || key === "-h") {
      console.log("Usage: node scripts/build_hyatt_longform_publish_readiness.mjs [--mode lifecycle|publish-readiness]");
      process.exit(0);
    }
    throw new Error(`Unknown argument: ${key}`);
  }
  if (!["lifecycle", "publish-readiness"].includes(args.mode)) {
    throw new Error(`Unsupported mode: ${args.mode}`);
  }
  return args;
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function requireFile(filePath) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    throw new Error(`Missing required file: ${filePath}`);
  }
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function sha256(filePath) {
  const hash = createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

function bytes(filePath) {
  return fs.statSync(filePath).size;
}

function artifact(filePath, role = undefined) {
  const data = { path: filePath, sha256: sha256(filePath), bytes: bytes(filePath) };
  if (role) data.role = role;
  return data;
}

function copyArtifact(sourcePath, destPath, role = undefined) {
  requireFile(sourcePath);
  ensureDir(path.dirname(destPath));
  fs.copyFileSync(sourcePath, destPath);
  return artifact(destPath, role);
}

function copyIfExists(sourcePath, destPath, role = undefined) {
  if (!sourcePath || !fs.existsSync(sourcePath) || !fs.statSync(sourcePath).isFile()) return null;
  return copyArtifact(sourcePath, destPath, role);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function rel(from, to) {
  return path.relative(from, to).split(path.sep).join("/");
}

function readPasses(value) {
  return value === true || (typeof value === "string" && value.startsWith("pass"));
}

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".md") || filePath.endsWith(".txt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
  if (filePath.endsWith(".srt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".mp3")) return "audio/mpeg";
  if (filePath.endsWith(".mp4")) return "video/mp4";
  return "application/octet-stream";
}

function writeRangeServer(serverPath) {
  const serverSource = `import fs from "node:fs";
import http from "node:http";
import path from "node:path";

const root = process.cwd();
const port = Number(process.env.PORT || 8844);

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".json")) return "application/json; charset=utf-8";
  if (filePath.endsWith(".md") || filePath.endsWith(".txt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".png")) return "image/png";
  if (filePath.endsWith(".jpg") || filePath.endsWith(".jpeg")) return "image/jpeg";
  if (filePath.endsWith(".vtt")) return "text/vtt; charset=utf-8";
  if (filePath.endsWith(".srt")) return "text/plain; charset=utf-8";
  if (filePath.endsWith(".mp3")) return "audio/mpeg";
  if (filePath.endsWith(".mp4")) return "video/mp4";
  return "application/octet-stream";
}

function safePath(url) {
  const pathname = decodeURIComponent(String(url || "/").split("?")[0]);
  const relative = pathname === "/" ? "review.html" : pathname.replace(/^\\/+/, "");
  const candidate = path.resolve(root, relative);
  if (!candidate.startsWith(root + path.sep) && candidate !== root) return null;
  return candidate;
}

const server = http.createServer((req, res) => {
  const filePath = safePath(req.url);
  if (!filePath) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }
  fs.stat(filePath, (error, stat) => {
    if (error || !stat.isFile()) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    const headers = {
      "Content-Type": contentTypeFor(filePath),
      "Accept-Ranges": "bytes",
      "Access-Control-Allow-Origin": "*",
    };
    const range = req.headers.range;
    if (range) {
      const match = /^bytes=(\\d*)-(\\d*)$/.exec(range);
      if (!match) {
        res.writeHead(416, headers);
        res.end();
        return;
      }
      const start = match[1] ? Number(match[1]) : 0;
      const end = match[2] ? Math.min(Number(match[2]), stat.size - 1) : stat.size - 1;
      if (!Number.isFinite(start) || !Number.isFinite(end) || start > end || start >= stat.size) {
        res.writeHead(416, { ...headers, "Content-Range": \`bytes */\${stat.size}\` });
        res.end();
        return;
      }
      res.writeHead(206, {
        ...headers,
        "Content-Length": end - start + 1,
        "Content-Range": \`bytes \${start}-\${end}/\${stat.size}\`,
      });
      if (req.method === "HEAD") {
        res.end();
        return;
      }
      fs.createReadStream(filePath, { start, end }).pipe(res);
      return;
    }
    res.writeHead(200, { ...headers, "Content-Length": stat.size });
    if (req.method === "HEAD") {
      res.end();
      return;
    }
    fs.createReadStream(filePath).pipe(res);
  });
});

server.listen(port, "127.0.0.1", () => {
  console.log(\`serving \${root} at http://127.0.0.1:\${port}/review.html\`);
});
`;
  fs.writeFileSync(serverPath, serverSource, "utf8");
}

function publicCopyHasInternalTerms(metadata) {
  const terms = /\b(proof|render|sidecar|publish-readiness|publish readiness|long-form episode|package|review surface)\b/i;
  const publicText = [
    metadata.recommended_title,
    metadata.description,
    ...(metadata.hashtags || []),
    ...(metadata.tags || []),
    ...(metadata.chapters || []).map((chapter) => chapter.label),
  ].join("\n");
  return terms.test(publicText);
}

function stripRemoteReviewTitleSuffix(title) {
  return String(title || "").replace(/\s*\|\s*Cascade Effects\s*$/i, "").trim();
}

function tableRows(reads, keys) {
  return keys
    .map((key) => `<tr><th>${escapeHtml(key)}</th><td>${escapeHtml(reads[key] ?? "(missing)")}</td></tr>`)
    .join("\n");
}

function assertPublishReadinessGate(finalManifest, sourceFactcheckManifest, reads) {
  if (finalManifest.human_disposition !== "keep" || finalManifest.may_advance_to_publish_readiness !== true) {
    throw new Error("Publish-readiness refresh requires final assembly keep and may_advance_to_publish_readiness=true.");
  }
  if (sourceFactcheckManifest.status !== "verified_for_publish_readiness") {
    throw new Error(`Source/fact-check is not verified: ${sourceFactcheckManifest.status}`);
  }
  for (const read of REQUIRED_MUSIC_READS) {
    if (!readPasses(reads[read])) throw new Error(`Missing required passing music read: ${read}`);
  }
}

function buildPackage(mode) {
  for (const filePath of [
    proofManifestPath,
    finalRenderManifestPath,
    finalMp4Path,
    finalAssemblyReviewPath,
    metadataManifestPath,
    metadataPacketPath,
    sourceFactcheckManifestPath,
    sourceFactcheckReviewPath,
    sourceArtManifestPath,
    audioMixManifestPath,
    transitionSamplePath,
  ]) {
    requireFile(filePath);
  }

  const now = new Date().toISOString();
  const stamp = utcStamp();
  const stableLifecycle = mode === "lifecycle";
  const packageId = stableLifecycle ? "hyatt_publish_readiness_lifecycle" : `hyatt_publish_readiness_${stamp}`;
  const packageRoot = stableLifecycle
    ? path.join(restartRoot, "youtube/publish_readiness/hyatt_publish_readiness_lifecycle")
    : path.join(restartRoot, "youtube/publish_readiness", packageId);
  const mediaDir = path.join(packageRoot, "media");
  const captionDir = path.join(packageRoot, "captions");
  const qaDir = path.join(packageRoot, "qa_frames");
  const metadataDir = path.join(packageRoot, "metadata");
  const sourceDir = path.join(packageRoot, "source_factcheck");
  const thumbDir = path.join(packageRoot, "thumbnail");
  fs.rmSync(packageRoot, { recursive: true, force: true });
  ensureDir(packageRoot);

  const proofManifest = readJson(proofManifestPath);
  const finalManifest = readJson(finalRenderManifestPath);
  const metadataManifest = readJson(metadataManifestPath);
  const sourceFactcheckManifest = readJson(sourceFactcheckManifestPath);
  const sourceArtManifest = readJson(sourceArtManifestPath);
  const audioMixManifest = readJson(audioMixManifestPath);

  const reads = {
    ...(finalManifest.qa_reads || {}),
    ...(sourceFactcheckManifest.qa_reads || {}),
    ...(metadataManifest.qa_reads || {}),
    ...(audioMixManifest.reads || {}),
  };
  reads.lifecycle_review_html_read = "pass_always_on_review_html_created";
  reads.lifecycle_upload_lock_read = "pass_upload_and_public_release_locked";
  reads.lifecycle_final_assembly_gate_read = finalManifest.human_disposition === "keep"
    ? "pass_final_assembly_keep_recorded"
    : "blocked_pending_final_assembly_keep";

  const publicMetadataInternalTerms = publicCopyHasInternalTerms(metadataManifest);
  reads.metadata_public_copy_read = publicMetadataInternalTerms
    ? "reject_internal_terms_in_public_metadata"
    : "pass_no_internal_terms_in_public_metadata";
  if (!stableLifecycle) assertPublishReadinessGate(finalManifest, sourceFactcheckManifest, reads);
  if (!stableLifecycle && reads.metadata_public_copy_read.startsWith("reject")) {
    throw new Error("Public metadata contains internal terms.");
  }

  const localMp4 = path.join(mediaDir, "hyatt_regency_living_cover_final_review_1080p24.mp4");
  const localVtt = path.join(captionDir, "hyatt_regency_longform.script_locked_rail_safe.offset_intro_9s601.vtt");
  const localSrt = path.join(captionDir, "hyatt_regency_longform.script_locked_rail_safe.offset_intro_9s601.srt");
  const localTransitionSample = path.join(mediaDir, "vo_outro_subtle_tail_transition_20260519T040128Z.mp3");
  const localFinalManifest = path.join(packageRoot, "render_manifest.json");
  const localProofManifest = path.join(packageRoot, "rough_assembly_manifest.json");
  const localFinalAssemblyReview = path.join(packageRoot, "final_assembly_review_packet.md");
  const localMetadataManifest = path.join(metadataDir, "youtube_metadata_copy_manifest.json");
  const localMetadataPacket = path.join(metadataDir, "youtube_metadata_copy_packet.md");
  const localSourceFactcheckManifest = path.join(sourceDir, "source_factcheck_manifest.json");
  const localSourceFactcheckReview = path.join(sourceDir, "source_factcheck_review_packet.md");
  const localAudioMixManifest = path.join(mediaDir, "audio_mix_manifest.json");
  const localThumbnail = path.join(thumbDir, "hyatt_thumbnail_candidate_source_art_n6.png");

  const copied = {
    final_mp4: copyArtifact(finalMp4Path, localMp4, stableLifecycle ? "current_final_assembly_review_artifact_not_upload_candidate" : "final_mp4_upload_review_candidate"),
    youtube_upload_vtt: copyArtifact(
      path.join(finalRenderRoot, "youtube_sidecars/hyatt_regency_longform.script_locked_rail_safe.offset_intro_9s601.vtt"),
      localVtt,
      "youtube_caption_sidecar_vtt",
    ),
    youtube_upload_srt: copyArtifact(
      path.join(finalRenderRoot, "youtube_sidecars/hyatt_regency_longform.script_locked_rail_safe.offset_intro_9s601.srt"),
      localSrt,
      "youtube_caption_sidecar_srt",
    ),
    transition_sample_mp3: copyArtifact(transitionSamplePath, localTransitionSample, "vo_outro_transition_review_sample"),
    render_manifest: copyArtifact(finalRenderManifestPath, localFinalManifest, "final_render_manifest_copy"),
    rough_assembly_manifest: copyArtifact(proofManifestPath, localProofManifest, "rough_assembly_manifest_copy"),
    final_assembly_review: copyArtifact(finalAssemblyReviewPath, localFinalAssemblyReview, "final_assembly_review_packet_copy"),
    metadata_manifest: copyArtifact(metadataManifestPath, localMetadataManifest, "metadata_copy_manifest"),
    metadata_packet: copyArtifact(metadataPacketPath, localMetadataPacket, "metadata_copy_packet"),
    source_factcheck_manifest: copyArtifact(sourceFactcheckManifestPath, localSourceFactcheckManifest, "source_factcheck_manifest"),
    source_factcheck_review: copyArtifact(sourceFactcheckReviewPath, localSourceFactcheckReview, "source_factcheck_review_packet"),
    audio_mix_manifest: copyArtifact(audioMixManifestPath, localAudioMixManifest, "audio_mix_manifest_copy"),
    thumbnail_candidate: copyArtifact(sourceArtManifest.source_art_path, localThumbnail, "thumbnail_candidate_source_art"),
  };

  const frameSources = [
    "mp4_qa_0000p000_intro.jpg",
    "mp4_qa_0009p601_voice_start.jpg",
    "mp4_qa_0091p840_first_boundary_ease.jpg",
    "mp4_qa_0175p500_live_load_01.jpg",
    "mp4_qa_0444p000_live_load_02.jpg",
    "mp4_qa_0843p244_outro_start.jpg",
    "mp4_qa_0870p000_end_screen_hold.jpg",
  ];
  const qaFrames = {};
  for (const frameName of frameSources) {
    const frame = copyIfExists(path.join(finalRenderRoot, "qa/frames", frameName), path.join(qaDir, frameName), "qa_frame");
    if (frame) qaFrames[frameName] = frame;
  }

  const youtubeMetadata = {
    title: stripRemoteReviewTitleSuffix(metadataManifest.recommended_title),
    description: metadataManifest.description,
    chapters: metadataManifest.chapters,
    tags: metadataManifest.tags,
    hashtags: metadataManifest.hashtags,
    category: "Education",
    language: "en",
    made_for_kids: false,
    paid_promotion: false,
    review_upload_privacy_after_approval: "unlisted_after_explicit_approval_only",
    public_release_policy: "manual_only",
  };
  const youtubeMetadataPath = path.join(packageRoot, "youtube_metadata.json");
  writeJson(youtubeMetadataPath, youtubeMetadata);

  const historicalInvalidatedPages = fs.existsSync(historicalInvalidatedPublishPath)
    ? [
        {
          manifest_path: historicalInvalidatedPublishPath,
          manifest_sha256: sha256(historicalInvalidatedPublishPath),
          status: readJson(historicalInvalidatedPublishPath).status,
          role: "historical_tighten_reference_only_not_current_review_surface",
        },
      ]
    : [];

  const uploadLocks = {
    publish_ready: false,
    youtube_upload_ready: false,
    public_release_ready: false,
    may_youtube_action: false,
    upload_performed: false,
    upload_action_enabled_in_review_html: false,
    review_upload_privacy_after_approval: "unlisted_after_publish_readiness_keep_and_explicit_upload_approval",
    private_youtube_upload: false,
    public_release: false,
  };
  const blockers = stableLifecycle
    ? [
        "Final assembly human keep is required before this lifecycle page can become a publish-readiness package.",
        "Publish-readiness human keep is required before any YouTube review upload.",
        "Explicit upload authorization is required after publish-readiness keep.",
        "YouTube Content ID/music claim status must be checked after upload processing.",
        "Public release remains manual.",
      ]
    : [
        "Publish-readiness human keep is required before any YouTube review upload.",
        "Explicit upload authorization is required after publish-readiness keep.",
        "YouTube Content ID/music claim status must be checked after upload processing.",
        "Public release remains manual.",
      ];

  const publishManifest = {
    packet_id: packageId,
    review_id: "hyatt-regency",
    episode_id: "hyatt-regency",
    lifecycle_stage: stableLifecycle ? "in_progress" : "publish_readiness",
    stage: stableLifecycle ? "publish_readiness_lifecycle_review" : "publish_readiness",
    current_gate: stableLifecycle ? "final_assembly_review" : "publish_readiness_review",
    status: stableLifecycle
      ? "in_progress_blocked_pending_final_assembly_keep"
      : "review_ready_pending_human_publish_readiness_keep",
    human_disposition: stableLifecycle ? "defer" : "pending",
    final_assembly_disposition: finalManifest.human_disposition || "pending",
    created_utc: now,
    primary_review_artifact: {
      path: "review.html",
      sha256: "TBD",
      bytes: 0,
    },
    review_surface_type: "html_inline_media_local_refs",
    publish_readiness_review_html_path: path.join(packageRoot, "review.html"),
    publish_readiness_review_html_sha256: "TBD",
    publish_readiness_canonical_review_url: "http://127.0.0.1:8844/review.html",
    review_server: {
      type: "byte_range_capable_local_http",
      script_path: "range_static_server.mjs",
      url: "http://127.0.0.1:8844/review.html",
      range_probe_status: "pending",
    },
    remote_review: {
      status: "not_published",
      review_id: "hyatt-regency",
      remote_review_url: "https://cascadeeffects.tv/reviews/publish-readiness/hyatt-regency",
      route: "/reviews/publish-readiness/[reviewId]",
      site_visibility: "unlisted_noindex",
      storage_policy: "normalized_manifest_and_small_evidence_assets_only",
      large_video_upload_allowed: false,
      video_host: "youtube_unlisted_after_explicit_approval_only",
    },
    current_review_artifact: {
      role: stableLifecycle ? "current_final_assembly_review_artifact_not_upload_candidate" : "final_publish_readiness_review_artifact",
      final_assembly_human_disposition: finalManifest.human_disposition || "pending",
      mp4_path: rel(packageRoot, localMp4),
      mp4_sha256: copied.final_mp4.sha256,
      source_mp4_path: finalMp4Path,
      source_mp4_sha256: sha256(finalMp4Path),
    },
    source_final_render: {
      manifest_path: finalRenderManifestPath,
      manifest_sha256: sha256(finalRenderManifestPath),
      mp4_path: finalMp4Path,
      mp4_sha256: sha256(finalMp4Path),
    },
    local_assets: {
      mp4: { ...copied.final_mp4, rel: rel(packageRoot, localMp4) },
      vtt: { ...copied.youtube_upload_vtt, rel: rel(packageRoot, localVtt) },
      srt: { ...copied.youtube_upload_srt, rel: rel(packageRoot, localSrt) },
      thumbnail_candidate: { ...copied.thumbnail_candidate, rel: rel(packageRoot, localThumbnail) },
      vo_outro_transition_sample_mp3: { ...copied.transition_sample_mp3, rel: rel(packageRoot, localTransitionSample) },
      qa_frames: Object.fromEntries(
        Object.entries(qaFrames).map(([name, frame]) => [name, { ...frame, rel: rel(packageRoot, frame.path) }]),
      ),
    },
    media: {
      final_mp4: { path: rel(packageRoot, localMp4), sha256: copied.final_mp4.sha256, bytes: copied.final_mp4.bytes },
      caption_vtt: { path: rel(packageRoot, localVtt), sha256: copied.youtube_upload_vtt.sha256, bytes: copied.youtube_upload_vtt.bytes },
      caption_srt: { path: rel(packageRoot, localSrt), sha256: copied.youtube_upload_srt.sha256, bytes: copied.youtube_upload_srt.bytes },
      thumbnail_candidate: { path: rel(packageRoot, localThumbnail), sha256: copied.thumbnail_candidate.sha256, bytes: copied.thumbnail_candidate.bytes },
      vo_outro_transition_sample: { path: rel(packageRoot, localTransitionSample), sha256: copied.transition_sample_mp3.sha256, bytes: copied.transition_sample_mp3.bytes },
    },
    youtube_metadata: {
      manifest_path: localMetadataManifest,
      manifest_sha256: sha256(localMetadataManifest),
      public_metadata_path: youtubeMetadataPath,
      public_metadata_sha256: sha256(youtubeMetadataPath),
      title: youtubeMetadata.title,
      description: youtubeMetadata.description,
      chapters: youtubeMetadata.chapters,
      tags: youtubeMetadata.tags,
      hashtags: youtubeMetadata.hashtags,
    },
    source_factcheck: {
      status: sourceFactcheckManifest.status,
      manifest_path: localSourceFactcheckManifest,
      manifest_sha256: sha256(localSourceFactcheckManifest),
      review_packet_path: localSourceFactcheckReview,
      review_packet_sha256: sha256(localSourceFactcheckReview),
      rights_and_usage_notes: sourceFactcheckManifest.rights_and_usage_notes,
    },
    music_integration_contract: {
      audio_mix_manifest_path: localAudioMixManifest,
      audio_mix_manifest_sha256: sha256(localAudioMixManifest),
      source_audio_mix_manifest_path: audioMixManifestPath,
      source_audio_mix_manifest_sha256: sha256(audioMixManifestPath),
      vo_outro_blend_plan: audioMixManifest.vo_outro_blend_plan,
      outro_transition_review_sample: {
        mp3: { path: rel(packageRoot, localTransitionSample), sha256: copied.transition_sample_mp3.sha256 },
      },
      reads: audioMixManifest.reads,
    },
    historical_invalidated_publish_readiness_pages: historicalInvalidatedPages,
    required_reads: stableLifecycle
      ? [
          "lifecycle_review_html_read",
          "lifecycle_upload_lock_read",
          "lifecycle_final_assembly_gate_read",
          "html_primary_review_read",
          "html_media_refs_read",
          "html_range_server_read",
          "html_upload_lock_read",
        ]
      : [
          ...REQUIRED_MUSIC_READS,
          "final_assembly_human_keep_read",
          "source_factcheck_status_read",
          "metadata_public_copy_read",
          "final_mp4_packaged_read",
          "caption_sidecar_packaged_read",
          "html_publish_readiness_review_read",
          "upload_lock_state_read",
        ],
    reads: {
      ...reads,
      html_primary_review_read: "pass_review_html_created_as_primary_lifecycle_artifact",
      html_media_refs_read: "pass_package_local_relative_media_refs",
      html_range_server_read: "pending_http_range_probe",
      html_canonical_review_url_read: "pending_http_review_url",
      html_upload_lock_read: "pass_upload_locks_visible_and_false",
      final_assembly_human_keep_read: finalManifest.human_disposition === "keep" ? "pass" : "blocked_pending_final_assembly_keep",
      source_factcheck_status_read: sourceFactcheckManifest.status === "verified_for_publish_readiness"
        ? "pass_verified_for_publish_readiness"
        : `blocked_${sourceFactcheckManifest.status || "missing_source_factcheck_status"}`,
      final_mp4_packaged_read: "pass",
      caption_sidecar_packaged_read: "pass_vtt_and_srt_packaged",
      html_publish_readiness_review_read: stableLifecycle
        ? "pass_lifecycle_review_html_created_not_publish_ready"
        : "pass_publish_readiness_review_html_created",
      upload_lock_state_read: "pass_upload_and_public_release_locked",
    },
    blockers,
    locks: uploadLocks,
    upload_locks: uploadLocks,
    may_youtube_action: false,
    may_advance_to_upload: false,
    next_review_question: stableLifecycle
      ? "Review the current final assembly artifact. Publish readiness remains blocked until final assembly keep."
      : "Review publish readiness and reply with exactly one disposition: keep, tighten, or reject.",
  };

  const manifestPath = path.join(packageRoot, "publish_readiness_manifest.json");
  writeJson(manifestPath, publishManifest);

  const qaKeys = [
    "lifecycle_review_html_read",
    "lifecycle_final_assembly_gate_read",
    "full_decode_read",
    "dimensions_read",
    "fps_read",
    "video_stream_read",
    "audio_stream_read",
    "caption_sidecar_read",
    "visible_rail_captions_burned_in_read",
    "youtube_end_screen_template_read",
    "vo_outro_blend_plan_read",
    "outro_prelap_start_read",
    "outro_no_restart_at_voice_end_read",
    "metadata_public_copy_read",
    "source_factcheck_status_read",
    "upload_lock_state_read",
  ];
  const chapterHtml = (metadataManifest.chapters || [])
    .map((chapter) => `<li><span>${escapeHtml(chapter.time)}</span> ${escapeHtml(chapter.label)}</li>`)
    .join("\n");
  const frameHtml = Object.entries(qaFrames)
    .map(([name, frame]) => `<figure><img src="${escapeHtml(rel(packageRoot, frame.path))}" alt="${escapeHtml(name)}"><figcaption>${escapeHtml(name)}</figcaption></figure>`)
    .join("\n");
  const tagHtml = (metadataManifest.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
  const sourceRows = Object.entries(sourceFactcheckManifest.primary_sources || {})
    .map(([, source]) => `<tr><th>${escapeHtml(source.title)}</th><td><a href="${escapeHtml(source.url)}">${escapeHtml(source.url)}</a></td></tr>`)
    .join("\n");
  const blockerHtml = blockers.map((blocker) => `<li>${escapeHtml(blocker)}</li>`).join("\n");
  const lifecycleLabel = stableLifecycle ? "In-Progress Lifecycle Review" : "Publish Readiness Review";
  const gateCopy = stableLifecycle
    ? "This page is the stable publish-readiness lifecycle surface. It is not upload-ready because final assembly is still pending human keep."
    : "This page is a publish-readiness package awaiting human disposition. Upload remains locked until a later explicit approval.";
  const reviewHtmlPath = path.join(packageRoot, "review.html");
  const reviewHtml = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Hyatt Regency ${escapeHtml(lifecycleLabel)}</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #12100e; color: #f3eadf; }
    body { margin: 0; background: #12100e; }
    main { max-width: 1180px; margin: 0 auto; padding: 32px 24px 64px; }
    h1, h2, h3 { margin: 0 0 14px; line-height: 1.05; }
    h1 { font-size: 34px; }
    h2 { font-size: 22px; margin-top: 34px; }
    p, li, td, th { color: #d8ccbd; line-height: 1.48; }
    .grid { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.75fr); gap: 22px; align-items: start; }
    video, img { max-width: 100%; border-radius: 6px; background: #050505; }
    section, .panel { border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.045); border-radius: 8px; padding: 18px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border-top: 1px solid rgba(255,255,255,.10); padding: 8px 6px; text-align: left; vertical-align: top; }
    th { color: #f5dfbd; width: 34%; font-weight: 700; }
    pre { white-space: pre-wrap; color: #f2e8d8; background: rgba(0,0,0,.28); border-radius: 6px; padding: 14px; overflow-wrap: anywhere; }
    .tags { display: flex; flex-wrap: wrap; gap: 8px; }
    .tags span { border: 1px solid rgba(255,255,255,.18); border-radius: 999px; padding: 5px 9px; color: #ead8c3; }
    .frames { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
    figure { margin: 0; }
    figcaption { color: #ad9f91; font-size: 12px; margin-top: 6px; overflow-wrap: anywhere; }
    .lock { color: #f0c38f; font-weight: 700; }
    .blocked { color: #ffcf96; }
    .status { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 18px 0 22px; }
    .status div { border: 1px solid rgba(255,255,255,.12); border-radius: 8px; padding: 12px; background: rgba(0,0,0,.22); }
    .status strong { display: block; color: #fff4df; margin-bottom: 4px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } main { padding: 20px 14px 48px; } }
  </style>
</head>
<body>
<main>
  <h1>Hyatt Regency ${escapeHtml(lifecycleLabel)}</h1>
  <p>${escapeHtml(gateCopy)} <span class="lock">Upload and public release remain locked.</span></p>

  <div class="status">
    <div><strong>Lifecycle stage</strong>${escapeHtml(publishManifest.lifecycle_stage)}</div>
    <div><strong>Current gate</strong>${escapeHtml(publishManifest.current_gate)}</div>
    <div><strong>Final assembly disposition</strong>${escapeHtml(publishManifest.final_assembly_disposition)}</div>
    <div><strong>YouTube action</strong>unavailable</div>
  </div>

  <div class="grid">
    <section>
      <h2>Current Review Artifact</h2>
      <video src="${escapeHtml(rel(packageRoot, localMp4))}" controls preload="metadata" poster="${escapeHtml(rel(packageRoot, localThumbnail))}">
        <track kind="captions" src="${escapeHtml(rel(packageRoot, localVtt))}" srclang="en" label="English">
      </video>
      <table>
        <tr><th>Role</th><td>${escapeHtml(publishManifest.current_review_artifact.role)}</td></tr>
        <tr><th>MP4 SHA-256</th><td>${escapeHtml(copied.final_mp4.sha256)}</td></tr>
        <tr><th>Manifest</th><td><a href="publish_readiness_manifest.json">publish_readiness_manifest.json</a></td></tr>
        <tr><th>Captions</th><td><a href="${escapeHtml(rel(packageRoot, localVtt))}">VTT</a> / <a href="${escapeHtml(rel(packageRoot, localSrt))}">SRT</a></td></tr>
        <tr><th>Transition sample</th><td><audio controls src="${escapeHtml(rel(packageRoot, localTransitionSample))}"></audio></td></tr>
      </table>
    </section>
    <section>
      <h2>Thumbnail Candidate</h2>
      <img src="${escapeHtml(rel(packageRoot, localThumbnail))}" alt="Hyatt thumbnail candidate">
      <p>Candidate only. Final thumbnail selection remains a review decision.</p>
    </section>
  </div>

  <section>
    <h2>Blockers</h2>
    <ul class="blocked">${blockerHtml}</ul>
  </section>

  <section>
    <h2>YouTube Metadata</h2>
    <h3>${escapeHtml(metadataManifest.recommended_title)}</h3>
    <pre>${escapeHtml(metadataManifest.description)}</pre>
    <h3>Chapters</h3>
    <ol>${chapterHtml}</ol>
    <h3>Tags</h3>
    <div class="tags">${tagHtml}</div>
  </section>

  <section>
    <h2>Source Notes</h2>
    <table>${sourceRows}</table>
  </section>

  <section>
    <h2>QA Reads</h2>
    <table>${tableRows(publishManifest.reads, qaKeys)}</table>
  </section>

  <section>
    <h2>QA Frames</h2>
    <div class="frames">${frameHtml}</div>
  </section>

  <section>
    <h2>Locks</h2>
    <table>
      <tr><th>publish_ready</th><td>${publishManifest.upload_locks.publish_ready}</td></tr>
      <tr><th>youtube_upload_ready</th><td>${publishManifest.upload_locks.youtube_upload_ready}</td></tr>
      <tr><th>may_youtube_action</th><td>${publishManifest.upload_locks.may_youtube_action}</td></tr>
      <tr><th>upload_performed</th><td>${publishManifest.upload_locks.upload_performed}</td></tr>
      <tr><th>public release</th><td>manual only</td></tr>
    </table>
  </section>
</main>
</body>
</html>
`;
  fs.writeFileSync(reviewHtmlPath, reviewHtml, "utf8");

  const serverPath = path.join(packageRoot, "range_static_server.mjs");
  writeRangeServer(serverPath);

  publishManifest.primary_review_artifact = {
    path: "review.html",
    sha256: sha256(reviewHtmlPath),
    bytes: bytes(reviewHtmlPath),
  };
  publishManifest.publish_readiness_review_html_sha256 = sha256(reviewHtmlPath);
  publishManifest.review_html = artifact(reviewHtmlPath, "primary_publish_readiness_lifecycle_review_html");
  publishManifest.review_url = "http://127.0.0.1:8844/review.html";
  publishManifest.range_static_server = artifact(serverPath, "byte_range_static_review_server");
  writeJson(manifestPath, publishManifest);

  console.log(
    JSON.stringify(
      {
        mode,
        packageRoot,
        reviewHtmlPath,
        manifestPath,
        reviewUrl: "http://127.0.0.1:8844/review.html",
        finalMp4: localMp4,
        status: publishManifest.status,
        finalAssemblyDisposition: publishManifest.final_assembly_disposition,
        uploadLocks,
      },
      null,
      2,
    ),
  );
}

buildPackage(parseArgs(process.argv.slice(2)).mode);
