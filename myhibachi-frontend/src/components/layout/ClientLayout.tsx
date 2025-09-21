'use client';

import { usePathname } from 'next/navigation';

import ChatWidget from '@/components/chat/ChatWidget';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Don't show ChatWidget on any excluded pages
  const shouldShowChat = pathname && !pathname.startsWith('/test');

  return (
    <>
      {children}
      {shouldShowChat && <ChatWidget page={pathname || '/'} />}
    </>
  );
}
