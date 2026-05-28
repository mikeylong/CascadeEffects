#!/usr/bin/env node
import { put } from '@vercel/blob';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const VIDEO_EXTENSIONS = new Set(['.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm']);
const DEFAULT_SITE_URL = 'https://cascadeeffects.tv';
const DEFAULT_MAX_REMOTE_ASSET_BYTES = 25 * 1024 * 1024;
const VALIDATION_MODES = new Set(['inception', 'in_progress', 'publish_readiness']);
const BANNED_VIDEO_TITLE_SUFFIX = '| Cascade Effects';

const UNLISTED_ACCESS_NOTE =
  'This unlisted YouTube review video can be viewed by anyone with the link. Keep the cascadeeffects.tv URL and YouTube watch URL limited to reviewers.';

function parseArgs(argv) {
  const args = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) {
      args._.push(value);
      continue;
    }

    const key = value.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith('--')) {
      args[key] = true;
    } else {
      args[key] = next;
      index += 1;
    }
  }
  return args;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function maybeReadJson(filePath) {
  try {
    return readJson(filePath);
  } catch {
    return null;
  }
}

function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function sha256Text(text) {
  const hash = crypto.createHash('sha256');
  hash.update(text);
  return hash.digest('hex');
}

function isRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function stringValue(value, fallback = '') {
  return typeof value === 'string' ? value : fallback;
}

function booleanValue(value, fallback = false) {
  return typeof value === 'boolean' ? value : fallback;
}

function numberValue(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function cleanArray(value) {
  return Array.isArray(value) ? value.filter((item) => typeof item === 'string') : [];
}

function sanitizeId(value) {
  return String(value || '')
    .trim()
    .replace(/[^a-zA-Z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 96);
}

function normalizeMode(value) {
  const mode = String(value || 'publish-readiness').trim().replace(/-/g, '_');
  if (mode === 'publish') return 'publish_readiness';
  if (mode === 'publish_readiness') return 'publish_readiness';
  if (mode === 'in_progress') return 'in_progress';
  if (mode === 'inception') return 'inception';
  throw new Error('Invalid --mode. Use --mode inception or --mode publish-readiness.');
}

function lifecycleStageFromManifest(manifest, fallbackMode) {
  const remoteReview = isRecord(manifest.remote_review) ? manifest.remote_review : {};
  const raw =
    stringValue(manifest.lifecycleStage) ||
    stringValue(manifest.lifecycle_stage) ||
    stringValue(manifest.review_lifecycle_stage) ||
    stringValue(remoteReview.lifecycleStage) ||
    stringValue(remoteReview.lifecycle_stage) ||
    fallbackMode;
  const stage = raw.trim().replace(/-/g, '_');
  return VALIDATION_MODES.has(stage) ? stage : fallbackMode;
}

function resolvePacketInput(packetInput) {
  if (!packetInput) throw new Error('Missing --packet <publish-readiness-dir-or-manifest>.');
  const resolved = path.resolve(packetInput);
  const stat = fs.statSync(resolved);
  if (stat.isDirectory()) {
    const manifestPath = path.join(resolved, 'publish_readiness_manifest.json');
    if (!fs.existsSync(manifestPath)) {
      throw new Error(`No publish_readiness_manifest.json found in ${resolved}`);
    }
    return { packetRoot: resolved, manifestPath };
  }
  return { packetRoot: path.dirname(resolved), manifestPath: resolved };
}

function walkFiles(root, predicate, depth = 4) {
  const results = [];
  function visit(current, remainingDepth) {
    if (remainingDepth < 0) return;
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const next = path.join(current, entry.name);
      if (entry.isDirectory()) {
        visit(next, remainingDepth - 1);
      } else if (entry.isFile() && predicate(next)) {
        results.push(next);
      }
    }
  }
  visit(root, depth);
  return results.sort();
}

function findYoutubeReviewReceipt(packetRoot, explicitReceiptPath) {
  if (explicitReceiptPath) {
    const resolved = path.resolve(explicitReceiptPath);
    if (!fs.existsSync(resolved)) throw new Error(`YouTube review upload/status receipt not found: ${resolved}`);
    return resolved;
  }
  const matches = walkFiles(
    packetRoot,
    (filePath) => {
      const base = path.basename(filePath).toLowerCase();
      return base.endsWith('.json') && base.includes('youtube') && base.includes('receipt');
    },
    2,
  );
  return matches[0] ?? '';
}

function pathFromArtifact(artifact) {
  if (!isRecord(artifact)) return '';
  return stringValue(artifact.path) || stringValue(artifact.rel) || stringValue(artifact.url);
}

function localAsset(packetRoot, artifact, label, kind) {
  if (!artifact) return null;
  const rawPath = typeof artifact === 'string' ? artifact : pathFromArtifact(artifact);
  if (!rawPath || /^https?:\/\//.test(rawPath)) return null;
  const resolved = path.isAbsolute(rawPath) ? rawPath : path.resolve(packetRoot, rawPath);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) return null;
  const stat = fs.statSync(resolved);
  const record = isRecord(artifact) ? artifact : {};
  return {
    label,
    kind,
    path: resolved,
    url: '',
    sha256: stringValue(record.sha256) || sha256File(resolved),
    bytes: numberValue(record.bytes) ?? stat.size,
    mimeType: mimeTypeFor(resolved),
  };
}

function mimeTypeFor(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  if (extension === '.json') return 'application/json; charset=utf-8';
  if (extension === '.md' || extension === '.txt') return 'text/plain; charset=utf-8';
  if (extension === '.vtt') return 'text/vtt; charset=utf-8';
  if (extension === '.srt') return 'text/plain; charset=utf-8';
  if (extension === '.png') return 'image/png';
  if (extension === '.jpg' || extension === '.jpeg') return 'image/jpeg';
  if (extension === '.webp') return 'image/webp';
  if (extension === '.mp3') return 'audio/mpeg';
  if (extension === '.m4a') return 'audio/mp4';
  if (extension === '.wav') return 'audio/wav';
  return 'application/octet-stream';
}

function parseTimestampToSeconds(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, value);
  const text = String(value || '').trim();
  if (!text) return 0;
  if (/^\d+(\.\d+)?$/.test(text)) return Number(text);
  const parts = text.split(':').map((part) => Number(part));
  if (parts.some((part) => !Number.isFinite(part))) return 0;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return 0;
}

function youtubeWatchUrl(videoId) {
  return videoId ? `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}` : '';
}

function youtubeEmbedUrl(videoId) {
  return videoId
    ? `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?enablejsapi=1&rel=0&modestbranding=1&playsinline=1`
    : '';
}

function hasBannedVideoTitleSuffix(value) {
  return String(value || '').includes(BANNED_VIDEO_TITLE_SUFFIX);
}

function videoStatusFromReceipt(receipt) {
  const youtube = isRecord(receipt?.youtube) ? receipt.youtube : {};
  const status = isRecord(youtube.status) ? youtube.status : {};
  const afterStatus = isRecord(receipt?.after) ? receipt.after : {};
  const verification = isRecord(receipt?.verification) ? receipt.verification : {};
  const verificationAfter = isRecord(verification.after) ? verification.after : {};
  const topStatus = isRecord(receipt?.status) ? receipt.status : {};
  const updateResponse = isRecord(receipt?.update_response) ? receipt.update_response : {};
  const updateStatus = isRecord(updateResponse.status) ? updateResponse.status : {};
  const statusSource =
    Object.keys(status).length > 0
      ? status
      : Object.keys(afterStatus).length > 0
        ? afterStatus
        : Object.keys(verificationAfter).length > 0
          ? verificationAfter
          : topStatus;
  const rawStatus = isRecord(statusSource.raw_response) ? statusSource.raw_response : {};
  const firstItem = Array.isArray(rawStatus.items) && isRecord(rawStatus.items[0]) ? rawStatus.items[0] : {};
  const itemStatus = isRecord(firstItem.status) ? firstItem.status : {};
  const itemSnippet = isRecord(firstItem.snippet) ? firstItem.snippet : {};
  const itemLocalized = isRecord(itemSnippet.localized) ? itemSnippet.localized : {};
  return {
    videoId: stringValue(youtube.video_id) || stringValue(statusSource.video_id) || stringValue(receipt?.video_id),
    watchUrl: stringValue(youtube.video_url) || stringValue(statusSource.video_url) || stringValue(receipt?.video_url),
    title:
      stringValue(receipt?.new_title) ||
      stringValue(statusSource.title) ||
      stringValue(itemLocalized.title) ||
      stringValue(itemSnippet.title),
    privacyStatus: stringValue(statusSource.privacy_status) || stringValue(updateStatus.privacyStatus) || stringValue(receipt?.privacy),
    processingStatus: stringValue(statusSource.processing_status),
    uploadStatus: stringValue(statusSource.upload_status) || stringValue(itemStatus.uploadStatus),
    embeddable: booleanValue(itemStatus.embeddable, booleanValue(updateStatus.embeddable, true)),
    channelId: stringValue(youtube.channel_id) || stringValue(statusSource.channel_id),
    channelTitle: stringValue(youtube.channel_title) || stringValue(statusSource.channel_title),
  };
}

function videoStatusFromManifest(manifest) {
  const source =
    (isRecord(manifest.youtube_review) && manifest.youtube_review) ||
    (isRecord(manifest.youtube_unlisted_review) && manifest.youtube_unlisted_review) ||
    (isRecord(manifest.youtube_private_review) && manifest.youtube_private_review) ||
    (isRecord(manifest.youtube_private_review_upload) && manifest.youtube_private_review_upload) ||
    {};
  return {
    videoId: stringValue(source.video_id) || stringValue(source.videoId),
    watchUrl: stringValue(source.video_url) || stringValue(source.watchUrl),
    title: stringValue(source.title),
    privacyStatus: stringValue(source.privacy_status) || stringValue(source.privacyStatus),
    processingStatus: stringValue(source.processing_status) || stringValue(source.processingStatus),
    uploadStatus: stringValue(source.upload_status) || stringValue(source.uploadStatus),
    embeddable: booleanValue(source.embeddable, true),
    channelId: stringValue(source.channel_id) || stringValue(source.channelId),
    channelTitle: stringValue(source.channel_title) || stringValue(source.channelTitle),
  };
}

function normalizeYoutubeReview({ manifest, packetRoot, receiptPath }) {
  const receipt = receiptPath ? maybeReadJson(receiptPath) : null;
  const fromReceipt = receipt ? videoStatusFromReceipt(receipt) : {};
  const fromManifest = videoStatusFromManifest(manifest);
  const videoId = fromReceipt.videoId || fromManifest.videoId;
  if (!videoId) return null;

  const watchUrl = fromReceipt.watchUrl || fromManifest.watchUrl || youtubeWatchUrl(videoId);
  const receiptSha256 = receiptPath && fs.existsSync(receiptPath) ? sha256File(receiptPath) : '';
  const receiptRel = receiptPath ? path.relative(packetRoot, receiptPath) : '';

  return {
    host: 'youtube_unlisted',
    videoId,
    watchUrl,
    embedUrl: youtubeEmbedUrl(videoId),
    title: fromReceipt.title || fromManifest.title,
    privacyStatus: fromReceipt.privacyStatus || fromManifest.privacyStatus,
    processingStatus: fromReceipt.processingStatus || fromManifest.processingStatus,
    uploadStatus: fromReceipt.uploadStatus || fromManifest.uploadStatus,
    embeddable: typeof fromReceipt.embeddable === 'boolean' ? fromReceipt.embeddable : fromManifest.embeddable,
    receiptPath:
      receiptPath ||
      stringValue(manifest.youtube_review?.receipt_path) ||
      stringValue(manifest.youtube_review?.receiptPath) ||
      stringValue(manifest.youtube_review?.receipt?.path) ||
      stringValue(manifest.youtube_unlisted_review?.receipt_path) ||
      stringValue(manifest.youtube_unlisted_review?.receiptPath) ||
      stringValue(manifest.youtube_unlisted_review?.receipt?.path) ||
      stringValue(manifest.youtube_private_review?.receipt_path) ||
      stringValue(manifest.youtube_private_review?.receiptPath) ||
      stringValue(manifest.youtube_private_review?.receipt?.path) ||
      stringValue(manifest.youtube_private_review_upload?.receipt?.path),
    receiptRelativePath: receiptRel,
    receiptSha256:
      receiptSha256 ||
      stringValue(manifest.youtube_review?.receipt_sha256) ||
      stringValue(manifest.youtube_review?.receiptSha256) ||
      stringValue(manifest.youtube_review?.receipt?.sha256) ||
      stringValue(manifest.youtube_unlisted_review?.receipt_sha256) ||
      stringValue(manifest.youtube_unlisted_review?.receiptSha256) ||
      stringValue(manifest.youtube_unlisted_review?.receipt?.sha256) ||
      stringValue(manifest.youtube_private_review?.receipt_sha256) ||
      stringValue(manifest.youtube_private_review?.receiptSha256) ||
      stringValue(manifest.youtube_private_review?.receipt?.sha256) ||
      stringValue(manifest.youtube_private_review_upload?.receipt?.sha256),
    channelId: fromReceipt.channelId || fromManifest.channelId,
    channelTitle: fromReceipt.channelTitle || fromManifest.channelTitle,
    accessNote: UNLISTED_ACCESS_NOTE,
  };
}

function normalizeChapters(chapters) {
  if (!Array.isArray(chapters)) return [];
  return chapters
    .map((chapter) => {
      if (!isRecord(chapter)) return null;
      const timestamp = stringValue(chapter.timestamp) || stringValue(chapter.time);
      const title = stringValue(chapter.title);
      if (!timestamp || !title) return null;
      return {
        title,
        timestamp,
        seconds: numberValue(chapter.seconds) ?? parseTimestampToSeconds(timestamp),
        summary: stringValue(chapter.summary),
      };
    })
    .filter(Boolean);
}

function normalizeMetadata(manifest) {
  const copy = isRecord(manifest.metadata?.copy) ? manifest.metadata.copy : {};
  const metadata = isRecord(manifest.metadata) ? manifest.metadata : {};
  const youtube = isRecord(manifest.youtube_metadata) ? manifest.youtube_metadata : {};
  return {
    title: stringValue(metadata.title) || stringValue(copy.recommended_title) || stringValue(youtube.title),
    description: stringValue(metadata.description) || stringValue(copy.description) || stringValue(youtube.description),
    chapters: normalizeChapters(metadata.chapters ?? copy.chapters ?? youtube.chapters),
    tags: cleanArray(metadata.tags ?? copy.tags ?? youtube.tags),
    hashtags: cleanArray(metadata.hashtags ?? copy.hashtags ?? youtube.hashtags),
    category: stringValue(metadata.category) || stringValue(youtube.category_recommendation) || stringValue(copy.category),
    audience: stringValue(metadata.audience) || stringValue(youtube.audience_recommendation) || stringValue(copy.audience),
    visibility: stringValue(metadata.visibility) || stringValue(youtube.visibility_recommendation) || stringValue(copy.visibility),
  };
}

function normalizeLocks(manifest) {
  const locks = isRecord(manifest.locks) ? manifest.locks : {};
  return {
    publishReady: booleanValue(locks.publishReady ?? locks.publish_ready ?? manifest.publish_ready),
    youtubeUploadReady: booleanValue(locks.youtubeUploadReady ?? locks.youtube_upload_ready ?? manifest.youtube_upload_ready),
    publicReleaseReady: booleanValue(locks.publicReleaseReady ?? locks.public_release_ready ?? manifest.public_release_ready),
    mayYoutubeAction: booleanValue(locks.mayYoutubeAction ?? locks.may_youtube_action ?? manifest.may_youtube_action),
    uploadPerformed: booleanValue(locks.uploadPerformed ?? locks.upload_performed ?? manifest.upload_performed),
  };
}

function normalizeReads(manifest) {
  const reads = {
    ...(isRecord(manifest.reads) ? manifest.reads : {}),
    ...(isRecord(manifest.readiness_reads) ? manifest.readiness_reads : {}),
  };
  return Object.fromEntries(Object.entries(reads).map(([key, value]) => [key, String(value)]));
}

function addIfAsset(target, asset) {
  if (asset) target.push(asset);
}

function uniqueAssets(assets) {
  const seen = new Set();
  return assets.filter((asset) => {
    const key = asset.path || asset.url || asset.label;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function normalizeAssets(manifest, packetRoot) {
  const media = isRecord(manifest.media) ? manifest.media : {};
  const captionPackage = isRecord(manifest.caption_package) ? manifest.caption_package : {};
  const support = isRecord(manifest.support_artifacts) ? manifest.support_artifacts : {};
  const captions = [];
  const qaFrames = [];
  const transitionSamples = [];
  const evidence = [];

  addIfAsset(captions, localAsset(packetRoot, media.vtt, 'Upload VTT sidecar', 'caption'));
  addIfAsset(captions, localAsset(packetRoot, media.upload_vtt, 'Upload VTT sidecar', 'caption'));
  addIfAsset(captions, localAsset(packetRoot, media.srt, 'Upload SRT sidecar', 'caption'));
  addIfAsset(captions, localAsset(packetRoot, media.upload_srt, 'Upload SRT sidecar', 'caption'));
  addIfAsset(captions, localAsset(packetRoot, captionPackage.youtube_upload_sidecar_vtt, 'Upload VTT sidecar', 'caption'));
  addIfAsset(captions, localAsset(packetRoot, captionPackage.youtube_upload_sidecar_srt, 'Upload SRT sidecar', 'caption'));

  const thumbnail =
    localAsset(packetRoot, media.thumbnail_candidate, 'Thumbnail candidate', 'thumbnail') ||
    localAsset(packetRoot, manifest.thumbnail_candidate, 'Thumbnail candidate', 'thumbnail');

  if (Array.isArray(media.qa_frames)) {
    for (const frame of media.qa_frames) {
      addIfAsset(qaFrames, localAsset(packetRoot, frame, stringValue(frame?.label) || 'QA frame', 'qa-frame'));
    }
  }

  addIfAsset(
    transitionSamples,
    localAsset(packetRoot, media.vo_outro_transition_sample, 'VO/outro transition sample', 'transition-sample'),
  );
  if (Array.isArray(media.transition_samples)) {
    for (const sample of media.transition_samples) {
      addIfAsset(transitionSamples, localAsset(packetRoot, sample, stringValue(sample?.label) || 'Transition sample', 'transition-sample'));
    }
  }

  addIfAsset(evidence, localAsset(packetRoot, manifest.metadata?.packet, 'YouTube metadata packet', 'evidence'));
  for (const [label, artifact] of Object.entries(support)) {
    addIfAsset(evidence, localAsset(packetRoot, artifact, label.replaceAll('_', ' '), 'evidence'));
  }

  return {
    captions: uniqueAssets(captions),
    thumbnail,
    qaFrames: uniqueAssets(qaFrames),
    transitionSamples: uniqueAssets(transitionSamples),
    evidence: uniqueAssets(evidence),
  };
}

function inferEpisodeId(reviewId, packetRoot) {
  const source = `${reviewId} ${packetRoot}`.toLowerCase();
  if (source.includes('challenger')) return 'challenger';
  if (source.includes('therac')) return 'therac-25';
  if (source.includes('hyatt')) return 'hyatt-regency';
  if (source.includes('tacoma')) return 'tacoma-narrows';
  if (source.includes('semmelweis')) return 'semmelweis';
  if (source.includes('titanic')) return 'titanic';
  if (source.includes('piltdown')) return 'piltdown-man';
  if (source.includes('737')) return '737-max';
  return reviewId.split('_')[0] || 'unknown';
}

function inferEpisodeTitle(episodeId, metadata) {
  const labels = {
    challenger: 'Challenger',
    'therac-25': 'Therac-25',
    'hyatt-regency': 'Hyatt Regency',
    semmelweis: 'Semmelweis',
    'tacoma-narrows': 'Tacoma Narrows',
    'piltdown-man': 'Piltdown Man',
    '737-max': '737 MAX',
    titanic: 'Titanic',
  };
  return labels[episodeId] || metadata.title || episodeId;
}

function localReviewUrl(manifest) {
  return (
    stringValue(manifest.localReviewUrl) ||
    stringValue(manifest.local_review_url) ||
    stringValue(manifest.publish_readiness_canonical_review_url) ||
    stringValue(manifest.review_url) ||
    stringValue(manifest.local_review_server?.url) ||
    stringValue(manifest.local_review_server?.review_url) ||
    stringValue(manifest.html_browser_qa?.url)
  );
}

function normalizePacket(packetInput, options = {}) {
  const { packetRoot, manifestPath } = resolvePacketInput(packetInput);
  const manifest = readJson(manifestPath);
  const receiptPath = findYoutubeReviewReceipt(packetRoot, options.receipt);
  const mode = normalizeMode(options.mode);
  const remoteReview = isRecord(manifest.remote_review) ? manifest.remote_review : {};
  const reviewId = sanitizeId(
    options.reviewId ||
      manifest.reviewId ||
      manifest.review_id ||
      remoteReview.review_id ||
      manifest.episode_id ||
      manifest.episodeId ||
      manifest.packet_id ||
      path.basename(packetRoot),
  );
  const siteUrl = String(options.siteUrl || DEFAULT_SITE_URL).replace(/\/$/, '');
  const metadata = normalizeMetadata(manifest);
  const episodeId = stringValue(manifest.episode_id) || stringValue(manifest.episodeId) || inferEpisodeId(reviewId, packetRoot);
  const lifecycleStage = lifecycleStageFromManifest(manifest, mode);
  const youtubeReview = normalizeYoutubeReview({ manifest, packetRoot, receiptPath });
  const smallAssets = normalizeAssets(manifest, packetRoot);
  const manifestSha = sha256File(manifestPath);
  const sourcePacketPath = packetRoot;
  const remoteReviewUrl = `${siteUrl}/reviews/publish-readiness/${reviewId}`;

  const normalized = {
    schemaVersion: 1,
    lifecycleStage,
    reviewId,
    episodeId,
    episodeTitle: stringValue(manifest.episodeTitle) || stringValue(manifest.episode_title) || inferEpisodeTitle(episodeId, metadata),
    createdUtc: stringValue(manifest.createdUtc) || stringValue(manifest.created_utc) || new Date().toISOString(),
    sourcePacketPath,
    status: stringValue(manifest.status) || (lifecycleStage === 'inception' ? 'inception_review_initialized' : ''),
    humanDisposition: stringValue(manifest.humanDisposition) || stringValue(manifest.human_disposition),
    nextReviewQuestion: stringValue(manifest.nextReviewQuestion) || stringValue(manifest.next_review_question),
    localReviewUrl: localReviewUrl(manifest),
    remoteReviewUrl,
    youtubeReview,
    locks: normalizeLocks(manifest),
    assets: {
      video: youtubeReview,
      captions: smallAssets.captions,
      thumbnail: smallAssets.thumbnail,
      qaFrames: smallAssets.qaFrames,
      transitionSamples: smallAssets.transitionSamples,
      evidence: smallAssets.evidence,
    },
    metadata,
    reads: normalizeReads(manifest),
    hashes: {
      publishReadinessManifest: manifestSha,
      youtubeReviewReceipt: youtubeReview?.receiptSha256 || '',
      finalMp4: stringValue(manifest.final_mp4?.sha256) || stringValue(manifest.media?.mp4?.sha256),
    },
    blockers: Array.isArray(manifest.blockers)
      ? manifest.blockers
      : Array.isArray(manifest.remaining_blockers)
        ? manifest.remaining_blockers
        : [],
  };

  return {
    packetRoot,
    manifestPath,
    receiptPath,
    normalized,
    issues: validateNormalizedManifest(normalized, mode),
    warnings: validateRemoteReviewWarnings(normalized),
  };
}

function validateNormalizedManifest(manifest, mode = 'publish_readiness') {
  const issues = [];
  if (!manifest.reviewId) issues.push('missing reviewId');
  if (!manifest.episodeId) issues.push('missing episodeId');
  if (!manifest.metadata.title && mode === 'publish_readiness') issues.push('missing metadata.title');
  if (hasBannedVideoTitleSuffix(manifest.metadata.title)) {
    issues.push('metadata.title must not append `| Cascade Effects`');
  }
  if (mode === 'publish_readiness') {
    if (!manifest.youtubeReview?.videoId) issues.push('missing unlisted YouTube video id');
    if (!manifest.youtubeReview?.receiptPath) issues.push('missing YouTube review upload/status receipt');
    if (!manifest.youtubeReview?.privacyStatus) {
      issues.push('missing YouTube privacy status; expected unlisted');
    } else if (manifest.youtubeReview.privacyStatus !== 'unlisted') {
      issues.push(`YouTube privacy must be unlisted, got ${manifest.youtubeReview.privacyStatus}`);
    }
    if (manifest.youtubeReview?.embeddable === false) {
      issues.push('YouTube review video must be embeddable for cascadeeffects.tv playback');
    }
    if (hasBannedVideoTitleSuffix(manifest.youtubeReview?.title)) {
      issues.push('YouTube review title must not append `| Cascade Effects`');
    }
  }
  if (manifest.locks.publicReleaseReady || manifest.locks.mayYoutubeAction) {
    issues.push('remote review manifest must not enable public release or YouTube actions');
  }
  return issues;
}

function validateRemoteReviewWarnings(manifest) {
  const warnings = [];
  if (!manifest.localReviewUrl) warnings.push('localReviewUrl is empty');
  if (manifest.assets.qaFrames.length === 0 && manifest.lifecycleStage === 'publish_readiness') {
    warnings.push('no QA frames found for remote evidence upload');
  }
  if (manifest.youtubeReview?.embeddable === false) warnings.push('YouTube review video is not embeddable');
  if (
    manifest.youtubeReview?.processingStatus &&
    !['succeeded', 'processed'].includes(manifest.youtubeReview.processingStatus)
  ) {
    warnings.push(`YouTube processing status is ${manifest.youtubeReview.processingStatus}`);
  }
  return warnings;
}

function uploadCandidateAssets(manifest) {
  const candidates = [
    ...manifest.assets.captions,
    ...(manifest.assets.thumbnail ? [manifest.assets.thumbnail] : []),
    ...manifest.assets.qaFrames,
    ...manifest.assets.transitionSamples,
    ...manifest.assets.evidence,
  ];
  return candidates.filter((asset) => asset.path && fs.existsSync(asset.path));
}

function assertNoVideoUploadCandidates(assets) {
  const offenders = assets.filter((asset) => VIDEO_EXTENSIONS.has(path.extname(asset.path).toLowerCase()));
  if (offenders.length > 0) {
    throw new Error(
      `Refusing to upload video files to Vercel Blob: ${offenders.map((asset) => asset.path).join(', ')}`,
    );
  }
}

function assertSmallAssetSizes(assets, maxBytes) {
  const offenders = assets.filter((asset) => fs.statSync(asset.path).size > maxBytes);
  if (offenders.length > 0) {
    throw new Error(
      `Refusing to upload oversized remote review assets: ${offenders.map((asset) => `${asset.path} (${asset.bytes} bytes)`).join(', ')}`,
    );
  }
}

function remoteAssetPath(reviewId, asset) {
  const extension = path.extname(asset.path);
  const base = sanitizeId(path.basename(asset.path, extension)) || sanitizeId(asset.label);
  const kind = sanitizeId(asset.kind || 'evidence');
  return `reviews/publish-readiness/${reviewId}/assets/${kind}/${base}${extension.toLowerCase()}`;
}

async function uploadAssetsAndManifest(context, options) {
  if (context.issues.length > 0) {
    throw new Error(`Remote publish blocked:\n- ${context.issues.join('\n- ')}`);
  }

  const maxBytes = Number(options.maxAssetBytes || DEFAULT_MAX_REMOTE_ASSET_BYTES);
  const candidates = uploadCandidateAssets(context.normalized);
  assertNoVideoUploadCandidates(candidates);
  assertSmallAssetSizes(candidates, maxBytes);

  const uploadedByPath = new Map();
  if (!options.dryRun) {
    for (const asset of candidates) {
      const pathname = remoteAssetPath(context.normalized.reviewId, asset);
      const result = await put(pathname, fs.readFileSync(asset.path), {
        access: 'public',
        addRandomSuffix: false,
        allowOverwrite: true,
        contentType: asset.mimeType,
      });
      uploadedByPath.set(asset.path, result.url);
    }
  }

  const rewrite = (asset) => ({
    ...asset,
    url: options.dryRun ? `dry-run:${remoteAssetPath(context.normalized.reviewId, asset)}` : uploadedByPath.get(asset.path) || asset.url,
  });

  const remoteManifest = {
    ...context.normalized,
    assets: {
      ...context.normalized.assets,
      captions: context.normalized.assets.captions.map(rewrite),
      thumbnail: context.normalized.assets.thumbnail ? rewrite(context.normalized.assets.thumbnail) : undefined,
      qaFrames: context.normalized.assets.qaFrames.map(rewrite),
      transitionSamples: context.normalized.assets.transitionSamples.map(rewrite),
      evidence: context.normalized.assets.evidence.map(rewrite),
    },
  };

  const manifestBody = JSON.stringify(remoteManifest, null, 2) + '\n';
  let manifestUrl = `dry-run:reviews/publish-readiness/${context.normalized.reviewId}/manifest.json`;
  if (!options.dryRun) {
    const result = await put(`reviews/publish-readiness/${context.normalized.reviewId}/manifest.json`, manifestBody, {
      access: 'public',
      addRandomSuffix: false,
      allowOverwrite: true,
      contentType: 'application/json; charset=utf-8',
    });
    manifestUrl = result.url;
  }

  const receipt = {
    receiptType: 'cascadeeffects_publish_readiness_remote_review',
    createdUtc: new Date().toISOString(),
    dryRun: Boolean(options.dryRun),
    reviewId: context.normalized.reviewId,
    remoteReviewUrl: context.normalized.remoteReviewUrl,
    manifestBlobUrl: manifestUrl,
    manifestSha256: sha256Text(manifestBody),
    videoHostingPolicy: 'youtube_unlisted_review_no_final_mp4_uploaded_to_vercel',
    youtubeReview: context.normalized.youtubeReview,
    uploadedAssets: candidates.map((asset) => ({
      label: asset.label,
      kind: asset.kind,
      path: asset.path,
      url: remoteManifest.assets.captions
        .concat(remoteManifest.assets.thumbnail ? [remoteManifest.assets.thumbnail] : [])
        .concat(remoteManifest.assets.qaFrames, remoteManifest.assets.transitionSamples, remoteManifest.assets.evidence)
        .find((candidate) => candidate.path === asset.path)?.url,
      bytes: asset.bytes,
      sha256: asset.sha256,
    })),
    warnings: context.warnings,
  };

  const receiptPath = path.join(context.packetRoot, `remote_review_receipt_${context.normalized.reviewId}.json`);
  if (!options.dryRun) {
    fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
  }
  return { remoteManifest, receipt, receiptPath };
}

function printValidation(context, json = false) {
  const payload = {
    ok: context.issues.length === 0,
    publishable: context.issues.length === 0,
    mode: context.normalized.lifecycleStage,
    reviewId: context.normalized.reviewId,
    remoteReviewUrl: context.normalized.remoteReviewUrl,
    localReviewUrl: context.normalized.localReviewUrl,
    youtubeVideoId: context.normalized.youtubeReview?.videoId || '',
    youtubePrivacyStatus: context.normalized.youtubeReview?.privacyStatus || '',
    issues: context.issues,
    warnings: context.warnings,
    uploadPolicy: 'youtube_unlisted_review_no_final_mp4_uploaded_to_vercel',
  };

  if (json) {
    console.log(JSON.stringify({ ...payload, manifest: context.normalized }, null, 2));
    return;
  }

  console.log(`Review ID: ${payload.reviewId}`);
  console.log(`Mode: ${payload.mode}`);
  console.log(`Remote URL: ${payload.remoteReviewUrl}`);
  console.log(`Local URL: ${payload.localReviewUrl || '(missing)'}`);
  console.log(`YouTube video: ${payload.youtubeVideoId || '(missing)'}`);
  console.log(`Publishable: ${payload.publishable ? 'yes' : 'no'}`);
  for (const issue of payload.issues) console.log(`ISSUE: ${issue}`);
  for (const warning of payload.warnings) console.log(`WARNING: ${warning}`);
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest);

  if (!['validate', 'publish'].includes(command)) {
    throw new Error(
      'Usage: npm run reviews:validate -- --packet <dir> [--mode inception|publish-readiness] | npm run reviews:publish -- --packet <dir> [--mode inception|publish-readiness] [--receipt <json>] [--dry-run]',
    );
  }

  const context = normalizePacket(args.packet, {
    receipt: args.receipt || args['youtube-receipt'],
    reviewId: args['review-id'],
    siteUrl: args['site-url'],
    mode: args.mode,
  });

  if (command === 'validate') {
    printValidation(context, Boolean(args.json));
    return;
  }

  const result = await uploadAssetsAndManifest(context, {
    dryRun: Boolean(args['dry-run']),
    maxAssetBytes: args['max-asset-bytes'],
  });
  console.log(JSON.stringify({
    ok: true,
    dryRun: Boolean(args['dry-run']),
    remoteReviewUrl: context.normalized.remoteReviewUrl,
    receiptPath: result.receiptPath,
    manifestBlobUrl: result.receipt.manifestBlobUrl,
    videoHostingPolicy: result.receipt.videoHostingPolicy,
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
