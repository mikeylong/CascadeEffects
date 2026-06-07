import { list } from '@vercel/blob';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

import { BackplateOptionsReview } from '@/components/reviews/backplate-options-review';
import { normalizeBackplateReviewManifest } from '@/lib/reviews/backplate-options';

type PageProps = {
  params: Promise<{ reviewId: string }> | { reviewId: string };
};

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export const metadata: Metadata = {
  title: 'Season 2 Backplate Options Review',
  robots: {
    index: false,
    follow: false,
    nocache: true,
  },
};

const REVIEW_ID_PATTERN = /^[a-zA-Z0-9][a-zA-Z0-9_-]{2,127}$/;

async function resolveParams(params: PageProps['params']) {
  return Promise.resolve(params);
}

async function readLocalManifest(reviewId: string): Promise<unknown | null> {
  const root = process.env.CASCADE_REVIEW_MANIFEST_ROOT;
  if (!root) return null;

  const manifestPath = path.resolve(root, 'backplate-options', reviewId, 'manifest.json');
  const normalizedRoot = path.resolve(root);
  if (!manifestPath.startsWith(normalizedRoot + path.sep)) return null;

  try {
    return JSON.parse(await readFile(manifestPath, 'utf8'));
  } catch {
    return null;
  }
}

async function readBlobManifest(reviewId: string): Promise<unknown | null> {
  const prefix = `reviews/backplate-options/${reviewId}/`;
  const result = await list({ prefix, limit: 1000 });
  const manifestBlob = result.blobs.find((blob) => blob.pathname === `${prefix}manifest.json`);

  if (!manifestBlob) return null;

  const response = await fetch(manifestBlob.url, { cache: 'no-store' });
  if (!response.ok) return null;

  return response.json();
}

async function loadManifest(reviewId: string) {
  if (!REVIEW_ID_PATTERN.test(reviewId)) notFound();

  const raw = (await readLocalManifest(reviewId)) ?? (await readBlobManifest(reviewId));
  if (!raw) notFound();

  const manifest = normalizeBackplateReviewManifest(raw);
  if (manifest.reviewId !== reviewId) notFound();

  return manifest;
}

export default async function BackplateOptionsReviewPage({ params }: PageProps) {
  const { reviewId } = await resolveParams(params);
  const manifest = await loadManifest(reviewId);

  return <BackplateOptionsReview manifest={manifest} />;
}
