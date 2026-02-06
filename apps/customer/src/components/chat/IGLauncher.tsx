'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { MessageCircle, Instagram, X } from 'lucide-react';

import { getContactData, openIG } from '@/lib/contactData';

export default function IGLauncher() {
  const pathname = usePathname();
  const onContact = pathname === '/contact';
  const [isOpen, setIsOpen] = useState(false);

  if (!onContact) return null;

  const { igUser, igUrl } = getContactData();

  const handleMessengerClick = () => {
    try {
      if (window.FB?.CustomerChat?.show) {
        window.FB.CustomerChat.show();

        // GTM tracking
        if (
          typeof window !== 'undefined' &&
          (window as unknown as { dataLayer?: unknown[] }).dataLayer
        ) {
          (window as unknown as { dataLayer: unknown[] }).dataLayer.push({
            event: 'chat_open',
            channel: 'messenger',
          });
        }
      } else {
        console.warn('Facebook Messenger not available');
      }
    } catch (error) {
      console.warn('Error opening Messenger:', error);
    }
    setIsOpen(false);
  };

  const handleInstagramClick = () => {
    if (igUser || igUrl) {
      openIG(igUser, igUrl);
    }
    setIsOpen(false);
  };

  return (
    <>
      {/* Floating Action Button */}
      <div className="fixed right-4 bottom-20 z-40">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl focus:ring-2 focus:ring-orange-500 focus:outline-none"
          aria-label={isOpen ? 'Close chat options' : 'Open chat options'}
        >
          {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
        </button>
      </div>

      {/* Chat Options Panel */}
      {isOpen && (
        <div className="fixed right-4 bottom-36 z-40 min-w-[280px] rounded-2xl border border-gray-200 bg-white p-4 shadow-2xl">
          <div className="space-y-3">
            <div className="mb-3 text-sm font-medium text-gray-800">
              Choose how to chat with us:
            </div>

            {/* Messenger Option */}
            <button
              onClick={handleMessengerClick}
              className="flex w-full items-center gap-3 rounded-xl bg-blue-50 p-3 transition-colors hover:bg-blue-100 focus:ring-2 focus:ring-blue-500 focus:outline-none"
              aria-label="Chat on Facebook Messenger"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                <MessageCircle size={20} className="text-white" />
              </div>
              <div className="text-left">
                <div className="font-medium text-gray-800">≡ƒÆ¼ Chat on Messenger</div>
                <div className="text-xs text-gray-600">Instant messaging with our team</div>
              </div>
            </button>

            {/* Instagram Option */}
            {(igUser || igUrl) && (
              <button
                onClick={handleInstagramClick}
                className="flex w-full items-center gap-3 rounded-xl bg-purple-50 p-3 transition-colors hover:bg-purple-100 focus:ring-2 focus:ring-purple-500 focus:outline-none"
                aria-label="Message on Instagram"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500">
                  <Instagram size={20} className="text-white" />
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-800">≡ƒô╕ Message on Instagram</div>
                  <div className="text-xs text-gray-600">DM us @{igUser || 'myhibachichef'}</div>
                </div>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-30" onClick={() => setIsOpen(false)} aria-hidden="true" />
      )}
    </>
  );
}
