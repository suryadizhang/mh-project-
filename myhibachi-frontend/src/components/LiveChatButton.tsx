"use client";
import { openTawkChat } from '@/lib/tawk';

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
  const handleChatClick = () => {
    openTawkChat();
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
      onClick={handleChatClick}
      className={getButtonClasses()}
      title="Start live chat with our team"
    >
      <i className="bi bi-chat-dots-fill"></i>
      <span>Live Chat</span>
    </button>
  );
}
