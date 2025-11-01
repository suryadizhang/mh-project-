"""
Model Fine-Tuner - OpenAI Fine-Tuning Automation

This module automates the OpenAI fine-tuning process:
- Uploads training files to OpenAI
- Triggers fine-tuning jobs
- Monitors training progress
- Validates trained models
- Tracks costs and performance

Author: MyHibachi Development Team
Created: October 31, 2025
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from openai import OpenAI

logger = logging.getLogger(__name__)


class ModelFineTuner:
    """
    Automate OpenAI fine-tuning process.
    
    Example:
        ```python
        fine_tuner = ModelFineTuner()
        
        # Start fine-tuning
        job = await fine_tuner.start_fine_tune(
            training_file_path="data/training/mhc_support_v1.jsonl",
            model_suffix="mhc-support-v1"
        )
        
        # Monitor progress
        result = await fine_tuner.monitor_fine_tune(job['job_id'])
        
        if result['success']:
            print(f"New model: {result['model_id']}")
        ```
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        min_examples: int = 200,
        max_examples: int = 10000
    ):
        """
        Initialize fine-tuner.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            min_examples: Minimum training examples required
            max_examples: Maximum training examples to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.min_examples = min_examples
        self.max_examples = max_examples
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(
            f"ModelFineTuner initialized: "
            f"min={min_examples}, max={max_examples}"
        )
    
    async def start_fine_tune(
        self,
        training_file_path: str,
        model_suffix: str = "mhc-support",
        base_model: str = "gpt-4o-mini",
        n_epochs: Optional[int] = None,
        validation_split: float = 0.1
    ) -> Dict[str, Any]:
        """
        Start fine-tuning job.
        
        Args:
            training_file_path: Path to JSONL training file
            model_suffix: Suffix for model name (e.g., "mhc-support-v2")
            base_model: Base model to fine-tune
            n_epochs: Number of training epochs (auto if None)
            validation_split: % of data for validation
        
        Returns:
            {
                "job_id": str,
                "status": str,
                "model": str,
                "training_file": str,
                "created_at": int,
                "estimated_cost_usd": float,
                "estimated_duration_minutes": int
            }
        
        Raises:
            ValueError: If dataset too small or file doesn't exist
        """
        self.logger.info(f"Starting fine-tune job: {model_suffix}")
        
        # Validate file exists
        if not Path(training_file_path).exists():
            raise ValueError(f"Training file not found: {training_file_path}")
        
        # Validate dataset size
        with open(training_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            num_examples = len(lines)
        
        if num_examples < self.min_examples:
            raise ValueError(
                f"Dataset too small: {num_examples} examples "
                f"(need at least {self.min_examples})"
            )
        
        if num_examples > self.max_examples:
            self.logger.warning(
                f"Dataset has {num_examples} examples, "
                f"but max is {self.max_examples}. Consider sampling."
            )
        
        self.logger.info(f"Training dataset: {num_examples} examples")
        
        try:
            # Upload training file to OpenAI
            self.logger.info("📤 Uploading training file to OpenAI...")
            
            with open(training_file_path, 'rb') as f:
                training_file = self.client.files.create(
                    file=f,
                    purpose='fine-tune'
                )
            
            self.logger.info(f"✅ File uploaded: {training_file.id}")
            
            # Calculate optimal epochs if not specified
            if n_epochs is None:
                n_epochs = self._calculate_optimal_epochs(num_examples)
                self.logger.info(f"Auto-calculated epochs: {n_epochs}")
            
            # Start fine-tuning job
            self.logger.info(f"🚀 Starting fine-tune with model: {base_model}")
            
            fine_tune_job = self.client.fine_tuning.jobs.create(
                training_file=training_file.id,
                model=base_model,
                suffix=model_suffix,
                hyperparameters={
                    "n_epochs": n_epochs
                }
            )
            
            # Estimate cost and duration
            estimated_cost = self._estimate_cost(num_examples, n_epochs)
            estimated_duration = self._estimate_duration(num_examples, n_epochs)
            
            result = {
                "job_id": fine_tune_job.id,
                "status": fine_tune_job.status,
                "model": fine_tune_job.model,
                "training_file": training_file.id,
                "created_at": fine_tune_job.created_at,
                "estimated_cost_usd": estimated_cost,
                "estimated_duration_minutes": estimated_duration,
                "n_epochs": n_epochs,
                "num_examples": num_examples
            }
            
            self.logger.info(
                f"✅ Fine-tune job started: {fine_tune_job.id}",
                extra=result
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error starting fine-tune: {str(e)}", exc_info=True)
            raise
    
    async def monitor_fine_tune(
        self,
        job_id: str,
        poll_interval: int = 60
    ) -> Dict[str, Any]:
        """
        Monitor fine-tuning progress.
        
        Polls OpenAI API every poll_interval seconds until job completes.
        
        Args:
            job_id: Fine-tuning job ID
            poll_interval: Seconds between status checks
        
        Returns:
            {
                "success": bool,
                "model_id": str,
                "finished_at": int,
                "trained_tokens": int,
                "cost_usd": float,
                "error": Optional[str]
            }
        """
        self.logger.info(f"👀 Monitoring fine-tune job: {job_id}")
        
        start_time = time.time()
        last_status = None
        
        try:
            while True:
                # Fetch job status
                job = self.client.fine_tuning.jobs.retrieve(job_id)
                
                # Log status changes
                if job.status != last_status:
                    self.logger.info(f"Status: {job.status}")
                    last_status = job.status
                
                # Check for completion
                if job.status == "succeeded":
                    elapsed_minutes = (time.time() - start_time) / 60
                    
                    result = {
                        "success": True,
                        "model_id": job.fine_tuned_model,
                        "finished_at": job.finished_at,
                        "trained_tokens": job.trained_tokens,
                        "cost_usd": self._calculate_cost(job.trained_tokens),
                        "elapsed_minutes": round(elapsed_minutes, 1),
                        "result_files": job.result_files
                    }
                    
                    self.logger.info(
                        f"✅ Fine-tuning complete! Model: {job.fine_tuned_model}",
                        extra=result
                    )
                    
                    return result
                
                elif job.status == "failed":
                    error_msg = job.error if hasattr(job, 'error') else "Unknown error"
                    
                    self.logger.error(f"❌ Fine-tuning failed: {error_msg}")
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "failed_at": job.finished_at if hasattr(job, 'finished_at') else None
                    }
                
                elif job.status == "cancelled":
                    self.logger.warning("⚠️ Fine-tuning was cancelled")
                    
                    return {
                        "success": False,
                        "error": "Job was cancelled",
                        "cancelled_at": job.finished_at if hasattr(job, 'finished_at') else None
                    }
                
                # Job still running - wait before next check
                time.sleep(poll_interval)
                
        except Exception as e:
            self.logger.error(f"Error monitoring fine-tune: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_optimal_epochs(self, num_examples: int) -> int:
        """
        Calculate optimal number of epochs based on dataset size.
        
        Rules:
        - Small datasets (< 500): 4 epochs
        - Medium datasets (500-2000): 3 epochs
        - Large datasets (> 2000): 2 epochs
        """
        if num_examples < 500:
            return 4
        elif num_examples < 2000:
            return 3
        else:
            return 2
    
    def _estimate_cost(self, num_examples: int, n_epochs: int) -> float:
        """
        Estimate fine-tuning cost.
        
        Pricing (GPT-4o-mini):
        - Training: ~$8 per 1M tokens
        - Assume 500 tokens per example on average
        """
        total_tokens = num_examples * 500 * n_epochs
        cost = (total_tokens / 1_000_000) * 8.0
        return round(cost, 2)
    
    def _calculate_cost(self, trained_tokens: int) -> float:
        """Calculate actual cost from trained tokens"""
        cost = (trained_tokens / 1_000_000) * 8.0
        return round(cost, 2)
    
    def _estimate_duration(self, num_examples: int, n_epochs: int) -> int:
        """
        Estimate fine-tuning duration in minutes.
        
        Rough estimate:
        - ~1 minute per 100 examples per epoch
        """
        minutes = (num_examples / 100) * n_epochs
        return round(minutes)
    
    async def get_fine_tune_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get current status of fine-tuning job (single check).
        
        Args:
            job_id: Fine-tuning job ID
        
        Returns:
            Job status details
        """
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            
            return {
                "job_id": job.id,
                "status": job.status,
                "model": job.model,
                "created_at": job.created_at,
                "finished_at": job.finished_at if hasattr(job, 'finished_at') else None,
                "fine_tuned_model": job.fine_tuned_model if hasattr(job, 'fine_tuned_model') else None,
                "trained_tokens": job.trained_tokens if hasattr(job, 'trained_tokens') else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting job status: {str(e)}", exc_info=True)
            raise
    
    async def list_fine_tune_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent fine-tuning jobs.
        
        Args:
            limit: Maximum number of jobs to return
        
        Returns:
            List of job summaries
        """
        try:
            jobs = self.client.fine_tuning.jobs.list(limit=limit)
            
            return [
                {
                    "job_id": job.id,
                    "status": job.status,
                    "model": job.model,
                    "created_at": job.created_at,
                    "fine_tuned_model": job.fine_tuned_model if hasattr(job, 'fine_tuned_model') else None
                }
                for job in jobs.data
            ]
            
        except Exception as e:
            self.logger.error(f"Error listing jobs: {str(e)}", exc_info=True)
            raise
    
    async def cancel_fine_tune(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running fine-tuning job.
        
        Args:
            job_id: Fine-tuning job ID
        
        Returns:
            Cancellation confirmation
        """
        try:
            self.logger.info(f"Cancelling fine-tune job: {job_id}")
            
            job = self.client.fine_tuning.jobs.cancel(job_id)
            
            return {
                "job_id": job.id,
                "status": job.status,
                "cancelled": job.status == "cancelled"
            }
            
        except Exception as e:
            self.logger.error(f"Error cancelling job: {str(e)}", exc_info=True)
            raise


# Global singleton
_fine_tuner: Optional[ModelFineTuner] = None


def get_fine_tuner() -> ModelFineTuner:
    """
    Get global fine-tuner instance.
    
    Returns:
        ModelFineTuner singleton
    """
    global _fine_tuner
    
    if _fine_tuner is None:
        _fine_tuner = ModelFineTuner()
    
    return _fine_tuner
