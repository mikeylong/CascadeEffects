import type { Metadata } from 'next';

import { CascadeEffectsCaseStudy } from '@/components/case-study/cascade-effects-case-study';
import { caseStudyHero } from '@/lib/case-study/cascade-effects-case-study';
import { siteIdentity } from '@/lib/site-facts';

export const metadata: Metadata = {
  title: `${siteIdentity.title} Case Study`,
  description:
    'A public case study on how Cascade Effects turned a mechanism-led editorial idea into a research, script, voiceover, and visual production pipeline.',
  alternates: {
    canonical: '/case-study',
  },
  robots: {
    index: false,
    follow: false,
    googleBot: {
      index: false,
      follow: false,
    },
  },
  openGraph: {
    title: `${siteIdentity.title} Case Study`,
    description:
      'How Cascade Effects found a production language for mechanism-led documentary work.',
    url: `${siteIdentity.url}/case-study`,
    siteName: siteIdentity.title,
    type: 'article',
    images: [
      {
        url: caseStudyHero.image,
        width: 1672,
        height: 941,
        alt: caseStudyHero.imageAlt,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: `${siteIdentity.title} Case Study`,
    description:
      'How Cascade Effects found a production language for mechanism-led documentary work.',
    images: [
      {
        url: caseStudyHero.image,
        alt: caseStudyHero.imageAlt,
      },
    ],
  },
};

export default function CaseStudyPage() {
  return <CascadeEffectsCaseStudy />;
}
