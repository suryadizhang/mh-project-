'use client';

import { useRouter } from 'next/navigation';

import { cn } from '@/lib/utils';

import styles from './FreeQuoteButton.module.css';

interface FreeQuoteButtonProps {
  variant?: 'primary' | 'secondary' | 'floating';
  text?: string;
  className?: string;
}

export function FreeQuoteButton({
  variant = 'primary',
  text = 'Get Free Quote',
  className = '',
}: FreeQuoteButtonProps) {
  const router = useRouter();

  const variantStyles = {
    primary: styles.primary,
    secondary: styles.secondary,
    floating: styles.floating,
  };

  const handleClick = () => {
    router.push('/quote');
  };

  return (
    <button
      onClick={handleClick}
      className={cn(styles.btn, variantStyles[variant], className)}
      aria-label="Go to quote calculator page"
    >
      <span className={styles.icon}>💰</span>
      {text}
    </button>
  );
}
