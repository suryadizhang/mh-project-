/**
 * TypeScript Types for AI Readiness System
 *
 * Defines all interfaces for shadow learning, intent readiness monitoring,
 * ML confidence prediction, and quality tracking.
 */

export type IntentType = 'faq' | 'quote' | 'booking' | 'menu' | 'complaint' | 'pricing' | 'unknown';

export type ReadinessStatus = 'ready' | 'training' | 'not_ready' | 'error';

export type AlertSeverity = 'critical' | 'warning' | 'info';

export type AIMode = 'shadow' | 'active' | 'disabled';

// ============================================
// Dashboard & Overview
// ============================================

export interface ReadinessDashboard {
  overall_readiness: OverallReadiness;
  intent_breakdown: Record<IntentType, IntentReadiness>;
  quality_metrics: QualityMetrics;
  recommendations: string[];
  routing_stats: RoutingStats;
  recent_alerts: Alert[];
  ml_predictor_status: MLPredictorStatus;
  system_config: SystemConfig;
}

export interface OverallReadiness {
  score: number; // 0-100
  status: ReadinessStatus;
  ready_intents: IntentType[];
  training_intents: IntentType[];
  total_pairs_collected: number;
  avg_similarity: number;
  avg_confidence: number;
  estimated_cost_savings: number;
  can_activate: boolean;
  blocking_reasons: string[];
}

// ============================================
// Intent-Specific Readiness (Option B)
// ============================================

export interface IntentReadiness {
  intent: IntentType;
  readiness_score: number; // 0-100
  status: ReadinessStatus;

  // Data Collection
  pairs_collected: number;
  min_pairs_required: number;
  pairs_progress: number; // 0-100

  // Quality Metrics
  avg_similarity: number;
  min_similarity_required: number;
  similarity_trend: 'improving' | 'stable' | 'declining';

  // ML Confidence (Option C)
  avg_confidence: number;
  min_confidence_required: number;
  confidence_trend: 'improving' | 'stable' | 'declining';

  // Traffic Routing
  current_traffic_percent: number;
  recommended_traffic_percent: number;
  local_ai_requests: number;
  teacher_ai_requests: number;

  // Activation
  can_activate: boolean;
  can_increase_traffic: boolean;
  blocking_reasons: string[];

  // Recent Performance
  last_24h_pairs: number;
  last_24h_avg_similarity: number;
  last_7d_avg_similarity: number;
}

// ============================================
// Quality Monitoring & Comparison
// ============================================

export interface QualityMetrics {
  teacher_metrics: ModelMetrics;
  student_metrics: ModelMetrics;
  comparison: ModelComparison;
  degradation_alerts: Alert[];
}

export interface ModelMetrics {
  avg_response_time_ms: number;
  avg_similarity_score: number;
  avg_confidence_score: number;
  total_requests: number;
  success_rate: number;
  avg_tokens_used: number;
  avg_cost_per_request: number;
}

export interface ModelComparison {
  similarity_delta: number; // student - teacher
  response_time_delta_ms: number;
  cost_savings_percent: number;
  quality_acceptable: boolean;
  recommendation: 'increase_traffic' | 'maintain' | 'decrease_traffic' | 'rollback';
}

// ============================================
// Routing & Traffic Stats
// ============================================

export interface RoutingStats {
  total_requests: number;
  local_ai_requests: number;
  teacher_ai_requests: number;
  local_ai_percentage: number;

  by_intent: Record<IntentType, IntentRoutingStats>;

  cost_metrics: {
    teacher_total_cost: number;
    local_ai_total_cost: number;
    total_savings: number;
    savings_percentage: number;
  };

  performance_metrics: {
    avg_teacher_response_time_ms: number;
    avg_local_response_time_ms: number;
    response_time_improvement: number;
  };
}

export interface IntentRoutingStats {
  intent: IntentType;
  total_requests: number;
  local_ai_count: number;
  teacher_ai_count: number;
  local_ai_percentage: number;
  avg_similarity: number;
  avg_confidence: number;
}

// ============================================
// ML Confidence Predictor (Option C)
// ============================================

export interface MLPredictorStatus {
  model_version: string;
  last_trained: string;
  training_samples: number;
  model_accuracy: number;
  feature_importance: Record<string, number>;

  performance_metrics: {
    precision: number;
    recall: number;
    f1_score: number;
    auc_roc: number;
  };

  prediction_stats: {
    total_predictions: number;
    high_confidence_count: number;
    medium_confidence_count: number;
    low_confidence_count: number;
  };

  needs_retraining: boolean;
  retrain_reason?: string;
}

export interface ConfidencePrediction {
  message: string;
  intent: IntentType;
  predicted_confidence: number;
  recommendation: 'use_local' | 'use_teacher' | 'uncertain';
  reasoning: string;
  features_analyzed: Record<string, any>;
}

// ============================================
// Alerts & Notifications
// ============================================

export interface Alert {
  id: string;
  severity: AlertSeverity;
  intent: IntentType;
  message: string;
  created_at: string;

  metrics?: {
    current_similarity?: number;
    threshold?: number;
    delta?: number;
  };

  actions?: AlertAction[];
  auto_rollback_triggered?: boolean;
}

export interface AlertAction {
  type: 'rollback' | 'decrease_traffic' | 'disable' | 'investigate';
  label: string;
  endpoint: string;
  method: 'POST' | 'GET';
}

// ============================================
// Rollback History
// ============================================

export interface RollbackEvent {
  id: string;
  intent: IntentType;
  timestamp: string;
  trigger: 'manual' | 'auto' | 'quality_alert';
  reason: string;

  before_state: {
    traffic_percent: number;
    avg_similarity: number;
    mode: AIMode;
  };

  after_state: {
    traffic_percent: number;
    avg_similarity: number;
    mode: AIMode;
  };

  triggered_by: string;
  notes?: string;
}

// ============================================
// System Configuration
// ============================================

export interface SystemConfig {
  shadow_learning_enabled: boolean;
  local_ai_mode: AIMode;
  ollama_base_url: string;
  ollama_model_name: string;

  thresholds: {
    min_similarity_score: number;
    min_confidence_score: number;

    faq_min_pairs: number;
    faq_min_similarity: number;

    quote_min_pairs: number;
    quote_min_similarity: number;

    booking_min_pairs: number;
    booking_min_similarity: number;
  };

  auto_rollback: {
    enabled: boolean;
    similarity_drop_threshold: number;
    confidence_drop_threshold: number;
  };
}

// ============================================
// API Request/Response Types
// ============================================

export interface TrafficSplitUpdateRequest {
  intent: IntentType;
  percentage: number; // 0-100
  reason?: string;
}

export interface ActivationRequest {
  reason: string;
  enable_intents?: IntentType[];
  start_percentage?: number; // Default 10%
}

export interface DisableRequest {
  reason: string;
  emergency?: boolean;
}

export interface ConfidenceTestRequest {
  message: string;
  intent: IntentType;
}

export interface RetrainRequest {
  force?: boolean;
  min_samples?: number;
}

// ============================================
// Shadow Learning Stats
// ============================================

export interface ShadowLearningStats {
  total_pairs: number;
  high_quality_pairs: number; // similarity >= 0.85
  avg_similarity: number;
  by_intent: Record<IntentType, IntentStats>;
  collection_rate: {
    last_hour: number;
    last_24h: number;
    last_7d: number;
  };
}

export interface IntentStats {
  intent: IntentType;
  count: number;
  avg_similarity: number;
  high_quality_count: number;
}

// ============================================
// Training Data Export
// ============================================

export interface TrainingDataExport {
  export_id: string;
  created_at: string;
  pair_count: number;
  intents_included: IntentType[];
  min_similarity: number;
  format: 'jsonl' | 'csv' | 'parquet';
  download_url: string;
}

// ============================================
// Chart & Visualization Data
// ============================================

export interface SimilarityTrendData {
  timestamp: string;
  intent: IntentType;
  similarity: number;
  confidence: number;
  is_local_ai: boolean;
}

export interface CostTrendData {
  timestamp: string;
  teacher_cost: number;
  local_cost: number;
  savings: number;
  requests_count: number;
}

export interface ResponseTimeData {
  timestamp: string;
  teacher_time_ms: number;
  local_time_ms: number;
  improvement_percent: number;
}

// ============================================
// Component Props Types
// ============================================

export interface ReadinessOverviewProps {
  dashboard: ReadinessDashboard;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export interface IntentReadinessCardProps {
  readiness: IntentReadiness;
  onTrafficUpdate: (intent: IntentType, percentage: number) => Promise<void>;
  onRollback: (intent: IntentType) => Promise<void>;
}

export interface ActivationButtonProps {
  overallReadiness: OverallReadiness;
  onActivate: (request: ActivationRequest) => Promise<void>;
  onDisable: (request: DisableRequest) => Promise<void>;
  isActivating: boolean;
}

export interface QualityComparisonChartProps {
  data: SimilarityTrendData[];
  timeRange: '1h' | '24h' | '7d' | '30d';
  onTimeRangeChange: (range: string) => void;
}

export interface AlertsListProps {
  alerts: Alert[];
  onActionClick: (alert: Alert, action: AlertAction) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
}

export interface TrafficSplitControlProps {
  routingStats: RoutingStats;
  intentReadiness: Record<IntentType, IntentReadiness>;
  onUpdateTraffic: (intent: IntentType, percentage: number) => Promise<void>;
}

export interface ConfidenceTestPanelProps {
  onTest: (request: ConfidenceTestRequest) => Promise<ConfidencePrediction>;
}
