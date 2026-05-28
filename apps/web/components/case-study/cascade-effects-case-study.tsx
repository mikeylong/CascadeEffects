import Image from 'next/image';
import Link from 'next/link';
import { ArrowUpRight } from 'lucide-react';

import {
  caseStudyChanges,
  caseStudyConstraints,
  caseStudyCurrentState,
  caseStudyExplorations,
  caseStudyHero,
  caseStudyImageToVideo,
  caseStudyOpening,
  caseStudyPaperArchitecture,
  caseStudyProofImages,
  caseStudySections,
  caseStudyStack,
} from '@/lib/case-study/cascade-effects-case-study';
import { siteIdentity } from '@/lib/site-facts';

import styles from './cascade-effects-case-study.module.css';

const stackVisualImages = {
  research: {
    src: '/brand/case-study/stack/research-paper-architecture-source.png',
    alt: 'Ink-Lit Paper Architecture miniature of research documents and evidence trays connected by a dry cyan signal path.',
  },
  draft: {
    src: '/brand/case-study/stack/script-drafting-paper-architecture-source.png',
    alt: 'Ink-Lit Paper Architecture miniature of folded paper script pages and a cyan drafting path.',
  },
  review: {
    src: '/brand/case-study/stack/script-review-paper-architecture-source.png',
    alt: 'Ink-Lit Paper Architecture miniature of draft and review papers connected by revision signal paths.',
  },
  voice: {
    src: '/brand/case-study/stack/voiceover-paper-architecture-source.png',
    alt: 'Ink-Lit Paper Architecture miniature of a folded paper microphone and cyan voice waveform.',
  },
  publish: {
    src: '/brand/case-study/stack/publishing-paper-architecture-source.png',
    alt: 'Ink-Lit Paper Architecture miniature of proof frames, gallery plates, and a publishing package surface.',
  },
} as const;

const currentArtifactClassNames = {
  banner: styles.currentArtifactBanner,
  square: styles.currentArtifactSquare,
  video: styles.currentArtifactVideo,
  gallery: styles.currentArtifactGallery,
} as const;

export function CascadeEffectsCaseStudy() {
  return (
    <main className={styles.page}>
      <section className={styles.hero} aria-labelledby="case-study-title">
        <div className={styles.heroMedia} aria-hidden="true">
          <Image
            src={caseStudyHero.image}
            alt=""
            fill
            priority
            sizes="100vw"
            className={styles.heroImage}
          />
        </div>

        <div className={styles.heroContent}>
          <p className={styles.eyebrow}>{caseStudyHero.eyebrow}</p>
          <h1 id="case-study-title">{caseStudyHero.title}</h1>
          <p className={styles.heroDek}>{caseStudyHero.dek}</p>
          <p className={styles.heroQuestion}>{caseStudyHero.question}</p>
        </div>
      </section>

      <section className={styles.introSection} aria-labelledby="case-study-summary">
        <div className={styles.sectionInner}>
          <p className={styles.eyebrow}>Summary</p>
          <h2 id="case-study-summary">The channel had to separate story, identity, and production.</h2>
          <div className={styles.introText}>
            {caseStudyOpening.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.storySection} aria-label="Case study narrative">
        {caseStudySections.map((section) => (
          <article className={styles.storyBlock} key={section.title}>
            <div className={styles.storyHeading}>
              <h2>{section.title}</h2>
            </div>
            <div className={styles.storyCopy}>
              {section.body.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className={styles.explorationSection} aria-labelledby="exploration-title">
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeading}>
            <p className={styles.eyebrow}>Early and archived explorations</p>
            <h2 id="exploration-title">Two failures set the boundaries.</h2>
            <p>
              The early visual work mattered most when it failed. Particle simulation turned
              mechanism into atmosphere. Collage and generated-image boards turned mechanism into
              noise. Those failures made the boundaries useful.
            </p>
          </div>

          <div className={styles.proofStrip} aria-label="Visual exploration sequence">
            {caseStudyProofImages.map((image) => (
              <figure key={image.src}>
                <Image
                  src={image.src}
                  alt={image.alt}
                  width={720}
                  height={405}
                  loading="lazy"
                  sizes="(max-width: 560px) 100vw, 50vw"
                />
                <figcaption>
                  <strong>{image.label}</strong>
                  <span>{image.note}</span>
                </figcaption>
              </figure>
            ))}
          </div>

          <div className={styles.explorationGrid}>
            {caseStudyExplorations.map((item) => (
              <article className={styles.explorationCard} key={item.title}>
                <p className={styles.cardMeta}>{item.period}</p>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <p className={styles.lesson}>{item.lesson}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.motionSection} aria-labelledby="image-to-video-title">
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeading}>
            <p className={styles.eyebrow}>{caseStudyImageToVideo.eyebrow}</p>
            <h2 id="image-to-video-title">{caseStudyImageToVideo.title}</h2>
            <p>{caseStudyImageToVideo.body}</p>
            <p>{caseStudyImageToVideo.lesson}</p>
          </div>

          <div className={styles.motionClipGrid} aria-label="Rejected image-to-video clips">
            {caseStudyImageToVideo.clips.map((clip) => (
              <figure className={styles.motionClip} key={clip.src}>
                <video
                  controls
                  loop
                  muted
                  playsInline
                  preload="metadata"
                  poster={clip.poster}
                >
                  <source src={clip.src} type="video/mp4" />
                </video>
                <figcaption>
                  <strong>{clip.label}</strong>
                  <span>{clip.note}</span>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.architectureSection} aria-labelledby="architecture-title">
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeading}>
            <p className={styles.eyebrow}>Identity system</p>
            <h2 id="architecture-title">{caseStudyPaperArchitecture.title}</h2>
            <p>{caseStudyPaperArchitecture.body}</p>
          </div>

          <div className={styles.architectureShowcase} aria-label="Ink-Lit Paper Architecture examples">
            {caseStudyPaperArchitecture.visuals.map((visual) => (
              <figure
                className={
                  visual.featured
                    ? `${styles.architectureFigure} ${styles.architectureFigureFeatured}`
                    : styles.architectureFigure
                }
                key={visual.src}
              >
                <Image
                  src={visual.src}
                  alt={visual.alt}
                  width={1280}
                  height={720}
                  loading="lazy"
                  sizes={visual.featured ? '(max-width: 1180px) 100vw, 50vw' : '(max-width: 560px) 100vw, 25vw'}
                />
                <figcaption>
                  <strong>{visual.label}</strong>
                  <span>{visual.note}</span>
                </figcaption>
              </figure>
            ))}
          </div>

          <div className={styles.architectureGrid}>
            {caseStudyPaperArchitecture.points.map((point) => (
              <article className={styles.architectureCard} key={point.title}>
                <h3>{point.title}</h3>
                <p>{point.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.constraintsSection} aria-labelledby="constraints-title">
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeading}>
            <p className={styles.eyebrow}>Constraints</p>
            <h2 id="constraints-title">The rules keep the lanes separate.</h2>
            <p>
              The useful rules are practical: what text can be trusted, where each visual style
              belongs, and when a draft is ready to move forward.
            </p>
          </div>

          <div className={styles.constraintsList}>
            {caseStudyConstraints.map((constraint) => (
              <div className={styles.constraintRow} key={constraint.label}>
                <span>{constraint.label}</span>
                <p>{constraint.value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.stackSection} aria-labelledby="stack-title">
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeading}>
            <p className={styles.eyebrow}>Production stack</p>
            <h2 id="stack-title">Research moves through review before production.</h2>
            <p>
              Each lane has a different job. The shared standard is simple: keep the evidence
              readable and make the next decision explicit.
            </p>
          </div>

          <div className={styles.stackGrid}>
            {caseStudyStack.map((item) => (
              <article className={styles.stackCard} key={item.title}>
                <div className={styles.stackVisual}>
                  <Image
                    src={stackVisualImages[item.visual].src}
                    alt={stackVisualImages[item.visual].alt}
                    width={941}
                    height={330}
                    loading="lazy"
                    sizes="(max-width: 560px) 100vw, (max-width: 1180px) 50vw, 20vw"
                  />
                </div>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <p className={styles.stackDetail}>{item.detail}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.changeSection} aria-labelledby="change-title">
        <div className={styles.sectionInner}>
          <div className={styles.sectionHeading}>
            <p className={styles.eyebrow}>What changed</p>
            <h2 id="change-title">The work moved into reusable rules.</h2>
          </div>

          <div className={styles.changeList}>
            {caseStudyChanges.map((change) => (
              <div className={styles.changeRow} key={change.before}>
                <p>{change.before}</p>
                <span aria-hidden="true">to</span>
                <p>{change.after}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.currentSection} aria-labelledby="current-title">
        <div className={styles.sectionInner}>
          <div className={styles.currentHeader}>
            <div>
              <p className={styles.eyebrow}>Current state</p>
              <h2 id="current-title">{caseStudyCurrentState.title}</h2>
            </div>
            <p>{caseStudyCurrentState.body}</p>
          </div>

          <div className={styles.currentIdentityGrid}>
            {caseStudyCurrentState.artifacts.map((artifact) => (
              <figure
                className={`${styles.currentArtifact} ${currentArtifactClassNames[artifact.variant]}`}
                key={artifact.title}
              >
                <Image
                  src={artifact.src}
                  alt={artifact.alt}
                  width={artifact.width}
                  height={artifact.height}
                  loading="lazy"
                  sizes={
                    artifact.variant === 'banner'
                      ? '100vw'
                      : artifact.variant === 'video'
                        ? '(max-width: 820px) 100vw, 50vw'
                        : '(max-width: 820px) 100vw, 25vw'
                  }
                />
                <figcaption>
                  <span>{artifact.label}</span>
                  <strong>{artifact.title}</strong>
                  <p>{artifact.note}</p>
                </figcaption>
              </figure>
            ))}

            <article className={styles.currentLogoCard}>
              <div className={styles.currentLogoLockup}>
                <Image
                  className={styles.currentBrandmark}
                  src={caseStudyCurrentState.logo.src}
                  alt={caseStudyCurrentState.logo.alt}
                  width={caseStudyCurrentState.logo.width}
                  height={caseStudyCurrentState.logo.height}
                  loading="lazy"
                  sizes="5rem"
                />
                <div>
                  <p className={styles.cardMeta}>Logo mark</p>
                  <h3>{siteIdentity.title}</h3>
                  <span>{siteIdentity.handle}</span>
                </div>
              </div>
              <div className={styles.currentTypeSpecimens} aria-label="Typography examples">
                <span>Cascade Effects</span>
                <span>Launch Episode 01</span>
              </div>
            </article>

            <article className={styles.currentPaletteCard}>
              <p className={styles.cardMeta}>Design tokens</p>
              <h3>Ink-Lit palette</h3>
              <p className={styles.currentCardNote}>
                The palette separates deep fields, paper forms, signal paths, shadow, and warning
                cues so the identity can flex without changing character.
              </p>
              <div className={styles.currentPaletteGrid}>
                {caseStudyCurrentState.palette.map((swatch) => (
                  <div className={styles.currentSwatch} key={swatch.label}>
                    <span style={{ backgroundColor: swatch.hex }} />
                    <div>
                      <strong>{swatch.label}</strong>
                      <small>{swatch.hex}</small>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className={styles.closingSection} aria-labelledby="closing-title">
        <div className={styles.sectionInner}>
          <h2 id="closing-title">Thanks for scrolling all the way down here.</h2>
          <Link
            href={siteIdentity.youtubeUrl}
            className={styles.homeLink}
            target="_blank"
            rel="noreferrer"
          >
            Visit the YouTube channel
            <ArrowUpRight aria-hidden="true" />
          </Link>
        </div>
      </section>
    </main>
  );
}
