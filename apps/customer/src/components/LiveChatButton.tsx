'use client';

import { Phone } from 'lucide-react';

import { initiateCall } from '@/lib/ringcentral';

interface LiveChatButtonProps {
  className?: string;
  variant?: 'primary' | 'outline' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
}

export default function LiveChatButton({
  className = '',
  variant = 'primary',
  size = 'md',
}: LiveChatButtonProps) {
  const handleCallClick = () => {
    initiateCall(); // Opens phone dialer with MyHibachi business number
  };

  const getButtonClasses = () => {
    const baseClasses = 'btn flex items-center gap-2 font-bold transition-all';

    const variantClasses = {
      primary: 'btn-primary',
      outline: 'btn-outline-primary',
      secondary: 'btn-secondary',
    };

    const sizeClasses = {
      sm: 'btn-sm',
      md: '',
      lg: 'btn-lg',
    };

    return `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  };

  return (
    <button
      onClick={handleCallClick}
      className={getButtonClasses()}
      title="Call MyHibachi - Click to dial (916) 740-8768"
    >
      <Phone size={18} className="inline-block" />
      <span>Call Us</span>
    </button>
  );
}
