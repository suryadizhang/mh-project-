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

  const baseClasses =
    'inline-flex items-center justify-center gap-2 font-bold rounded-xl transition-all duration-200';

  const variantClasses = {
    primary:
      'bg-gradient-to-r from-red-600 to-red-700 text-white shadow-lg hover:from-red-700 hover:to-red-800 hover:shadow-xl hover:-translate-y-0.5',
    outline:
      'border-2 border-red-600 text-red-600 bg-transparent hover:bg-red-600 hover:text-white',
    secondary:
      'bg-white text-red-600 border-2 border-red-600 hover:bg-red-600 hover:text-white shadow-lg hover:shadow-xl hover:-translate-y-0.5',
  };

  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  return (
    <button
      onClick={handleCallClick}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      title="Call MyHibachi - Click to dial (916) 740-8768"
    >
      <Phone size={size === 'sm' ? 16 : size === 'lg' ? 20 : 18} />
      <span>Call Us</span>
    </button>
  );
}
