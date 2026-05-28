import Image from 'next/image';

const SIGNAL_BRANDMARK_SRC =
  '/brand/youtube-channel/advanced-features-corrected-banner-20260520T210213Z/profile-icon-800x800-square-clean-edge-no-alpha.png';

type SignalBrandmarkProps = {
  className?: string;
  title?: string;
};

export function SignalBrandmark({ className, title }: SignalBrandmarkProps) {
  const isDecorative = !title;

  return (
    <Image
      className={className}
      src={SIGNAL_BRANDMARK_SRC}
      alt={title ?? ''}
      width={800}
      height={800}
      aria-hidden={isDecorative ? true : undefined}
      priority={false}
    />
  );
}
