"""
Tools Module for AI Orchestrator

This module exports all available tools and the base tool infrastructure.
Tools are automatically registered and made available to the orchestrator.

Available Tools:
- PricingTool: Calculate party quotes with travel fees
- TravelFeeTool: Calculate travel fees by zipcode
- ProteinTool: Calculate protein upgrade costs

Phase 3 Ready:
- VoiceAITool: Handle voice calls (if phone_call_rate >30%)
- RAGTool: Retrieve knowledge base info (if ai_error_rate >30%)
- ThreadingTool: Access conversation history (if follow_up_rate >50%)

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from .base_tool import BaseTool, ToolParameter, ToolRegistry, ToolResult
from .pricing_tool import PricingTool
from .protein_tool import ProteinTool
from .travel_fee_tool import TravelFeeTool

__all__ = [
    "BaseTool",
    "PricingTool",
    "ProteinTool",
    "ToolParameter",
    "ToolRegistry",
    "ToolResult",
    "TravelFeeTool",
]
