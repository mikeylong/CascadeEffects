import designSystemContract from '@/brand/contracts/design-system.contract.json';
import illustrationContract from '@/brand/contracts/illustration.contract.json';
import signalTokens from '@/brand/cascade-effects-signal.style-system.json';

export type BrandingRequirement = {
  label: string;
  value: string;
};

export type BrandingAsset = {
  role: string;
  title: string;
  status: string;
  statusLabel: string;
  dimensions: string;
  format: string;
  limit: string;
  usage: string;
  src: string;
  width: number;
  height: number;
  downloadHref: string;
};

type ColorToken = {
  $value: {
    hex: string;
  };
  $description: string;
};

type PaletteTokenSource = {
  group: string;
  key: string;
  label: string;
  token: ColorToken;
  usage: string;
};

export type BrandNavigationItem = {
  id: string;
  label: string;
};

export type BrandGuidelineGroup = {
  eyebrow: string;
  title: string;
  summary: string;
  items: readonly string[];
};

export type BrandPaletteSwatch = {
  group: string;
  key: string;
  label: string;
  hex: string;
  description: string;
  usage: string;
};

export type BrandReferenceRow = {
  label: string;
  value: string;
};

export type BrandTypographyFamilySpecimen = {
  key: string;
  label: string;
  sample: string;
  stack: string;
  guidance: string;
};

export type BrandTypographyMetadata = {
  token: string;
  family: string;
  size: string;
  weight: string;
  lineHeight: string;
  tracking: string;
};

export type BrandTypographyRenderStyle = {
  fontFamily: string;
  fontSize: string;
  fontWeight: string;
  letterSpacing: string;
  lineHeight: string;
  textTransform: 'none' | 'uppercase';
};

export type BrandTypographyRole = {
  key: string;
  label: string;
  sample: string;
  usage: string;
  avoid: string;
  metadata: BrandTypographyMetadata;
  renderStyle: BrandTypographyRenderStyle;
};

export type BrandTypographyHierarchyExample = {
  key: string;
  label: string;
  eyebrow: string;
  title: string;
  body: string;
  meta?: string;
};

export type BrandReferenceImage = {
  title: string;
  src: string;
  width: number;
  height: number;
  alt: string;
  note: string;
};

const assetRoot = '/brand/youtube-channel/advanced-features-corrected-banner-20260520T210213Z';

export const youtubeChannelBrandingPackage = {
  packageId: 'youtube_channel_brand_assets_advanced_features_corrected_banner_20260520T210213Z',
  route: '/design-system',
  status: 'review_required',
  mayAdvance: false,
  youtubeStudioUpdated: false,
  createdUtc: '2026-05-20T21:02:13Z',
  localPackagePath:
    '/Users/mike/CascadeEffects/channel/season-01/youtube_channel_brand_assets_advanced_features_corrected_banner_20260520T210213Z',
  summary:
    'The current YouTube channel banner, profile image, and video watermark package, gathered here for visual review and manual upload.',
  heroImage: `${assetRoot}/channel-banner-strip-2048x340.png`,
  heroImageAlt:
    'Kept Cascade Effects channel banner strip with evidence desk, Cascade of Effects title, shuttle, and liner in a folded-paper identity world.',
  contactSheet: `${assetRoot}/youtube-channel-branding-advanced-features-corrected-banner-contact-sheet.png`,
  previews: {
    bannerSafeOverlay: `${assetRoot}/channel-banner-safe-zone-overlay-2048x1152.png`,
    bannerTitleSafeCrop: `${assetRoot}/channel-banner-title-safe-crop-1235x338.png`,
    profile98: `${assetRoot}/profile-icon-youtube-circle-98px-dark.png`,
    profile176: `${assetRoot}/profile-icon-youtube-circle-176px-dark.png`,
    profile320: `${assetRoot}/profile-icon-youtube-circle-320px-dark.png`,
    watermarkOverlay1280: `${assetRoot}/video-watermark-overlay-preview-1280x720.png`,
    watermarkOverlay1920: `${assetRoot}/video-watermark-overlay-preview-1920x1080.png`,
  },
  sourcePrompt:
    'Use the kept evidence_desk_balanced_precision banner from youtube_channel_banner_evidence_desk_balanced_precision_tighten_20260518T224129Z. Do not regenerate the channel banner for this package. Keep the approved evidence-desk left concept, low shuttle terrain, accepted Paper Architecture title lockup, compliant 2048 x 1152 upload wrapper, and no YouTube Studio mutation.',
  manualChecklist: [
    'Review the banner, profile image, and watermark together.',
    'Confirm the profile image and watermark before upload.',
    'Open YouTube Studio, then Customization, then Branding.',
    'Upload the banner, profile image, and watermark manually.',
    'Confirm how the assets crop on desktop, mobile, and TV.',
    'Save the final upload receipts with the channel package.',
  ],
} as const;

export const brandReferenceNavigation: BrandNavigationItem[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'art-system', label: 'Art Direction' },
  { id: 'palette', label: 'Palette' },
  { id: 'typography', label: 'Typography' },
  { id: 'image-generation', label: 'Image Guidance' },
  { id: 'text-policy', label: 'Title & Type' },
  { id: 'platform-rules', label: 'Use Cases' },
  { id: 'youtube-package', label: 'YouTube Assets' },
  { id: 'qa', label: 'Review Checklist' },
];

export const brandReferenceSummary = {
  title: 'Cascade Effects Design System',
  activeProfile: illustrationContract.profileId,
  summary:
    'A practical design system reference for Cascade Effects illustration, color, typography, asset surfaces, and the current YouTube channel package.',
  position:
    'Use this page to keep the work recognizably Cascade Effects without turning every asset into a one-off style decision.',
} as const;

const paletteSources: PaletteTokenSource[] = [
  {
    group: 'Base',
    key: 'ink',
    label: 'Deep ink',
    token: signalTokens.color.base.ink,
    usage: 'Primary field for ink-lit page backgrounds and structural darkness.',
  },
  {
    group: 'Base',
    key: 'inkPanel',
    label: 'Ink panel',
    token: signalTokens.color.base.inkPanel,
    usage: 'Raised dark surface for panels, reference cards, and metadata bands.',
  },
  {
    group: 'Base',
    key: 'paper',
    label: 'Warm cream paper',
    token: signalTokens.color.base.white,
    usage: 'Paper forms, light title fill, and high-contrast foreground on ink fields.',
  },
  {
    group: 'Base',
    key: 'secondaryText',
    label: 'Muted cream-blue',
    token: signalTokens.color.base.secondaryText,
    usage: 'Secondary copy on dark surfaces where full cream is too loud.',
  },
  {
    group: 'Depth',
    key: 'overlaySlate',
    label: 'Lavender shadow',
    token: signalTokens.color.base.overlaySlate,
    usage: 'Paper shadows, model depth planes, and secondary identity overlays.',
  },
  {
    group: 'Depth',
    key: 'panelFrame',
    label: 'Blue-lavender frame',
    token: signalTokens.color.base.panelFrame,
    usage: 'Editorial borders, support surfaces, and quiet UI structure.',
  },
  {
    group: 'Accent',
    key: 'signal',
    label: 'Powder cyan signal',
    token: signalTokens.color.accent.signal,
    usage: 'Dry vellum signal traces and causal emphasis, not liquid effects.',
  },
  {
    group: 'Accent',
    key: 'alert',
    label: 'Restrained coral alert',
    token: signalTokens.color.accent.alert,
    usage: 'Small warning, breakage, and failure cues only.',
  },
];

export const brandPalette: BrandPaletteSwatch[] = paletteSources.map(({ token, ...source }) => ({
  ...source,
  hex: token.$value.hex,
  description: token.$description,
}));

export const brandTypographyFamilies: BrandReferenceRow[] = [
  {
    label: 'Display / title',
    value: `${designSystemContract.typography.display} Stack: ${signalTokens.fontFamily.display.$value.join(', ')}.`,
  },
  {
    label: 'Body',
    value: `${designSystemContract.typography.body} Stack: ${signalTokens.fontFamily.body.$value.join(', ')}.`,
  },
  {
    label: 'Technical labels',
    value: `${designSystemContract.typography.technical} Use for compact labels, metadata, and exact asset specs.`,
  },
];

export const brandTypographyRules: BrandReferenceRow[] = designSystemContract.typography.rules.map(
  (rule, index) => ({
    label: `Rule ${index + 1}`,
    value: rule,
  }),
);

type DimensionToken = {
  $value: {
    value: number;
    unit: string;
  };
};

type FontFamilyToken = {
  $value: readonly string[];
};

type FontWeightToken = {
  $value: number;
};

type NumberToken = {
  $value: number;
};

type TypographyTokenValue = {
  fontFamily: string;
  fontSize: string;
  fontWeight: string;
  letterSpacing: string;
  lineHeight: string;
};

type TypographyToken = {
  $value: TypographyTokenValue;
};

type BrandTypographyRoleSource = Omit<BrandTypographyRole, 'metadata' | 'renderStyle'>;

const dimensionToLabel = (token: DimensionToken): string =>
  `${token.$value.value}${token.$value.unit}`;

const fontFamilyToLabel = (token: FontFamilyToken): string => token.$value.join(', ');

const fontFamilyToCss = (token: FontFamilyToken): string =>
  token.$value
    .map((font) => {
      if (['sans-serif', 'monospace', 'serif', 'system-ui'].includes(font)) {
        return font;
      }

      return `"${font}"`;
    })
    .join(', ');

const typographyTokens = signalTokens.typography as unknown as Record<string, TypographyToken>;

const tokenLabelResolvers: Record<string, () => string> = {
  'fontFamily.display': () => fontFamilyToLabel(signalTokens.fontFamily.display),
  'fontFamily.body': () => fontFamilyToLabel(signalTokens.fontFamily.body),
  'fontFamily.ui': () => fontFamilyToLabel(signalTokens.fontFamily.ui),
  'size.font.caption': () => dimensionToLabel(signalTokens.size.font.caption),
  'size.font.label': () => dimensionToLabel(signalTokens.size.font.label),
  'size.font.body': () => dimensionToLabel(signalTokens.size.font.body),
  'size.font.bodyLg': () => dimensionToLabel(signalTokens.size.font.bodyLg),
  'size.font.cardTitle': () => dimensionToLabel(signalTokens.size.font.cardTitle),
  'size.font.section': () => dimensionToLabel(signalTokens.size.font.section),
  'size.font.display': () => dimensionToLabel(signalTokens.size.font.display),
  'size.font.thumbnail': () => dimensionToLabel(signalTokens.size.font.thumbnail),
  'size.font.hero': () => dimensionToLabel(signalTokens.size.font.hero),
  'size.font.monogram': () => dimensionToLabel(signalTokens.size.font.monogram),
  'fontWeight.display': () => `${(signalTokens.fontWeight.display as FontWeightToken).$value}`,
  'fontWeight.regular': () => `${(signalTokens.fontWeight.regular as FontWeightToken).$value}`,
  'fontWeight.medium': () => `${(signalTokens.fontWeight.medium as FontWeightToken).$value}`,
  'fontWeight.semibold': () => `${(signalTokens.fontWeight.semibold as FontWeightToken).$value}`,
  'fontWeight.bold': () => `${(signalTokens.fontWeight.bold as FontWeightToken).$value}`,
  'size.tracking.tight': () => dimensionToLabel(signalTokens.size.tracking.tight),
  'size.tracking.normal': () => dimensionToLabel(signalTokens.size.tracking.normal),
  'size.tracking.ui': () => dimensionToLabel(signalTokens.size.tracking.ui),
  'size.tracking.caps': () => dimensionToLabel(signalTokens.size.tracking.caps),
  'size.tracking.wide': () => dimensionToLabel(signalTokens.size.tracking.wide),
  'number.lineHeight.tight': () => `${(signalTokens.number.lineHeight.tight as NumberToken).$value}`,
  'number.lineHeight.snug': () => `${(signalTokens.number.lineHeight.snug as NumberToken).$value}`,
  'number.lineHeight.compact': () =>
    `${(signalTokens.number.lineHeight.compact as NumberToken).$value}`,
  'number.lineHeight.reading': () =>
    `${(signalTokens.number.lineHeight.reading as NumberToken).$value}`,
};

const tokenCssResolvers: Record<string, () => string> = {
  ...tokenLabelResolvers,
  'fontFamily.display': () => fontFamilyToCss(signalTokens.fontFamily.display),
  'fontFamily.body': () => fontFamilyToCss(signalTokens.fontFamily.body),
  'fontFamily.ui': () => fontFamilyToCss(signalTokens.fontFamily.ui),
};

const resolveTokenReference = (
  value: string,
  resolvers: Record<string, () => string>,
): string => {
  const match = value.match(/^\{(.+)\}$/);

  if (!match) {
    return value;
  }

  return resolvers[match[1]]?.() ?? value;
};

const createTypographyMetadata = (key: string): BrandTypographyMetadata => {
  const token = typographyTokens[key];

  return {
    token: `typography.${key}`,
    family: resolveTokenReference(token.$value.fontFamily, tokenLabelResolvers),
    size: resolveTokenReference(token.$value.fontSize, tokenLabelResolvers),
    weight: resolveTokenReference(token.$value.fontWeight, tokenLabelResolvers),
    lineHeight: resolveTokenReference(token.$value.lineHeight, tokenLabelResolvers),
    tracking: resolveTokenReference(token.$value.letterSpacing, tokenLabelResolvers),
  };
};

const createTypographyRenderStyle = (
  key: string,
  textTransform: BrandTypographyRenderStyle['textTransform'] = 'none',
): BrandTypographyRenderStyle => {
  const token = typographyTokens[key];

  return {
    fontFamily: resolveTokenReference(token.$value.fontFamily, tokenCssResolvers),
    fontSize: resolveTokenReference(token.$value.fontSize, tokenCssResolvers),
    fontWeight: resolveTokenReference(token.$value.fontWeight, tokenCssResolvers),
    letterSpacing: resolveTokenReference(token.$value.letterSpacing, tokenCssResolvers),
    lineHeight: resolveTokenReference(token.$value.lineHeight, tokenCssResolvers),
    textTransform,
  };
};

export const brandTypographyFamilySpecimens: BrandTypographyFamilySpecimen[] = [
  {
    key: 'display',
    label: 'Display / title',
    sample: 'Cascade of Effects',
    stack: fontFamilyToLabel(signalTokens.fontFamily.display),
    guidance: designSystemContract.typography.display,
  },
  {
    key: 'body',
    label: 'Body copy',
    sample: 'Explain the system plainly, then let the visual evidence do the rest.',
    stack: fontFamilyToLabel(signalTokens.fontFamily.body),
    guidance: designSystemContract.typography.body,
  },
  {
    key: 'metadata',
    label: 'Metadata labels',
    sample: 'SAFE AREA / 2048 x 1152',
    stack: 'IBM Plex Mono, monospace',
    guidance: designSystemContract.typography.technical,
  },
];

const brandTypographyRoleSources: BrandTypographyRoleSource[] = [
  {
    key: 'wordmark',
    label: 'Wordmark',
    sample: 'Cascade of Effects',
    usage: 'The Cascade Effects name in title-bearing identity art.',
    avoid: 'Do not trust generated source art for final spelling.',
  },
  {
    key: 'hero',
    label: 'Hero',
    sample: 'Cascade Effects',
    usage: 'Large first-viewport headlines and title-bearing hero compositions.',
    avoid: 'Avoid long taglines or decorative display copy in hero scale.',
  },
  {
    key: 'thumbnail',
    label: 'Thumbnail',
    sample: 'Challenger',
    usage: 'Large title treatment for small preview surfaces when titles are approved.',
    avoid: 'Keep episode thumbnails text-free unless a package explicitly approves text.',
  },
  {
    key: 'monogram',
    label: 'Monogram',
    sample: 'CE',
    usage: 'Compact CE mark or short identity lockups.',
    avoid: 'Do not force the full title into icon-size spaces.',
  },
  {
    key: 'sectionTitle',
    label: 'Section title',
    sample: 'Art Direction',
    usage: 'Major page-section headings inside the website design system.',
    avoid: 'Avoid decorative tracking or oversized editorial headlines inside dense sections.',
  },
  {
    key: 'cardTitle',
    label: 'Card title',
    sample: 'Current Channel Branding',
    usage: 'Repeated item titles in cards, asset panels, and gallery surfaces.',
    avoid: 'Avoid making repeated cards compete with page-level headings.',
  },
  {
    key: 'body',
    label: 'Body',
    sample: 'Explain the visible system without turning the page into a forensic wall.',
    usage: 'Primary explanatory copy and long-form reference text.',
    avoid: 'Avoid all-caps paragraphs or dense metadata language in body copy.',
  },
  {
    key: 'bodySmall',
    label: 'Small body',
    sample: 'Secondary notes stay compact and calm.',
    usage: 'Captions, secondary notes, and compact supporting copy.',
    avoid: 'Avoid using small body for primary instructions.',
  },
  {
    key: 'uiLabel',
    label: 'UI label',
    sample: 'Safe Area',
    usage: 'Interface labels, field-style metadata, and short action descriptors.',
    avoid: 'Avoid sentence-length labels; move detail into body copy.',
  },
  {
    key: 'seriesTag',
    label: 'Series tag',
    sample: 'First Eight',
    usage: 'Short editorial tags and recurring series markers.',
    avoid: 'Avoid using tags as decorative badges without editorial meaning.',
  },
  {
    key: 'callout',
    label: 'Callout',
    sample: 'Manual upload only',
    usage: 'Small emphasized notes, warnings, and supporting labels.',
    avoid: 'Avoid turning coral callouts into the dominant page color.',
  },
  {
    key: 'lowerThirdTitle',
    label: 'Lower-third title',
    sample: 'Hidden Systems, Visible Consequences',
    usage: 'Title layer for lower-third style identity or video-adjacent overlays.',
    avoid: 'Avoid multi-line paragraphs in lower-third title space.',
  },
  {
    key: 'lowerThirdMeta',
    label: 'Lower-third metadata',
    sample: 'Episode 04 / Engineering Drift',
    usage: 'Secondary metadata layer paired with lower-third titles.',
    avoid: 'Avoid metadata that is longer than the title it supports.',
  },
];

export const brandTypographyRoles: BrandTypographyRole[] = brandTypographyRoleSources
  .filter((role) => role.key in signalTokens.typography)
  .map((role) => ({
    ...role,
    metadata: createTypographyMetadata(role.key),
    renderStyle: createTypographyRenderStyle(
      role.key,
      ['uiLabel', 'seriesTag', 'callout', 'lowerThirdMeta'].includes(role.key) ? 'uppercase' : 'none',
    ),
  }));

export const brandTypographyHierarchyExamples: BrandTypographyHierarchyExample[] = [
  {
    key: 'website',
    label: 'Website section',
    eyebrow: 'Art system',
    title: 'Ink-Lit Paper Architectures',
    body: 'A calm section title, readable body copy, and compact labels should make the reference page easy to scan.',
    meta: 'Design system reference',
  },
  {
    key: 'channel',
    label: 'Channel identity',
    eyebrow: 'Channel art',
    title: 'Cascade of Effects',
    body: 'Title-bearing identity assets use deterministic local type over calm paper zones, never generated spelling.',
    meta: 'Banner / profile / watermark',
  },
  {
    key: 'lowerThird',
    label: 'Lower third',
    eyebrow: 'Video-adjacent',
    title: 'Hidden Systems, Visible Consequences',
    body: 'Lower-third type pairs a compact title with metadata that stays secondary.',
    meta: 'Episode 04 / Engineering Drift',
  },
];

export const brandArtGuidelines: BrandGuidelineGroup[] = [
  {
    eyebrow: 'House style',
    title: 'Ink-lit Paper Architectures',
    summary:
      'Cascade Effects visuals should feel like small physical models lit inside a dark editorial space.',
    items: [
      'Deep ink-blue fields with cream folded-paper forms and lavender paper shadows.',
      'Foam-core surfaces, scored seams, translucent vellum, gouache/pastel pigment, and controlled model lighting.',
      'Clean low-detail public anchors that remain readable at small sizes.',
      'One or two terraces or dry signal sheets at most; avoid dense evidence-board clutter.',
    ],
  },
  {
    eyebrow: 'Recognizability',
    title: 'Public Anchor First',
    summary:
      'Start with the thing a viewer recognizes, then add evidence and system details only when the format can hold them.',
    items: [
      `Useful anchors include ${illustrationContract.subjects.publicAnchors.join(', ')}.`,
      `Supporting details can include ${illustrationContract.subjects.evidenceObjects.join(', ')}.`,
      'Small website cards should usually show one dominant subject and let the surrounding page carry the context.',
    ],
  },
  {
    eyebrow: 'Material control',
    title: 'Clean Tactile Paper',
    summary:
      'The texture should feel tactile and handmade without becoming noisy or gritty.',
    items: [
      'Use subtle paper fiber only with clean low-detail paper planes.',
      'Let cream paper forms separate clearly from deep ink fields.',
      'Keep cyan as dry vellum signal flow; do not let it read as water.',
      'Use coral sparingly for warning or failure cues.',
    ],
  },
];

export const brandImageGenerationGuidelines: BrandGuidelineGroup[] = [
  {
    eyebrow: 'Working order',
    title: 'Art First, Type Second',
    summary:
      'Let the image carry the world and atmosphere. Add final titles and platform layout afterward.',
    items: [
      'Generate or select source art without readable title text, labels, logos, or watermarks unless the asset is explicitly a title-bearing brand image.',
      'Set exact titles locally so spelling, scale, and placement stay controlled.',
      'After a strong baseline is approved, make small changes as careful composites instead of regenerating the whole image.',
      'Preserve the approved palette, material feel, object density, and texture level between revisions.',
    ],
  },
  {
    eyebrow: 'Prompt shape',
    title: 'Say What The Material Is',
    summary:
      'Image instructions should describe the physical model, the lighting, and what must stay quiet.',
    items: [
      'Use ink-lit Paper Architectures, deep ink-blue fields, cream folded paper, lavender shadows, cyan vellum signal, and restrained coral accents.',
      'Ask for subtle paper fiber only, clean low-detail paper planes, and controlled model lighting.',
      'Keep cyan marks dry and signal-like, not watery or liquid.',
    ],
  },
  {
    eyebrow: 'Where it belongs',
    title: 'Use The Right Lane',
    summary:
      'This style is for the website and channel identity. Video-production art has its own workflows.',
    items: [
      'Allowed: CascadeEffects.tv website assets, YouTube channel-level branding, and CascadeEffects.tv website thumbnail-gallery images.',
      'Do not automatically use it for Shorts, long-form video visuals, chapter cards, effect maps, motion proofs, or episode thumbnails.',
      'For website gallery thumbnails, keep one strong subject and avoid extra evidence clutter.',
    ],
  },
];

export const brandAvoidList: readonly string[] = [
  'Gritty documentary mood, noir lighting, smoke, gore, explosions, or disaster spectacle.',
  'Photoreal water, waterfalls, rivers, streams, liquid spills, or glowing watercourse effects.',
  'Noisy paper grain, speckle, grit, sandy texture, AI shimmer, or texture that competes with the subject.',
  'Plastic toy gloss, mascot styling, flat icon art, or procedural placeholder art.',
  'Readable generated labels, logos, watermarks, or title text unless the asset is an approved title-bearing brand image.',
  'Decorative cyan or coral tags, flags, stickers, cubes, or warning tabs in small website gallery thumbnails.',
];

export const brandTextPolicy: BrandReferenceRow[] = [
  {
    label: 'Exact title',
    value: designSystemContract.titleTreatment.exactTitle,
  },
  {
    label: 'Composition',
    value: 'Add final titles locally after the image is selected, except for approved title-bearing brand references.',
  },
  {
    label: 'Style',
    value: designSystemContract.titleTreatment.style.join('; '),
  },
  {
    label: 'Rules',
    value:
      'Do not add taglines to launch package assets. Profile icons should stay mark-only. Episode-gallery images should stay text-free.',
  },
];

export const brandPlatformRules: BrandReferenceRow[] = [
  {
    label: 'Allowed surfaces',
    value:
      'CascadeEffects.tv website heroes/section art/open graph surfaces, YouTube channel-level branding, and CascadeEffects.tv website gallery thumbnails.',
  },
  {
    label: 'Use another style for',
    value:
      'Shorts visuals, long-form video visuals, Living Covers, chapter cards, effect maps, motion proofs, final frames, and episode thumbnails unless a workflow explicitly says otherwise.',
  },
  {
    label: 'Website gallery',
    value:
      'Use one dominant primary subject. Let the card title and page context carry the case details.',
  },
  {
    label: 'Safe zones',
    value: designSystemContract.layout.safeZones.join(' '),
  },
];

export const brandQaGuidelines: BrandReferenceRow[] = [
  {
    label: 'Brand fit',
    value:
      'The image should immediately feel like ink-lit Paper Architecture: deep field, cream forms, lavender depth, clean model lighting.',
  },
  {
    label: 'Small-size read',
    value:
      'The main subject and title, when present, should still read in small previews.',
  },
  {
    label: 'Texture restraint',
    value:
      'Paper texture should be subtle. If texture is the first thing you notice, the asset needs another pass.',
  },
  {
    label: 'No accidental text',
    value:
      'Source art should not contain stray labels, logos, watermarks, or misspelled generated title text.',
  },
  {
    label: 'Crop safety',
    value:
      'Important marks, titles, and subjects should stay inside the visible area for the platform where the asset will be used.',
  },
  {
    label: 'Current assets',
    value:
      'Use the current corrected banner and clean-edge profile source for YouTube channel branding review.',
  },
];

export const brandReferenceImages: BrandReferenceImage[] = [
  {
    title: 'Active homepage identity reference',
    src: '/brand/homepage-hero-paper-cloudless-clean-surface-desktop-v4.png',
    width: 1672,
    height: 941,
    alt: 'Cascade Effects ink-lit Paper Architecture homepage reference with folded-paper title and system-failure anchors.',
    note: 'Active title-bearing website identity reference; use for brand fit, not as a universal crop.',
  },
  {
    title: 'Mobile identity reference',
    src: '/brand/homepage-hero-paper-cloudless-clean-surface-mobile-v4.png',
    width: 916,
    height: 1717,
    alt: 'Mobile Cascade Effects ink-lit Paper Architecture reference with folded-paper title and vertical crop.',
    note: 'Phone-scale identity crop showing how the same material system survives narrow layouts.',
  },
  {
    title: 'Current YouTube banner strip',
    src: youtubeChannelBrandingPackage.heroImage,
    width: 2048,
    height: 340,
    alt: youtubeChannelBrandingPackage.heroImageAlt,
    note: 'Kept corrected channel banner strip retained for the YouTube package section.',
  },
];

export const brandingRequirements: BrandingRequirement[] = [
  {
    label: 'Banner upload',
    value: '2048 x 1152 px minimum; 2560 x 1440 px recommended.',
  },
  {
    label: 'Banner safe area',
    value: '1235 x 338 px at minimum size; 1544 x 423 px at 2560 x 1440.',
  },
  {
    label: 'Banner file size',
    value: '6 MB or smaller; no borders, frames, or guide overlays in final uploads.',
  },
  {
    label: 'Profile image',
    value: 'PNG/JPG/GIF/BMP, no animated GIF, 15 MB or smaller, renders at 98 x 98 px.',
  },
  {
    label: 'Watermark',
    value: 'Square image, 150 x 150 px minimum, under 1 MB.',
  },
];

export const brandingAssets: BrandingAsset[] = [
  {
    role: 'Banner',
    title: 'Kept Channel Banner',
    status: 'keep',
    statusLabel: 'Approved banner',
    dimensions: '2048 x 340 strip; 2048 x 1152 and 2560 x 1440 upload wrappers',
    format: 'PNG',
    limit: '< 6 MB',
    usage:
      'Approved evidence-desk banner treatment; keep YouTube Studio unchanged until the full package is ready.',
    src: `${assetRoot}/channel-banner-strip-2048x340.png`,
    width: 2048,
    height: 340,
    downloadHref: `${assetRoot}/channel-banner-upload-2048x1152.png`,
  },
  {
    role: 'Profile',
    title: 'Profile Image Derivative',
    status: 'review_required',
    statusLabel: 'Needs final approval',
    dimensions: '800 x 800 square',
    format: 'PNG, RGB, no alpha',
    limit: '< 15 MB',
    usage: 'Clean-edge square upload source; YouTube applies the circular avatar crop.',
    src: `${assetRoot}/profile-icon-800x800-square-clean-edge-no-alpha.png`,
    width: 800,
    height: 800,
    downloadHref: `${assetRoot}/profile-icon-800x800-square-clean-edge-no-alpha.png`,
  },
  {
    role: 'Watermark',
    title: 'Video Watermark',
    status: 'review_required',
    statusLabel: 'Needs final approval',
    dimensions: '800 x 800 and 150 x 150 square',
    format: 'PNG, RGBA',
    limit: '< 1 MB',
    usage: 'Transparent CE mark for YouTube video watermark placement.',
    src: `${assetRoot}/video-watermark-800x800.png`,
    width: 800,
    height: 800,
    downloadHref: `${assetRoot}/video-watermark-800x800.png`,
  },
];
