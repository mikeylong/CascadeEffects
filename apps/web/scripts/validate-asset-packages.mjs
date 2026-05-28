import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import Ajv2020 from 'ajv/dist/2020.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const schemaPath = path.join(repoRoot, 'brand', 'contracts', 'asset-package.schema.json');
const expectedProfileId = 'cascade-paper-architectures-ink-lit-v1';
const exactTitle = 'Cascade of Effects';
const approvedReferenceRenderRoot = 'brand/assets/reference-renders/';

const readJson = (targetPath) => JSON.parse(fs.readFileSync(targetPath, 'utf8'));

const formatInstancePath = (instancePath) => (instancePath ? instancePath : '/');

const normalizeRepoPath = (targetPath) => targetPath.replaceAll('\\', '/');

const hasLfsFilter = (relativeRepoPath) => {
  try {
    const output = execFileSync('git', ['check-attr', 'filter', '--', relativeRepoPath], {
      cwd: repoRoot,
      encoding: 'utf8',
    });

    return output.includes('filter: lfs');
  } catch {
    return false;
  }
};

const listJsonDocuments = () => {
  const contractsDir = path.join(repoRoot, 'brand', 'contracts');
  const packagesDir = path.join(repoRoot, 'brand', 'packages');

  const contracts = fs
    .readdirSync(contractsDir)
    .filter((fileName) => fileName.endsWith('.contract.json'))
    .map((fileName) => path.join(contractsDir, fileName));

  const packages = fs
    .readdirSync(packagesDir)
    .filter((fileName) => fileName.endsWith('.package.json'))
    .map((fileName) => path.join(packagesDir, fileName));

  return [...contracts, ...packages].sort();
};

const expectedDimensionsByRole = new Map([
  ['profile-icon', { width: 800, height: 800 }],
  ['channel-banner', { width: 2560, height: 1440 }],
  ['video-thumbnail', { width: 3840, height: 2160 }],
  ['shorts-cover-frame', { width: 1080, height: 1920 }],
  ['youtube-podcast-playlist', { width: 1280, height: 1280 }],
  ['podcast-master-artwork', { width: 3000, height: 3000 }],
  ['podcast-library-square', { width: 1280, height: 1280 }],
  ['podcast-library-mockup', { width: 2600, height: 2100 }],
  ['web-opengraph-image', { width: 1200, height: 630 }],
  ['web-twitter-image', { width: 1200, height: 630 }],
  ['web-app-icon', { width: 128, height: 128 }],
  ['homepage-brand-illustration', { width: 1600, height: 900 }],
]);

const forbiddenTrackedExtensions = ['.png', '.jpg', '.jpeg', '.webp'];

const validateReferenceRenderPath = (referencePath, relativePath, context) => {
  const errors = [];
  const normalizedPath = normalizeRepoPath(referencePath);

  if (path.isAbsolute(normalizedPath)) {
    errors.push(`${relativePath}: ${context} reference render path must be repo-relative: ${referencePath}.`);
  }

  if (!normalizedPath.startsWith(approvedReferenceRenderRoot)) {
    errors.push(
      `${relativePath}: ${context} reference render must live under ${approvedReferenceRenderRoot}; found ${referencePath}.`,
    );
  }

  if (path.posix.extname(normalizedPath).toLowerCase() !== '.png') {
    errors.push(`${relativePath}: ${context} reference render must be a PNG file: ${referencePath}.`);
  }

  if (!fs.existsSync(path.join(repoRoot, normalizedPath))) {
    errors.push(`${relativePath}: ${context} reference render does not exist: ${referencePath}.`);
  }

  if (!hasLfsFilter(normalizedPath)) {
    errors.push(`${relativePath}: ${context} reference render must be tracked by Git LFS: ${referencePath}.`);
  }

  return errors;
};

const collectSourceEvidence = (documentEntries) => {
  const errors = [];
  const evidenceItems = new Map();

  for (const { document, relativePath } of documentEntries) {
    for (const evidenceSet of document.sourceEvidence?.sets ?? []) {
      const storageRoot = normalizeRepoPath(evidenceSet.storage?.root ?? '');

      if (!storageRoot.startsWith(approvedReferenceRenderRoot)) {
        errors.push(
          `${relativePath}: sourceEvidence set ${evidenceSet.id} must store renders under ${approvedReferenceRenderRoot}.`,
        );
      }

      for (const item of evidenceSet.items ?? []) {
        const key = `${evidenceSet.id}:${item.id}`;
        const existingPath = evidenceItems.get(key);

        if (existingPath && existingPath !== item.path) {
          errors.push(`${relativePath}: duplicate sourceEvidence item ${key} uses multiple paths.`);
        }

        evidenceItems.set(key, item.path);
        errors.push(...validateReferenceRenderPath(item.path, relativePath, `sourceEvidence ${key}`));
      }
    }
  }

  return { evidenceItems, errors };
};

const validateContractRules = (document, relativePath) => {
  const errors = [];

  if (document.profileId !== expectedProfileId) {
    errors.push(`${relativePath}: profileId must be ${expectedProfileId}.`);
  }

  if (document.legacyPolicy?.status && document.legacyPolicy.status !== 'inactive-reference-only') {
    errors.push(`${relativePath}: legacy policy must be inactive-reference-only.`);
  }

  return errors;
};

const validatePackageRules = (document, relativePath, evidenceItems) => {
  const errors = [];
  const seenRoles = new Set();

  if (document.largeAssetPolicy?.sourceControl !== 'contracts-manifests-provenance-only') {
    errors.push(`${relativePath}: largeAssetPolicy.sourceControl must keep generated media out of git.`);
  }

  for (const extension of forbiddenTrackedExtensions) {
    if (!document.largeAssetPolicy?.forbiddenTrackedExtensions?.includes(extension)) {
      errors.push(`${relativePath}: largeAssetPolicy.forbiddenTrackedExtensions must include ${extension}.`);
    }
  }

  for (const contractPath of Object.values(document.sourceContracts ?? {})) {
    const absoluteContractPath = path.join(repoRoot, contractPath);
    if (!fs.existsSync(absoluteContractPath)) {
      errors.push(`${relativePath}: referenced contract does not exist: ${contractPath}.`);
    }
  }

  for (const deliverable of document.deliverables ?? []) {
    if (seenRoles.has(deliverable.role)) {
      errors.push(`${relativePath}: duplicate deliverable role ${deliverable.role}.`);
    }
    seenRoles.add(deliverable.role);

    const expectedDimensions = expectedDimensionsByRole.get(deliverable.role);
    if (expectedDimensions) {
      const { width, height } = deliverable.dimensions;
      if (width !== expectedDimensions.width || height !== expectedDimensions.height) {
        errors.push(
          `${relativePath}: ${deliverable.role} must be ${expectedDimensions.width}x${expectedDimensions.height}; found ${width}x${height}.`,
        );
      }
    }

    if (deliverable.source?.trackedInGit !== false) {
      errors.push(`${relativePath}: ${deliverable.role} generated media must not be tracked in git.`);
    }

    if (deliverable.texture_noise_read !== 'pass') {
      errors.push(
        `${relativePath}: ${deliverable.role} texture_noise_read must be pass before package use; found ${deliverable.texture_noise_read}.`,
      );
    }

    if (deliverable.copyPolicy?.mode === 'title-only') {
      if (deliverable.copyPolicy.exactTitle !== exactTitle) {
        errors.push(`${relativePath}: ${deliverable.role} title-only assets must use ${exactTitle}.`);
      }

      if (deliverable.copyPolicy.allowExtraCopy !== false) {
        errors.push(`${relativePath}: ${deliverable.role} title-only assets must not allow extra copy.`);
      }
    }

    if (deliverable.copyPolicy?.mode === 'mark-only' && deliverable.copyPolicy.exactTitle) {
      errors.push(`${relativePath}: ${deliverable.role} mark-only assets must not include the full title.`);
    }

    if (
      deliverable.source?.compositionMethod === 'generated-source-plus-local-title' &&
      deliverable.copyPolicy?.allowGeneratedTextInSourceArtwork !== false
    ) {
      errors.push(`${relativePath}: ${deliverable.role} source artwork must be generated without text.`);
    }

    if (
      deliverable.copyPolicy?.allowGeneratedTextInSourceArtwork === true &&
      deliverable.source?.compositionMethod !== 'approved-title-bearing-source'
    ) {
      errors.push(
        `${relativePath}: ${deliverable.role} can allow generated title text only when using an approved title-bearing source.`,
      );
    }

    if (
      deliverable.source?.compositionMethod === 'approved-title-bearing-source' &&
      deliverable.copyPolicy?.mode !== 'title-only'
    ) {
      errors.push(`${relativePath}: ${deliverable.role} approved title-bearing source must be title-only.`);
    }

    const referenceRenders = deliverable.source?.referenceRenders ?? [];

    const isEpisodeTemplate = deliverable.copyPolicy?.mode === 'episode-template';

    if (document.id === 'youtube-channel-launch-v1' && !isEpisodeTemplate && referenceRenders.length === 0) {
      errors.push(`${relativePath}: ${deliverable.role} must reference at least one approved launch reference render.`);
    }

    for (const referenceRender of referenceRenders) {
      const evidenceKey = `${referenceRender.evidenceSetId}:${referenceRender.evidenceItemId}`;
      const approvedEvidencePath = evidenceItems.get(evidenceKey);

      if (!approvedEvidencePath) {
        errors.push(`${relativePath}: ${deliverable.role} references unknown source evidence item ${evidenceKey}.`);
      } else if (approvedEvidencePath !== referenceRender.path) {
        errors.push(
          `${relativePath}: ${deliverable.role} reference render ${evidenceKey} must use ${approvedEvidencePath}; found ${referenceRender.path}.`,
        );
      }

      errors.push(
        ...validateReferenceRenderPath(referenceRender.path, relativePath, `${deliverable.role} ${evidenceKey}`),
      );
    }
  }

  return errors;
};

const schema = readJson(schemaPath);
const ajv = new Ajv2020({
  allErrors: true,
  strict: false,
});
const validate = ajv.compile(schema);

const documentPaths = listJsonDocuments();
const documentEntries = documentPaths.map((documentPath) => ({
  documentPath,
  relativePath: path.relative(repoRoot, documentPath),
  document: readJson(documentPath),
}));
const validationErrors = [];
const { evidenceItems, errors: sourceEvidenceErrors } = collectSourceEvidence(documentEntries);

validationErrors.push(...sourceEvidenceErrors);

for (const { document, relativePath } of documentEntries) {
  const valid = validate(document);

  if (!valid) {
    validationErrors.push(`Asset rule validation failed for ${relativePath}.`);
    for (const error of validate.errors ?? []) {
      const location = formatInstancePath(error.instancePath);
      const message = error.message ?? 'Validation error';
      validationErrors.push(`- ${location}: ${message}`);
    }
  }

  validationErrors.push(...validateContractRules(document, relativePath));

  if (document.kind === 'asset-package') {
    validationErrors.push(...validatePackageRules(document, relativePath, evidenceItems));
  }
}

if (validationErrors.length > 0) {
  console.error(validationErrors.join('\n'));
  process.exit(1);
}

console.log(`Asset-package validation passed for ${documentPaths.length} documents.`);
