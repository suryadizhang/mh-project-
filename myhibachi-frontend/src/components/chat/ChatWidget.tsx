'use client'

import { useState, useEffect, useRef } from 'react'
import { X, Send, ExternalLink } from 'lucide-react'
import Image from 'next/image'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: Array<{ title: string; href: string }>
  confidence?: 'high' | 'medium' | 'low'
}

interface ChatWidgetProps {
  page?: string
}

const WELCOME_SUGGESTIONS: Record<string, string[]> = {
  '/BookUs': [
    "What's included in the menu?",
    'How much is the deposit?',
    'Do you serve Sacramento?',
    "What's the minimum notice for booking?"
  ],
  '/menu': [
    'What proteins do you offer?',
    'What comes with the hibachi experience?',
    'Do you have vegetarian options?',
    "What's included in kids meals?"
  ],
  '/faqs': [
    'How far do you travel?',
    'What are your time slots?',
    'Do you provide the grill?',
    'How does pricing work?'
  ],
  '/contact': [
    'How do I get a quote?',
    "What's your phone number?",
    'How quickly do you respond?',
    'Can I book over the phone?'
  ],
  '/blog': [
    "What's new with My Hibachi?",
    'Do you have cooking tips?',
    'What events do you cater?',
    'How did My Hibachi start?'
  ],
  default: [
    'How much does hibachi cost?',
    "What's included in the service?",
    'Do you travel to my location?',
    'How do I book an event?'
  ]
}

export default function ChatWidget({ page }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showHandoff, setShowHandoff] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const storageKey = `mh_chat_${page}`

  // Load chat from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        try {
          const parsed = JSON.parse(stored) as Message[]
          setMessages(parsed.map(m => ({ ...m, timestamp: new Date(m.timestamp) })))
        } catch (e) {
          console.warn('Failed to parse stored chat:', e)
        }
      }
    }
  }, [storageKey])

  // Save chat to localStorage
  useEffect(() => {
    if (messages.length > 0 && typeof window !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(messages))
    }
  }, [messages, storageKey])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check if chat should start collapsed
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isClosed = localStorage.getItem('mh_chat_closed') === 'true'
      if (isClosed) {
        setIsOpen(false)
      }
    }
  }, [])

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion)
  }

  const sendMessage = async (content: string = inputValue.trim()) => {
    if (!content || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8001/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          page: page || '/',
          consent_to_save: false
        })
      })

      if (!response.ok) throw new Error('Failed to get response')

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        confidence: data.confidence > 0.7 ? 'high' : data.confidence > 0.4 ? 'medium' : 'low'
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content:
          "I'm having trouble right now. Please click 'Talk to a human' below for immediate help via Instagram, Facebook, text, or phone! 📱💬📞",
        timestamp: new Date(),
        confidence: 'low'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const toggleChat = () => {
    setIsOpen(!isOpen)
    if (typeof window !== 'undefined') {
      localStorage.setItem('mh_chat_closed', (!isOpen).toString())
    }
  }

  const handleEmailUs = () => {
    window.open(
      'mailto:cs@myhibachichef.com?subject=My%20Hibachi%20Inquiry&body=Hi%20My%20Hibachi!%20I%20need%20help%20with...',
      '_blank'
    )
  }

  const handleInstagramDM = () => {
    window.open('https://www.instagram.com/direct/inbox/', '_blank')
  }

  const handleFacebookChat = () => {
    window.open('https://m.me/myhibachichef', '_blank')
  }

  const handleTextMessage = () => {
    window.open('sms:+19167408768?body=Hi%20My%20Hibachi!%20I%20need%20help%20with...', '_blank')
  }

  const handlePhoneCall = () => {
    window.open('tel:+19167408768', '_blank')
  }

  const getConfidenceColor = (confidence?: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-500'
      case 'medium':
        return 'bg-yellow-500'
      case 'low':
        return 'bg-red-500'
      default:
        return 'bg-gray-400'
    }
  }

  if (!isOpen) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={toggleChat}
          className="relative w-16 h-16 rounded-full shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl overflow-hidden"
          aria-label="Open My Hibachi Assistant"
        >
          <Image
            src="/My Hibachi logo.svg"
            alt="My Hibachi Assistant"
            width={64}
            height={64}
            className="w-full h-full object-cover rounded-full"
            style={{ objectFit: 'cover' }}
          />
          {messages.length === 0 && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse shadow-sm" />
          )}
        </button>
      </div>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 z-40 w-72 sm:w-80 bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col max-h-[400px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white p-2 rounded-t-2xl flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 flex items-center justify-center rounded-full overflow-hidden">
            <Image
              src="/My Hibachi logo.svg"
              alt="My Hibachi"
              width={24}
              height={24}
              className="w-full h-full object-cover rounded-full"
              style={{ objectFit: 'cover' }}
            />
          </div>
          <div>
            <h3 className="font-medium" style={{ fontSize: '14px' }}>
              My Hibachi Assistant
            </h3>
          </div>
        </div>
        <button
          onClick={toggleChat}
          className="p-1 hover:bg-white/20 rounded-full transition-colors flex items-center justify-center"
          aria-label="Close chat"
        >
          <X size={16} className="text-white" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="text-center">
            <p className="text-gray-600 mb-4" style={{ fontSize: '14px' }}>
              👋 Hi! I can help you with:
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {(WELCOME_SUGGESTIONS[page || ''] || WELCOME_SUGGESTIONS.default).map(
                (suggestion: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-2 py-1 bg-orange-50 hover:bg-orange-100 text-orange-700 rounded-full transition-colors border border-orange-200"
                    style={{ fontSize: '13px' }}
                  >
                    {suggestion}
                  </button>
                )
              )}
            </div>
          </div>
        )}

        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] p-2 rounded-2xl ${
                message.type === 'user'
                  ? 'bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'assistant' && (
                  <div className="flex-shrink-0 mt-1">
                    <Image
                      src="/My Hibachi logo.png"
                      alt="Assistant"
                      width={16}
                      height={16}
                      className="opacity-70"
                    />
                  </div>
                )}
                <div className="flex-1">
                  <p className="whitespace-pre-wrap" style={{ fontSize: '14px' }}>
                    {message.content}
                  </p>

                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {message.citations.map((citation, i) => (
                        <a
                          key={i}
                          href={citation.href}
                          className="flex items-center text-xs text-blue-600 hover:text-blue-800 underline"
                        >
                          <ExternalLink size={12} className="mr-1" />
                          {citation.title}
                        </a>
                      ))}
                    </div>
                  )}

                  {message.confidence && message.type === 'assistant' && (
                    <div className="flex items-center mt-2 space-x-2">
                      <div
                        className={`w-2 h-2 rounded-full ${getConfidenceColor(message.confidence)}`}
                      />
                      {message.confidence === 'low' && (
                        <button
                          onClick={() => setShowHandoff(true)}
                          className="text-xs text-blue-600 hover:text-blue-800 underline font-medium"
                        >
                          Need more help? Talk to a human →
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 p-3 rounded-2xl">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about our menu, booking, or service areas..."
            className="flex-1 p-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            style={{ fontSize: '14px' }}
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className="bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white p-1.5 rounded-lg hover:shadow-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} />
          </button>
        </div>

        <div className="flex justify-between items-center mt-2">
          <button
            onClick={() => setShowHandoff(true)}
            className="text-xs text-orange-600 hover:text-orange-800 underline font-medium flex items-center space-x-1"
          >
            <span>💬</span>
            <span>Talk to a human</span>
          </button>
          <p className="text-xs text-gray-400">Press Enter to send</p>
        </div>
      </div>

      {/* Contact Options Modal */}
      {showHandoff && (
        <div className="absolute inset-0 bg-black/50 rounded-2xl flex items-center justify-center p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-sm relative">
            {/* Close Button */}
            <button
              onClick={() => setShowHandoff(false)}
              className="absolute top-3 right-3 p-1.5 hover:bg-gray-100 rounded-full transition-colors flex items-center justify-center"
              aria-label="Close contact options"
            >
              <X size={18} className="text-gray-500" />
            </button>

            <h3 className="font-semibold mb-4 text-center">Contact Us 💬</h3>

            {/* Quick Contact Options */}
            <div className="space-y-3 mb-4">
              <button
                onClick={handleInstagramDM}
                className="w-full flex items-center justify-center space-x-2 p-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-md transition-all"
              >
                <span>📱</span>
                <span className="text-sm font-medium">Instagram DM</span>
              </button>

              <button
                onClick={handleFacebookChat}
                className="w-full flex items-center justify-center space-x-2 p-3 bg-blue-600 text-white rounded-lg hover:shadow-md transition-all"
              >
                <span>💬</span>
                <span className="text-sm font-medium">Facebook Chat</span>
              </button>

              <button
                onClick={handleTextMessage}
                className="w-full flex items-center justify-center space-x-2 p-3 bg-green-600 text-white rounded-lg hover:shadow-md transition-all"
              >
                <span>📲</span>
                <span className="text-sm font-medium">Text Us: (916) 740-8768</span>
              </button>

              <button
                onClick={handlePhoneCall}
                className="w-full flex items-center justify-center space-x-2 p-3 bg-orange-600 text-white rounded-lg hover:shadow-md transition-all"
              >
                <span>📞</span>
                <span className="text-sm font-medium">Call Us: (916) 740-8768</span>
              </button>
            </div>

            {/* Email Contact Option */}
            <div className="border-t pt-4 text-center">
              <p className="text-sm text-gray-600 mb-3">Or send us an email:</p>
              <button
                onClick={handleEmailUs}
                className="inline-flex items-center justify-center space-x-2 w-full p-3 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg transition-all border border-gray-300"
              >
                <span>📧</span>
                <span className="text-sm font-medium">cs@myhibachichef.com</span>
              </button>
              <p className="text-xs text-gray-500 mt-2">Click to open your email app</p>
            </div>

            {/* Back to Chat Button */}
            <div className="border-t pt-4 mt-4">
              <button
                onClick={() => setShowHandoff(false)}
                className="w-full p-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg text-sm font-medium transition-colors"
              >
                ← Back to Chat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
