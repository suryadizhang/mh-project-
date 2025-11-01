"""
Machine Learning & Self-Learning Module

This module contains all AI training, fine-tuning, and continuous learning components:
- PII scrubbing and data safety
- Training dataset builders
- Fine-tuning automation
- Model evaluation and A/B testing
- Feedback collection and processing
- Performance analytics

Author: MyHibachi Development Team
Created: October 31, 2025
Version: 2.0.0 (Self-Learning Edition)
"""

from .pii_scrubber import PIIScrubber, get_pii_scrubber
from .training_dataset_builder import TrainingDatasetBuilder, get_dataset_builder
from .model_fine_tuner import ModelFineTuner, get_fine_tuner
from .model_deployment import ModelDeployment, get_deployment_manager
from .feedback_processor import FeedbackProcessor, get_feedback_processor

__all__ = [
    # PII Safety
    "PIIScrubber",
    "get_pii_scrubber",
    
    # Training Pipeline
    "TrainingDatasetBuilder",
    "get_dataset_builder",
    
    # Fine-Tuning
    "ModelFineTuner",
    "get_fine_tuner",
    
    # Deployment
    "ModelDeployment",
    "get_deployment_manager",
    
    # Feedback
    "FeedbackProcessor",
    "get_feedback_processor",
]
