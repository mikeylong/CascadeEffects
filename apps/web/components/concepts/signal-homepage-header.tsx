'use client';

import { siteIdentity } from '@/lib/site-facts';
import { Play } from 'lucide-react';
import { useEffect, useState } from 'react';

import { SignalBrandmark } from '@/components/brand/signal-brandmark';

import styles from './signal-homepage.module.css';

export function SignalHomepageHeader() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const hero = document.getElementById('top');

    if (!hero) {
      return;
    }

    const updateVisibility = () => {
      setIsVisible(hero.getBoundingClientRect().bottom <= 0);
    };

    if (typeof window.IntersectionObserver === 'undefined') {
      const frame = window.requestAnimationFrame(updateVisibility);
      window.addEventListener('scroll', updateVisibility, { passive: true });
      window.addEventListener('resize', updateVisibility);

      return () => {
        window.cancelAnimationFrame(frame);
        window.removeEventListener('scroll', updateVisibility);
        window.removeEventListener('resize', updateVisibility);
      };
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(!entry.isIntersecting);
      },
      { threshold: 0 },
    );

    observer.observe(hero);

    return () => {
      observer.disconnect();
    };
  }, []);

  const hiddenTabIndex = isVisible ? undefined : -1;

  return (
    <header
      className={`${styles.header} ${isVisible ? styles.headerVisible : ''}`}
      aria-hidden={!isVisible}
    >
      <a
        href="#top"
        className={styles.brand}
        aria-label={siteIdentity.title}
        tabIndex={hiddenTabIndex}
      >
        <SignalBrandmark className={styles.brandMark} />
        <span className={styles.brandWordmark}>{siteIdentity.title}</span>
      </a>

      <a
        className={styles.headerLink}
        href={siteIdentity.youtubeWatchUrl}
        target="_blank"
        rel="noreferrer"
        aria-label="Watch on YouTube"
        tabIndex={hiddenTabIndex}
      >
        <Play className={styles.headerLinkIcon} aria-hidden="true" />
        <span className={styles.headerLinkLabelFull}>Watch on YouTube</span>
        <span className={styles.headerLinkLabelCompact}>YouTube</span>
      </a>
    </header>
  );
}
