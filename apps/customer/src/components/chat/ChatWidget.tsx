'use client';

import { ExternalLink, Send, X } from 'lucide-react';
import Image from 'next/image';
import { useEffect, useRef, useState, useCallback } from 'react';

interface Citation {
  href: string;
  title: string;
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  confidence?: 'high' | 'medium' | 'low';
}

interface ChatWidgetProps {
  page?: string;
}

const WELCOME_SUGGESTIONS: Record<string, string[]> = {
  '/BookUs': [
    "Book a table for tonight",
    "What's included in the menu?",
    'How much is the deposit?',
    "Modify my reservation",
  ],
  '/menu': [
    'Book hibachi for this weekend',
    'What proteins do you offer?',
    'Make a reservation for 6 people',
    "What's included in kids meals?",
  ],
  '/faqs': [
    'How do I make a booking?',
    'Cancel my reservation',
    'Change my booking time',
    'View my reservations',
  ],
  '/contact': [
    'Book a table now',
    'How do I get a quote?',
    'Make a reservation',
    'Check availability',
  ],
  '/blog': [
    'Book hibachi catering',
    'Make a reservation',
    'Schedule an event',
    'How do I book?',
  ],
  default: [
    'Book a table for tonight',
    'Make a reservation',
    'Check my booking',
    'Cancel my reservation',
  ],
};

export default function ChatWidget({ page }: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHandoff, setShowHandoff] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const userIdRef = useRef<string>(
    typeof window !== 'undefined'
      ? localStorage.getItem('mh_user_id') || Math.random().toString(36).substring(7)
      : Math.random().toString(36).substring(7),
  );
  const threadIdRef = useRef<string>(
    typeof window !== 'undefined'
      ? localStorage.getItem(`mh_thread_${page}`) || Math.random().toString(36).substring(7)
      : Math.random().toString(36).substring(7),
  );

  const storageKey = `mh_chat_${page}`;

  // Store user and thread IDs
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('mh_user_id', userIdRef.current);
      localStorage.setItem(`mh_thread_${page}`, threadIdRef.current);
    }
  }, [page]);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Updated to use new AI API WebSocket endpoint (port 8002) with customer role
    const wsUrl = `ws://localhost:8002/ws/chat?user_id=${userIdRef.current}&thread_id=${threadIdRef.current}&channel=website&user_role=customer`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to AI API');
        setIsConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle new AI API WebSocket message format
          if (data.type === 'ai_response') {
            const assistantMessage: Message = {
              id: data.message_id || (Date.now() + 1).toString(),
              type: 'assistant',
              content: data.content,
              timestamp: new Date(data.timestamp || Date.now()),
              confidence: data.metadata?.confidence > 0.7 ? 'high' : data.metadata?.confidence > 0.4 ? 'medium' : 'low',
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setIsLoading(false);
            setIsTyping(false);
          } else if (data.type === 'typing') {
            setIsTyping(data.metadata?.is_typing || false);
          } else if (data.type === 'connection_status') {
            console.log('AI API connection status:', data.content);
          } else if (data.type === 'system') {
            if (data.content !== 'pong') { // Filter out ping/pong messages
              console.log('AI API system message:', data.content);
            }
          } else if (data.type === 'error') {
            const errorMessage: Message = {
              id: (Date.now() + 1).toString(),
              type: 'assistant',
              content:
                data.content ||
                "I'm having trouble right now. Please click 'Talk to a human' below for immediate help! 📱💬📞",
              timestamp: new Date(),
              confidence: 'low',
            };
            setMessages((prev) => [...prev, errorMessage]);
            setIsLoading(false);
            setIsTyping(false);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsLoading(false);
        setIsTyping(false);

        // Attempt to reconnect after a delay
        if (!reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setIsLoading(false);
        setIsTyping(false);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setIsConnected(false);
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    if (isOpen) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [isOpen, connectWebSocket]);

  // Load chat from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        try {
          const parsed = JSON.parse(stored) as Message[];
          setMessages(parsed.map((m) => ({ ...m, timestamp: new Date(m.timestamp) })));
        } catch (e) {
          console.warn('Failed to parse stored chat:', e);
        }
      }
    }
  }, [storageKey]);

  // Save chat to localStorage
  useEffect(() => {
    if (messages.length > 0 && typeof window !== 'undefined') {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    }
  }, [messages, storageKey]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check if chat should start collapsed
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isClosed = localStorage.getItem('mh_chat_closed') === 'true';
      if (isClosed) {
        setIsOpen(false);
      }
    }
  }, []);

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const sendMessage = async (content: string = inputValue.trim()) => {
    if (!content || isLoading || !isConnected || !wsRef.current) {
      if (!isConnected) {
        // Fallback to HTTP if WebSocket is not connected
        return sendMessageHTTP(content);
      }
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Send message via WebSocket
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content: content,
          page: page || '/',
          timestamp: new Date().toISOString(),
        }),
      );
    } catch (error) {
      console.error('WebSocket send error:', error);
      // Fallback to HTTP
      setIsLoading(false);
      return sendMessageHTTP(content);
    }
  };

  // Fallback HTTP method for when WebSocket is not available
  const sendMessageHTTP = async (content: string) => {
    if (!content) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Use new AI API REST endpoint (port 8002) with customer role
      const response = await fetch('http://localhost:8002/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          conversation_id: threadIdRef.current,
          user_id: userIdRef.current,
          user_role: 'customer',
          channel: 'website',
          context: {
            page: page || '/',
            customer_chat: true
          }
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();

      const assistantMessage: Message = {
        id: data.message_id || (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.content,
        timestamp: new Date(data.timestamp || Date.now()),
        confidence: data.confidence > 0.7 ? 'high' : data.confidence > 0.4 ? 'medium' : 'low',
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content:
          "I'm having trouble right now. Please click 'Talk to a human' below for immediate help via Instagram, Facebook, text, or phone! 📱💬📞",
        timestamp: new Date(),
        confidence: 'low',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (typeof window !== 'undefined') {
      localStorage.setItem('mh_chat_closed', (!isOpen).toString());
    }
  };

  const handleEmailUs = () => {
    window.open(
      'mailto:cs@myhibachichef.com?subject=My%20Hibachi%20Inquiry&body=Hi%20My%20Hibachi!%20I%20need%20help%20with...',
      '_blank',
    );
  };

  const handleInstagramDM = () => {
    window.open('https://www.instagram.com/direct/inbox/', '_blank');
  };

  const handleFacebookChat = () => {
    window.open('https://m.me/myhibachichef', '_blank');
  };

  const handleTextMessage = () => {
    window.open('sms:+19167408768?body=Hi%20My%20Hibachi!%20I%20need%20help%20with...', '_blank');
  };

  const handlePhoneCall = () => {
    window.open('tel:+19167408768', '_blank');
  };

  const getConfidenceColor = (confidence?: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed right-4 bottom-4 z-50">
        <button
          onClick={toggleChat}
          className="relative h-16 w-16 overflow-hidden rounded-full shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl"
          aria-label="Open My Hibachi Assistant"
        >
          <Image
            src="/My Hibachi logo.svg"
            alt="My Hibachi Assistant"
            width={64}
            height={64}
            className="h-full w-full rounded-full object-cover"
            style={{ objectFit: 'cover' }}
          />
          {messages.length === 0 && (
            <div className="absolute -top-1 -right-1 h-3 w-3 animate-pulse rounded-full bg-blue-500 shadow-sm" />
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="fixed right-4 bottom-4 z-40 flex max-h-[400px] w-72 flex-col rounded-2xl border border-gray-200 bg-white shadow-2xl sm:w-80">
      {/* Header */}
      <div className="flex items-center justify-between rounded-t-2xl bg-gradient-to-r from-[#ffb800] to-[#db2b28] p-2 text-white">
        <div className="flex items-center space-x-2">
          <div className="flex h-6 w-6 items-center justify-center overflow-hidden rounded-full">
            <Image
              src="/My Hibachi logo.svg"
              alt="My Hibachi"
              width={24}
              height={24}
              className="h-full w-full rounded-full object-cover"
              style={{ objectFit: 'cover' }}
            />
          </div>
          <div className="flex-1">
            <h3 className="font-medium" style={{ fontSize: '14px' }}>
              My Hibachi Assistant
            </h3>
            <div className="flex items-center space-x-1">
              <div
                className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-yellow-400'}`}
              />
              <span className="text-xs text-white/80">
                {isConnected ? 'Connected' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={toggleChat}
          className="flex items-center justify-center rounded-full p-1 transition-colors hover:bg-white/20"
          aria-label="Close chat"
        >
          <X size={16} className="text-white" />
        </button>
      </div>

      {/* Messages */}
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="text-center">
            <p className="mb-4 text-gray-600" style={{ fontSize: '14px' }}>
              👋 Hi! I can help you with booking reservations:
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {(WELCOME_SUGGESTIONS[page || ''] || WELCOME_SUGGESTIONS.default).map(
                (suggestion: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="rounded-full border border-orange-200 bg-orange-50 px-2 py-1 text-orange-700 transition-colors hover:bg-orange-100"
                    style={{ fontSize: '13px' }}
                  >
                    {suggestion}
                  </button>
                ),
              )}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl p-2 ${
                message.type === 'user'
                  ? 'bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'assistant' && (
                  <div className="mt-1 flex-shrink-0">
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
                      {message.citations.map(
                        (citation: { href: string; title: string }, i: number) => (
                          <a
                            key={i}
                            href={citation.href}
                            className="flex items-center text-xs text-blue-600 underline hover:text-blue-800"
                          >
                            <ExternalLink size={12} className="mr-1" />
                            {citation.title}
                          </a>
                        ),
                      )}
                    </div>
                  )}

                  {message.confidence && message.type === 'assistant' && (
                    <div className="mt-2 flex items-center space-x-2">
                      <div
                        className={`h-2 w-2 rounded-full ${getConfidenceColor(message.confidence)}`}
                      />
                      {message.confidence === 'low' && (
                        <button
                          onClick={() => setShowHandoff(true)}
                          className="text-xs font-medium text-blue-600 underline hover:text-blue-800"
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

        {(isLoading || isTyping) && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-gray-100 p-3">
              <div className="flex items-center space-x-2">
                <Image
                  src="/My Hibachi logo.png"
                  alt="Assistant"
                  width={16}
                  height={16}
                  className="opacity-70"
                />
                <div className="flex space-x-1">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                    style={{ animationDelay: '0.1s' }}
                  />
                  <div
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                    style={{ animationDelay: '0.2s' }}
                  />
                </div>
                {isTyping && (
                  <span className="ml-2 text-xs text-gray-500">Assistant is typing...</span>
                )}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isConnected
                ? 'Ask about bookings, reservations, or menu options...'
                : 'Connecting to booking assistant...'
            }
            className="flex-1 rounded-lg border border-gray-300 p-1.5 focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
            style={{ fontSize: '14px' }}
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className="rounded-lg bg-gradient-to-r from-[#ffb800] to-[#db2b28] p-1.5 text-white transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send size={16} />
          </button>
        </div>

        <div className="mt-2 flex items-center justify-between">
          <button
            onClick={() => setShowHandoff(true)}
            className="flex items-center space-x-1 text-xs font-medium text-orange-600 underline hover:text-orange-800"
          >
            <span>💬</span>
            <span>Talk to a human</span>
          </button>
          <p className="text-xs text-gray-400">Press Enter to send</p>
        </div>
      </div>

      {/* Contact Options Modal */}
      {showHandoff && (
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-black/50 p-4">
          <div className="relative w-full max-w-sm rounded-xl bg-white p-6">
            {/* Close Button */}
            <button
              onClick={() => setShowHandoff(false)}
              className="absolute top-3 right-3 flex items-center justify-center rounded-full p-1.5 transition-colors hover:bg-gray-100"
              aria-label="Close contact options"
            >
              <X size={18} className="text-gray-500" />
            </button>

            <h3 className="mb-4 text-center font-semibold">Contact Us 💬</h3>

            {/* Quick Contact Options */}
            <div className="mb-4 space-y-3">
              <button
                onClick={handleInstagramDM}
                className="flex w-full items-center justify-center space-x-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 p-3 text-white transition-all hover:shadow-md"
              >
                <span>📱</span>
                <span className="text-sm font-medium">Instagram DM</span>
              </button>

              <button
                onClick={handleFacebookChat}
                className="flex w-full items-center justify-center space-x-2 rounded-lg bg-blue-600 p-3 text-white transition-all hover:shadow-md"
              >
                <span>💬</span>
                <span className="text-sm font-medium">Facebook Chat</span>
              </button>

              <button
                onClick={handleTextMessage}
                className="flex w-full items-center justify-center space-x-2 rounded-lg bg-green-600 p-3 text-white transition-all hover:shadow-md"
              >
                <span>📲</span>
                <span className="text-sm font-medium">Text Us: (916) 740-8768</span>
              </button>

              <button
                onClick={handlePhoneCall}
                className="flex w-full items-center justify-center space-x-2 rounded-lg bg-orange-600 p-3 text-white transition-all hover:shadow-md"
              >
                <span>📞</span>
                <span className="text-sm font-medium">Call Us: (916) 740-8768</span>
              </button>
            </div>

            {/* Email Contact Option */}
            <div className="border-t pt-4 text-center">
              <p className="mb-3 text-sm text-gray-600">Or send us an email:</p>
              <button
                onClick={handleEmailUs}
                className="inline-flex w-full items-center justify-center space-x-2 rounded-lg border border-gray-300 bg-gray-100 p-3 text-gray-800 transition-all hover:bg-gray-200"
              >
                <span>📧</span>
                <span className="text-sm font-medium">cs@myhibachichef.com</span>
              </button>
              <p className="mt-2 text-xs text-gray-500">Click to open your email app</p>
            </div>

            {/* Back to Chat Button */}
            <div className="mt-4 border-t pt-4">
              <button
                onClick={() => setShowHandoff(false)}
                className="w-full rounded-lg bg-gray-200 p-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-300"
              >
                ← Back to Chat
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
