/**
 * RingCentral Live Chat API Integration
 *
 * This service provides real-time communication with RingCentral agents
 * directly within our custom chat interface, without using their widget.
 */

export interface LiveChatSession {
  sessionId: string;
  agentId?: string;
  agentName?: string;
  status: 'waiting' | 'connected' | 'ended';
  startedAt: Date;
}

export interface LiveChatMessage {
  id: string;
  sessionId: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  agentName?: string;
}

export interface StartLiveChatRequest {
  name: string;
  phone: string;
  email?: string;
  initialMessage?: string;
  context?: {
    page?: string;
    previousMessages?: Array<{ role: string; content: string }>;
  };
}

export interface StartLiveChatResponse {
  success: boolean;
  session?: LiveChatSession;
  error?: string;
}

/**
 * Start a live chat session with RingCentral agent
 */
export async function startLiveChat(request: StartLiveChatRequest): Promise<StartLiveChatResponse> {
  try {
    const response = await fetch('/api/ringcentral/chat/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to start live chat' }));
      return {
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
      };
    }

    const data = await response.json();
    return {
      success: true,
      session: {
        sessionId: data.session_id,
        agentId: data.agent_id,
        agentName: data.agent_name,
        status: data.status,
        startedAt: new Date(data.started_at),
      },
    };
  } catch (error) {
    console.error('Error starting live chat:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to start live chat',
    };
  }
}

/**
 * Send a message in an active live chat session
 */
export async function sendLiveChatMessage(
  sessionId: string,
  message: string,
): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch('/api/ringcentral/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to send message' }));
      return {
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
      };
    }

    return { success: true };
  } catch (error) {
    console.error('Error sending message:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to send message',
    };
  }
}

/**
 * Poll for new messages in a live chat session
 */
export async function pollLiveChatMessages(
  sessionId: string,
  lastMessageId?: string,
): Promise<{ success: boolean; messages?: LiveChatMessage[]; error?: string }> {
  try {
    const params = new URLSearchParams({ session_id: sessionId });
    if (lastMessageId) {
      params.append('after', lastMessageId);
    }

    const response = await fetch(`/api/ringcentral/chat/messages?${params.toString()}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to fetch messages' }));
      return {
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
      };
    }

    const data = await response.json();

    interface MessageData {
      id: string;
      session_id: string;
      type: string;
      content: string;
      timestamp: string;
      agent_name?: string;
    }

    return {
      success: true,
      messages: data.messages.map((msg: MessageData) => ({
        id: msg.id,
        sessionId: msg.session_id,
        type: msg.type,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        agentName: msg.agent_name,
      })),
    };
  } catch (error) {
    console.error('Error polling messages:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch messages',
    };
  }
}

/**
 * End a live chat session
 */
export async function endLiveChat(
  sessionId: string,
): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch('/api/ringcentral/chat/end', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to end chat' }));
      return {
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
      };
    }

    return { success: true };
  } catch (error) {
    console.error('Error ending chat:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to end chat',
    };
  }
}

/**
 * Check live chat session status
 */
export async function getLiveChatStatus(sessionId: string): Promise<{
  success: boolean;
  status?: LiveChatSession['status'];
  agentName?: string;
  error?: string;
}> {
  try {
    const response = await fetch(`/api/ringcentral/chat/status?session_id=${sessionId}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Failed to get status' }));
      return {
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
      };
    }

    const data = await response.json();
    return {
      success: true,
      status: data.status,
      agentName: data.agent_name,
    };
  } catch (error) {
    console.error('Error getting chat status:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get status',
    };
  }
}
