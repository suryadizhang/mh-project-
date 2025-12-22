'use client';

import dynamic from 'next/dynamic';
import { usePathname } from 'next/navigation';

import { ChatWidgetSkeleton } from '@/components/loading';
import { env } from '@/lib/env';

// Lazy load ChatWidget - it's 1186 lines and not needed for initial render
const ChatWidget = dynamic(() => import('@/components/chat/ChatWidget'), {
  ssr: false,
  loading: () => <ChatWidgetSkeleton />,
});

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Don't show ChatWidget on test pages or if AI chat is disabled
  const isAIChatEnabled = env.NEXT_PUBLIC_AI_CHAT_ENABLED;
  const shouldShowChat = isAIChatEnabled && pathname && !pathname.startsWith('/test');

  return (
    <>
      {children}
      {shouldShowChat && <ChatWidget page={pathname || '/'} />}
    </>
  );
}
