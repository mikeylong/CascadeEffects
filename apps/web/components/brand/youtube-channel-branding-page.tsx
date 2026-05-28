import Image from 'next/image';
import type { CSSProperties } from 'react';
import { CheckCircle2, Download } from 'lucide-react';

import { signalTheme } from '@/lib/brand-tokens';
import { resolveThemeVariables } from '@/lib/brand-tokens';
import {
  brandArtGuidelines,
  brandAvoidList,
  brandImageGenerationGuidelines,
  brandPalette,
  brandPlatformRules,
  brandQaGuidelines,
  brandReferenceImages,
  brandReferenceNavigation,
  brandReferenceSummary,
  brandTextPolicy,
  brandTypographyFamilySpecimens,
  brandTypographyHierarchyExamples,
  brandTypographyRoles,
  brandTypographyRules,
  brandingAssets,
  brandingRequirements,
  youtubeChannelBrandingPackage,
} from '@/lib/brand/youtube-channel-branding';
import type { BrandTypographyRole } from '@/lib/brand/youtube-channel-branding';
import { siteIdentity } from '@/lib/site-facts';

import styles from './youtube-channel-branding-page.module.css';

type SectionHeadingProps = {
  id: string;
  eyebrow: string;
  title: string;
  summary?: string;
};

type CssVariableStyle = CSSProperties & Record<`--${string}`, string>;

const typographyRoleStyle = (role: BrandTypographyRole): CssVariableStyle => ({
  '--type-family': role.renderStyle.fontFamily,
  '--type-size': role.renderStyle.fontSize,
  '--type-weight': role.renderStyle.fontWeight,
  '--type-line-height': role.renderStyle.lineHeight,
  '--type-tracking': role.renderStyle.letterSpacing,
  '--type-transform': role.renderStyle.textTransform,
});

const familySpecimenClassNames: Record<string, string> = {
  display: styles.typeFamilyDisplay,
  body: styles.typeFamilyBody,
  metadata: styles.typeFamilyMetadata,
};

function SectionHeading({ id, eyebrow, title, summary }: SectionHeadingProps) {
  return (
    <div className={styles.sectionHeading}>
      <p className={styles.eyebrow}>{eyebrow}</p>
      <h2 id={id}>{title}</h2>
      {summary ? <p>{summary}</p> : null}
    </div>
  );
}

export function BrandReferencePage() {
  return (
    <main className={styles.page} style={resolveThemeVariables(signalTheme)}>
      <section className={styles.hero} id="overview" aria-labelledby="overview-title">
        <div className={styles.heroCopy}>
          <p className={styles.eyebrow}>Design system</p>
          <h1 className={styles.title} id="overview-title">
            {siteIdentity.title} Design System
          </h1>
          <p className={styles.summary}>{brandReferenceSummary.summary}</p>
          <p className={styles.positioning}>{brandReferenceSummary.position}</p>
          <div className={styles.statusRail} aria-label="Design system scope">
            <span className={styles.statusPill}>Ink-lit paper style</span>
            <span className={styles.statusPill}>Website and channel art</span>
            <span className={styles.statusPill}>Manual YouTube upload</span>
          </div>
        </div>

        <figure className={styles.bannerFigure}>
          <Image
            className={styles.bannerImage}
            src={youtubeChannelBrandingPackage.heroImage}
            alt={youtubeChannelBrandingPackage.heroImageAlt}
            width={2048}
            height={340}
            priority
            sizes="(max-width: 900px) 100vw, 92vw"
          />
          <figcaption>Current YouTube banner strip, shown as part of the design system.</figcaption>
        </figure>
      </section>

      <nav className={styles.referenceNav} aria-label="Design system sections">
        {brandReferenceNavigation.map((item) => (
          <a href={`#${item.id}`} key={item.id}>
            {item.label}
          </a>
        ))}
      </nav>

      <section className={styles.referenceSection} id="art-system" aria-labelledby="art-title">
        <div className={styles.sectionInner}>
          <SectionHeading
            id="art-title"
            eyebrow="Art system"
            title="Ink-Lit Paper Architectures"
            summary="The house art direction explains hidden systems with tactile paper construction, clean public anchors, and restrained cause-and-effect signal language."
          />

          <div className={styles.guidelineGrid}>
            {brandArtGuidelines.map((group) => (
              <article className={styles.guidelineCard} key={group.title}>
                <p className={styles.cardEyebrow}>{group.eyebrow}</p>
                <h3>{group.title}</h3>
                <p>{group.summary}</p>
                <ul>
                  {group.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          <div className={styles.referenceImageGrid} aria-label="Reference images">
            {brandReferenceImages.slice(0, 2).map((image) => (
              <figure key={image.src}>
                <Image
                  src={image.src}
                  alt={image.alt}
                  width={image.width}
                  height={image.height}
                  loading="eager"
                  sizes="(max-width: 900px) 100vw, 45vw"
                />
                <figcaption>
                  <strong>{image.title}</strong>
                  {image.note}
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.altSection} id="palette" aria-labelledby="palette-title">
        <div className={styles.sectionInner}>
          <SectionHeading
            id="palette-title"
            eyebrow="Color palette"
            title="Tokens And Usage"
            summary="Use the active ink-lit palette with strong separation between deep fields, cream paper, lavender depth, dry cyan signal, and restrained coral warning cues."
          />

          <div className={styles.paletteGrid}>
            {brandPalette.map((swatch) => (
              <article className={styles.swatchCard} key={swatch.key}>
                <div
                  className={styles.swatch}
                  style={{ '--swatch-color': swatch.hex } as CSSProperties}
                  aria-hidden="true"
                />
                <div className={styles.swatchBody}>
                  <p className={styles.cardEyebrow}>{swatch.group}</p>
                  <h3>{swatch.label}</h3>
                  <p className={styles.hexValue}>{swatch.hex}</p>
                  <p>{swatch.usage}</p>
                  <p className={styles.swatchDescription}>{swatch.description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section
        className={styles.referenceSection}
        id="typography"
        aria-labelledby="typography-title"
      >
        <div className={styles.sectionInner}>
          <SectionHeading
            id="typography-title"
            eyebrow="Typography"
            title="Type That Stays Readable"
            summary="Use bold Inter-based title type, clean body copy, and compact mono labels without letting generated art control final spelling."
          />

          <div className={styles.typeSectionBlock}>
            <div className={styles.typeBlockHeader}>
              <h3>Type Stack</h3>
              <p>Start with the family behavior before choosing a specific role.</p>
            </div>
            <div className={styles.typeStackGrid} aria-label="Typography family specimens">
              {brandTypographyFamilySpecimens.map((family) => (
                <article className={styles.typeStackCard} key={family.key}>
                  <p className={styles.cardEyebrow}>{family.label}</p>
                  <p
                    className={`${styles.typeFamilySample} ${
                      familySpecimenClassNames[family.key] ?? styles.typeFamilyBody
                    }`}
                  >
                    {family.sample}
                  </p>
                  <p>{family.guidance}</p>
                  <p className={styles.typeStackMeta}>{family.stack}</p>
                </article>
              ))}
            </div>
          </div>

          <div className={styles.typeSectionBlock}>
            <div className={styles.typeBlockHeader}>
              <h3>Scale Specimens</h3>
              <p>Each row renders live type and shows the token values behind it.</p>
            </div>
            <div className={styles.typeSpecimenList} aria-label="Typography scale specimens">
              {brandTypographyRoles.map((role) => (
                <article
                  className={styles.typeSpecimenRow}
                  key={role.key}
                  style={typographyRoleStyle(role)}
                >
                  <div className={styles.typeSpecimenMain}>
                    <p className={styles.cardEyebrow}>{role.metadata.token}</p>
                    <h3>{role.label}</h3>
                    <p className={styles.typeSpecimenText}>{role.sample}</p>
                  </div>
                  <dl className={styles.typeMetaGrid} aria-label={`${role.label} token metadata`}>
                    <div>
                      <dt>Family</dt>
                      <dd>{role.metadata.family}</dd>
                    </div>
                    <div>
                      <dt>Size</dt>
                      <dd>{role.metadata.size}</dd>
                    </div>
                    <div>
                      <dt>Weight</dt>
                      <dd>{role.metadata.weight}</dd>
                    </div>
                    <div>
                      <dt>Line</dt>
                      <dd>{role.metadata.lineHeight}</dd>
                    </div>
                    <div>
                      <dt>Tracking</dt>
                      <dd>{role.metadata.tracking}</dd>
                    </div>
                  </dl>
                  <div className={styles.typeSpecimenNotes}>
                    <p>
                      <span>Use</span>
                      {role.usage}
                    </p>
                    <p>
                      <span>Avoid</span>
                      {role.avoid}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className={styles.typeSectionBlock}>
            <div className={styles.typeBlockHeader}>
              <h3>Hierarchy Examples</h3>
              <p>Use the roles together in realistic page, channel, and video-adjacent contexts.</p>
            </div>
            <div className={styles.typeHierarchyGrid} aria-label="Typography hierarchy examples">
              {brandTypographyHierarchyExamples.map((example) => (
                <article className={styles.typeHierarchyCard} key={example.key}>
                  <p className={styles.typeHierarchyLabel}>{example.label}</p>
                  <p className={styles.typeHierarchyEyebrow}>{example.eyebrow}</p>
                  <h3
                    className={
                      example.key === 'channel'
                        ? styles.typeHierarchyDisplayTitle
                        : styles.typeHierarchyTitle
                    }
                  >
                    {example.title}
                  </h3>
                  <p className={styles.typeHierarchyBody}>{example.body}</p>
                  {example.meta ? (
                    <p className={styles.typeHierarchyMeta}>{example.meta}</p>
                  ) : null}
                </article>
              ))}
            </div>
          </div>

          <div className={styles.typeSectionBlock}>
            <div className={styles.typeBlockHeader}>
              <h3>Usage Matrix</h3>
              <p>Keep type choices tied to the surface they are meant to serve.</p>
            </div>
            <div className={styles.typeUsageMatrix} aria-label="Typography usage matrix">
              <div className={styles.typeUsageHeader} aria-hidden="true">
                <span>Role</span>
                <span>Use</span>
                <span>Avoid</span>
              </div>
              {brandTypographyRoles.map((role) => (
                <div className={styles.typeUsageRow} key={role.key}>
                  <span>{role.label}</span>
                  <p>{role.usage}</p>
                  <p>{role.avoid}</p>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.typeSectionBlock}>
            <div className={styles.typeBlockHeader}>
              <h3>Rules</h3>
              <p>These constraints apply whenever final text is composed locally.</p>
            </div>
            <div className={styles.typeRulesGrid}>
              {brandTypographyRules.map((rule) => (
                <article className={styles.typeRuleCard} key={rule.label}>
                  <p className={styles.cardEyebrow}>{rule.label}</p>
                  <p>{rule.value}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section
        className={styles.referenceSection}
        id="image-generation"
        aria-labelledby="image-generation-title"
      >
        <div className={styles.sectionInner}>
          <SectionHeading
            id="image-generation-title"
            eyebrow="Image generation"
            title="Image Guidance"
            summary="Create the visual world first. Add final titles, crops, and platform framing after the art direction is settled."
          />

          <div className={styles.guidelineGrid}>
            {brandImageGenerationGuidelines.map((group) => (
              <article className={styles.guidelineCard} key={group.title}>
                <p className={styles.cardEyebrow}>{group.eyebrow}</p>
                <h3>{group.title}</h3>
                <p>{group.summary}</p>
                <ul>
                  {group.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          <div className={styles.avoidPanel}>
            <h3>Keep Out Of The Look</h3>
            <ul>
              {brandAvoidList.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className={styles.altSection} id="text-policy" aria-labelledby="text-title">
        <div className={styles.sectionInner}>
          <SectionHeading
            id="text-title"
            eyebrow="Title and type"
            title="Local Type, Exact Spelling"
            summary="Readable titles are composed locally unless a package explicitly permits approved title-bearing identity art."
          />
          <div className={styles.requirementsTable}>
            {brandTextPolicy.map((rule) => (
              <div className={styles.requirementRow} key={rule.label}>
                <span>{rule.label}</span>
                <p>{rule.value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section
        className={styles.referenceSection}
        id="platform-rules"
        aria-labelledby="platform-title"
      >
        <div className={styles.sectionInner}>
          <SectionHeading
            id="platform-title"
            eyebrow="Use cases"
            title="Where This Look Belongs"
            summary="Keep this visual language on the website and channel identity surfaces, then use platform-native crops and file limits."
          />

          <div className={styles.twoColumnTables}>
            <div className={styles.requirementsTable}>
              {brandPlatformRules.map((rule) => (
                <div className={styles.requirementRow} key={rule.label}>
                  <span>{rule.label}</span>
                  <p>{rule.value}</p>
                </div>
              ))}
            </div>
            <div className={styles.requirementsTable}>
              {brandingRequirements.map((requirement) => (
                <div className={styles.requirementRow} key={requirement.label}>
                  <span>{requirement.label}</span>
                  <p>{requirement.value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section
        className={styles.altSection}
        id="youtube-package"
        aria-labelledby="youtube-package-title"
      >
        <div className={styles.sectionInner}>
          <SectionHeading
            id="youtube-package-title"
            eyebrow="YouTube package"
            title="Current Channel Branding Assets"
            summary={youtubeChannelBrandingPackage.summary}
          />

          <div className={styles.statusRail} aria-label="Current YouTube package status">
            <span className={styles.statusPill}>Banner approved</span>
            <span className={styles.statusPill}>Profile and watermark pending review</span>
            <span className={styles.statusPill}>YouTube Studio unchanged</span>
          </div>

          <div className={styles.assetGrid}>
            {brandingAssets.map((asset) => (
              <article className={styles.assetCard} key={asset.role}>
                <div className={styles.assetPreview}>
                  <Image
                    src={asset.src}
                    alt={`${asset.title} preview`}
                    width={asset.width}
                    height={asset.height}
                    loading="eager"
                    sizes="(max-width: 760px) 100vw, 30vw"
                  />
                </div>
                <div className={styles.assetBody}>
                  <p className={styles.assetRole}>{asset.role}</p>
                  <h3>{asset.title}</h3>
                  <dl className={styles.assetMeta}>
                    <div>
                      <dt>Status</dt>
                      <dd>{asset.statusLabel}</dd>
                    </div>
                    <div>
                      <dt>Dimensions</dt>
                      <dd>{asset.dimensions}</dd>
                    </div>
                    <div>
                      <dt>Format</dt>
                      <dd>{asset.format}</dd>
                    </div>
                    <div>
                      <dt>Limit</dt>
                      <dd>{asset.limit}</dd>
                    </div>
                  </dl>
                  <p>{asset.usage}</p>
                  <a className={styles.assetLink} href={asset.downloadHref}>
                    <Download aria-hidden="true" />
                    Open upload asset
                  </a>
                </div>
              </article>
            ))}
          </div>

          <div className={styles.previewGrid}>
            <figure className={styles.previewWide}>
              <Image
                src={youtubeChannelBrandingPackage.previews.bannerSafeOverlay}
                alt="Kept banner upload canvas with all-device title safe area overlay."
                width={2048}
                height={1152}
                loading="eager"
                sizes="(max-width: 900px) 100vw, 58vw"
              />
              <figcaption>All-device title safe area overlay.</figcaption>
            </figure>
            <figure>
              <Image
                src={youtubeChannelBrandingPackage.previews.bannerTitleSafeCrop}
                alt="Banner title-safe crop preview."
                width={1235}
                height={338}
                loading="eager"
                sizes="(max-width: 900px) 100vw, 38vw"
              />
              <figcaption>Title-safe crop.</figcaption>
            </figure>
            <figure>
              <Image
                src={youtubeChannelBrandingPackage.previews.watermarkOverlay1280}
                alt="Video watermark overlay preview on a 1280 by 720 frame."
                width={1280}
                height={720}
                loading="eager"
                sizes="(max-width: 900px) 100vw, 38vw"
              />
              <figcaption>Watermark overlay preview.</figcaption>
            </figure>
          </div>

          <div className={styles.profilePreviewRow} aria-label="Profile crop previews">
            {[98, 176, 320].map((size) => {
              const src =
                size === 98
                  ? youtubeChannelBrandingPackage.previews.profile98
                  : size === 176
                    ? youtubeChannelBrandingPackage.previews.profile176
                    : youtubeChannelBrandingPackage.previews.profile320;

              return (
                <figure key={size} className={styles.profilePreview}>
                  <Image
                    src={src}
                    alt={`Profile image circular crop preview at ${size} pixels.`}
                    width={size}
                    height={size}
                    loading="eager"
                  />
                  <figcaption>{size}px crop</figcaption>
                </figure>
              );
            })}
          </div>

          <ol className={styles.checklist}>
            {youtubeChannelBrandingPackage.manualChecklist.map((item) => (
              <li key={item}>
                <CheckCircle2 aria-hidden="true" />
                <span>{item}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className={styles.referenceSection} id="qa" aria-labelledby="qa-title">
        <div className={styles.sectionInner}>
          <SectionHeading
            id="qa-title"
            eyebrow="Review checklist"
            title="What To Check"
            summary="A short human review pass before any asset is treated as part of the brand system."
          />

          <div className={styles.requirementsTable}>
            {brandQaGuidelines.map((item) => (
              <div className={styles.requirementRow} key={`${item.label}-${item.value}`}>
                <span>{item.label}</span>
                <p>{item.value}</p>
              </div>
            ))}
          </div>

          <figure className={styles.contactSheet}>
            <Image
              src={youtubeChannelBrandingPackage.contactSheet}
              alt="Contact sheet of the Cascade Effects YouTube channel branding review package."
              width={2400}
              height={1600}
              loading="eager"
              sizes="100vw"
            />
            <figcaption>Review contact sheet.</figcaption>
          </figure>
        </div>
      </section>
    </main>
  );
}
