import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const readText = (targetPath) => fs.readFileSync(targetPath, 'utf8');
const readJson = (targetPath) => JSON.parse(readText(targetPath));
const repoPath = (...segments) => path.join(repoRoot, ...segments);
const displayPath = (targetPath) => path.relative(repoRoot, targetPath).replaceAll('\\', '/');

const designSystemContract = readJson(
  repoPath('brand', 'contracts', 'design-system.contract.json'),
);
const galleryContract = designSystemContract.layout?.webEpisodeGallery ?? {};
const activeProofId = galleryContract.activeProofId;
const bannedLiveProofIds = galleryContract.bannedInLiveWiring ?? [];

if (!activeProofId) {
  console.error('brand/contracts/design-system.contract.json: missing layout.webEpisodeGallery.activeProofId.');
  process.exit(1);
}

const expectedEpisodes = [
  'challenger',
  'therac-25',
  'hyatt-regency',
  'semmelweis',
  'tacoma-narrows',
  'piltdown-man',
  '737-max',
  'titanic',
];

const bannedAltTerms = [
  { label: 'water', pattern: /\bwater(?:s|fall|falls|course|courses)?\b/i },
  { label: 'river', pattern: /\brivers?\b/i },
  { label: 'stream', pattern: /\bstreams?\b/i },
  { label: 'canal', pattern: /\bcanals?\b/i },
  { label: 'liquid', pattern: /\bliquid\b/i },
  { label: 'spill', pattern: /\bspills?\b/i },
  { label: 'evidence tray', pattern: /\bevidence trays?\b/i },
  { label: 'ledger', pattern: /\bledgers?\b/i },
  { label: 'gauge', pattern: /\bgauges?\b/i },
  { label: 'connection detail', pattern: /\bconnection details?\b/i },
  { label: 'terminal card', pattern: /\bterminal cards?\b/i },
  { label: 'system diagram', pattern: /\bsystem diagrams?\b/i },
  { label: 'arrow', pattern: /\barrows?\b/i },
  { label: 'O-ring', pattern: /\bo-?rings?\b/i },
  { label: 'lifeboat', pattern: /\blifeboats?\b/i },
  { label: 'angle-of-attack', pattern: /\bangle[- ]of[- ]attack\b/i },
  { label: 'trim wheel', pattern: /\btrim wheels?\b/i },
  { label: 'shop drawing', pattern: /\bshop drawings?\b/i },
  { label: 'deck section', pattern: /\bdeck[- ]sections?\b/i },
  { label: 'signal path', pattern: /\bsignal paths?\b/i },
];

const errors = [];

const expectFile = (targetPath, context) => {
  if (!fs.existsSync(targetPath)) {
    errors.push(`${context} is missing: ${displayPath(targetPath)}`);
  }
};

const siteFactsPath = repoPath('lib', 'site-facts.ts');
const siteFacts = readText(siteFactsPath);
const siteFactsRelative = displayPath(siteFactsPath);
const activeRuntimeRoot = `/brand/episode-gallery/${activeProofId}/`;

for (const proofId of bannedLiveProofIds) {
  const bannedRuntimeRoot = `/brand/episode-gallery/${proofId}/`;

  if (siteFacts.includes(bannedRuntimeRoot)) {
    errors.push(`${siteFactsRelative}: live thumbnailSrc must not reference ${bannedRuntimeRoot}.`);
  }
}

const thumbnailSrcs = [...siteFacts.matchAll(/thumbnailSrc:\s*'([^']+)'/g)].map((match) => match[1]);
const thumbnailAlts = [...siteFacts.matchAll(/thumbnailAlt:\s*'([^']+)'/g)].map((match) => match[1]);

if (thumbnailSrcs.length !== expectedEpisodes.length) {
  errors.push(
    `${siteFactsRelative}: expected ${expectedEpisodes.length} thumbnailSrc values; found ${thumbnailSrcs.length}.`,
  );
}

if (thumbnailAlts.length !== expectedEpisodes.length) {
  errors.push(
    `${siteFactsRelative}: expected ${expectedEpisodes.length} thumbnailAlt values; found ${thumbnailAlts.length}.`,
  );
}

for (const episodeId of expectedEpisodes) {
  const runtimeSrc = `${activeRuntimeRoot}${episodeId}-thumbnail-${activeProofId}.webp`;

  if (!thumbnailSrcs.includes(runtimeSrc)) {
    errors.push(`${siteFactsRelative}: missing active thumbnailSrc for ${episodeId}: ${runtimeSrc}`);
  }

  expectFile(
    repoPath('public', ...runtimeSrc.split('/').filter(Boolean)),
    `Runtime WebP for ${episodeId}`,
  );
  expectFile(
    repoPath(
      'brand',
      'assets',
      'episode-gallery',
      activeProofId,
      'source-renders',
      `${episodeId}-thumbnail-${activeProofId}-source.png`,
    ),
    `Source PNG for ${episodeId}`,
  );
}

for (const src of thumbnailSrcs) {
  if (!src.startsWith(activeRuntimeRoot)) {
    errors.push(`${siteFactsRelative}: thumbnailSrc must use ${activeRuntimeRoot}; found ${src}`);
  }

  if (!src.endsWith('.webp')) {
    errors.push(`${siteFactsRelative}: thumbnailSrc must point at a WebP runtime asset; found ${src}`);
  }
}

for (const [index, alt] of thumbnailAlts.entries()) {
  for (const { label, pattern } of bannedAltTerms) {
    if (pattern.test(alt)) {
      errors.push(`${siteFactsRelative}: thumbnailAlt ${index + 1} reintroduces banned ${label} language: "${alt}"`);
    }
  }
}

const activeProofRoot = repoPath('brand', 'assets', 'episode-gallery', activeProofId);
const activeProvenancePath = repoPath('brand', 'assets', 'episode-gallery', activeProofId, 'provenance.md');
expectFile(activeProvenancePath, 'Active proof provenance');

if (fs.existsSync(activeProvenancePath)) {
  const activeProvenance = readText(activeProvenancePath);

  if (/^Status:\s*rejected/im.test(activeProvenance)) {
    errors.push(`${displayPath(activeProvenancePath)}: active proof provenance is marked rejected.`);
  }

  const requiredProvenancePhrases = [
    'Status: active reference.',
    'Use one dominant primary subject only.',
    'Omit evidence-object and system-clue clutter',
    'Card pills and local titles remain the context carrier',
  ];

  for (const phrase of requiredProvenancePhrases) {
    if (!activeProvenance.includes(phrase)) {
      errors.push(`${displayPath(activeProvenancePath)}: missing provenance phrase "${phrase}".`);
    }
  }
}

const rejectedProofPath = repoPath(
  'brand',
  'assets',
  'episode-gallery',
  'proof-v5-ink-lit-regenerated',
  'provenance.md',
);

if (fs.existsSync(rejectedProofPath)) {
  const rejectedProof = readText(rejectedProofPath);

  if (!/^Status:\s*rejected\/non-promotable\./im.test(rejectedProof)) {
    errors.push(`${displayPath(rejectedProofPath)}: proof-v5 must remain marked rejected/non-promotable.`);
  }
} else {
  errors.push('Rejected proof-v5 provenance is missing.');
}

expectFile(activeProofRoot, 'Active proof folder');
expectFile(
  repoPath('output', 'episode-gallery', activeProofId, 'first-eight-contact-sheet-320x180.png'),
  '320x180 contact sheet',
);
expectFile(
  repoPath('output', 'episode-gallery', activeProofId, 'first-eight-preview-168x94.png'),
  '168x94 contact sheet',
);

const proofShortId = activeProofId.match(/^proof-v\d+/)?.[0] ?? activeProofId;
expectFile(repoPath('output', 'playwright', `${proofShortId}-home-desktop.png`), 'Desktop homepage QA screenshot');
expectFile(repoPath('output', 'playwright', `${proofShortId}-home-mobile.png`), 'Mobile homepage QA screenshot');

if (errors.length > 0) {
  console.error(errors.join('\n'));
  process.exit(1);
}

console.log(
  `Episode-gallery thumbnail validation passed for ${expectedEpisodes.length} thumbnails using ${activeProofId}.`,
);
