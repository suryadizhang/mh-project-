/**
 * AI Readiness API Service
 * 
 * Client service for all Shadow Learning, AI Readiness, and ML Confidence endpoints
 * Handles communication with the backend API for AI monitoring and control.
 */

import type {
  ReadinessDashboard,
  IntentReadiness,
  IntentType,
  TrafficSplitUpdateRequest,
  ActivationRequest,
  DisableRequest,
  Alert,
  RollbackEvent,
  MLPredictorStatus,
  ConfidenceTestRequest,
  ConfidencePrediction,
  SystemConfig,
  RoutingStats,
  ShadowLearningStats,
  TrainingDataExport,
} from '@/types/aiReadiness';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const AI_READINESS_BASE = `${API_BASE_URL}/api/v1/ai/readiness`;
const SHADOW_LEARNING_BASE = `${API_BASE_URL}/api/v1/ai/shadow`;

/**
 * Base fetch wrapper with error handling
 */
async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
}

/**
 * AI Readiness Service
 */
export class AIReadinessService {
  // ============================================
  // Dashboard & Overview
  // ============================================

  /**
   * Get complete readiness dashboard
   */
  static async getDashboard(): Promise<ReadinessDashboard> {
    return apiFetch<ReadinessDashboard>(`${AI_READINESS_BASE}/dashboard`);
  }

  /**
   * Get intent-specific readiness
   */
  static async getIntentReadiness(intent: IntentType): Promise<IntentReadiness> {
    return apiFetch<IntentReadiness>(`${AI_READINESS_BASE}/intent/${intent}`);
  }

  /**
   * Get quick overall status
   */
  static async getOverallStatus(): Promise<{ ready: boolean; score: number; message: string }> {
    return apiFetch(`${AI_READINESS_BASE}/overall`);
  }

  // ============================================
  // Traffic Routing
  // ============================================

  /**
   * Get routing statistics
   */
  static async getRoutingStats(): Promise<RoutingStats> {
    return apiFetch<RoutingStats>(`${AI_READINESS_BASE}/routing/stats`);
  }

  /**
   * Update traffic split percentage for an intent
   */
  static async updateTrafficSplit(
    intent: IntentType,
    percentage: number,
    reason?: string
  ): Promise<{ success: boolean; message: string }> {
    const request: TrafficSplitUpdateRequest = { intent, percentage, reason };
    
    return apiFetch(`${AI_READINESS_BASE}/routing/update-split`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ============================================
  // Activation & Deactivation
  // ============================================

  /**
   * ONE-CLICK ACTIVATION: Enable local AI
   */
  static async enableLocalAI(request: ActivationRequest): Promise<{ 
    success: boolean; 
    message: string;
    intents_enabled: IntentType[];
    traffic_percentages: Record<IntentType, number>;
  }> {
    return apiFetch(`${AI_READINESS_BASE}/activation/enable`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Disable local AI (emergency stop)
   */
  static async disableLocalAI(request: DisableRequest): Promise<{ 
    success: boolean; 
    message: string;
  }> {
    return apiFetch(`${AI_READINESS_BASE}/activation/disable`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ============================================
  // Quality Monitoring
  // ============================================

  /**
   * Get quality degradation alerts
   */
  static async getQualityAlerts(): Promise<Alert[]> {
    return apiFetch<Alert[]>(`${AI_READINESS_BASE}/quality/alerts`);
  }

  /**
   * Get teacher vs student comparison
   */
  static async getQualityComparison(
    intent?: IntentType,
    timeRange?: '1h' | '24h' | '7d' | '30d'
  ): Promise<{
    teacher_metrics: any;
    student_metrics: any;
    comparison: any;
    trend_data: any[];
  }> {
    const params = new URLSearchParams();
    if (intent) params.append('intent', intent);
    if (timeRange) params.append('time_range', timeRange);

    const url = `${AI_READINESS_BASE}/quality/comparison${params.toString() ? `?${params}` : ''}`;
    return apiFetch(url);
  }

  /**
   * Manually rollback an intent
   */
  static async rollbackIntent(
    intent: IntentType,
    reason: string
  ): Promise<{ success: boolean; message: string }> {
    return apiFetch(`${AI_READINESS_BASE}/quality/rollback/${intent}`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  /**
   * Get rollback history
   */
  static async getRollbackHistory(intent?: IntentType): Promise<RollbackEvent[]> {
    const url = intent 
      ? `${AI_READINESS_BASE}/quality/rollback-history?intent=${intent}`
      : `${AI_READINESS_BASE}/quality/rollback-history`;
    
    return apiFetch<RollbackEvent[]>(url);
  }

  // ============================================
  // ML Confidence Predictor (Option C)
  // ============================================

  /**
   * Get ML predictor statistics
   */
  static async getMLPredictorStats(): Promise<MLPredictorStatus> {
    return apiFetch<MLPredictorStatus>(`${AI_READINESS_BASE}/ml/predictor-stats`);
  }

  /**
   * Test confidence prediction for a message
   */
  static async testConfidence(request: ConfidenceTestRequest): Promise<ConfidencePrediction> {
    return apiFetch<ConfidencePrediction>(`${AI_READINESS_BASE}/ml/test-confidence`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Force retrain ML model
   */
  static async retrainPredictor(force: boolean = false): Promise<{
    success: boolean;
    message: string;
    model_version: string;
    training_samples: number;
  }> {
    return apiFetch(`${AI_READINESS_BASE}/ml/retrain`, {
      method: 'POST',
      body: JSON.stringify({ force }),
    });
  }

  // ============================================
  // Configuration
  // ============================================

  /**
   * Get current system configuration
   */
  static async getConfig(): Promise<SystemConfig> {
    return apiFetch<SystemConfig>(`${AI_READINESS_BASE}/config`);
  }

  /**
   * Reset all statistics
   */
  static async resetStats(): Promise<{ success: boolean; message: string }> {
    return apiFetch(`${AI_READINESS_BASE}/reset-stats`, {
      method: 'POST',
    });
  }

  // ============================================
  // Shadow Learning
  // ============================================

  /**
   * Check Ollama health
   */
  static async checkOllamaHealth(): Promise<{
    status: 'healthy' | 'unhealthy' | 'error';
    message: string;
    model_loaded: boolean;
    model_name?: string;
  }> {
    return apiFetch(`${SHADOW_LEARNING_BASE}/health`);
  }

  /**
   * Get Ollama model information
   */
  static async getModelInfo(): Promise<{
    model_name: string;
    model_size: string;
    parameters: string;
    quantization: string;
    family: string;
  }> {
    return apiFetch(`${SHADOW_LEARNING_BASE}/model-info`);
  }

  /**
   * Test Ollama generation
   */
  static async testGenerate(prompt: string): Promise<{
    success: boolean;
    response: string;
    tokens_used: number;
    time_ms: number;
  }> {
    return apiFetch(`${SHADOW_LEARNING_BASE}/test-generate`, {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }

  /**
   * Get shadow learning statistics
   */
  static async getShadowStats(): Promise<ShadowLearningStats> {
    return apiFetch<ShadowLearningStats>(`${SHADOW_LEARNING_BASE}/stats`);
  }

  /**
   * Get training data for export
   */
  static async getTrainingData(
    minSimilarity: number = 0.85,
    intent?: IntentType,
    limit: number = 1000
  ): Promise<TrainingDataExport> {
    const params = new URLSearchParams({
      min_similarity: minSimilarity.toString(),
      limit: limit.toString(),
    });
    
    if (intent) params.append('intent', intent);

    return apiFetch<TrainingDataExport>(
      `${SHADOW_LEARNING_BASE}/training-data?${params.toString()}`
    );
  }

  /**
   * Get shadow learning readiness (quick check)
   */
  static async getShadowReadiness(): Promise<{
    ready: boolean;
    pairs_collected: number;
    avg_similarity: number;
    status: string;
  }> {
    return apiFetch(`${SHADOW_LEARNING_BASE}/readiness`);
  }
}

/**
 * Convenience exports for common operations
 */
export const aiReadinessService = AIReadinessService;

// Export individual methods for easier imports
export const {
  getDashboard,
  getIntentReadiness,
  getOverallStatus,
  getRoutingStats,
  updateTrafficSplit,
  enableLocalAI,
  disableLocalAI,
  getQualityAlerts,
  getQualityComparison,
  rollbackIntent,
  getRollbackHistory,
  getMLPredictorStats,
  testConfidence,
  retrainPredictor,
  getConfig,
  resetStats,
  checkOllamaHealth,
  getModelInfo,
  testGenerate,
  getShadowStats,
  getTrainingData,
  getShadowReadiness,
} = AIReadinessService;

export default AIReadinessService;
