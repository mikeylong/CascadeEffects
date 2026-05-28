import type { Metadata } from 'next';
import localFont from 'next/font/local';

import { primaryConcept } from '@/lib/site-concepts';
import { siteIdentity } from '@/lib/site-facts';

import './globals.css';

const socialPreviewImage = '/brand/social/cascadeeffects-social-card-homepage-hero-20260513T221407Z.png';

const inter = localFont({
  src: [
    {
      path: './fonts/inter-latin-400-normal.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/inter-latin-700-normal.woff2',
      weight: '700',
      style: 'normal',
    },
    {
      path: './fonts/inter-latin-800-normal.woff2',
      weight: '800',
      style: 'normal',
    },
  ],
  variable: '--font-sans',
  display: 'swap',
});

const ibmPlexMono = localFont({
  src: [
    {
      path: './fonts/ibm-plex-mono-latin-400-normal.woff2',
      weight: '400',
      style: 'normal',
    },
    {
      path: './fonts/ibm-plex-mono-latin-500-normal.woff2',
      weight: '500',
      style: 'normal',
    },
    {
      path: './fonts/ibm-plex-mono-latin-600-normal.woff2',
      weight: '600',
      style: 'normal',
    },
  ],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(siteIdentity.url),
  title: primaryConcept.meta.title,
  description: primaryConcept.meta.description,
  alternates: {
    canonical: '/',
  },
  openGraph: {
    title: primaryConcept.meta.title,
    description: primaryConcept.meta.description,
    url: siteIdentity.url,
    siteName: siteIdentity.title,
    locale: 'en_US',
    type: 'website',
    images: [
      {
        url: socialPreviewImage,
        width: 1200,
        height: 630,
        alt: `${siteIdentity.title} site preview`,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: primaryConcept.meta.title,
    description: primaryConcept.meta.description,
    images: [
      {
        url: socialPreviewImage,
        alt: `${siteIdentity.title} site preview`,
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${ibmPlexMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
