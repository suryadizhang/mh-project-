"""
Comprehensive Test Suite for AI Monitoring System
Tests metrics collection, alert analysis, predictive monitoring, and feedback loop
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_monitoring_service import AIMonitoringService
from services.alert_analyzer_service import AlertAnalyzerService
from services.predictive_monitor import PredictiveMonitor
from models.monitoring import (
    AIMetric,
    Alert,
    PredictiveWarning,
    FeedbackMetric,
    AlertRule
)


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_orchestrator():
    """Mock AI orchestrator"""
    orchestrator = AsyncMock()
    orchestrator.analyze_alert = AsyncMock(
        return_value={
            "severity": "high",
            "root_cause": "High response time due to API rate limiting",
            "recommendations": [
                "Implement request caching",
                "Add retry logic with exponential backoff",
                "Consider upgrading API tier"
            ],
            "estimated_impact": "15-20% performance degradation"
        }
    )
    return orchestrator


@pytest.fixture
def monitoring_service(mock_db_session):
    """Create AIMonitoringService instance"""
    return AIMonitoringService(db_session=mock_db_session)


@pytest.fixture
def alert_analyzer(mock_db_session, mock_orchestrator):
    """Create AlertAnalyzerService instance"""
    return AlertAnalyzerService(
        db_session=mock_db_session,
        ai_orchestrator=mock_orchestrator
    )


@pytest.fixture
def predictive_monitor(mock_db_session, mock_orchestrator):
    """Create PredictiveMonitor instance"""
    return PredictiveMonitor(
        db_session=mock_db_session,
        ai_orchestrator=mock_orchestrator
    )


class TestAIMonitoringService:
    """Test AI metrics collection and tracking"""

    @pytest.mark.asyncio
    async def test_collect_ai_metrics_all_channels(self, monitoring_service):
        """Test collecting AI metrics across all channels"""
        metrics = await monitoring_service.collect_ai_metrics()
        
        # Verify all channels are tracked
        assert "channels" in metrics
        channels = metrics["channels"]
        
        expected_channels = ["email", "sms", "instagram", "facebook", "phone"]
        for channel in expected_channels:
            assert channel in channels
            assert "requests" in channels[channel]
            assert "avg_response_time" in channels[channel]
            assert "success_rate" in channels[channel]

    @pytest.mark.asyncio
    async def test_record_ai_request_email(self, monitoring_service, mock_db_session):
        """Test recording AI request for email channel"""
        await monitoring_service.record_ai_request(
            channel="email",
            request_type="compose",
            tokens_used=150,
            response_time=0.85,
            success=True,
            metadata={"subject": "Booking confirmation"}
        )
        
        # Verify metric was added to database
        mock_db_session.add.assert_called_once()
        metric = mock_db_session.add.call_args[0][0]
        
        assert isinstance(metric, AIMetric)
        assert metric.channel == "email"
        assert metric.request_type == "compose"
        assert metric.tokens_used == 150
        assert metric.response_time == 0.85
        assert metric.success is True

    @pytest.mark.asyncio
    async def test_record_ai_request_voice(self, monitoring_service, mock_db_session):
        """Test recording AI request for voice channel"""
        await monitoring_service.record_ai_request(
            channel="phone",
            request_type="conversation",
            tokens_used=450,
            response_time=1.2,
            success=True,
            metadata={
                "call_duration": 120,
                "transcription_cost": 0.025,
                "tts_cost": 0.15
            }
        )
        
        mock_db_session.add.assert_called_once()
        metric = mock_db_session.add.call_args[0][0]
        
        assert metric.channel == "phone"
        assert metric.tokens_used == 450
        assert "call_duration" in metric.metadata

    @pytest.mark.asyncio
    async def test_calculate_channel_costs(self, monitoring_service):
        """Test calculating AI costs per channel"""
        costs = await monitoring_service.calculate_channel_costs(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        
        assert "total_cost" in costs
        assert "by_channel" in costs
        assert "by_hour" in costs

    @pytest.mark.asyncio
    async def test_get_performance_trends(self, monitoring_service):
        """Test retrieving performance trends"""
        trends = await monitoring_service.get_performance_trends(
            metric_name="ai.response_time",
            hours=24
        )
        
        assert "current_value" in trends
        assert "trend" in trends
        assert "change_percent" in trends

    @pytest.mark.asyncio
    async def test_health_check_all_services(self, monitoring_service):
        """Test health check for all AI services"""
        with patch('services.speech_service.SpeechService.health_check') as mock_speech:
            mock_speech.return_value = {
                "deepgram": {"status": "healthy", "latency": 0.05},
                "elevenlabs": {"status": "healthy", "latency": 0.08}
            }
            
            health = await monitoring_service.health_check()
            
            assert "ai_orchestrator" in health
            assert "voice_ai" in health
            assert health["voice_ai"]["deepgram"]["status"] == "healthy"


class TestAlertAnalyzerService:
    """Test AI-powered alert analysis"""

    @pytest.mark.asyncio
    async def test_analyze_alert_high_response_time(self, alert_analyzer, mock_db_session):
        """Test analyzing high response time alert"""
        alert = Alert(
            id=1,
            alert_type="performance",
            severity="high",
            metric_name="ai.response_time",
            current_value=2.5,
            threshold=1.0,
            message="AI response time exceeded threshold"
        )
        
        analysis = await alert_analyzer.analyze_alert(alert)
        
        assert "severity" in analysis
        assert "root_cause" in analysis
        assert "recommendations" in analysis
        assert len(analysis["recommendations"]) > 0
        
        # Verify analysis was saved
        mock_db_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_analyze_alert_high_cost(self, alert_analyzer):
        """Test analyzing high cost alert"""
        alert = Alert(
            id=2,
            alert_type="cost",
            severity="warning",
            metric_name="ai.costs.hourly",
            current_value=25.0,
            threshold=15.0,
            message="AI costs exceeded hourly budget"
        )
        
        analysis = await alert_analyzer.analyze_alert(alert)
        
        assert analysis["severity"] in ["low", "medium", "high", "critical"]
        assert "recommendations" in analysis

    @pytest.mark.asyncio
    async def test_get_similar_historical_alerts(self, alert_analyzer):
        """Test finding similar historical alerts"""
        alert = Alert(
            alert_type="performance",
            metric_name="ai.response_time"
        )
        
        similar = await alert_analyzer.get_similar_historical_alerts(alert, limit=5)
        
        assert isinstance(similar, list)
        # Would check resolved alerts if data exists

    @pytest.mark.asyncio
    async def test_suggest_resolution_steps(self, alert_analyzer):
        """Test AI-generated resolution steps"""
        alert = Alert(
            alert_type="error",
            severity="critical",
            message="Voice AI service unavailable"
        )
        
        steps = await alert_analyzer.suggest_resolution_steps(alert)
        
        assert isinstance(steps, list)
        assert len(steps) > 0

    @pytest.mark.asyncio
    async def test_batch_analyze_alerts(self, alert_analyzer):
        """Test analyzing multiple alerts in batch"""
        alerts = [
            Alert(id=1, alert_type="performance", metric_name="ai.latency"),
            Alert(id=2, alert_type="cost", metric_name="ai.costs.total"),
            Alert(id=3, alert_type="error", metric_name="ai.errors")
        ]
        
        analyses = await alert_analyzer.batch_analyze(alerts)
        
        assert len(analyses) == 3
        for analysis in analyses:
            assert "root_cause" in analysis


class TestPredictiveMonitor:
    """Test predictive monitoring and forecasting"""

    @pytest.mark.asyncio
    async def test_predict_metric_trend_response_time(self, predictive_monitor):
        """Test predicting response time trend"""
        prediction = await predictive_monitor.predict_metric_trend(
            metric_name="ai.response_time",
            hours_ahead=24
        )
        
        assert "predicted_value" in prediction
        assert "confidence" in prediction
        assert "trend" in prediction
        assert prediction["trend"] in ["increasing", "decreasing", "stable"]

    @pytest.mark.asyncio
    async def test_predict_cost_trajectory(self, predictive_monitor):
        """Test predicting cost trajectory"""
        forecast = await predictive_monitor.predict_cost_trajectory(
            days_ahead=7
        )
        
        assert "daily_forecast" in forecast
        assert "total_projected_cost" in forecast
        assert len(forecast["daily_forecast"]) == 7

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, predictive_monitor):
        """Test anomaly detection"""
        anomalies = await predictive_monitor.detect_anomalies(
            metric_name="ai.requests",
            hours=24
        )
        
        assert isinstance(anomalies, list)
        for anomaly in anomalies:
            assert "timestamp" in anomaly
            assert "value" in anomaly
            assert "expected_range" in anomaly

    @pytest.mark.asyncio
    async def test_generate_predictive_warning(self, predictive_monitor, mock_db_session):
        """Test generating predictive warning"""
        warning = await predictive_monitor.generate_predictive_warning(
            metric_name="ai.costs.daily",
            predicted_value=150.0,
            threshold=100.0,
            confidence=0.85,
            hours_until=12
        )
        
        # Verify warning was saved
        mock_db_session.add.assert_called_once()
        warning_obj = mock_db_session.add.call_args[0][0]
        
        assert isinstance(warning_obj, PredictiveWarning)
        assert warning_obj.metric_name == "ai.costs.daily"
        assert warning_obj.predicted_value == 150.0

    @pytest.mark.asyncio
    async def test_capacity_planning_recommendation(self, predictive_monitor):
        """Test capacity planning recommendations"""
        recommendation = await predictive_monitor.recommend_capacity_changes(
            current_load=1000,
            growth_rate=0.15
        )
        
        assert "recommended_capacity" in recommendation
        assert "timeline" in recommendation
        assert "estimated_cost" in recommendation


class TestFeedbackLoop:
    """Test AI feedback loop and learning"""

    @pytest.mark.asyncio
    async def test_record_user_feedback(self, monitoring_service, mock_db_session):
        """Test recording user feedback on AI response"""
        await monitoring_service.record_feedback(
            ai_request_id=123,
            feedback_type="quality",
            rating=4,
            comments="Good response but slightly slow"
        )
        
        mock_db_session.add.assert_called_once()
        feedback = mock_db_session.add.call_args[0][0]
        
        assert isinstance(feedback, FeedbackMetric)
        assert feedback.ai_request_id == 123
        assert feedback.rating == 4

    @pytest.mark.asyncio
    async def test_calculate_feedback_score(self, monitoring_service):
        """Test calculating average feedback score"""
        score = await monitoring_service.calculate_feedback_score(
            channel="email",
            start_date=datetime.now() - timedelta(days=7)
        )
        
        assert "average_rating" in score
        assert "total_feedback" in score
        assert "sentiment" in score

    @pytest.mark.asyncio
    async def test_identify_improvement_areas(self, monitoring_service):
        """Test identifying areas for AI improvement"""
        areas = await monitoring_service.identify_improvement_areas()
        
        assert isinstance(areas, list)
        for area in areas:
            assert "channel" in area
            assert "issue" in area
            assert "suggested_action" in area


class TestAlertRuleEngine:
    """Test custom alert rule engine"""

    @pytest.mark.asyncio
    async def test_create_alert_rule(self, monitoring_service, mock_db_session):
        """Test creating custom alert rule"""
        rule = await monitoring_service.create_alert_rule(
            name="High Voice AI Latency",
            metric_name="ai.voice.latency",
            operator="greater_than",
            threshold=2.0,
            severity="warning",
            notification_channels=["email", "slack"]
        )
        
        mock_db_session.add.assert_called_once()
        rule_obj = mock_db_session.add.call_args[0][0]
        
        assert isinstance(rule_obj, AlertRule)
        assert rule_obj.metric_name == "ai.voice.latency"
        assert rule_obj.threshold == 2.0

    @pytest.mark.asyncio
    async def test_evaluate_alert_rules(self, monitoring_service):
        """Test evaluating all alert rules"""
        rules = [
            AlertRule(
                id=1,
                name="High Cost",
                metric_name="ai.costs.hourly",
                operator="greater_than",
                threshold=10.0,
                severity="warning"
            )
        ]
        
        with patch.object(monitoring_service, 'get_metric_value') as mock_get_metric:
            mock_get_metric.return_value = 15.0
            
            triggered = await monitoring_service.evaluate_rules(rules)
            
            assert len(triggered) > 0
            assert triggered[0]["rule_id"] == 1

    @pytest.mark.asyncio
    async def test_alert_rule_with_complex_condition(self, monitoring_service):
        """Test alert rule with multiple conditions"""
        rule = AlertRule(
            name="Complex Rule",
            metric_name="ai.response_time",
            operator="greater_than",
            threshold=1.5,
            secondary_conditions={
                "ai.error_rate": {"operator": "greater_than", "value": 0.05}
            }
        )
        
        # Both conditions met
        with patch.object(monitoring_service, 'get_metric_value') as mock_get:
            mock_get.side_effect = [2.0, 0.08]  # response_time, error_rate
            
            is_triggered = await monitoring_service.evaluate_rule(rule)
            assert is_triggered is True


class TestMonitoringIntegration:
    """Test monitoring system integration"""

    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_flow(
        self,
        monitoring_service,
        alert_analyzer,
        predictive_monitor
    ):
        """Test complete monitoring flow: metric → alert → analysis → prediction"""
        
        # 1. Record AI metrics
        await monitoring_service.record_ai_request(
            channel="phone",
            request_type="conversation",
            tokens_used=500,
            response_time=2.5,  # High latency
            success=True
        )
        
        # 2. Detect anomaly and create alert
        anomalies = await predictive_monitor.detect_anomalies(
            metric_name="ai.response_time",
            hours=1
        )
        
        if len(anomalies) > 0:
            alert = Alert(
                alert_type="performance",
                severity="warning",
                metric_name="ai.response_time",
                current_value=2.5,
                threshold=1.0
            )
            
            # 3. Analyze alert with AI
            analysis = await alert_analyzer.analyze_alert(alert)
            
            assert "root_cause" in analysis
            assert len(analysis["recommendations"]) > 0
            
            # 4. Generate predictive warning
            warning = await predictive_monitor.generate_predictive_warning(
                metric_name="ai.response_time",
                predicted_value=3.0,
                threshold=2.0,
                confidence=0.9,
                hours_until=2
            )
            
            assert warning is not None

    @pytest.mark.asyncio
    async def test_dashboard_data_aggregation(self, monitoring_service):
        """Test aggregating data for monitoring dashboard"""
        dashboard = await monitoring_service.get_dashboard_data()
        
        # Verify all dashboard sections
        assert "system_health" in dashboard
        assert "ai_metrics" in dashboard
        assert "active_alerts" in dashboard
        assert "predictive_warnings" in dashboard
        assert "recent_feedback" in dashboard
        
        # System health check
        assert dashboard["system_health"]["status"] in ["healthy", "degraded", "unhealthy"]
        
        # AI metrics summary
        assert "total_requests" in dashboard["ai_metrics"]
        assert "avg_response_time" in dashboard["ai_metrics"]
        assert "success_rate" in dashboard["ai_metrics"]

    @pytest.mark.asyncio
    async def test_real_time_metrics_stream(self, monitoring_service):
        """Test real-time metrics streaming"""
        # Simulate real-time metric collection
        async def generate_metrics():
            for i in range(5):
                await monitoring_service.record_ai_request(
                    channel="sms",
                    request_type="reply",
                    tokens_used=100 + i * 10,
                    response_time=0.5 + i * 0.1,
                    success=True
                )
        
        await generate_metrics()
        
        # Get latest metrics
        latest = await monitoring_service.get_latest_metrics(limit=5)
        assert len(latest) == 5


class TestMonitoringPerformance:
    """Test monitoring system performance"""

    @pytest.mark.asyncio
    async def test_bulk_metric_insertion(self, monitoring_service, mock_db_session):
        """Test inserting multiple metrics efficiently"""
        metrics = [
            {
                "channel": "email",
                "request_type": "compose",
                "tokens_used": 150,
                "response_time": 0.8,
                "success": True
            }
            for _ in range(100)
        ]
        
        import time
        start = time.time()
        await monitoring_service.bulk_record_metrics(metrics)
        duration = time.time() - start
        
        # Should complete quickly
        assert duration < 1.0  # 1 second for 100 metrics

    @pytest.mark.asyncio
    async def test_metric_aggregation_performance(self, monitoring_service):
        """Test performance of metric aggregation queries"""
        import time
        start = time.time()
        
        await monitoring_service.get_aggregated_metrics(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            granularity="hour"
        )
        
        duration = time.time() - start
        
        # Should aggregate 30 days of data quickly
        assert duration < 2.0  # 2 seconds max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
