import type { ThemeDefinition } from '@/lib/brand-tokens';
import { resolveThemeVariables } from '@/lib/brand-tokens';
import type { SignalContent } from '@/lib/concepts/signal-content';
import {
  launchEpisodes,
  siteIdentity,
} from '@/lib/site-facts';
import { Mail } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { SignalHomepageFeed } from '@/components/concepts/signal-homepage-feed';
import { SignalHomepageHeader } from '@/components/concepts/signal-homepage-header';

import styles from './signal-homepage.module.css';

type SignalHomepageProps = {
  theme: ThemeDefinition;
  content: SignalContent;
};

const HOMEPAGE_EPISODE_COUNT = 8;
const homepageEpisodes = launchEpisodes.slice(0, HOMEPAGE_EPISODE_COUNT);
const heroArtworkSrc =
  '/brand/homepage-hero-paper-cloudless-clean-surface-desktop-v4.png';
const mobileHeroArtworkSrc =
  '/brand/homepage-hero-paper-cloudless-clean-surface-mobile-v4.png';
const tabletLandscapeHeroArtworkSrc =
  '/brand/homepage-hero-paper-cloudless-clean-surface-tablet-landscape-v4.png';
const tabletPortraitHeroArtworkSrc =
  '/brand/homepage-hero-paper-cloudless-clean-surface-tablet-portrait-v4.png';

export function SignalHomepage({ theme, content }: SignalHomepageProps) {
  return (
    <main className={styles.page} style={resolveThemeVariables(theme)}>
      <SignalHomepageHeader />

      <section id="top" className={styles.hero}>
        <div className={styles.heroArtwork} aria-hidden="true">
          <picture>
            <source
              media="(max-width: 600px)"
              srcSet={mobileHeroArtworkSrc}
              sizes="100vw"
            />
            <source
              media="(min-width: 601px) and (max-width: 1024px) and (orientation: portrait)"
              srcSet={tabletPortraitHeroArtworkSrc}
              sizes="100vw"
            />
            <source
              media="(min-width: 601px) and (max-width: 1180px) and (orientation: landscape)"
              srcSet={tabletLandscapeHeroArtworkSrc}
              sizes="100vw"
            />
            <Image
              className={styles.heroArtworkImage}
              src={heroArtworkSrc}
              alt=""
              width={1672}
              height={941}
              priority
              sizes="100vw"
            />
          </picture>
        </div>

        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>{siteIdentity.title}</h1>
        </div>
      </section>

      <section id="episodes" className={styles.section}>
        <SignalHomepageFeed
          episodes={homepageEpisodes}
        />

        <div className={styles.feedbackPanel}>
          <p className={styles.feedbackPrompt}>{content.feedbackPrompt}</p>

          <a className={styles.feedbackLink} href={`mailto:${siteIdentity.email}`}>
            <Mail className={styles.ctaIcon} aria-hidden="true" />
            {siteIdentity.email}
          </a>
        </div>
      </section>

      <footer className={styles.footer}>
        <a
          className={styles.footerHandle}
          href={siteIdentity.youtubeUrl}
          target="_blank"
          rel="noreferrer"
        >
          {siteIdentity.handle}
        </a>
        <Link className={styles.footerLink} href="/origin-story">
          Origin Story
        </Link>
      </footer>
    </main>
  );
}
