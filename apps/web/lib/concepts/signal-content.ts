export const signalContent = {
  heroTitle: 'The overlooked detail that changed everything',
  heroBody:
    'Evidence-led documentaries about decisions, design failures, and paper trails where one small signal changed everything after.',
  feedbackPrompt: 'Send feedback and story ideas.',
} as const;

export type SignalContent = typeof signalContent;
