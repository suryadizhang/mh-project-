"use client";
import { initiateCall } from '@/lib/ringcentral';

interface LiveChatButtonProps {
  className?: string;
  variant?: 'primary' | 'outline' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
}

export default function LiveChatButton({
  className = '',
  variant = 'primary',
  size = 'md'
}: LiveChatButtonProps) {
  const handleCallClick = () => {
    initiateCall(); // Opens phone dialer with MyHibachi business number
  };

  const getButtonClasses = () => {
    const baseClasses = 'btn d-flex align-items-center gap-2 fw-bold transition-all';

    const variantClasses = {
      primary: 'btn-primary',
      outline: 'btn-outline-primary',
      secondary: 'btn-secondary'
    };

    const sizeClasses = {
      sm: 'btn-sm',
      md: '',
      lg: 'btn-lg'
    };

    return `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  };

  return (
    <button
      onClick={handleCallClick}
      className={getButtonClasses()}
      title="Call MyHibachi - Click to dial (916) 740-8768"
    >
      <i className="bi bi-telephone-fill"></i>
      <span>Call Us</span>
    </button>
  );
}
