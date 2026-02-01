'use client';

import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  FileText,
  MessageSquare,
  Paperclip,
  X,
  ChevronDown,
  Save,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  QUICK_REPLIES,
  REPLY_TEMPLATES,
  EMAIL_SIGNATURE,
  SMS_CHAR_LIMIT,
} from '../constants';
import { useDraftAutoSave, formatDraftSavedTime } from '../hooks';
import type { ChannelType, ReplyTemplate } from '../types';

interface ComposePaneProps {
  threadId: string | null;
  channel: ChannelType;
  recipientName?: string;
  recipientEmail?: string;
  onSend: (content: string) => Promise<void>;
  onAIGenerate?: () => Promise<string>;
  isLoading?: boolean;
  placeholder?: string;
}

/**
 * ComposePane - Message composition area
 *
 * Features:
 * - Rich text editor (for email)
 * - Plain text (for SMS/social)
 * - Quick reply templates
 * - AI-generated replies
 * - Draft auto-save
 * - Signature insertion
 * - Character count (SMS)
 */
export function ComposePane({
  threadId,
  channel,
  recipientName,
  recipientEmail,
  onSend,
  onAIGenerate,
  isLoading = false,
  placeholder,
}: ComposePaneProps) {
  const [content, setContent] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isEmailChannel = channel === 'email';
  const isSmsChannel = channel === 'sms';

  // Auto-save drafts
  const { lastSaved, clearDraft } = useDraftAutoSave({
    threadId,
    content,
    onRestore: saved => setContent(saved),
  });

  // Reset content when thread changes
  useEffect(() => {
    setContent('');
  }, [threadId]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [content]);

  const handleSend = async () => {
    if (!content.trim() || sending) return;

    setSending(true);
    try {
      // Append signature for email
      const finalContent = isEmailChannel ? content + EMAIL_SIGNATURE : content;

      await onSend(finalContent);
      setContent('');
      clearDraft();
    } finally {
      setSending(false);
    }
  };

  const handleAIGenerate = async () => {
    if (!onAIGenerate || aiGenerating) return;

    setAiGenerating(true);
    try {
      const aiReply = await onAIGenerate();
      setContent(aiReply);
    } finally {
      setAiGenerating(false);
    }
  };

  const handleTemplateSelect = (template: ReplyTemplate) => {
    // Replace placeholders with actual values
    let text = template.text
      .replace(/\{\{customer_name\}\}/g, recipientName || 'Customer')
      .replace(/\{\{response_content\}\}/g, '');

    setContent(text);
    setShowTemplates(false);
    textareaRef.current?.focus();
  };

  const handleQuickReply = (text: string) => {
    setContent(text);
    setShowQuickReplies(false);
    textareaRef.current?.focus();
  };

  const quickReplies = QUICK_REPLIES[channel] || QUICK_REPLIES.general;

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {/* Quick Replies Toggle */}
          <button
            onClick={() => {
              setShowQuickReplies(!showQuickReplies);
              setShowTemplates(false);
            }}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors
              ${
                showQuickReplies
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }
            `}
          >
            <MessageSquare className="h-4 w-4" />
            Quick Replies
          </button>

          {/* Email Templates (email only) */}
          {isEmailChannel && (
            <div className="relative">
              <button
                onClick={() => {
                  setShowTemplates(!showTemplates);
                  setShowQuickReplies(false);
                }}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors
                  ${
                    showTemplates
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }
                `}
              >
                <FileText className="h-4 w-4" />
                Templates
                <ChevronDown className="h-3 w-3" />
              </button>

              {/* Templates dropdown */}
              {showTemplates && (
                <div className="absolute left-0 top-full mt-1 z-20 w-72 bg-white border border-gray-200 rounded-lg shadow-lg py-1">
                  {REPLY_TEMPLATES.map(template => (
                    <button
                      key={template.id}
                      onClick={() => handleTemplateSelect(template)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-50"
                    >
                      <div className="font-medium text-sm text-gray-900">
                        {template.name}
                      </div>
                      <div className="text-xs text-gray-500 line-clamp-1">
                        {template.text.substring(0, 60)}...
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* AI Generate Button */}
          {onAIGenerate && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleAIGenerate}
              disabled={aiGenerating}
              className="text-purple-600 border-purple-200 hover:bg-purple-50"
            >
              <Sparkles
                className={`h-4 w-4 mr-1.5 ${
                  aiGenerating ? 'animate-spin' : ''
                }`}
              />
              {aiGenerating ? 'Generating...' : 'AI Reply'}
            </Button>
          )}
        </div>

        {/* Draft saved indicator */}
        {lastSaved && (
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <Save className="h-3 w-3" />
            Draft saved {formatDraftSavedTime(lastSaved)}
          </span>
        )}
      </div>

      {/* Quick Replies Panel */}
      {showQuickReplies && (
        <div className="mb-3 flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg">
          {quickReplies.map(reply => (
            <button
              key={reply.id}
              onClick={() => handleQuickReply(reply.text)}
              className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full hover:bg-gray-100 transition-colors"
            >
              {reply.label}
            </button>
          ))}
        </div>
      )}

      {/* Compose Area */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder={
            placeholder ||
            `Type your ${channel === 'sms' ? 'SMS' : 'message'}...`
          }
          className="
            w-full min-h-[80px] max-h-[200px] px-4 py-3 pr-24
            border border-gray-300 rounded-lg resize-none
            focus:ring-2 focus:ring-indigo-500 focus:border-transparent
            placeholder-gray-400 text-gray-900
          "
          onKeyDown={e => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              handleSend();
            }
          }}
        />

        {/* Send button */}
        <div className="absolute right-2 bottom-2 flex items-center gap-2">
          <Button
            onClick={handleSend}
            disabled={!content.trim() || sending || isLoading}
            size="sm"
          >
            <Send className="h-4 w-4 mr-1" />
            {sending ? 'Sending...' : 'Send'}
          </Button>
        </div>
      </div>

      {/* Footer info */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
        <div>
          {isEmailChannel && (
            <span>
              Sending as cs@myhibachichef.com • Signature will be appended
            </span>
          )}
          {isSmsChannel && (
            <span
              className={
                content.length > SMS_CHAR_LIMIT ? 'text-orange-500' : ''
              }
            >
              {content.length}/{SMS_CHAR_LIMIT} characters
              {content.length > SMS_CHAR_LIMIT &&
                ' (will be split into multiple messages)'}
            </span>
          )}
        </div>
        <div>
          <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">
            {navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}+Enter
          </kbd>{' '}
          to send
        </div>
      </div>
    </div>
  );
}

export default ComposePane;
