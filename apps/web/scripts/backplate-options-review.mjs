#!/usr/bin/env node
import { put } from '@vercel/blob';
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const APP_ROOT = path.resolve(import.meta.dirname, '..');
const REPO_ROOT = path.resolve(APP_ROOT, '..', '..');
const DEFAULT_SITE_URL = 'https://cascadeeffects.tv';
const DEFAULT_MAX_REMOTE_ASSET_BYTES = 25 * 1024 * 1024;
const EXPECTED_EPISODES = 8;
const DEFAULT_EXPECTED_GENERATED_OPTIONS = 24;
const DEFAULT_EXPECTED_EXISTING_OPTIONS = 2;
const DEFAULT_EXPECTED_OPTIONS = 26;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const REVIEW_ID_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9_-]{2,127}$/;

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

function isRecord(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readRecord(value) {
  return isRecord(value) ? value : {};
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

function optionKindCounts(options) {
  return options.reduce(
    (counts, option) => {
      if (option.kind === 'existing') counts.existing += 1;
      else counts.generated += 1;
      return counts;
    },
    { generated: 0, existing: 0 },
  );
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function sha256Bytes(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function sha256File(filePath) {
  return sha256Bytes(fs.readFileSync(filePath));
}

function sha256Text(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function sanitizePathPart(value) {
  return String(value || '')
    .trim()
    .replace(/[^a-zA-Z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 96);
}

function repoRelative(filePath) {
  const relative = path.relative(REPO_ROOT, filePath);
  return relative.startsWith('..') ? filePath : relative;
}

function resolveInputPath(input, label) {
  if (!input) throw new Error(`Missing --${label} <path>.`);
  const candidates = [
    path.resolve(process.cwd(), input),
    path.resolve(REPO_ROOT, input),
    path.resolve(APP_ROOT, input),
  ];
  const found = candidates.find((candidate) => fs.existsSync(candidate));
  if (!found) throw new Error(`${label} not found: ${input}`);
  return found;
}

function resolveArtifactPath(rawPath, manifestDir) {
  if (!rawPath) return '';
  if (path.isAbsolute(rawPath)) return rawPath;
  const candidates = [
    path.resolve(REPO_ROOT, rawPath),
    path.resolve(manifestDir, rawPath),
    path.resolve(process.cwd(), rawPath),
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) ?? candidates[0];
}

function isPng(filePath) {
  if (path.extname(filePath).toLowerCase() !== '.png') return false;
  if (!fs.existsSync(filePath)) return false;
  const header = fs.readFileSync(filePath).subarray(0, PNG_SIGNATURE.length);
  return header.equals(PNG_SIGNATURE);
}

function findMayAdvanceTrue(value, trail = []) {
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => findMayAdvanceTrue(item, trail.concat(String(index))));
  }
  if (!isRecord(value)) return [];

  const matches = [];
  for (const [key, item] of Object.entries(value)) {
    const nextTrail = trail.concat(key);
    if ((key === 'may_advance' || key === 'mayAdvance') && item === true) {
      matches.push(nextTrail.join('.'));
    }
    matches.push(...findMayAdvanceTrue(item, nextTrail));
  }
  return matches;
}

function localAsset({ label, kind, sourcePath, expectedSha256, manifestDir, episodeId = '', optionId = '' }) {
  const resolved = resolveArtifactPath(sourcePath, manifestDir);
  const exists = Boolean(resolved && fs.existsSync(resolved) && fs.statSync(resolved).isFile());
  const bytes = exists ? fs.statSync(resolved).size : 0;
  const actualSha256 = exists ? sha256File(resolved) : '';

  return {
    label,
    kind,
    episodeId,
    optionId,
    sourcePath,
    path: resolved,
    url: '',
    sha256: expectedSha256 || actualSha256,
    actualSha256,
    bytes,
    mimeType: 'image/png',
  };
}

function normalizeOption(optionValue, episodeId, manifestDir) {
  const option = readRecord(optionValue);
  const optionId = stringValue(option.id);
  const sourcePath =
    stringValue(option.path) ||
    stringValue(option.imagePath) ||
    stringValue(option.image_path) ||
    stringValue(option.artifact_path) ||
    stringValue(option.artifactFinalPath) ||
    stringValue(option.artifact_final_path);
  const sha256 =
    stringValue(option.sha256) ||
    stringValue(option.artifactFinalSha256) ||
    stringValue(option.artifact_final_sha256);

  return {
    id: optionId,
    kind: stringValue(option.kind, 'new'),
    status: stringValue(option.status),
    path: sourcePath,
    imageUrl: stringValue(option.imageUrl) || stringValue(option.image_url) || stringValue(option.url),
    sha256,
    promptPath: stringValue(option.promptPath) || stringValue(option.prompt_path),
    promptSha256: stringValue(option.promptSha256) || stringValue(option.prompt_sha256),
    personPresenceRequired: booleanValue(option.personPresenceRequired, booleanValue(option.person_presence_required)),
    personPresenceAssertion: stringValue(option.personPresenceAssertion) || stringValue(option.person_presence_assertion),
    asset: localAsset({
      label: `${episodeId} ${optionId}`,
      kind: 'option',
      sourcePath,
      expectedSha256: sha256,
      manifestDir,
      episodeId,
      optionId,
    }),
  };
}

function normalizeEpisode(episodeValue, manifestDir) {
  const episode = readRecord(episodeValue);
  const contactSheet = readRecord(episode.contactSheet ?? episode.contact_sheet);
  const episodeId = stringValue(episode.episodeId) || stringValue(episode.episode_id);
  const contactSheetPath = stringValue(contactSheet.path) || stringValue(episode.contact_sheet_path);
  const contactSheetSha256 = stringValue(contactSheet.sha256) || stringValue(episode.contact_sheet_sha256);
  const options = Array.isArray(episode.options) ? episode.options.map((option) => normalizeOption(option, episodeId, manifestDir)) : [];
  const counts = optionKindCounts(options);

  return {
    episodeId,
    title: stringValue(episode.title),
    status: stringValue(episode.status),
    mayAdvance: booleanValue(episode.mayAdvance, booleanValue(episode.may_advance)),
    generatedOptionCount: numberValue(episode.generatedOptionCount) ?? numberValue(episode.generated_option_count) ?? counts.generated,
    existingOptionCount: numberValue(episode.existingOptionCount) ?? numberValue(episode.existing_option_count) ?? counts.existing,
    manifestPath: stringValue(episode.manifestPath) || stringValue(episode.manifest_path),
    manifestSha256: stringValue(episode.manifestSha256) || stringValue(episode.manifest_sha256),
    receiptPath: stringValue(episode.receiptPath) || stringValue(episode.receipt_path),
    personPresenceRequired: booleanValue(episode.personPresenceRequired, booleanValue(episode.person_presence_required)),
    contactSheet: {
      path: contactSheetPath,
      url: stringValue(contactSheet.url) || stringValue(contactSheet.imageUrl) || stringValue(contactSheet.image_url),
      sha256: contactSheetSha256,
      asset: localAsset({
        label: `${episodeId} contact sheet`,
        kind: 'contact-sheet',
        sourcePath: contactSheetPath,
        expectedSha256: contactSheetSha256,
        manifestDir,
        episodeId,
      }),
    },
    options,
  };
}

function expectedCounts(source) {
  const summary = readRecord(source.summary);
  const summaryGeneratedOptions =
    numberValue(summary.generatedOptionCount) ??
    numberValue(summary.generated_option_count) ??
    numberValue(summary.newOptionCount) ??
    numberValue(summary.new_option_count);
  const summaryExistingOptions = numberValue(summary.existingOptionCount) ?? numberValue(summary.existing_option_count);
  const summaryOptions = numberValue(summary.optionCount) ?? numberValue(summary.option_count);

  return {
    episodes: numberValue(summary.episodeCount) ?? numberValue(summary.episode_count) ?? EXPECTED_EPISODES,
    generatedOptions: summaryGeneratedOptions ?? DEFAULT_EXPECTED_GENERATED_OPTIONS,
    existingOptions: summaryExistingOptions ?? DEFAULT_EXPECTED_EXISTING_OPTIONS,
    options: summaryOptions ?? (summaryGeneratedOptions !== undefined && summaryExistingOptions !== undefined
      ? summaryGeneratedOptions + summaryExistingOptions
      : DEFAULT_EXPECTED_OPTIONS),
  };
}

function normalizePacket(manifestInput, options = {}) {
  const manifestPath = resolveInputPath(manifestInput, 'manifest');
  const manifestDir = path.dirname(manifestPath);
  const source = readJson(manifestPath);
  const reviewId = stringValue(options.reviewId) || stringValue(source.reviewId) || stringValue(source.review_id);
  const siteUrl = String(options.siteUrl || DEFAULT_SITE_URL).replace(/\/$/, '');
  const episodes = Array.isArray(source.episodes) ? source.episodes.map((episode) => normalizeEpisode(episode, manifestDir)) : [];
  const generatedOptionCount = episodes.reduce((total, episode) => total + episode.generatedOptionCount, 0);
  const existingOptionCount = episodes.reduce((total, episode) => total + episode.existingOptionCount, 0);
  const sourceManifestSha256 = sha256File(manifestPath);

  const normalized = {
    schemaVersion: 1,
    reviewId,
    createdAt: stringValue(source.createdAt) || stringValue(source.created_at) || new Date().toISOString(),
    status: stringValue(source.status),
    humanDisposition: stringValue(source.humanDisposition) || stringValue(source.human_disposition),
    mayAdvance: booleanValue(source.mayAdvance, booleanValue(source.may_advance)),
    batchId: stringValue(source.batchId) || stringValue(source.batch_id),
    personPresenceRequired: booleanValue(source.personPresenceRequired, booleanValue(source.person_presence_required)),
    remoteReviewUrl: `${siteUrl}/reviews/season-02/backplate-options/${reviewId}`,
    sourceManifestPath: repoRelative(manifestPath),
    sourceManifestSha256,
    episodes,
    summary: {
      episodeCount: episodes.length,
      generatedOptionCount,
      existingOptionCount,
      optionCount: episodes.reduce((total, episode) => total + episode.options.length, 0),
      contactSheetCount: episodes.filter((episode) => Boolean(episode.contactSheet.path)).length,
    },
  };

  return {
    manifestPath,
    manifestDir,
    source,
    normalized,
    issues: validateNormalized(normalized, source, Number(options.maxAssetBytes || DEFAULT_MAX_REMOTE_ASSET_BYTES)),
    warnings: [],
  };
}

function uploadCandidateAssets(manifest) {
  return manifest.episodes.flatMap((episode) => [
    episode.contactSheet.asset,
    ...episode.options.map((option) => option.asset),
  ]);
}

function validateAsset(asset, maxAssetBytes) {
  const issues = [];
  if (!asset.sourcePath) issues.push(`${asset.label}: missing image path`);
  if (!asset.path || !fs.existsSync(asset.path)) issues.push(`${asset.label}: image not found`);
  if (asset.path && fs.existsSync(asset.path) && !isPng(asset.path)) issues.push(`${asset.label}: image must be a PNG`);
  if (asset.bytes > maxAssetBytes) issues.push(`${asset.label}: image exceeds ${maxAssetBytes} bytes`);
  if (asset.sha256 && asset.actualSha256 && asset.sha256 !== asset.actualSha256) {
    issues.push(`${asset.label}: sha256 mismatch`);
  }
  if (!asset.sha256) issues.push(`${asset.label}: missing sha256`);
  return issues;
}

function validateNormalized(manifest, source, maxAssetBytes) {
  const issues = [];
  const expected = expectedCounts(source);
  if (!REVIEW_ID_PATTERN.test(manifest.reviewId)) issues.push('invalid reviewId');
  if (manifest.summary.episodeCount !== expected.episodes) {
    issues.push(`expected ${expected.episodes} episodes, got ${manifest.summary.episodeCount}`);
  }
  if (manifest.summary.generatedOptionCount !== expected.generatedOptions) {
    issues.push(`expected ${expected.generatedOptions} generated options, got ${manifest.summary.generatedOptionCount}`);
  }
  if (manifest.summary.existingOptionCount !== expected.existingOptions) {
    issues.push(`expected ${expected.existingOptions} existing options, got ${manifest.summary.existingOptionCount}`);
  }
  if (manifest.summary.optionCount !== expected.options) {
    issues.push(`expected ${expected.options} option images, got ${manifest.summary.optionCount}`);
  }

  const mayAdvancePaths = findMayAdvanceTrue(source);
  if (mayAdvancePaths.length > 0) {
    issues.push(`may_advance must remain false; true at ${mayAdvancePaths.join(', ')}`);
  }

  for (const episode of manifest.episodes) {
    if (!episode.episodeId) issues.push('episode missing episodeId');
    if (episode.mayAdvance) issues.push(`${episode.episodeId}: mayAdvance must remain false`);
    for (const asset of [episode.contactSheet.asset, ...episode.options.map((option) => option.asset)]) {
      issues.push(...validateAsset(asset, maxAssetBytes));
    }
  }

  return issues;
}

function remoteAssetPath(reviewId, asset) {
  const extension = path.extname(asset.path).toLowerCase();
  const kind = asset.kind === 'contact-sheet' ? 'contact-sheets' : 'options';
  const base =
    asset.kind === 'contact-sheet'
      ? `${sanitizePathPart(asset.episodeId)}-contact-sheet`
      : `${sanitizePathPart(asset.episodeId)}-${sanitizePathPart(asset.optionId)}`;
  return `reviews/backplate-options/${reviewId}/assets/${kind}/${base}${extension}`;
}

function rewriteRemoteManifest(manifest, uploadedByPath, dryRun) {
  return {
    ...manifest,
    episodes: manifest.episodes.map((episode) => ({
      episodeId: episode.episodeId,
      title: episode.title,
      status: episode.status,
      mayAdvance: episode.mayAdvance,
      generatedOptionCount: episode.generatedOptionCount,
      existingOptionCount: episode.existingOptionCount,
      manifestPath: episode.manifestPath,
      manifestSha256: episode.manifestSha256,
      receiptPath: episode.receiptPath,
      personPresenceRequired: episode.personPresenceRequired,
      contactSheet: {
        path: episode.contactSheet.path,
        url: dryRun ? `dry-run:${remoteAssetPath(manifest.reviewId, episode.contactSheet.asset)}` : uploadedByPath.get(episode.contactSheet.asset.path),
        sha256: episode.contactSheet.sha256,
      },
      options: episode.options.map((option) => ({
        id: option.id,
        kind: option.kind,
        status: option.status,
        path: option.path,
        imageUrl: dryRun ? `dry-run:${remoteAssetPath(manifest.reviewId, option.asset)}` : uploadedByPath.get(option.asset.path),
        sha256: option.sha256,
        promptPath: option.promptPath,
        promptSha256: option.promptSha256,
        personPresenceRequired: option.personPresenceRequired,
        personPresenceAssertion: option.personPresenceAssertion,
      })),
    })),
  };
}

async function uploadAssetsAndManifest(context, options) {
  if (context.issues.length > 0) {
    throw new Error(`Remote publish blocked:\n- ${context.issues.join('\n- ')}`);
  }

  const dryRun = Boolean(options.dryRun);
  const uploadEndpoint = stringValue(options.uploadEndpoint);
  const uploadKey = stringValue(options.uploadKey);
  const vercelCurlDeployment = stringValue(options.vercelCurlDeployment);
  const candidates = uploadCandidateAssets(context.normalized);
  const uploadedByPath = new Map();

  if ((uploadEndpoint || vercelCurlDeployment) && !uploadKey) {
    throw new Error('Missing --upload-key for protected upload endpoint.');
  }

  if (!dryRun) {
    for (const asset of candidates) {
      const pathname = remoteAssetPath(context.normalized.reviewId, asset);
      if (uploadEndpoint || vercelCurlDeployment) {
        console.error(`Uploading ${asset.label}`);
      }
      const url = vercelCurlDeployment
        ? putViaVercelCurl({
            deployment: vercelCurlDeployment,
            uploadKey,
            pathname,
            body: fs.readFileSync(asset.path),
            contentType: asset.mimeType,
          })
        : uploadEndpoint
          ? await putViaUploadEndpoint({ endpoint: uploadEndpoint, uploadKey, pathname, body: fs.readFileSync(asset.path), contentType: asset.mimeType })
        : (await put(pathname, fs.readFileSync(asset.path), {
            access: 'public',
            addRandomSuffix: false,
            allowOverwrite: true,
            contentType: asset.mimeType,
          })).url;
      uploadedByPath.set(asset.path, url);
    }
  }

  const remoteManifest = rewriteRemoteManifest(context.normalized, uploadedByPath, dryRun);
  const manifestBody = JSON.stringify(remoteManifest, null, 2) + '\n';
  let manifestBlobUrl = `dry-run:reviews/backplate-options/${context.normalized.reviewId}/manifest.json`;

  if (!dryRun) {
    const manifestPathname = `reviews/backplate-options/${context.normalized.reviewId}/manifest.json`;
    if (uploadEndpoint || vercelCurlDeployment) {
      console.error('Uploading remote manifest');
    }
    manifestBlobUrl = vercelCurlDeployment
      ? putViaVercelCurl({
          deployment: vercelCurlDeployment,
          uploadKey,
          pathname: manifestPathname,
          body: Buffer.from(manifestBody),
          contentType: 'application/json; charset=utf-8',
        })
      : uploadEndpoint
        ? await putViaUploadEndpoint({
          endpoint: uploadEndpoint,
          uploadKey,
          pathname: manifestPathname,
          body: Buffer.from(manifestBody),
          contentType: 'application/json; charset=utf-8',
        })
      : (await put(manifestPathname, manifestBody, {
          access: 'public',
          addRandomSuffix: false,
          allowOverwrite: true,
          contentType: 'application/json; charset=utf-8',
        })).url;
  }

  const receipt = {
    receiptType: 'cascadeeffects_backplate_options_remote_review',
    createdUtc: new Date().toISOString(),
    dryRun,
    reviewId: context.normalized.reviewId,
    remoteReviewUrl: context.normalized.remoteReviewUrl,
    manifestBlobUrl,
    sourceManifestPath: context.normalized.sourceManifestPath,
    sourceManifestSha256: context.normalized.sourceManifestSha256,
    manifestSha256: sha256Text(manifestBody),
    mayAdvance: false,
    uploadedAssets: candidates.map((asset) => ({
      label: asset.label,
      kind: asset.kind,
      path: repoRelative(asset.path),
      url: dryRun ? `dry-run:${remoteAssetPath(context.normalized.reviewId, asset)}` : uploadedByPath.get(asset.path),
      bytes: asset.bytes,
      sha256: asset.sha256,
    })),
    assertions: {
      generatedMediaWrittenToGitTrackedPaths: false,
      noGatePromoted: true,
      sourceArtKeepRemainsPending: true,
      livingCoverKeepRemainsPending: true,
      publicReleaseManualOnly: true,
    },
  };

  const receiptPath = path.join(path.dirname(context.manifestPath), `remote_review_receipt_${context.normalized.reviewId}.json`);
  if (!dryRun) {
    fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
  }

  return { remoteManifest, receipt, receiptPath };
}

async function putViaUploadEndpoint({ endpoint, uploadKey, pathname, body, contentType }) {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-ce-upload-key': uploadKey,
    },
    body: JSON.stringify({
      pathname,
      contentType,
      base64: Buffer.from(body).toString('base64'),
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Upload endpoint failed for ${pathname}: ${response.status} ${message}`);
  }

  const payload = await response.json();
  if (!payload.url) throw new Error(`Upload endpoint did not return a URL for ${pathname}`);
  return payload.url;
}

function putViaVercelCurl({ deployment, uploadKey, pathname, body, contentType }) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ce-backplate-upload-'));
  const bodyPath = path.join(tempDir, 'body.json');
  const configPath = path.join(tempDir, 'curl.conf');
  const payload = JSON.stringify({
    pathname,
    contentType,
    base64: Buffer.from(body).toString('base64'),
  });

  fs.writeFileSync(bodyPath, payload);
  fs.writeFileSync(
    configPath,
    [
      'request = "POST"',
      'silent',
      'show-error',
      'header = "content-type: application/json"',
      `header = "x-ce-upload-key: ${uploadKey}"`,
      `data-binary = "@${bodyPath}"`,
    ].join('\n') + '\n',
  );

  try {
    const result = spawnSync(
      'npx',
      ['vercel@latest', 'curl', '/api/reviews/backplate-options/blob-upload', '--deployment', deployment, '--yes', '--', '--config', configPath],
      {
        cwd: REPO_ROOT,
        encoding: 'utf8',
        maxBuffer: 20 * 1024 * 1024,
      },
    );

    if (result.status !== 0) {
      throw new Error(`vercel curl failed for ${pathname}: ${result.stderr || result.stdout}`);
    }

    const payload = JSON.parse(result.stdout);
    if (!payload.url) throw new Error(`vercel curl upload did not return a URL for ${pathname}`);
    return payload.url;
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function printValidation(context, json = false) {
  const payload = {
    ok: context.issues.length === 0,
    publishable: context.issues.length === 0,
    reviewId: context.normalized.reviewId,
    remoteReviewUrl: context.normalized.remoteReviewUrl,
    sourceManifestPath: context.normalized.sourceManifestPath,
    episodeCount: context.normalized.summary.episodeCount,
    optionCount: context.normalized.summary.optionCount,
    contactSheetCount: context.normalized.summary.contactSheetCount,
    uploadAssetCount: uploadCandidateAssets(context.normalized).length,
    issues: context.issues,
    warnings: context.warnings,
  };

  if (json) {
    console.log(JSON.stringify({ ...payload, manifest: context.normalized }, null, 2));
    return;
  }

  console.log(`Review ID: ${payload.reviewId}`);
  console.log(`Remote URL: ${payload.remoteReviewUrl}`);
  console.log(`Episodes: ${payload.episodeCount}`);
  console.log(`Option images: ${payload.optionCount}`);
  console.log(`Upload assets: ${payload.uploadAssetCount}`);
  console.log(`Publishable: ${payload.publishable ? 'yes' : 'no'}`);
  for (const issue of payload.issues) console.log(`ISSUE: ${issue}`);
  for (const warning of payload.warnings) console.log(`WARNING: ${warning}`);
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest);

  if (!['validate', 'publish'].includes(command)) {
    throw new Error(
      'Usage: node scripts/backplate-options-review.mjs validate --manifest <manifest.json> [--json] | node scripts/backplate-options-review.mjs publish --manifest <manifest.json> [--dry-run]',
    );
  }

  const context = normalizePacket(args.manifest, {
    reviewId: args['review-id'],
    siteUrl: args['site-url'],
    maxAssetBytes: args['max-asset-bytes'],
  });

  if (command === 'validate') {
    printValidation(context, Boolean(args.json));
    return;
  }

  const result = await uploadAssetsAndManifest(context, {
    dryRun: Boolean(args['dry-run']),
    uploadEndpoint: args['upload-endpoint'],
    uploadKey: args['upload-key'],
    vercelCurlDeployment: args['vercel-curl-deployment'],
  });
  console.log(JSON.stringify({
    ok: true,
    dryRun: Boolean(args['dry-run']),
    remoteReviewUrl: context.normalized.remoteReviewUrl,
    receiptPath: result.receiptPath,
    manifestBlobUrl: result.receipt.manifestBlobUrl,
    uploadAssetCount: result.receipt.uploadedAssets.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
