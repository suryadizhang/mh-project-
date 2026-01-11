'use client';

import dynamic from 'next/dynamic';
import {
  ExternalLink,
  Maximize2,
  Minimize2,
  Send,
  Trash2,
  Volume2,
  VolumeX,
  X,
} from 'lucide-react';
import Image from 'next/image';
import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiErrorBoundary } from '@/components/ErrorBoundary';
import { useProtectedPhone, useProtectedPaymentEmail } from '@/components/ui/ProtectedPhone';
import { getWsUrl } from '@/lib/env';
import { logger, logWebSocket } from '@/lib/logger';

// Lazy load EscalationForm - only 5% of users escalate
const EscalationForm = dynamic(() => import('./EscalationForm'), {
  ssr: false,
  loading: () => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="rounded-lg bg-white p-8">Loading...</div>
    </div>
  ),
});

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
  '/book-us/': [
    'Book a table for tonight',
    "What's included in the menu?",
    'How much is the deposit?',
    'Modify my reservation',
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
  '/blog': ['Book hibachi catering', 'Make a reservation', 'Schedule an event', 'How do I book?'],
  default: [
    'Book a table for tonight',
    'Make a reservation',
    'Check my booking',
    'Cancel my reservation',
  ],
};

function ChatWidgetComponent({ page }: ChatWidgetProps) {
  // Anti-scraper protected contact info
  const { tel: protectedTel } = useProtectedPhone();
  const { email: protectedEmail } = useProtectedPaymentEmail();

  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHandoff, setShowHandoff] = useState(false);
  const [showEscalationForm, setShowEscalationForm] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionFailed, setConnectionFailed] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('mh_chat_sound');
      return saved !== 'false'; // Default to enabled
    }
    return true;
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0); // Use ref to avoid re-render loops
  const audioRef = useRef<HTMLAudioElement | null>(null);
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

  // User contact information state
  const [userName, setUserName] = useState<string | null>(
    typeof window !== 'undefined' ? localStorage.getItem('mh_user_name') : null,
  );
  const [userPhone, setUserPhone] = useState<string | null>(
    typeof window !== 'undefined' ? localStorage.getItem('mh_user_phone') : null,
  );
  const [userEmail, setUserEmail] = useState<string | null>(
    typeof window !== 'undefined' ? localStorage.getItem('mh_user_email') : null,
  );
  const [showContactPrompt, setShowContactPrompt] = useState(false);
  const [tempName, setTempName] = useState('');
  const [tempPhone, setTempPhone] = useState('');
  const [tempEmail, setTempEmail] = useState('');
  const [contactError, setContactError] = useState('');

  const storageKey = `mh_chat_${page}`;

  // Store user and thread IDs
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('mh_user_id', userIdRef.current);
      localStorage.setItem(`mh_thread_${page}`, threadIdRef.current);
    }
  }, [page]);

  // Initialize audio for notification sound
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Create a simple notification sound using Web Audio API
      audioRef.current = new Audio(
        'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleogWQb3NvJFhF05ltNvXroc7I1GDr9DfvJlWLT10osbXspZCKUVyo8jftYxGJUlvocLYsIpLKE5yocTYsYpNKlF0oc',
      );
    }
  }, []);

  // Play notification sound
  const playNotificationSound = useCallback(() => {
    if (soundEnabled && audioRef.current) {
      audioRef.current.volume = 0.3;
      audioRef.current.play().catch(() => {
        // Ignore autoplay errors
      });
    }
  }, [soundEnabled]);

  // Toggle sound setting
  const toggleSound = useCallback(() => {
    setSoundEnabled((prev) => {
      const newValue = !prev;
      if (typeof window !== 'undefined') {
        localStorage.setItem('mh_chat_sound', String(newValue));
      }
      return newValue;
    });
  }, []);

  // Store user contact information when it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (userName) {
        localStorage.setItem('mh_user_name', userName);
      }
      if (userPhone) {
        localStorage.setItem('mh_user_phone', userPhone);
      }
      if (userEmail) {
        localStorage.setItem('mh_user_email', userEmail);
      }
    }
  }, [userName, userPhone, userEmail]);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Use centralized WebSocket URL helper (derives wss:// from API URL in production)
    const wsBaseUrl = getWsUrl();
    const wsUrl = `${wsBaseUrl}/api/v1/ws/chat?user_id=${userIdRef.current}&thread_id=${threadIdRef.current}&channel=website&user_role=customer`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        logWebSocket('connected', { url: wsUrl });
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
              confidence:
                data.metadata?.confidence > 0.7
                  ? 'high'
                  : data.metadata?.confidence > 0.4
                    ? 'medium'
                    : 'low',
            };
            setMessages((prev) => [...prev, assistantMessage]);
            playNotificationSound();
            setIsLoading(false);
            setIsTyping(false);
          } else if (data.type === 'typing') {
            setIsTyping(data.metadata?.is_typing || false);
          } else if (data.type === 'connection_status') {
            logWebSocket('status', { content: data.content });
          } else if (data.type === 'system') {
            if (data.content !== 'pong') {
              // Filter out ping/pong messages
              logger.debug('AI API system message', { content: data.content });
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
          logger.error('Failed to parse WebSocket message', error as Error);
        }
      };

      ws.onclose = () => {
        logWebSocket('close', { code: 1000 });
        setIsConnected(false);
        setIsLoading(false);
        setIsTyping(false);
        retryCountRef.current += 1;

        // Stop retrying after 3 attempts
        if (retryCountRef.current < 3 && !reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null;
            connectWebSocket();
          }, 3000);
        } else if (retryCountRef.current >= 3) {
          setConnectionFailed(true);
        }
      };

      ws.onerror = () => {
        // Suppress error logging in development when backend is down
        if (process.env.NODE_ENV === 'development') {
          console.debug('[ChatWidget] WebSocket connection failed - backend may be offline');
        } else {
          logWebSocket('error', {});
        }
        setIsConnected(false);
        setIsLoading(false);
        setIsTyping(false);
      };
    } catch (error) {
      // Suppress error logging in development
      if (process.env.NODE_ENV !== 'development') {
        logger.error('Failed to create WebSocket connection', error as Error);
      }
      setIsConnected(false);
      setConnectionFailed(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- uses refs intentionally to prevent re-render loops
  }, [playNotificationSound]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (isOpen) {
      connectWebSocket();
      retryCountRef.current = 0; // Reset retry count when opening
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
          logger.warn('Failed to parse stored chat', { error: e });
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
    if (!content || isLoading) {
      return;
    }

    // Check if we need to collect user contact info first
    if (!userName || !userPhone) {
      setShowContactPrompt(true);
      return;
    }

    if (!isConnected || !wsRef.current) {
      // Fallback to HTTP if WebSocket is not connected
      return sendMessageHTTP(content);
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
      // Send message via WebSocket with user contact info
      // Note: All users are automatically added to newsletter (opt-out via STOP command)
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          content: content,
          page: page || '/',
          timestamp: new Date().toISOString(),
          userName: userName,
          userPhone: userPhone,
          userEmail: userEmail,
          autoSubscribeNewsletter: true, // Always true - opt-out system
          userId: userIdRef.current,
        }),
      );
    } catch (error) {
      logWebSocket('error', { error });
      // Fallback to HTTP
      setIsLoading(false);
      return sendMessageHTTP(content);
    }
  };

  // Phone formatting helper
  const formatPhoneForDisplay = (value: string): string => {
    const digits = value.replace(/\D/g, '');

    if (digits.length <= 3) {
      return digits;
    } else if (digits.length <= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    } else {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`;
    }
  };

  // Save contact info and continue with message
  const saveContactAndContinue = () => {
    const trimmedName = tempName.trim();
    const cleanedPhone = tempPhone.replace(/\D/g, '');

    // Validation
    if (trimmedName.length < 2) {
      setContactError('Please enter your full name (at least 2 characters)');
      return;
    }

    if (cleanedPhone.length < 10) {
      setContactError('Please enter a valid phone number (at least 10 digits)');
      return;
    }

    // Validate email if provided (optional but recommended for newsletter)
    if (tempEmail.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(tempEmail.trim())) {
        setContactError('Please enter a valid email address');
        return;
      }
    }

    // Save to state (will trigger localStorage save via useEffect)
    setUserName(trimmedName);
    setUserPhone(cleanedPhone);
    if (tempEmail.trim()) {
      setUserEmail(tempEmail.trim().toLowerCase());
    }
    setShowContactPrompt(false);
    setContactError('');
    setTempName('');
    setTempPhone('');
    setTempEmail('');

    // Log for debugging
    logger.info('User contact info collected', {
      name: trimmedName,
      phoneLength: cleanedPhone.length,
      email: tempEmail.trim() || 'not provided',
      autoSubscribe: true,
    });

    // Send the original message after contact info is saved
    setTimeout(() => {
      sendMessage(inputValue);
    }, 100);
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
      const response = await fetch('http://localhost:8002/api/v1/chat', {
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
            customer_chat: true,
          },
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
      logger.error('Chat error', error as Error);
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
    if (protectedEmail) {
      window.open(
        `mailto:${protectedEmail}?subject=My%20Hibachi%20Inquiry&body=Hi%20My%20Hibachi!%20I%20need%20help%20with...`,
        '_blank',
      );
    }
  };

  const handleInstagramDM = () => {
    window.open('https://www.instagram.com/direct/inbox/', '_blank');
  };

  const handleFacebookChat = () => {
    window.open('https://m.me/myhibachichef', '_blank');
  };

  const handleTextMessage = () => {
    if (protectedTel) {
      window.open(
        `sms:${protectedTel}?body=Hi%20My%20Hibachi!%20I%20need%20help%20with...`,
        '_blank',
      );
    }
  };

  const handlePhoneCall = () => {
    if (protectedTel) {
      window.open(`tel:${protectedTel}`, '_blank');
    }
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
      <div className="fixed right-4 bottom-20 z-40">
        <button
          onClick={toggleChat}
          className="relative h-14 w-14 overflow-hidden rounded-full shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl sm:h-16 sm:w-16"
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
    <div
      className={`fixed z-50 flex flex-col rounded-2xl border border-gray-200 bg-white shadow-2xl transition-all duration-300 ${isExpanded
        ? 'right-2 bottom-4 left-2 max-h-[85vh] sm:right-4 sm:left-auto sm:h-[540px] sm:w-[720px] md:h-[560px] md:w-[840px] lg:h-[580px] lg:w-[960px]'
        : 'right-2 bottom-20 h-[70vh] max-h-[570px] w-[calc(100vw-1rem)] max-w-[380px] sm:right-4 sm:h-[540px] sm:w-[360px] md:h-[570px] md:w-[380px]'
        }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between rounded-t-2xl bg-gradient-to-r from-[#ffb800] to-[#db2b28] p-3 text-white">
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-full">
            <Image
              src="/My Hibachi logo.svg"
              alt="My Hibachi"
              width={32}
              height={32}
              className="h-full w-full rounded-full object-cover"
              style={{ objectFit: 'cover' }}
            />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-medium">My Hibachi Assistant</h3>
            <div className="flex items-center space-x-1.5">
              <div
                className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-green-300 shadow-[0_0_6px_rgba(134,239,172,0.8)]' : connectionFailed ? 'bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.8)]' : 'bg-yellow-300 shadow-[0_0_6px_rgba(253,224,71,0.8)]'}`}
              />
              <span className="text-sm text-white/90">
                {isConnected ? 'Connected' : connectionFailed ? 'Offline Mode' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          {/* Clear chat button */}
          {messages.length > 0 && (
            <button
              onClick={() => {
                if (window.confirm('Clear chat history?')) {
                  setMessages([]);
                  if (typeof window !== 'undefined') {
                    localStorage.removeItem(storageKey);
                  }
                }
              }}
              className="flex h-10 w-10 items-center justify-center rounded-full transition-colors hover:bg-white/20"
              aria-label="Clear chat"
              title="Clear chat"
            >
              <Trash2 size={18} className="text-white" />
            </button>
          )}
          {/* Sound toggle button */}
          <button
            onClick={toggleSound}
            className="flex h-10 w-10 items-center justify-center rounded-full transition-colors hover:bg-white/20"
            aria-label={soundEnabled ? 'Mute notifications' : 'Enable notifications'}
            title={soundEnabled ? 'Mute' : 'Unmute'}
          >
            {soundEnabled ? (
              <Volume2 size={18} className="text-white" />
            ) : (
              <VolumeX size={18} className="text-white" />
            )}
          </button>
          {/* Expand/Minimize button */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex h-10 w-10 items-center justify-center rounded-full transition-colors hover:bg-white/20"
            aria-label={isExpanded ? 'Minimize chat' : 'Expand chat'}
            title={isExpanded ? 'Minimize' : 'Expand'}
          >
            {isExpanded ? (
              <Minimize2 size={18} className="text-white" />
            ) : (
              <Maximize2 size={18} className="text-white" />
            )}
          </button>
          {/* Close button */}
          <button
            onClick={toggleChat}
            className="flex h-10 w-10 items-center justify-center rounded-full transition-colors hover:bg-white/20"
            aria-label="Close chat"
            title="Close"
          >
            <X size={20} className="text-white" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {/* Offline Fallback UI */}
        {connectionFailed && messages.length === 0 && (
          <div className="space-y-4 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-orange-100">
              <span className="text-3xl">📱</span>
            </div>
            <div>
              <h4 className="mb-2 font-semibold text-gray-800">Chat Temporarily Unavailable</h4>
              <p className="mb-4 text-sm text-gray-600">
                Our AI assistant is currently offline, but we&apos;re still here to help!
              </p>
            </div>
            <div className="space-y-2">
              <a
                href={protectedTel || 'tel:+19167408768'}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-500 px-4 py-3 font-medium text-white transition-colors hover:bg-green-600"
              >
                <span>📞</span> Call Us Now
              </a>
              <a
                href={`mailto:${protectedEmail || 'cs@myhibachichef.com'}`}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-3 font-medium text-white transition-colors hover:bg-blue-600"
              >
                <span>✉️</span> Email Us
              </a>
              <a
                href="/contact"
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                <span>💬</span> Contact Page
              </a>
            </div>
            <button
              onClick={() => {
                setConnectionFailed(false);
                retryCountRef.current = 0;
                connectWebSocket();
              }}
              className="text-sm text-orange-600 underline hover:text-orange-700"
            >
              Try reconnecting
            </button>
          </div>
        )}

        {/* Normal welcome message when connected or still connecting */}
        {!connectionFailed && messages.length === 0 && (
          <div className="text-center">
            <p className="mb-4 text-sm text-gray-600">
              👋 Hi! I can help you with booking reservations:
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {(WELCOME_SUGGESTIONS[page || ''] || WELCOME_SUGGESTIONS.default).map(
                (suggestion: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="min-h-[44px] rounded-full border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-700 transition-colors hover:bg-orange-100"
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
              className={`max-w-[85%] rounded-2xl p-3 ${message.type === 'user'
                ? 'bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white'
                : 'bg-gray-100 text-gray-800'
                }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'assistant' && (
                  <div className="mt-1 flex-shrink-0">
                    <Image
                      src="/My Hibachi logo.webp"
                      alt="Assistant"
                      width={20}
                      height={20}
                      className="opacity-70"
                    />
                  </div>
                )}
                <div className="flex-1">
                  <p className="text-base leading-relaxed whitespace-pre-wrap">{message.content}</p>
                  <p
                    className={`mt-1 text-xs ${message.type === 'user' ? 'text-white/70' : 'text-gray-500'}`}
                  >
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
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
                          onClick={() => setShowEscalationForm(true)}
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
                  src="/My Hibachi logo.webp"
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
            className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-r from-[#ffb800] to-[#db2b28] text-white transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send size={20} />
          </button>
        </div>

        <div className="mt-2 flex items-center justify-between">
          <button
            onClick={() => setShowEscalationForm(true)}
            className="flex items-center space-x-1 text-xs font-medium text-orange-600 underline hover:text-orange-800"
          >
            <span>💬</span>
            <span>Talk to a human</span>
          </button>
          <p className="text-xs text-gray-400">Press Enter to send</p>
        </div>
      </div>

      {/* Contact Information Collection Modal */}
      {showContactPrompt && (
        <div className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl bg-black/50 p-4">
          <div className="relative w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl">
            {/* Close Button */}
            <button
              onClick={() => setShowContactPrompt(false)}
              className="absolute top-3 right-3 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-500 transition-colors hover:bg-gray-200 hover:text-gray-700"
              aria-label="Close"
              title="Skip for now"
            >
              <X size={18} />
            </button>

            {/* Welcome Header */}
            <div className="mb-4 text-center">
              <div className="mb-2 text-4xl">👋</div>
              <h3 className="mb-1 text-lg font-semibold text-gray-800">Welcome to MyHibachi!</h3>
              <p className="text-sm text-gray-600">
                Please provide your contact information so we can serve you better and create a
                personalized experience.
              </p>
            </div>

            {/* Error Message */}
            {contactError && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3">
                <p className="text-sm text-red-800">{contactError}</p>
              </div>
            )}

            {/* Name Input */}
            <div className="mb-4">
              <label htmlFor="chat-name" className="mb-1 block text-sm font-medium text-gray-700">
                Full Name *
              </label>
              <input
                id="chat-name"
                type="text"
                placeholder="Enter your full name"
                value={tempName}
                onChange={(e) => {
                  setTempName(e.target.value);
                  setContactError('');
                }}
                required
                minLength={2}
                maxLength={100}
                autoFocus
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    // Move to phone input if name is valid
                    if (tempName.trim().length >= 2) {
                      document.getElementById('chat-phone')?.focus();
                    }
                  }
                }}
              />
            </div>

            {/* Phone Input */}
            <div className="mb-4">
              <label htmlFor="chat-phone" className="mb-1 block text-sm font-medium text-gray-700">
                Phone Number *
              </label>
              <input
                id="chat-phone"
                type="tel"
                placeholder="Enter your phone number"
                value={formatPhoneForDisplay(tempPhone)}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '');
                  setTempPhone(value);
                  setContactError('');
                }}
                required
                maxLength={14}
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
                onKeyPress={(e) => {
                  if (
                    e.key === 'Enter' &&
                    tempName.trim().length >= 2 &&
                    tempPhone.replace(/\D/g, '').length >= 10
                  ) {
                    e.preventDefault();
                    saveContactAndContinue();
                  }
                }}
              />
              <p className="mt-1 text-xs text-gray-500">
                Required - So we can follow up on your inquiries
              </p>
            </div>

            {/* Email Input (optional) */}
            <div className="mb-4">
              <label htmlFor="chat-email" className="mb-1 block text-sm font-medium text-gray-700">
                Email Address (Optional)
              </label>
              <input
                id="chat-email"
                type="email"
                placeholder="Enter your email (optional)"
                value={tempEmail}
                onChange={(e) => {
                  setTempEmail(e.target.value);
                  setContactError('');
                }}
                className="w-full rounded-lg border border-gray-300 px-4 py-3 text-base focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
                onKeyPress={(e) => {
                  if (
                    e.key === 'Enter' &&
                    tempName.trim().length >= 2 &&
                    tempPhone.replace(/\D/g, '').length >= 10
                  ) {
                    e.preventDefault();
                    saveContactAndContinue();
                  }
                }}
              />
              <p className="mt-1 text-xs text-gray-500">
                Recommended - For exclusive hibachi deals and updates
              </p>
            </div>

            {/* Newsletter Auto-Subscribe Notice */}
            <div className="mb-4 rounded-lg border border-orange-200 bg-orange-50 p-3">
              <p className="text-xs text-gray-700">
                📧 <strong>You&apos;ll automatically receive our newsletter</strong> with exclusive
                offers and hibachi tips.
                <br />
                <span className="text-gray-600">
                  Don&apos;t want updates? Simply reply <strong>&quot;STOP&quot;</strong> anytime to
                  unsubscribe.
                </span>
              </p>
            </div>

            {/* Continue Button */}
            <button
              onClick={saveContactAndContinue}
              disabled={tempName.trim().length < 2 || tempPhone.replace(/\D/g, '').length < 10}
              className="w-full rounded-lg bg-gradient-to-r from-[#ffb800] to-[#db2b28] p-3 font-medium text-white transition-all hover:shadow-md disabled:cursor-not-allowed disabled:from-gray-400 disabled:to-gray-400 disabled:opacity-50"
            >
              Start Chatting 💬
            </button>

            {/* Privacy Note */}
            <p className="mt-3 text-center text-xs text-gray-500">
              🔒 Your information is safe and only used to provide you with the best service and
              follow up on your booking inquiries.
            </p>
          </div>
        </div>
      )}

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
                <span className="text-sm font-medium">Call Us</span>
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
                <span className="text-sm font-medium">{protectedEmail || 'Contact Us'}</span>
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

      {/* Escalation Form Modal */}
      {showEscalationForm && (
        <EscalationForm
          conversationId={threadIdRef.current}
          userName={userName}
          userPhone={userPhone}
          userEmail={userEmail}
          onClose={() => setShowEscalationForm(false)}
          onSuccess={() => {
            // Optionally show a message in chat
            const confirmMessage: Message = {
              id: Math.random().toString(36).substring(7),
              type: 'assistant',
              content:
                "Thank you! We've received your request. Our team will contact you shortly. 📞",
              timestamp: new Date(),
              confidence: 'high',
            };
            setMessages((prev) => [...prev, confirmMessage]);
          }}
        />
      )}
    </div>
  );
}

// Wrap component with error boundary
export default function ChatWidget(props: ChatWidgetProps) {
  return (
    <ApiErrorBoundary apiEndpoint="/api/chat">
      <ChatWidgetComponent {...props} />
    </ApiErrorBoundary>
  );
}
