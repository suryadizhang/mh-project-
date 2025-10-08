'use client';

import { Send, X, MessageSquare, Bot, User as UserIcon } from 'lucide-react';
import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agent_type?: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

interface AdminChatWidgetProps {
  className?: string;
  defaultOpen?: boolean;
}

export const AdminChatWidget: React.FC<AdminChatWidgetProps> = ({ 
  className, 
  defaultOpen = false 
}) => {
  const { token, stationContext, hasPermission } = useAuth();
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Chat access control
  const canUseChat = hasPermission('use_ai_chat') || hasPermission('manage_ai_chat');

  const availableAgents = [
    { id: 'general', name: 'General Assistant', description: 'General admin tasks and questions' },
    { id: 'analytics', name: 'Analytics Agent', description: 'Data analysis and reporting' },
    { id: 'customer_service', name: 'Customer Service', description: 'Customer support and CRM' },
    { id: 'operations', name: 'Operations', description: 'Operational tasks and management' },
    { id: 'technical', name: 'Technical Support', description: 'System and technical issues' },
  ];

  // WebSocket connection management with station context
  const connectWebSocket = useCallback(() => {
    if (!canUseChat || !token || !stationContext) return;
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Use the new unified chat WebSocket endpoint with station context
    const wsUrl = `ws://localhost:8002/ws/chat?` +
      `station_id=${stationContext.station_id}&` +
      `role=${stationContext.role}&` +
      `channel=admin_panel`;

    try {
      const ws = new WebSocket(wsUrl);
      ws.addEventListener('open', () => {
        // Send authentication after connection
        ws.send(JSON.stringify({
          type: 'auth',
          token: token,
          station_context: stationContext
        }));
      });

      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Admin chat WebSocket connected');
        setIsConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'ai_response') {
            const assistantMessage: Message = {
              id: data.message_id || (Date.now() + 1).toString(),
              type: 'assistant',
              content: data.content,
              timestamp: new Date(data.timestamp || Date.now()),
              agent_type: data.agent_type,
              confidence: data.confidence,
              metadata: data.metadata
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setIsLoading(false);
            setIsTyping(false);
          } else if (data.type === 'typing') {
            setIsTyping(data.is_typing || false);
          } else if (data.type === 'system') {
            if (data.content !== 'pong') {
              const systemMessage: Message = {
                id: (Date.now() + 1).toString(),
                type: 'system',
                content: data.content,
                timestamp: new Date(),
              };
              setMessages((prev) => [...prev, systemMessage]);
            }
          } else if (data.type === 'error') {
            const errorMessage: Message = {
              id: (Date.now() + 1).toString(),
              type: 'assistant',
              content: data.content || "I'm experiencing technical difficulties. Please try again.",
              timestamp: new Date(),
              confidence: 0,
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
        console.log('Admin chat WebSocket disconnected');
        setIsConnected(false);
        setIsLoading(false);
        setIsTyping(false);

        // Attempt to reconnect after a delay
        if (!reconnectTimeoutRef.current && canUseChat) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('Admin chat WebSocket error:', error);
        setIsConnected(false);
        setIsLoading(false);
        setIsTyping(false);
      };
    } catch (error) {
      console.error('Failed to create admin chat WebSocket connection:', error);
      setIsConnected(false);
    }
  }, [canUseChat, token, stationContext]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (isOpen && canUseChat) {
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
  }, [isOpen, connectWebSocket, canUseChat]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (content: string = inputValue.trim()) => {
    if (!content || isLoading || !canUseChat) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Try WebSocket first, fallback to HTTP
    if (isConnected && wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content: content,
          agent_type: selectedAgent || 'general',
          context: {
            station_id: stationContext?.station_id,
            user_role: stationContext?.role,
            permissions: stationContext?.permissions,
            channel: 'admin_panel'
          },
          timestamp: new Date().toISOString(),
        }));
      } catch (error) {
        console.error('WebSocket send error:', error);
        setIsLoading(false);
        await sendMessageHTTP(content);
      }
    } else {
      await sendMessageHTTP(content);
    }
  };

  // Fallback HTTP method
  const sendMessageHTTP = async (content: string) => {
    if (!content || !token || !stationContext) return;

    try {
      const response = await fetch('http://localhost:8002/api/v1/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: content,
          agent_type: selectedAgent || 'general',
          context: {
            station_id: stationContext.station_id,
            user_role: stationContext.role,
            permissions: stationContext.permissions,
            channel: 'admin_panel'
          }
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      const assistantMessage: Message = {
        id: data.message_id || (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.content,
        timestamp: new Date(data.timestamp || Date.now()),
        agent_type: data.agent_type,
        confidence: data.confidence,
        metadata: data.metadata
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Admin chat HTTP error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "I'm experiencing technical difficulties. Please try again or contact support.",
        timestamp: new Date(),
        confidence: 0,
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

  const getAgentIcon = (agentType?: string) => {
    switch (agentType) {
      case 'analytics': return '📊';
      case 'customer_service': return '🎧';
      case 'operations': return '⚙️';
      case 'technical': return '🔧';
      default: return '🤖';
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'bg-gray-400';
    if (confidence > 0.8) return 'bg-green-500';
    if (confidence > 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (!canUseChat) {
    return (
      <Card className={className}>
        <CardContent className="p-6 text-center">
          <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">AI Chat access not available with your current permissions.</p>
        </CardContent>
      </Card>
    );
  }

  if (!isOpen) {
    return (
      <div className={className}>
        <Button
          onClick={() => setIsOpen(true)}
          className="flex items-center space-x-2"
          variant="outline"
        >
          <Bot className="h-4 w-4" />
          <span>Open AI Assistant</span>
        </Button>
      </div>
    );
  }

  return (
    <Card className={`${className} flex flex-col h-[600px]`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-blue-600" />
            <span>AI Assistant</span>
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Agent Selection */}
        <div className="mt-2">
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select an agent...</option>
            {availableAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name} - {agent.description}
              </option>
            ))}
          </select>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0 p-4">
        {/* Messages */}
        <div className="flex-1 space-y-4 overflow-y-auto mb-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500">
              <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="mb-2">Welcome to your AI Assistant!</p>
              <p className="text-sm">
                Station: <strong>{stationContext?.station_name}</strong><br />
                Role: <strong>{stationContext?.role}</strong>
              </p>
              <p className="text-xs mt-2">Select an agent above and start chatting.</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.type === 'system'
                    ? 'bg-yellow-50 border border-yellow-200 text-yellow-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {message.type === 'assistant' && (
                    <span className="text-lg flex-shrink-0">
                      {getAgentIcon(message.agent_type)}
                    </span>
                  )}
                  {message.type === 'user' && (
                    <UserIcon className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                    
                    {message.type === 'assistant' && (
                      <div className="mt-2 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {message.agent_type && (
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {availableAgents.find(a => a.id === message.agent_type)?.name || message.agent_type}
                            </span>
                          )}
                          {message.confidence !== undefined && (
                            <div className="flex items-center space-x-1">
                              <div className={`h-2 w-2 rounded-full ${getConfidenceColor(message.confidence)}`} />
                              <span className="text-xs text-gray-500">
                                {Math.round(message.confidence * 100)}%
                              </span>
                            </div>
                          )}
                        </div>
                        <span className="text-xs text-gray-500">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {(isLoading || isTyping) && (
            <div className="flex justify-start">
              <div className="rounded-lg bg-gray-100 p-3">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getAgentIcon(selectedAgent)}</span>
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
                    <span className="text-xs text-gray-500">AI is thinking...</span>
                  )}
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t pt-4">
          <div className="flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                selectedAgent 
                  ? `Ask the ${availableAgents.find(a => a.id === selectedAgent)?.name}...`
                  : "Select an agent to start chatting..."
              }
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading || !selectedAgent}
            />
            <Button
              onClick={() => sendMessage()}
              disabled={!inputValue.trim() || isLoading || !selectedAgent}
              size="sm"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Connected to station: {stationContext?.station_name} | Role: {stationContext?.role}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default AdminChatWidget;