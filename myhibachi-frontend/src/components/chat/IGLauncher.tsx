'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import { MessageCircle, Instagram, X } from 'lucide-react'
import { getContactData, openIG } from '@/lib/contactData'

export default function IGLauncher() {
  const pathname = usePathname()
  const onContact = pathname === '/contact'
  const [isOpen, setIsOpen] = useState(false)

  if (!onContact) return null

  const { igUser, igUrl } = getContactData()

  const handleMessengerClick = () => {
    try {
      if (window.FB?.CustomerChat?.show) {
        window.FB.CustomerChat.show()

        // GTM tracking
        if (typeof window !== 'undefined' && (window as unknown as { dataLayer?: unknown[] }).dataLayer) {
          ;(window as unknown as { dataLayer: unknown[] }).dataLayer.push({ event: 'chat_open', channel: 'messenger' })
        }
      } else {
        console.warn('Facebook Messenger not available')
      }
    } catch (error) {
      console.warn('Error opening Messenger:', error)
    }
    setIsOpen(false)
  }

  const handleInstagramClick = () => {
    if (igUser || igUrl) {
      openIG(igUser, igUrl)
    }
    setIsOpen(false)
  }

  return (
    <>
      {/* Floating Action Button */}
      <div className="fixed bottom-20 right-4 z-40">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-14 h-14 bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-orange-500 flex items-center justify-center"
          aria-label={isOpen ? "Close chat options" : "Open chat options"}
        >
          {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
        </button>
      </div>

      {/* Chat Options Panel */}
      {isOpen && (
        <div className="fixed bottom-36 right-4 z-40 bg-white rounded-2xl shadow-2xl border border-gray-200 p-4 min-w-[280px]">
          <div className="space-y-3">
            <div className="text-sm font-medium text-gray-800 mb-3">
              Choose how to chat with us:
            </div>

            {/* Messenger Option */}
            <button
              onClick={handleMessengerClick}
              className="w-full flex items-center gap-3 p-3 bg-blue-50 hover:bg-blue-100 rounded-xl transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Chat on Facebook Messenger"
            >
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                <MessageCircle size={20} className="text-white" />
              </div>
              <div className="text-left">
                <div className="font-medium text-gray-800">💬 Chat on Messenger</div>
                <div className="text-xs text-gray-600">Instant messaging with our team</div>
              </div>
            </button>

            {/* Instagram Option */}
            {(igUser || igUrl) && (
              <button
                onClick={handleInstagramClick}
                className="w-full flex items-center gap-3 p-3 bg-purple-50 hover:bg-purple-100 rounded-xl transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500"
                aria-label="Message on Instagram"
              >
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                  <Instagram size={20} className="text-white" />
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-800">📸 Message on Instagram</div>
                  <div className="text-xs text-gray-600">DM us @{igUser || 'myhibachichef'}</div>
                </div>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}
    </>
  )
}
