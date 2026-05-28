import { createElement, type ComponentType, type ReactElement } from 'react';

import { signalTheme, type ThemeDefinition } from '@/lib/brand-tokens';
import { signalContent, type SignalContent } from '@/lib/concepts/signal-content';
import { siteIdentity } from '@/lib/site-facts';
import { SignalHomepage } from '@/components/concepts/signal-homepage';

export type SiteConceptId = 'signal';

export type LandingConceptRenderProps<TContent = unknown> = {
  theme: ThemeDefinition;
  content: TContent;
};

export type LandingConceptDefinition<TContent = unknown> = {
  id: SiteConceptId;
  slug: string;
  theme: ThemeDefinition;
  Component: ComponentType<LandingConceptRenderProps<TContent>>;
  content: TContent;
  meta: {
    title: string;
    description: string;
    ogTitle: string;
    ogSubtitle: string;
  };
};

export const concepts = [
  {
    id: 'signal',
    slug: 'signal',
    theme: signalTheme,
    Component: SignalHomepage,
    content: signalContent,
    meta: {
      title: siteIdentity.title,
      description: signalContent.heroBody,
      ogTitle: siteIdentity.title,
      ogSubtitle: signalContent.heroBody,
    },
  },
] satisfies [LandingConceptDefinition<SignalContent>];

export type AnyLandingConcept = (typeof concepts)[number];
export const primaryConcept: AnyLandingConcept = concepts[0];

export const renderLandingConcept = <TContent,>(
  concept: LandingConceptDefinition<TContent>,
): ReactElement => {
  const ConceptPage = concept.Component as ComponentType<LandingConceptRenderProps<TContent>>;

  return createElement(ConceptPage, {
    theme: concept.theme,
    content: concept.content,
  });
};
