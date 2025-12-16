'use client';

import { useState, useEffect, useRef } from 'react';
import { X, Send, ExternalLink, MessageCircle, Instagram, Phone, Mail } from 'lucide-react';
import Image from 'next/image';
import { usePathname } from 'next/navigation';

import { getContactData, openIG } from '@/lib/contactData';
import { logger } from '@/lib/logger';
import { submitChatLead } from '@/lib/leadService';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Array<{ title: string; href: string }>;
  confidence?: 'high' | 'medium' | 'low';
}

interface AssistantProps {
  page?: string;
}

const WELCOME_SUGGESTIONS: Record<string, string[]> = {
  '/BookUs': [
    'Contact a person',
    'How much will my party cost?',
    "What's included in the menu?",
    'How much is the deposit?',
  ],
  '/menu': [
    'Contact a person',
    'Get a quote for my event',
    'What proteins do you offer?',
    'Do you have vegetarian options?',
  ],
  '/faqs': [
    'Contact a person',
    'How far do you travel?',
    'What are your time slots?',
    'How much does hibachi catering cost?',
  ],
  '/contact': [
    'Contact a person',
    'How do I get a quote?',
    "What's your phone number?",
    'How quickly do you respond?',
  ],
  '/quote': [
    'Contact a person',
    "What's included in the base price?",
    'Do you charge travel fees?',
    'How do I book after getting a quote?',
  ],
  '/blog': [
    'Contact a person',
    "What's new with My Hibachi?",
    'Do you have cooking tips?',
    'What events do you cater?',
  ],
  default: [
    'Contact a person',
    'How much does hibachi cost?',
    "What's included in the service?",
    'Do you travel to my location?',
  ],
};

export default function Assistant({ page }: AssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showHandoff, setShowHandoff] = useState(false);
  const [showLeadCapture, setShowLeadCapture] = useState(false);
  const [leadName, setLeadName] = useState('');
  const [leadPhone, setLeadPhone] = useState('');
  const [leadCaptureError, setLeadCaptureError] = useState('');
  const [isSubmittingLead, setIsSubmittingLead] = useState(false);
  const [isEscalated, setIsEscalated] = useState(false); // AI pause when human escalation requested
  const [escalationReason, setEscalationReason] = useState<string>(''); // Track why user escalated
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const pathname = usePathname();

  const storageKey = `mh_chat_${page}`;

  // Smart keywords that AI can handle even after escalation
  const aiCanHandleKeywords = [
    // Booking/Rebooking
    'book',
    'booking',
    'rebook',
    'reschedule',
    'new booking',
    'another event',
    'next party',
    // Pricing/Quotes
    'price',
    'cost',
    'quote',
    'how much',
    'pricing',
    'rate',
    'fee',
    // Menu/Service info
    'menu',
    'food',
    'options',
    'vegetarian',
    'protein',
    'included',
    'what do you serve',
    // Availability
    'available',
    'availability',
    'open',
    'schedule',
    'calendar',
    'date',
    // General questions
    'how does it work',
    'what is',
    'tell me about',
    'information',
    'details',
    // Location/Travel
    'location',
    'area',
    'travel',
    'service area',
    'do you go to',
  ];

  // Issues that need human attention (don't auto-resume AI)
  const humanOnlyKeywords = [
    'complaint',
    'complain',
    'problem',
    'issue',
    'wrong',
    'mistake',
    'error',
    'refund',
    'cancel',
    'dispute',
    'unhappy',
    'disappointed',
    'bad experience',
    'speak to manager',
    'supervisor',
    'urgent',
    'emergency',
  ];

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

  // Check if lead has been captured for this chat
  useEffect(() => {
    if (typeof window !== 'undefined' && isOpen) {
      const leadCaptured = localStorage.getItem('mh_chat_lead_captured');
      if (!leadCaptured && messages.length === 0) {
        setShowLeadCapture(true);
      }
    }
  }, [isOpen, messages.length]);

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const submitLeadCapture = async () => {
    // Validate inputs
    if (!leadName.trim()) {
      setLeadCaptureError('Please enter your name');
      return;
    }
    if (!leadPhone.trim()) {
      setLeadCaptureError('Please enter your phone number');
      return;
    }
    const digitsOnly = leadPhone.replace(/\D/g, '');
    if (digitsOnly.length < 10) {
      setLeadCaptureError('Please enter a valid phone number with at least 10 digits');
      return;
    }

    setIsSubmittingLead(true);
    setLeadCaptureError('');

    try {
      // Use centralized lead service
      const result = await submitChatLead({
        name: leadName,
        phone: leadPhone,
      });

      if (result.success) {
        // Mark lead as captured
        localStorage.setItem('mh_chat_lead_captured', 'true');
        setShowLeadCapture(false);
        logger.info('Chat lead captured successfully', { leadId: result.data.id });

        // Add welcome message
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: `Hi ${leadName}! ≡ƒæï Thanks for reaching out. How can I help you today?`,
          timestamp: new Date(),
          confidence: 'high',
        };
        setMessages([welcomeMessage]);
      } else {
        logger.warn('Chat lead submission failed', { error: result.error });
        setLeadCaptureError('Failed to save your information. Please try again.');
      }
    } catch (error) {
      logger.error('Lead capture error', error as Error);
      setLeadCaptureError('An error occurred. Please try again.');
    } finally {
      setIsSubmittingLead(false);
    }
  };

  const skipLeadCapture = () => {
    // Allow user to skip lead capture
    localStorage.setItem('mh_chat_lead_captured', 'skip');
    setShowLeadCapture(false);
  };

  const sendMessage = async (content: string = inputValue.trim()) => {
    if (!content || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    // SMART ESCALATION LOGIC
    // Check if user escalated but now asking something AI can handle
    if (isEscalated) {
      const messageLower = content.toLowerCase();

      // Check if it's a human-only issue (complaint, refund, etc.)
      const isHumanOnlyIssue = humanOnlyKeywords.some((keyword) => messageLower.includes(keyword));

      // Check if it's something AI can help with (booking, pricing, info)
      const isAiHandleable = aiCanHandleKeywords.some((keyword) => messageLower.includes(keyword));

      if (isHumanOnlyIssue) {
        // Keep escalated for serious issues
        const blockedMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content:
            '🙋 I understand this requires human attention. A team member will contact you shortly to resolve this issue. For urgent matters, please use the contact options below to reach us directly.',
          timestamp: new Date(),
          confidence: 'high',
        };
        setMessages((prev) => [...prev, blockedMessage]);
        return;
      }

      if (isAiHandleable) {
        // Auto-resume AI for simple questions/bookings
        setIsEscalated(false);
        const resumeMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content: '👋 I can help you with that! Let me answer your question...',
          timestamp: new Date(),
          confidence: 'high',
        };
        setMessages((prev) => [...prev, resumeMessage]);

        // GTM tracking - AI auto-resumed
        if (
          typeof window !== 'undefined' &&
          (window as unknown as { dataLayer?: unknown[] }).dataLayer
        ) {
          // Sanitize user input - use keyword category instead of raw text (PII protection)
          const getSanitizedIntent = (message: string): string => {
            const lowerMessage = message.toLowerCase();
            const foundKeyword = aiCanHandleKeywords.find(k => lowerMessage.includes(k));
            return foundKeyword || 'general_inquiry';
          };

          (window as unknown as { dataLayer: unknown[] }).dataLayer.push({
            event: 'ai_auto_resumed',
            previous_escalation: escalationReason,
            user_intent: getSanitizedIntent(content),
          });
        }
        // Continue to AI processing below
      } else {
        // Ambiguous case - offer choice
        const choiceMessage: Message = {
          id: Date.now().toString(),
          type: 'assistant',
          content:
            "I can try to help with that, or you can wait for a team member to contact you. Would you like me to answer, or would you prefer to speak with our staff? (Type 'AI help' or 'wait for human')",
          timestamp: new Date(),
          confidence: 'medium',
        };
        setMessages((prev) => [...prev, choiceMessage]);
        return;
      }
    }

    // Handle user's choice in ambiguous case
    const contentLower = content.toLowerCase();
    if (
      contentLower.includes('ai help') ||
      (contentLower.includes('yes') &&
        messages[messages.length - 1]?.content.includes('Would you like me to answer'))
    ) {
      setIsEscalated(false);
      const resumeMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: '✅ Great! Let me help you with that...',
        timestamp: new Date(),
        confidence: 'high',
      };
      setMessages((prev) => [...prev, resumeMessage]);
      // Continue to AI processing
    } else if (contentLower.includes('wait for human') || contentLower.includes('human')) {
      const waitMessage: Message = {
        id: Date.now().toString(),
        type: 'assistant',
        content: '👍 No problem. A team member will contact you shortly via phone or text.',
        timestamp: new Date(),
        confidence: 'high',
      };
      setMessages((prev) => [...prev, waitMessage]);
      return;
    }

    setIsLoading(true);

    // Check if user wants to contact a person
    const contactKeywords = [
      'contact a person',
      'talk to human',
      'speak to someone',
      'contact person',
      'human support',
      'live chat',
      'real person',
      'customer service',
      'staff',
      'team member',
    ];
    const isContactRequest = contactKeywords.some((keyword) =>
      content.toLowerCase().includes(keyword),
    );

    if (isContactRequest) {
      const contactMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content:
          "≡ƒæï I'd be happy to connect you with our team! You can choose how you'd like to chat with us:",
        timestamp: new Date(),
        confidence: 'high',
      };
      setMessages((prev) => [...prev, contactMessage]);
      setIsLoading(false);
      setShowHandoff(true);
      return;
    }

    try {
      const response = await fetch('/api/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, page }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        citations: data.citations,
        confidence: data.confidence,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content:
          "I'm sorry, I'm having trouble right now. Please try again or talk to a human for immediate help.",
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
          <div>
            <h3 className="font-medium" style={{ fontSize: '14px' }}>
              My Hibachi Assistant
            </h3>
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
              ≡ƒæï Hi! I can help you with:
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
              className={`max-w-[80%] rounded-2xl p-2 ${message.type === 'user'
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
                      {message.citations.map((citation, i) => (
                        <a
                          key={i}
                          href={citation.href}
                          className="flex items-center text-xs text-blue-600 underline hover:text-blue-800"
                        >
                          <ExternalLink size={12} className="mr-1" />
                          {citation.title}
                        </a>
                      ))}
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
                          className="text-xs text-blue-600 underline hover:text-blue-800"
                        >
                          Talk to a human
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
            <div className="rounded-2xl bg-gray-100 p-3">
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
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        {/* Escalation Status Banner */}
        {isEscalated && (
          <div className="mb-3 rounded-lg border border-blue-200 bg-blue-50 p-3">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="mb-1 text-sm font-medium text-blue-800">
                  🙋 Waiting for human contact
                </p>
                <p className="text-xs text-blue-600">
                  A team member will reach out soon. Or ask me anything - I can help with bookings,
                  pricing, and more!
                </p>
              </div>
              <button
                onClick={() => {
                  setIsEscalated(false);
                  const resumeMsg: Message = {
                    id: Date.now().toString(),
                    type: 'assistant',
                    content: '✅ AI chat resumed! How can I help you?',
                    timestamp: new Date(),
                    confidence: 'high',
                  };
                  setMessages((prev) => [...prev, resumeMsg]);
                }}
                className="ml-2 text-xs whitespace-nowrap text-blue-600 underline hover:text-blue-800"
              >
                Resume AI
              </button>
            </div>
          </div>
        )}

        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isEscalated
                ? 'Ask me anything (or wait for human contact)...'
                : 'Ask about our menu, booking, or service areas...'
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
            className="text-xs text-gray-500 underline hover:text-gray-700"
          >
            Talk to a human
          </button>
          <p className="text-xs text-gray-400">Press Enter to send</p>
        </div>
      </div>

      {/* Lead Capture Modal */}
      {showLeadCapture && (
        <div className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-6">
            <div className="mb-4 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-[#ffb800] to-[#db2b28]">
                <MessageCircle size={24} className="text-white" />
              </div>
              <h3 className="mb-2 font-semibold" style={{ fontSize: '16px' }}>
                Welcome to My Hibachi! ≡ƒæï
              </h3>
              <p className="text-gray-600" style={{ fontSize: '13px' }}>
                Before we start, let us know who we&apos;re chatting with
              </p>
            </div>

            {leadCaptureError && (
              <div
                className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-700"
                style={{ fontSize: '13px' }}
              >
                {leadCaptureError}
              </div>
            )}

            <div className="mb-4 space-y-3">
              <div>
                <label htmlFor="lead-name" className="mb-1 block text-sm font-medium text-gray-700">
                  Your Name *
                </label>
                <input
                  id="lead-name"
                  type="text"
                  value={leadName}
                  onChange={(e) => setLeadName(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full rounded-lg border border-gray-300 p-2 focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
                  style={{ fontSize: '14px' }}
                  disabled={isSubmittingLead}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      submitLeadCapture();
                    }
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="lead-phone"
                  className="mb-1 block text-sm font-medium text-gray-700"
                >
                  Phone Number *
                </label>
                <input
                  id="lead-phone"
                  type="tel"
                  value={leadPhone}
                  onChange={(e) => setLeadPhone(e.target.value)}
                  placeholder="Enter your phone number"
                  maxLength={20}
                  className="w-full rounded-lg border border-gray-300 p-2 focus:border-transparent focus:ring-2 focus:ring-orange-500 focus:outline-none"
                  style={{ fontSize: '14px' }}
                  disabled={isSubmittingLead}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      submitLeadCapture();
                    }
                  }}
                />
                <p className="mt-1 text-xs text-gray-500">
                  We&apos;ll use this to follow up on your inquiry
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <button
                onClick={submitLeadCapture}
                disabled={isSubmittingLead}
                className="w-full rounded-lg bg-gradient-to-r from-[#ffb800] to-[#db2b28] p-3 font-medium text-white transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
                style={{ fontSize: '14px' }}
              >
                {isSubmittingLead ? 'Starting Chat...' : 'Start Chatting ≡ƒæï'}
              </button>

              <button
                onClick={skipLeadCapture}
                disabled={isSubmittingLead}
                className="w-full p-2 text-gray-600 transition-colors hover:text-gray-800"
                style={{ fontSize: '13px' }}
              >
                Skip for now
              </button>
            </div>

            <p className="mt-4 text-center text-xs text-gray-400">
              By continuing, you agree to our Privacy Policy
            </p>
          </div>
        </div>
      )}

      {/* Handoff Modal */}
      {showHandoff && (
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-black/50 p-4">
          <div className="w-full max-w-sm rounded-xl bg-white p-6">
            <h3 className="mb-2 text-center font-semibold" style={{ fontSize: '16px' }}>
              ≡ƒÆ¼ Choose How to Chat
            </h3>
            <p className="mb-4 text-center text-gray-600" style={{ fontSize: '12px' }}>
              Select your preferred way to connect with our team
            </p>

            {/* Contact Options */}
            <div className="mb-4 space-y-3">
              {/* SMS Text Message - Primary Human Contact */}
              {(() => {
                const { phone } = getContactData();
                return phone ? (
                  <a
                    href={`sms:${phone}${/iPhone|iPad|iPod/.test(navigator.userAgent) ? '&' : '?'}body=Hi, I need help with my hibachi catering inquiry.`}
                    className="flex w-full items-center gap-3 rounded-lg border-2 border-green-200 bg-green-50 p-4 transition-colors hover:border-green-300 hover:bg-green-100"
                    style={{ fontSize: '14px' }}
                    onClick={() => {
                      // Set escalation state - AI will stop responding
                      setIsEscalated(true);
                      setEscalationReason('sms_requested');
                      setShowHandoff(false);

                      // Add escalation message with smart hint
                      const escalationMessage: Message = {
                        id: Date.now().toString(),
                        type: 'assistant',
                        content:
                          "📱 Perfect! A team member will text you back shortly. Meanwhile, I'm still here if you need help with bookings, pricing, or any questions!",
                        timestamp: new Date(),
                        confidence: 'high',
                      };
                      setMessages((prev) => [...prev, escalationMessage]);

                      // GTM tracking
                      if (
                        typeof window !== 'undefined' &&
                        (window as unknown as { dataLayer?: unknown[] }).dataLayer
                      ) {
                        (window as unknown as { dataLayer: unknown[] }).dataLayer.push({
                          event: 'contact_initiated',
                          channel: 'sms',
                          from: 'chat_assistant',
                          escalated: true,
                          escalation_reason: 'sms_requested',
                        });
                      }
                    }}
                  >
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-green-600">
                      <MessageCircle size={20} className="text-white" />
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium">Text Us (SMS)</div>
                      <div className="text-xs text-gray-500">
                        Get instant response from our team
                      </div>
                    </div>
                  </a>
                ) : null;
              })()}

              {/* Phone Call - Direct Voice Contact */}
              {(() => {
                const { phone } = getContactData();
                return phone ? (
                  <a
                    href={`tel:${phone}`}
                    className="flex w-full items-center gap-3 rounded-lg border-2 border-blue-200 bg-blue-50 p-4 transition-colors hover:border-blue-300 hover:bg-blue-100"
                    style={{ fontSize: '14px' }}
                    onClick={() => {
                      // Set escalation state - AI will stop responding
                      setIsEscalated(true);
                      setEscalationReason('phone_requested');
                      setShowHandoff(false);

                      // Add escalation message with smart hint
                      const escalationMessage: Message = {
                        id: Date.now().toString(),
                        type: 'assistant',
                        content:
                          "📞 Great! Feel free to call us now. Meanwhile, I'm still here if you need help with bookings, pricing, or any questions!",
                        timestamp: new Date(),
                        confidence: 'high',
                      };
                      setMessages((prev) => [...prev, escalationMessage]);

                      // GTM tracking
                      if (
                        typeof window !== 'undefined' &&
                        (window as unknown as { dataLayer?: unknown[] }).dataLayer
                      ) {
                        (window as unknown as { dataLayer: unknown[] }).dataLayer.push({
                          event: 'contact_initiated',
                          channel: 'phone',
                          from: 'chat_assistant',
                          escalated: true,
                          escalation_reason: 'phone_requested',
                        });
                      }
                    }}
                  >
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-600">
                      <Phone size={20} className="text-white" />
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium">Call Us</div>
                      <div className="text-xs text-gray-500">Speak with our team directly</div>
                    </div>
                  </a>
                ) : null;
              })()}

              {/* Messenger Option */}
              <button
                onClick={() => {
                  // Helper for fallback to Facebook page (prevents tabnabbing)
                  const openFacebookPage = () => {
                    window.open(
                      'https://www.facebook.com/people/My-hibachi/61577483702847/',
                      '_blank',
                      'noopener,noreferrer'
                    );
                  };

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
                      openFacebookPage();
                    }
                  } catch (error) {
                    console.warn('Error opening Messenger:', error);
                    openFacebookPage();
                  }
                  setShowHandoff(false);
                }}
                className="flex w-full items-center gap-3 rounded-lg border-2 border-blue-200 bg-blue-50 p-4 transition-colors hover:border-blue-300 hover:bg-blue-100"
                style={{ fontSize: '14px' }}
              >
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-600">
                  <MessageCircle size={20} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <div className="font-medium">Facebook Messenger</div>
                  <div className="text-xs text-gray-500">Instant responses on Facebook</div>
                </div>
              </button>

              {/* Instagram Option */}
              {(() => {
                const { igUser, igUrl } = getContactData();
                return igUser || igUrl ? (
                  <button
                    onClick={() => {
                      openIG(igUser, igUrl);
                      setShowHandoff(false);
                    }}
                    className="flex w-full items-center gap-3 rounded-lg border-2 border-purple-200 bg-purple-50 p-4 transition-colors hover:border-purple-300 hover:bg-purple-100"
                    style={{ fontSize: '14px' }}
                  >
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-pink-500">
                      <Instagram size={20} className="text-white" />
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium">Instagram DM</div>
                      <div className="text-xs text-gray-500">Message us @my_hibachi_chef</div>
                    </div>
                  </button>
                ) : null;
              })()}

              {/* Quick Contact Options */}
              <div className="border-t border-gray-200 pt-2">
                <p className="mb-2 text-center text-xs text-gray-500">Or contact us directly:</p>
                <div className="grid grid-cols-2 gap-2">
                  {/* Phone Option */}
                  {(() => {
                    const { phone } = getContactData();
                    return phone ? (
                      <a
                        href={`tel:${phone}`}
                        className="flex items-center gap-2 rounded-lg bg-green-50 p-2 text-center transition-colors hover:bg-green-100"
                        style={{ fontSize: '12px' }}
                        onClick={() => setShowHandoff(false)}
                      >
                        <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-green-600">
                          <Phone size={12} className="text-white" />
                        </div>
                        <span className="font-medium">Call</span>
                      </a>
                    ) : null;
                  })()}

                  {/* Email Option */}
                  {(() => {
                    const { email } = getContactData();
                    return email ? (
                      <a
                        href={`mailto:${email}`}
                        className="flex items-center gap-2 rounded-lg bg-orange-50 p-2 text-center transition-colors hover:bg-orange-100"
                        style={{ fontSize: '12px' }}
                        onClick={() => setShowHandoff(false)}
                      >
                        <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-orange-600">
                          <Mail size={12} className="text-white" />
                        </div>
                        <span className="font-medium">Email</span>
                      </a>
                    ) : null;
                  })()}
                </div>
              </div>

              {/* Contact Page Link - Only show if not on contact page */}
              {pathname !== '/contact' && (
                <a
                  href="/contact#chat"
                  className="flex w-full items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3 transition-colors hover:bg-gray-100"
                  style={{ fontSize: '13px' }}
                  onClick={() => setShowHandoff(false)}
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-600">
                    <ExternalLink size={16} className="text-white" />
                  </div>
                  <span>View All Contact Options</span>
                </a>
              )}
            </div>

            {/* Close Button */}
            <button
              onClick={() => setShowHandoff(false)}
              className="w-full rounded-lg border border-gray-300 p-3 font-medium transition-colors hover:bg-gray-50"
              style={{ fontSize: '14px' }}
            >
              ΓåÉ Back to Chat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
