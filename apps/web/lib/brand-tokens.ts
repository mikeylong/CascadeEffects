import type { CSSProperties } from 'react';

import signalRawTokens from '@/brand/cascade-effects-signal.style-system.json';

type ColorToken = {
  $value: {
    components: number[];
    alpha: number;
    hex: string;
  };
};

type DimensionToken = {
  $value: {
    value: number;
    unit: string;
  };
};

type NumberToken = {
  $value: number;
};

type FontFamilyToken = {
  $value: string[];
};

type CubicBezierToken = {
  $value: number[];
};

export type CssVariableMap = CSSProperties & Record<`--${string}`, string>;

export type OgPalette = {
  background: string;
  foreground: string;
  muted: string;
  accent: string;
  frame: string;
  panel: string;
  panelAlt: string;
  shadow: string;
  alert?: string;
};

export type ThemeDefinition = {
  id: string;
  label: string;
  source: string;
  cssVariables: CssVariableMap;
  og: OgPalette;
};

const genericFamilies = new Set(['sans-serif', 'monospace', 'serif', 'system-ui']);

const colorToCss = (token: ColorToken): string => {
  const {
    components: [red, green, blue],
    alpha,
    hex,
  } = token.$value;

  if (alpha === 1) {
    return hex;
  }

  const toChannel = (value: number) => Math.round(value * 255);

  return `rgba(${toChannel(red)}, ${toChannel(green)}, ${toChannel(blue)}, ${alpha})`;
};

const dimensionToCss = (token: DimensionToken): string => `${token.$value.value}${token.$value.unit}`;
const numberToCss = (token: NumberToken): string => `${token.$value}`;
const cubicBezierToCss = (token: CubicBezierToken): string => `cubic-bezier(${token.$value.join(', ')})`;

const fontFamilyToCss = (token: FontFamilyToken): string =>
  token.$value.map((font) => (genericFamilies.has(font) ? font : `"${font}"`)).join(', ');

const createShadowCss = (
  color: string,
  offsetY: string,
  blur: string,
  spread = '0px',
): string => `0 ${offsetY} ${blur} ${spread} ${color}`;

const signalTokens = signalRawTokens;

const createSignalCssVariables = (): CssVariableMap => {
  const ink = colorToCss(signalTokens.color.base.ink);
  const inkPanel = colorToCss(signalTokens.color.base.inkPanel);
  const overlaySlate = colorToCss(signalTokens.color.base.overlaySlate);
  const panelFrame = colorToCss(signalTokens.color.base.panelFrame);
  const white = colorToCss(signalTokens.color.base.white);
  const secondaryText = colorToCss(signalTokens.color.base.secondaryText);
  const signal = colorToCss(signalTokens.color.accent.signal);
  const alert = colorToCss(signalTokens.color.accent.alert);
  const white12 = colorToCss(signalTokens.color.alpha.white12);
  const white24 = colorToCss(signalTokens.color.alpha.white24);
  const white40 = colorToCss(signalTokens.color.alpha.white40);
  const white72 = colorToCss(signalTokens.color.alpha.white72);
  const ink08 = colorToCss(signalTokens.color.alpha.ink08);
  const ink12 = colorToCss(signalTokens.color.alpha.ink12);
  const ink24 = colorToCss(signalTokens.color.alpha.ink24);
  const ink72 = colorToCss(signalTokens.color.alpha.ink72);
  const signal16 = colorToCss(signalTokens.color.alpha.signal16);
  const signal32 = colorToCss(signalTokens.color.alpha.signal32);
  const alert16 = colorToCss(signalTokens.color.alpha.alert16);
  const alert32 = colorToCss(signalTokens.color.alpha.alert32);

  return {
    '--color-ink': ink,
    '--color-ink-panel': inkPanel,
    '--color-overlay-slate': overlaySlate,
    '--color-panel-frame': panelFrame,
    '--color-white': white,
    '--color-secondary-text': secondaryText,
    '--color-signal': signal,
    '--color-signal-wash': signal16,
    '--color-signal-strong': signal32,
    '--color-alert': alert,
    '--color-alert-wash': alert16,
    '--color-alert-strong': alert32,
    '--color-white-12': white12,
    '--color-white-24': white24,
    '--color-white-40': white40,
    '--color-white-72': white72,
    '--color-ink-08': ink08,
    '--color-ink-12': ink12,
    '--color-ink-24': ink24,
    '--color-ink-72': ink72,
    '--font-display-family': fontFamilyToCss(signalTokens.fontFamily.display),
    '--font-body-family': fontFamilyToCss(signalTokens.fontFamily.body),
    '--font-ui-family': fontFamilyToCss(signalTokens.fontFamily.ui),
    '--type-caption': dimensionToCss(signalTokens.size.font.caption),
    '--type-label': dimensionToCss(signalTokens.size.font.label),
    '--type-body': dimensionToCss(signalTokens.size.font.body),
    '--type-body-lg': dimensionToCss(signalTokens.size.font.bodyLg),
    '--type-card-title': dimensionToCss(signalTokens.size.font.cardTitle),
    '--type-section': dimensionToCss(signalTokens.size.font.section),
    '--type-display': dimensionToCss(signalTokens.size.font.display),
    '--type-thumbnail': dimensionToCss(signalTokens.size.font.thumbnail),
    '--type-hero': dimensionToCss(signalTokens.size.font.hero),
    '--type-monogram': dimensionToCss(signalTokens.size.font.monogram),
    '--line-tight': numberToCss(signalTokens.number.lineHeight.tight),
    '--line-snug': numberToCss(signalTokens.number.lineHeight.snug),
    '--line-compact': numberToCss(signalTokens.number.lineHeight.compact),
    '--line-reading': numberToCss(signalTokens.number.lineHeight.reading),
    '--tracking-tight': dimensionToCss(signalTokens.size.tracking.tight),
    '--tracking-normal': dimensionToCss(signalTokens.size.tracking.normal),
    '--tracking-ui': dimensionToCss(signalTokens.size.tracking.ui),
    '--tracking-caps': dimensionToCss(signalTokens.size.tracking.caps),
    '--tracking-wide': dimensionToCss(signalTokens.size.tracking.wide),
    '--radius-sm': dimensionToCss(signalTokens.size.radius.sm),
    '--radius-md': dimensionToCss(signalTokens.size.radius.md),
    '--radius-lg': dimensionToCss(signalTokens.size.radius.lg),
    '--radius-xl': dimensionToCss(signalTokens.size.radius.xl),
    '--radius-pill': dimensionToCss(signalTokens.size.radius.pill),
    '--stroke-hairline': dimensionToCss(signalTokens.size.stroke.hairline),
    '--stroke-thin': dimensionToCss(signalTokens.size.stroke.thin),
    '--stroke-regular': dimensionToCss(signalTokens.size.stroke.regular),
    '--stroke-emphasis': dimensionToCss(signalTokens.size.stroke.emphasis),
    '--layout-card-padding': dimensionToCss(signalTokens.layout.cardPadding),
    '--layout-gap': dimensionToCss(signalTokens.layout.panelGap),
    '--layout-section-gap': dimensionToCss(signalTokens.layout.sectionGap),
    '--layout-thumbnail-safe-inset-x': dimensionToCss(signalTokens.layout.thumbnailSafeInsetX),
    '--layout-thumbnail-safe-inset-y': dimensionToCss(signalTokens.layout.thumbnailSafeInsetY),
    '--layout-thumbnail-frame-padding': dimensionToCss(
      signalTokens.layout.thumbnailOuterFramePadding,
    ),
    '--layout-thumbnail-panel-gap': dimensionToCss(signalTokens.layout.thumbnailPanelGap),
    '--layout-title-slab-padding-x': dimensionToCss(signalTokens.layout.titleSlabPaddingX),
    '--layout-title-slab-padding-y': dimensionToCss(signalTokens.layout.titleSlabPaddingY),
    '--layout-callout-gap': dimensionToCss(signalTokens.layout.calloutGap),
    '--layout-lower-third-padding-x': dimensionToCss(signalTokens.layout.lowerThirdPaddingX),
    '--layout-lower-third-padding-y': dimensionToCss(signalTokens.layout.lowerThirdPaddingY),
    '--ratio-title-slab': numberToCss(signalTokens.number.ratio.thumbnailTitleSlab),
    '--ratio-artifact-panel': numberToCss(signalTokens.number.ratio.thumbnailArtifactPanel),
    '--rule-headline-words-min': numberToCss(signalTokens.number.rules.headlineWordsMin),
    '--rule-headline-words-max': numberToCss(signalTokens.number.rules.headlineWordsMax),
    '--rule-accent-words-max': numberToCss(signalTokens.number.rules.accentWordsMax),
    '--motion-fast': `${signalTokens.duration.fast.$value.value}${signalTokens.duration.fast.$value.unit}`,
    '--motion-base': `${signalTokens.duration.base.$value.value}${signalTokens.duration.base.$value.unit}`,
    '--motion-build': `${signalTokens.duration.build.$value.value}${signalTokens.duration.build.$value.unit}`,
    '--motion-slow-pan': `${signalTokens.duration.slowPan.$value.value}${signalTokens.duration.slowPan.$value.unit}`,
    '--ease-standard': cubicBezierToCss(signalTokens.cubicBezier.standard),
    '--ease-reveal': cubicBezierToCss(signalTokens.cubicBezier.reveal),
    '--shadow-panel': createShadowCss(
      ink08,
      dimensionToCss(signalTokens.size.shadow.panelOffsetY),
      dimensionToCss(signalTokens.size.shadow.panelBlur),
    ),
    '--shadow-slab': createShadowCss(
      ink24,
      dimensionToCss(signalTokens.size.shadow.slabOffsetY),
      dimensionToCss(signalTokens.size.shadow.slabBlur),
    ),
  };
};

export const signalTheme: ThemeDefinition = {
  id: 'cascade-paper-architectures-ink-lit-v1',
  label: 'Cascade Ink-Lit Paper Architectures',
  source: 'brand/cascade-effects-signal.style-system.json',
  cssVariables: createSignalCssVariables(),
  og: {
    background: colorToCss(signalTokens.color.base.ink),
    foreground: colorToCss(signalTokens.color.base.white),
    muted: colorToCss(signalTokens.color.alpha.white72),
    accent: colorToCss(signalTokens.color.accent.signal),
    frame: colorToCss(signalTokens.color.base.panelFrame),
    panel: colorToCss(signalTokens.color.base.white),
    panelAlt: colorToCss(signalTokens.color.base.inkPanel),
    shadow: createShadowCss(
      'rgba(9, 13, 27, 0.46)',
      dimensionToCss(signalTokens.size.shadow.slabOffsetY),
      dimensionToCss(signalTokens.size.shadow.slabBlur),
    ),
    alert: colorToCss(signalTokens.color.accent.alert),
  },
};

export const resolveThemeVariables = (theme: ThemeDefinition): CssVariableMap => theme.cssVariables;
