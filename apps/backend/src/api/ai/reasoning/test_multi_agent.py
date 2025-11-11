"""
Tests for Multi-Agent System (Layer 4)

Tests the coordinated behavior of Analyzer, Planner, Executor, and Critic agents.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import json

from api.ai.reasoning.multi_agent import (
    MultiAgentSystem,
    AnalyzerAgent,
    PlannerAgent,
    ExecutorAgent,
    CriticAgent,
    MultiAgentConfig,
    AgentRole,
    Analysis,
    ExecutionPlan,
    PlanStep,
    Critique,
    MultiAgentResult,
)


@pytest.fixture
def mock_model_provider():
    """Mock model provider for testing"""
    provider = Mock()
    provider.complete = AsyncMock()
    return provider


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry with sample tools"""
    registry = Mock()
    
    # Mock tool
    mock_tool = Mock()
    mock_tool.name = "check_availability"
    mock_tool.description = "Check chef availability for a date"
    mock_tool.function = Mock(return_value={"available": True, "chefs": 3})
    
    registry.list_tools = Mock(return_value=["check_availability", "get_pricing"])
    registry.get_tool = Mock(return_value=mock_tool)
    
    return registry


@pytest.fixture
def multi_agent_system(mock_model_provider, mock_tool_registry):
    """Multi-agent system instance for testing"""
    config = MultiAgentConfig(
        max_iterations=2,
        max_critique_cycles=2,
        critique_quality_threshold=0.85,
        timeout_seconds=10.0,
    )
    return MultiAgentSystem(mock_model_provider, mock_tool_registry, config)


class TestAnalyzerAgent:
    """Tests for AnalyzerAgent"""

    @pytest.mark.asyncio
    async def test_analyzer_parses_valid_analysis(self, mock_model_provider):
        """Test that analyzer correctly parses valid JSON response"""
        analyzer = AnalyzerAgent(mock_model_provider)
        
        # Mock response
        analysis_json = {
            "problem_statement": "Customer needs hibachi for 20 people on a specific date",
            "requirements": ["Check availability", "Get pricing", "Confirm chef count"],
            "constraints": ["Specific date requirement", "Capacity for 20 guests"],
            "complexity_factors": ["Multiple chefs needed", "Date-specific availability"],
            "success_criteria": ["Availability confirmed", "Accurate pricing provided"],
        }
        mock_model_provider.complete.return_value = json.dumps(analysis_json)
        
        # Execute
        result = await analyzer.analyze(
            "Can you handle 20 people for hibachi on December 15th?",
            {"channel": "web", "customer_id": "C123"}
        )
        
        # Verify
        assert isinstance(result, Analysis)
        assert result.problem_statement == analysis_json["problem_statement"]
        assert len(result.requirements) == 3
        assert len(result.constraints) == 2
        assert len(result.complexity_factors) == 2
        assert len(result.success_criteria) == 2

    @pytest.mark.asyncio
    async def test_analyzer_handles_invalid_json(self, mock_model_provider):
        """Test that analyzer handles invalid JSON gracefully"""
        analyzer = AnalyzerAgent(mock_model_provider)
        
        # Mock invalid response
        mock_model_provider.complete.return_value = "Not valid JSON at all"
        
        # Execute
        result = await analyzer.analyze(
            "Test query",
            {"channel": "web"}
        )
        
        # Should return minimal analysis instead of crashing
        assert isinstance(result, Analysis)
        assert result.problem_statement == "Test query"
        assert len(result.requirements) > 0  # Has fallback requirements


class TestPlannerAgent:
    """Tests for PlannerAgent"""

    @pytest.mark.asyncio
    async def test_planner_creates_valid_plan(self, mock_model_provider, mock_tool_registry):
        """Test that planner creates a valid execution plan"""
        planner = PlannerAgent(mock_model_provider, mock_tool_registry)
        
        # Mock response
        plan_json = {
            "goal": "Confirm availability and provide pricing for 20 people",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Check chef availability for December 15th",
                    "tool_name": "check_availability",
                    "tool_parameters": {"date": "2025-12-15", "guest_count": 20},
                    "expected_outcome": "Availability status and chef count",
                },
                {
                    "step_number": 2,
                    "description": "Calculate pricing for 20 guests",
                    "tool_name": "get_pricing",
                    "tool_parameters": {"guest_count": 20},
                    "expected_outcome": "Total price estimate",
                },
            ],
            "estimated_duration_ms": 3000,
            "fallback_strategy": "If tools fail, provide manual assistance phone number",
        }
        mock_model_provider.complete.return_value = json.dumps(plan_json)
        
        # Create analysis
        analysis = Analysis(
            problem_statement="Check availability for hibachi event",
            requirements=["Check availability", "Get pricing"],
            constraints=["Specific date"],
            complexity_factors=["Multiple steps"],
            success_criteria=["Availability confirmed"],
        )
        
        # Execute
        result = await planner.create_plan(analysis, {"date": "2025-12-15"})
        
        # Verify
        assert isinstance(result, ExecutionPlan)
        assert result.goal == plan_json["goal"]
        assert len(result.steps) == 2
        assert result.steps[0].tool_name == "check_availability"
        assert result.steps[0].tool_parameters == {"date": "2025-12-15", "guest_count": 20}
        assert result.estimated_duration_ms == 3000

    @pytest.mark.asyncio
    async def test_planner_handles_invalid_json(self, mock_model_provider, mock_tool_registry):
        """Test that planner handles invalid JSON gracefully"""
        planner = PlannerAgent(mock_model_provider, mock_tool_registry)
        
        # Mock invalid response
        mock_model_provider.complete.return_value = "Invalid JSON"
        
        analysis = Analysis(
            problem_statement="Test problem",
            requirements=[],
            constraints=[],
            complexity_factors=[],
            success_criteria=[],
        )
        
        # Execute
        result = await planner.create_plan(analysis, {})
        
        # Should return minimal plan
        assert isinstance(result, ExecutionPlan)
        assert len(result.steps) > 0  # Has fallback step


class TestExecutorAgent:
    """Tests for ExecutorAgent"""

    @pytest.mark.asyncio
    async def test_executor_executes_plan_successfully(self, mock_model_provider, mock_tool_registry):
        """Test successful plan execution"""
        executor = ExecutorAgent(mock_model_provider, mock_tool_registry)
        
        # Create plan
        plan = ExecutionPlan(
            goal="Test goal",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Check availability",
                    tool_name="check_availability",
                    tool_parameters={"date": "2025-12-15"},
                ),
            ],
            estimated_duration_ms=2000,
        )
        
        # Execute
        result = await executor.execute_plan(plan, {})
        
        # Verify
        assert result.steps[0].completed is True
        assert result.steps[0].result == {"available": True, "chefs": 3}

    @pytest.mark.asyncio
    async def test_executor_handles_tool_not_found(self, mock_model_provider, mock_tool_registry):
        """Test executor handles missing tools gracefully"""
        executor = ExecutorAgent(mock_model_provider, mock_tool_registry)
        
        # Mock tool not found
        mock_tool_registry.get_tool.return_value = None
        
        # Create plan
        plan = ExecutionPlan(
            goal="Test goal",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Use non-existent tool",
                    tool_name="non_existent_tool",
                ),
            ],
            estimated_duration_ms=2000,
        )
        
        # Execute
        result = await executor.execute_plan(plan, {})
        
        # Verify
        assert result.steps[0].completed is False
        assert "not found" in result.steps[0].result["error"].lower()

    @pytest.mark.asyncio
    async def test_executor_handles_tool_exception(self, mock_model_provider, mock_tool_registry):
        """Test executor handles tool execution errors"""
        executor = ExecutorAgent(mock_model_provider, mock_tool_registry)
        
        # Mock tool that raises exception
        mock_tool = Mock()
        mock_tool.function = Mock(side_effect=ValueError("Tool error"))
        mock_tool_registry.get_tool.return_value = mock_tool
        
        # Create plan
        plan = ExecutionPlan(
            goal="Test goal",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Tool that fails",
                    tool_name="failing_tool",
                ),
            ],
            estimated_duration_ms=2000,
        )
        
        # Execute
        result = await executor.execute_plan(plan, {})
        
        # Verify
        assert result.steps[0].completed is False
        assert "error" in result.steps[0].result


class TestCriticAgent:
    """Tests for CriticAgent"""

    @pytest.mark.asyncio
    async def test_critic_accepts_good_solution(self, mock_model_provider):
        """Test critic accepts high-quality solution"""
        critic = CriticAgent(mock_model_provider)
        
        # Mock response
        critique_json = {
            "is_complete": True,
            "quality_score": 0.95,
            "strengths": ["All requirements met", "Clear results"],
            "weaknesses": [],
            "missing_requirements": [],
            "recommendations": [],
            "final_verdict": "ACCEPT",
        }
        mock_model_provider.complete.return_value = json.dumps(critique_json)
        
        # Create test data
        analysis = Analysis(
            problem_statement="Test problem",
            requirements=["Req 1", "Req 2"],
            constraints=[],
            complexity_factors=[],
            success_criteria=["All requirements met"],
        )
        
        plan = ExecutionPlan(
            goal="Test goal",
            steps=[
                PlanStep(
                    step_number=1,
                    description="Step 1",
                    completed=True,
                    result={"status": "success"},
                ),
            ],
            estimated_duration_ms=2000,
        )
        
        # Execute
        result = await critic.critique(analysis, plan, {})
        
        # Verify
        assert isinstance(result, Critique)
        assert result.is_complete is True
        assert result.quality_score == 0.95
        assert result.final_verdict == "ACCEPT"

    @pytest.mark.asyncio
    async def test_critic_requests_revision(self, mock_model_provider):
        """Test critic requests revision for incomplete solution"""
        critic = CriticAgent(mock_model_provider)
        
        # Mock response
        critique_json = {
            "is_complete": False,
            "quality_score": 0.65,
            "strengths": ["Partial completion"],
            "weaknesses": ["Missing key requirement"],
            "missing_requirements": ["Pricing information"],
            "recommendations": ["Add pricing step"],
            "final_verdict": "REVISE",
        }
        mock_model_provider.complete.return_value = json.dumps(critique_json)
        
        analysis = Analysis(
            problem_statement="Test",
            requirements=["Availability", "Pricing"],
            constraints=[],
            complexity_factors=[],
            success_criteria=["Complete info"],
        )
        
        plan = ExecutionPlan(
            goal="Test",
            steps=[
                PlanStep(step_number=1, description="Only availability", completed=True),
            ],
            estimated_duration_ms=2000,
        )
        
        # Execute
        result = await critic.critique(analysis, plan, {})
        
        # Verify
        assert result.is_complete is False
        assert result.quality_score < 0.85
        assert result.final_verdict == "REVISE"
        assert len(result.missing_requirements) > 0


class TestMultiAgentSystem:
    """Tests for complete multi-agent system"""

    @pytest.mark.asyncio
    async def test_full_cycle_success(self, multi_agent_system, mock_model_provider):
        """Test complete analyze-plan-execute-critique cycle"""
        
        # Mock all LLM responses
        responses = [
            # Analysis
            json.dumps({
                "problem_statement": "Customer needs hibachi for 20 people",
                "requirements": ["Check availability"],
                "constraints": ["Date-specific"],
                "complexity_factors": ["Multiple factors"],
                "success_criteria": ["Availability confirmed"],
            }),
            # Plan
            json.dumps({
                "goal": "Confirm availability",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Check availability",
                        "tool_name": "check_availability",
                        "tool_parameters": {"date": "2025-12-15"},
                        "expected_outcome": "Availability status",
                    }
                ],
                "estimated_duration_ms": 2000,
            }),
            # Critique
            json.dumps({
                "is_complete": True,
                "quality_score": 0.90,
                "strengths": ["All requirements met"],
                "weaknesses": [],
                "missing_requirements": [],
                "recommendations": [],
                "final_verdict": "ACCEPT",
            }),
            # Final response
            "We have availability for 20 people on December 15th with 3 experienced chefs!",
        ]
        
        mock_model_provider.complete.side_effect = responses
        
        # Execute
        result = await multi_agent_system.process(
            "Can you handle 20 people on December 15th?",
            {"channel": "web"}
        )
        
        # Verify
        assert isinstance(result, MultiAgentResult)
        assert result.success is True
        assert result.critique_cycles == 1
        assert result.critique.final_verdict == "ACCEPT"
        assert len(result.messages) > 0
        assert result.cost_usd > 0
        assert result.duration_ms >= 0  # Can be 0 in fast unit tests

    @pytest.mark.asyncio
    async def test_revision_cycle(self, multi_agent_system, mock_model_provider):
        """Test that system revises based on critique"""
        
        # Mock responses: first cycle needs revision, second cycle accepted
        responses = [
            # Cycle 1: Analysis
            json.dumps({
                "problem_statement": "Test",
                "requirements": ["Req 1", "Req 2"],
                "constraints": [],
                "complexity_factors": [],
                "success_criteria": ["All requirements met"],
            }),
            # Cycle 1: Plan (incomplete)
            json.dumps({
                "goal": "Partial solution",
                "steps": [{"step_number": 1, "description": "Step 1"}],
                "estimated_duration_ms": 2000,
            }),
            # Cycle 1: Critique (REVISE)
            json.dumps({
                "is_complete": False,
                "quality_score": 0.60,
                "strengths": [],
                "weaknesses": ["Missing requirement 2"],
                "missing_requirements": ["Req 2"],
                "recommendations": ["Add step for Req 2"],
                "final_verdict": "REVISE",
            }),
            # Cycle 2: Plan (complete)
            json.dumps({
                "goal": "Complete solution",
                "steps": [
                    {"step_number": 1, "description": "Step 1"},
                    {"step_number": 2, "description": "Step 2"},
                ],
                "estimated_duration_ms": 3000,
            }),
            # Cycle 2: Critique (ACCEPT)
            json.dumps({
                "is_complete": True,
                "quality_score": 0.90,
                "strengths": ["All requirements met"],
                "weaknesses": [],
                "missing_requirements": [],
                "recommendations": [],
                "final_verdict": "ACCEPT",
            }),
            # Final response
            "Complete solution provided.",
        ]
        
        mock_model_provider.complete.side_effect = responses
        
        # Execute
        result = await multi_agent_system.process("Test query", {})
        
        # Verify
        assert result.success is True
        assert result.critique_cycles == 2  # Took 2 cycles to get accepted
        assert result.critique.final_verdict == "ACCEPT"

    @pytest.mark.asyncio
    async def test_max_cycles_reached(self, multi_agent_system, mock_model_provider):
        """Test that system stops after max critique cycles"""
        
        # Mock responses that always request revision
        responses = []
        
        # First cycle
        responses.append(json.dumps({  # Analysis
            "problem_statement": "Test",
            "requirements": [],
            "constraints": [],
            "complexity_factors": [],
            "success_criteria": [],
        }))
        responses.append(json.dumps({  # Plan 1
            "goal": "Test",
            "steps": [{"step_number": 1, "description": "Test"}],
            "estimated_duration_ms": 2000,
        }))
        responses.append(json.dumps({  # Critique 1 - REVISE
            "is_complete": False,
            "quality_score": 0.50,
            "strengths": [],
            "weaknesses": ["Needs revision"],
            "missing_requirements": [],
            "recommendations": [],
            "final_verdict": "REVISE",
        }))
        
        # Second cycle
        responses.append(json.dumps({  # Plan 2
            "goal": "Test",
            "steps": [{"step_number": 1, "description": "Test"}],
            "estimated_duration_ms": 2000,
        }))
        responses.append(json.dumps({  # Critique 2 - Still REVISE
            "is_complete": False,
            "quality_score": 0.55,
            "strengths": [],
            "weaknesses": ["Still needs work"],
            "missing_requirements": [],
            "recommendations": [],
            "final_verdict": "REVISE",
        }))
        
        # Final response
        responses.append("Best effort response despite revisions")
        
        mock_model_provider.complete.side_effect = responses
        
        # Execute
        result = await multi_agent_system.process("Test query", {})
        
        # Verify - should stop at max_critique_cycles (2)
        assert result.critique_cycles == multi_agent_system.config.max_critique_cycles
        assert result.critique.final_verdict == "REVISE"  # Last verdict

    @pytest.mark.asyncio
    async def test_system_handles_exception(self, multi_agent_system, mock_model_provider):
        """Test that system handles exceptions gracefully"""
        
        # Mock exception in analysis
        mock_model_provider.complete.side_effect = Exception("LLM API error")
        
        # Execute
        result = await multi_agent_system.process("Test query", {})
        
        # Verify - should return error result, not crash
        assert isinstance(result, MultiAgentResult)
        assert result.success is False
        assert result.error is not None
        assert "error" in result.response.lower()
        assert result.iterations == 0

    @pytest.mark.asyncio
    async def test_message_logging(self, multi_agent_system, mock_model_provider):
        """Test that agent messages are logged"""
        
        # Mock simple successful flow
        mock_model_provider.complete.side_effect = [
            json.dumps({
                "problem_statement": "Test",
                "requirements": [],
                "constraints": [],
                "complexity_factors": [],
                "success_criteria": [],
            }),
            json.dumps({
                "goal": "Test",
                "steps": [{"step_number": 1, "description": "Test"}],
                "estimated_duration_ms": 2000,
            }),
            json.dumps({
                "is_complete": True,
                "quality_score": 0.90,
                "strengths": [],
                "weaknesses": [],
                "missing_requirements": [],
                "recommendations": [],
                "final_verdict": "ACCEPT",
            }),
            "Final response",
        ]
        
        # Execute
        result = await multi_agent_system.process("Test query", {})
        
        # Verify messages logged
        assert len(result.messages) > 0
        
        # Check for messages from different agents
        agent_roles = [msg.from_agent for msg in result.messages]
        assert AgentRole.ANALYZER in agent_roles
        assert AgentRole.PLANNER in agent_roles
        assert AgentRole.EXECUTOR in agent_roles
        assert AgentRole.CRITIC in agent_roles


class TestMultiAgentConfig:
    """Tests for MultiAgentConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = MultiAgentConfig()
        
        assert config.max_iterations == 3
        assert config.max_critique_cycles == 2
        assert config.critique_quality_threshold == 0.85
        assert config.timeout_seconds == 15.0
        assert config.enable_parallel_execution is False
        assert config.log_agent_communication is True

    def test_custom_config(self):
        """Test custom configuration"""
        config = MultiAgentConfig(
            max_iterations=5,
            max_critique_cycles=3,
            critique_quality_threshold=0.90,
            timeout_seconds=20.0,
        )
        
        assert config.max_iterations == 5
        assert config.max_critique_cycles == 3
        assert config.critique_quality_threshold == 0.90
        assert config.timeout_seconds == 20.0
