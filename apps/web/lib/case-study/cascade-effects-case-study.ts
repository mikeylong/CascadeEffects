import {
  brandPalette,
  brandingAssets,
  youtubeChannelBrandingPackage,
} from '@/lib/brand/youtube-channel-branding';
import { siteIdentity } from '@/lib/site-facts';

export type CaseStudySection = {
  eyebrow: string;
  title: string;
  body: readonly string[];
};

export type CaseStudyExploration = {
  title: string;
  period: string;
  summary: string;
  lesson: string;
};

export type CaseStudyConstraint = {
  label: string;
  value: string;
};

export type CaseStudyStackItem = {
  title: string;
  summary: string;
  detail: string;
  visual: 'research' | 'draft' | 'review' | 'voice' | 'publish';
};

export type CaseStudyChange = {
  before: string;
  after: string;
};

export type CaseStudyProofImage = {
  src: string;
  alt: string;
  label: string;
  note: string;
};

export type CaseStudyMotionClip = {
  src: string;
  poster: string;
  label: string;
  note: string;
};

export type CaseStudyMotionSection = {
  eyebrow: string;
  title: string;
  body: string;
  lesson: string;
  clips: readonly CaseStudyMotionClip[];
};

export type CaseStudyCurrentArtifact = {
  title: string;
  label: string;
  note: string;
  src: string;
  alt: string;
  width: number;
  height: number;
  variant: 'banner' | 'square' | 'video' | 'gallery';
};

export type CaseStudyCurrentPaletteSwatch = {
  label: string;
  hex: string;
  usage: string;
};

export type CaseStudyIdentityPoint = {
  title: string;
  body: string;
};

export type CaseStudyIdentityVisual = {
  src: string;
  alt: string;
  label: string;
  note: string;
  featured?: boolean;
};

export type CaseStudyIdentitySection = {
  title: string;
  body: string;
  visuals: readonly CaseStudyIdentityVisual[];
  points: readonly CaseStudyIdentityPoint[];
};

export const caseStudyHero = {
  eyebrow: 'Channel case study',
  title: `${siteIdentity.title}`,
  dek:
    'How a familiar-disaster premise became a channel identity, research method, voiceover lane, and production pipeline.',
  question:
    'What changed, who failed to notice, and how did the system turn that blindness into consequence?',
  image: '/brand/homepage-hero-paper-cloudless-clean-surface-desktop-v8.png',
  mobileImage: '/brand/homepage-hero-paper-cloudless-clean-surface-mobile-v8.png',
  imageAlt:
    'Cascade Effects ink-lit paper architecture scene with folded systems, public anchors, and dry signal paths.',
} as const;

export const caseStudyOpening: readonly string[] = [
  'Cascade Effects starts with stories people think they know, then looks for the shift underneath the headline: what changed, who missed it, and why that miss mattered.',
  'The work had to separate four jobs that are easy to blur: editorial argument, public identity, voice production, and source-aware video. Each needed its own rules before the channel could repeat the format.',
];

export const caseStudySections: readonly CaseStudySection[] = [
  {
    eyebrow: 'Premise',
    title: 'Start with the shift inside the system',
    body: [
      'Every episode has to show the change before it shows the consequence. Challenger cannot stop at a launch disaster. Therac-25 cannot stop at a software failure. Titanic cannot stop at a shipwreck.',
      'The known subject gets the viewer in the door. The episode earns its time by making the cause chain underneath it easier to see.',
    ],
  },
  {
    eyebrow: 'Design problem',
    title: 'Avoid the familiar disaster traps',
    body: [
      'The early versions kept running into the same risks: timeline recap, disaster montage, generated spectacle, or a polished explainer that could belong to any channel.',
      'The useful standard became calmer and stricter: stay evidence-led, keep the cause chain readable, and make each handoff reviewable before it moves forward.',
    ],
  },
  {
    eyebrow: 'Production problem',
    title: 'Turn research into repeatable output',
    body: [
      'Research had to become a writer packet. The packet had to become a script. The script had to survive critique and fact-checking. The audio had to sound like the channel, not like a temporary tool test.',
      'That sequence turned into separate lanes for research, scripts, voiceover, visuals, metadata, publishing, and human keep points.',
    ],
  },
];

export const caseStudyExplorations: readonly CaseStudyExploration[] = [
  {
    title: 'Particle simulation',
    period: 'Pre-identity exploration',
    summary:
      'Particle workbench passes tested whether failure could read as drift, break-up, or dissolution.',
    lesson:
      'The effect had energy, but without evidence it turned the mechanism into atmosphere.',
  },
  {
    title: 'Collage and generated-image stress tests',
    period: 'Rejected archive direction',
    summary:
      'Collage boards and FLUX-era image tests pushed the work into dense symbols, pasted references, and overloaded metaphor.',
    lesson:
      'They made the lesson obvious: too many visual claims make the cause chain harder to read.',
  },
  {
    title: 'What survived',
    period: 'Working constraint',
    summary:
      'The useful discovery was not a single archived style. It was the need for boundaries.',
    lesson:
      'Brand identity, source-preserving video, exact text, and publishable review artifacts each needed their own lane.',
  },
];

export const caseStudyImageToVideo: CaseStudyMotionSection = {
  eyebrow: 'Image-to-video tests',
  title: 'The stills did not stay still',
  body:
    'Another archive thread started with generated still frames, then pushed them through image-to-video. Some results were funny because the failure was immediate: the model did not move the frame so much as rewrite it.',
  lesson:
    'That changed the pipeline. A still could be promising and still fail in motion, so still approval and motion approval became separate decisions.',
  clips: [
    {
      src: '/brand/case-study/image-to-video/plume-invented-i2v-reject.mp4',
      poster: '/brand/case-study/image-to-video/plume-invented-i2v-reject.jpg',
      label: 'Plume invented',
      note: 'A normal-operations still picks up launch escalation the story did not ask for.',
    },
    {
      src: '/brand/case-study/image-to-video/hand-intrusion-i2v-reject.mp4',
      poster: '/brand/case-study/image-to-video/hand-intrusion-i2v-reject.jpg',
      label: 'Hand enters frame',
      note: 'A clean evidence tray gains a new object at the edge of the shot.',
    },
    {
      src: '/brand/case-study/image-to-video/tray-rewrite-i2v-reject.mp4',
      poster: '/brand/case-study/image-to-video/tray-rewrite-i2v-reject.jpg',
      label: 'Tray rewrites itself',
      note: 'The evidence layout collapses into a different physical object.',
    },
    {
      src: '/brand/case-study/image-to-video/status-wall-silhouette-i2v-reject.mp4',
      poster: '/brand/case-study/image-to-video/status-wall-silhouette-i2v-reject.jpg',
      label: 'Silhouette appears',
      note: 'A wordless status-wall frame acquires a person the still never contained.',
    },
  ],
} as const;

export const caseStudyPaperArchitecture: CaseStudyIdentitySection = {
  title: 'The public identity became Ink-Lit Paper Architecture',
  body:
    'Ink-Lit Paper Architecture gives the channel a public face without pretending to be footage. It uses folded paper structures, deep blue fields, cream forms, cyan signal paths, lavender shadows, restrained coral warnings, and locally composed titles.',
  visuals: [
    {
      src: '/brand/homepage-hero-paper-cloudless-clean-surface-desktop-v8.png',
      alt: 'Ink-lit Paper Architecture identity scene with folded paper systems on a deep blue field.',
      label: 'System field',
      note: 'The full identity world: field, paper, signal, shadow, and warning cues in one frame.',
      featured: true,
    },
    {
      src: '/brand/episode-gallery/proof-v6-ink-lit-subjects/therac-25-thumbnail-proof-v6-ink-lit-subjects.webp',
      alt: 'Ink-lit Paper Architecture gallery thumbnail for the Therac-25 episode.',
      label: 'Range proof',
      note: 'A medical-machine subject shows the identity moving beyond launch imagery.',
    },
    {
      src: '/brand/episode-gallery/proof-v6-ink-lit-subjects/challenger-thumbnail-proof-v6-ink-lit-subjects.webp',
      alt: 'Ink-lit Paper Architecture thumbnail for the Challenger episode.',
      label: 'Package surface',
      note: 'The same language scaled down to a gallery and channel package read.',
    },
  ],
  points: [
    {
      title: 'What it does',
      body:
        'It gives the channel a recognizable public face while keeping source footage and brand art separate.',
    },
    {
      title: 'Where it belongs',
      body:
        'Website surfaces, channel identity, package art, podcast assets, and selected gallery thumbnails.',
    },
    {
      title: 'Where it stops',
      body:
        'Shorts and long-form documentary video default to source-preserving or episode-specific visual rules.',
    },
  ],
} as const;

export const caseStudyConstraints: readonly CaseStudyConstraint[] = [
  {
    label: 'Source hygiene',
    value:
      'Research, source media, and archived experiments stay separate until a workflow explicitly imports them.',
  },
  {
    label: 'Local control',
    value:
      'Titles, captions, public copy, and final metadata are composed locally so exact words survive platform crops.',
  },
  {
    label: 'Style boundaries',
    value:
      'Paper Architecture is a brand system. Production video has stricter source-preserving rules.',
  },
  {
    label: 'Human keep points',
    value:
      'Draft, review, tighten, reject, and keep are explicit states. A file existing is never the same as approval.',
  },
];

export const caseStudyStack: readonly CaseStudyStackItem[] = [
  {
    title: 'Research',
    visual: 'research',
    summary:
      'Each episode starts with source collection, a mechanism frame, a writer packet, and named evidence gaps.',
    detail:
      'The research has to support one question: what shifted, who missed it, and why the miss mattered.',
  },
  {
    title: 'Script drafting',
    visual: 'draft',
    summary:
      'The writer packet becomes a long-form audio essay, then short-specific scripts when a feed-native cut is needed.',
    detail:
      'The script becomes production material for audio, captions, timing, visuals, and downstream QA.',
  },
  {
    title: 'Script review',
    visual: 'review',
    summary:
      'Drafts go through Claude or another frontier-model critique, fact-checking, integration or explicit deferral, and human approval before audio.',
    detail:
      'A locked script is not enough. The exact revision has to be approved for voiceover.',
  },
  {
    title: 'Voiceover',
    visual: 'voice',
    summary:
      'The voice lane moved from ChatGPT/OpenAI voice trials to ElevenLabs, then to the current Mike voice profile.',
    detail:
      'Reviewable audio includes the WAV, transcript, provider, model, voice profile, and provenance.',
  },
  {
    title: 'Video and publishing',
    visual: 'publish',
    summary:
      'Narration maps, director of photography research, visual research, shot plans, proofs, captions, metadata, and upload checks stay gated.',
    detail:
      'Shorts, long-form video, podcast, and public metadata share standards without sharing the same review surface.',
  },
];

export const caseStudyChanges: readonly CaseStudyChange[] = [
  {
    before: 'Visual search',
    after: 'A named identity system and separate source-preserving video rules.',
  },
  {
    before: 'Motion tests',
    after: 'Separate still approval, motion approval, and source-preserving video gates.',
  },
  {
    before: 'Draft scripts',
    after: 'Scripts with critique, fact-checking, integration notes, and human audio approval.',
  },
  {
    before: 'Voice tests',
    after: 'ElevenLabs Mike voice packages with transcript and provenance checks.',
  },
];

export const caseStudyProofImages: readonly CaseStudyProofImage[] = [
  {
    src: '/brand/case-study/explorations/particle-workbench-dissolve.webp',
    alt: 'Particle workbench simulation showing the Challenger shape dissolving into bright particles on a black field.',
    label: 'Particle workbench',
    note: 'Early simulation language tested failure as drift, break-up, and dissolution.',
  },
  {
    src: '/brand/case-study/explorations/collage-flux-stress-test.webp',
    alt: 'Archived collage exploration board showing dense editorial collage references, symbolic objects, and overloaded visual systems.',
    label: 'Collage stress test',
    note: 'Collage and FLUX-era image passes showed how quickly mechanism could collapse into visual noise.',
  },
];

const profileAsset = brandingAssets.find((asset) => asset.role === 'Profile');
const currentPaletteKeys = new Set(['ink', 'paper', 'overlaySlate', 'signal', 'alert']);

export const caseStudyCurrentState = {
  title: 'The channel identity is reviewable',
  body:
    'The current state is a reviewable identity package: YouTube banner, profile mark, watermark, local logo lockup, palette, type behavior, and selected gallery surfaces. Production can keep changing without making the public channel feel improvised.',
  logo: {
    src:
      profileAsset?.src ??
      '/brand/youtube-channel/advanced-features-corrected-banner-20260520T210213Z/profile-icon-800x800-square-clean-edge-no-alpha.png',
    alt: 'Cascade Effects rendered profile logo mark on a dark field.',
    width: profileAsset?.width ?? 800,
    height: profileAsset?.height ?? 800,
  },
  palette: brandPalette
    .filter((swatch) => currentPaletteKeys.has(swatch.key))
    .map(({ label, hex, usage }) => ({ label, hex, usage })),
  artifacts: [
    {
      title: 'YouTube channel banner',
      label: 'Channel surface',
      note: 'The YouTube header carries the evidence-desk world, title lockup, and Ink-Lit field.',
      src: youtubeChannelBrandingPackage.heroImage,
      alt: youtubeChannelBrandingPackage.heroImageAlt,
      width: 2048,
      height: 340,
      variant: 'banner',
    },
    {
      title: 'Profile mark',
      label: 'Avatar system',
      note: 'The square source is checked against YouTube circular crops before upload.',
      src:
        profileAsset?.src ??
        '/brand/youtube-channel/advanced-features-corrected-banner-20260520T210213Z/profile-icon-800x800-square-clean-edge-no-alpha.png',
      alt: 'Cascade Effects profile mark source on a dark field.',
      width: profileAsset?.width ?? 800,
      height: profileAsset?.height ?? 800,
      variant: 'square',
    },
    {
      title: 'Video watermark preview',
      label: 'In-player mark',
      note: 'The watermark is reviewed inside a video frame, not only as an isolated asset.',
      src: youtubeChannelBrandingPackage.previews.watermarkOverlay1280,
      alt: 'Cascade Effects watermark overlay preview on a 16 by 9 video frame.',
      width: 1280,
      height: 720,
      variant: 'video',
    },
    {
      title: 'Gallery package surface',
      label: 'Episode identity',
      note: 'The first-eight slate uses the same identity language at gallery scale.',
      src: '/brand/episode-gallery/proof-v6-ink-lit-subjects/challenger-thumbnail-proof-v6-ink-lit-subjects.webp',
      alt: 'Ink-lit Paper Architecture gallery thumbnail for the Challenger episode.',
      width: 1672,
      height: 941,
      variant: 'gallery',
    },
  ] satisfies readonly CaseStudyCurrentArtifact[],
} as const;
