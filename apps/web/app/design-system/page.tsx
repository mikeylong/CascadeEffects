import type { Metadata } from 'next';

import { BrandReferencePage } from '@/components/brand/youtube-channel-branding-page';
import { youtubeChannelBrandingPackage } from '@/lib/brand/youtube-channel-branding';
import { siteIdentity } from '@/lib/site-facts';

export const metadata: Metadata = {
  title: `${siteIdentity.title} Design System`,
  description:
    'Cascade Effects internal design system reference for illustration, color, typography, image guidance, platform rules, and YouTube channel branding assets.',
  alternates: {
    canonical: '/design-system',
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
    title: `${siteIdentity.title} Design System`,
    description:
      'Review the Cascade Effects design system for illustration, color, typography, image guidance, and channel branding assets.',
    url: `${siteIdentity.url}/design-system`,
    siteName: siteIdentity.title,
    type: 'website',
    images: [
      {
        url: youtubeChannelBrandingPackage.heroImage,
        width: 2048,
        height: 340,
        alt: youtubeChannelBrandingPackage.heroImageAlt,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: `${siteIdentity.title} Design System`,
    description:
      'Review the Cascade Effects design system for illustration, color, typography, image guidance, and channel branding assets.',
    images: [
      {
        url: youtubeChannelBrandingPackage.heroImage,
        alt: youtubeChannelBrandingPackage.heroImageAlt,
      },
    ],
  },
};

export default function DesignSystemPage() {
  return <BrandReferencePage />;
}
