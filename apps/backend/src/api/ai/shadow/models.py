"""
Shadow Learning Database Models
Stores teacher-student pairs, RLHF scores, and training data exports
"""

from datetime import datetime
import enum

from models.base import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship


class ModelType(str, enum.Enum):
    """Model types for tutor pairs"""

    TEACHER = "teacher"  # OpenAI (GPT-4, GPT-3.5)
    STUDENT = "student"  # Local model (Llama-3)


class ExportStatus(str, enum.Enum):
    """Training data export job status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AITutorPair(Base):
    """
    Teacher-Student Response Pairs for Shadow Learning

    Stores parallel responses from OpenAI (teacher) and local model (student)
    for the same prompt. Used to train the local model to mimic teacher.
    """

    __tablename__ = "ai_tutor_pairs"

    id = Column(Integer, primary_key=True, index=True)

    # Request context
    prompt = Column(Text, nullable=False, comment="User's original prompt")
    context = Column(Text, nullable=True, comment="Conversation context/history")
    agent_type = Column(String(50), nullable=True, comment="Which AI agent type")

    # Teacher response (OpenAI)
    teacher_model = Column(String(50), nullable=False, comment="Teacher model name")
    teacher_response = Column(Text, nullable=False, comment="Teacher's response")
    teacher_tokens = Column(Integer, nullable=True)
    teacher_cost_usd = Column(Float, nullable=True)
    teacher_response_time_ms = Column(Integer, nullable=True)

    # Student response (Local Llama-3)
    student_model = Column(String(50), nullable=False, comment="Student model name")
    student_response = Column(Text, nullable=False, comment="Student's response")
    student_tokens = Column(Integer, nullable=True)
    student_response_time_ms = Column(Integer, nullable=True)

    # Similarity metrics
    similarity_score = Column(
        Float,
        nullable=True,
        comment="Cosine similarity between embeddings (0-1)",
    )
    quality_score = Column(Float, nullable=True, comment="Overall quality assessment (0-1)")

    # Customer impact tracking
    used_in_production = Column(
        Boolean,
        default=False,
        comment="Did we use student response in production?",
    )
    customer_feedback = Column(
        String(20),
        nullable=True,
        comment="Customer feedback: positive/negative/neutral",
    )

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rlhf_scores = relationship("AIRLHFScore", back_populates="tutor_pair")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_tutor_created", "created_at"),
        Index("idx_tutor_similarity", "similarity_score"),
        Index("idx_tutor_agent", "agent_type", "created_at"),
        Index("idx_tutor_production", "used_in_production", "created_at"),
    )


class AIRLHFScore(Base):
    """
    Reinforcement Learning from Human Feedback (RLHF) Scores

    Human reviewers score student responses to improve model training.
    Used for fine-tuning and determining when student is ready for production.
    """

    __tablename__ = "ai_rlhf_scores"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to tutor pair
    tutor_pair_id = Column(
        Integer,
        ForeignKey("ai_tutor_pairs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human feedback
    reviewer_id = Column(Integer, nullable=True, comment="Admin user who reviewed")

    # Scoring dimensions (1-5 scale)
    accuracy_score = Column(Integer, nullable=False, comment="How accurate is the response? (1-5)")
    helpfulness_score = Column(
        Integer, nullable=False, comment="How helpful is the response? (1-5)"
    )
    tone_score = Column(Integer, nullable=False, comment="Appropriate tone for brand? (1-5)")
    completeness_score = Column(
        Integer,
        nullable=False,
        comment="Addresses all aspects of query? (1-5)",
    )

    # Overall assessment
    overall_score = Column(Float, nullable=False, comment="Average of all scores (1-5)")
    would_use_in_production = Column(
        Boolean,
        nullable=False,
        comment="Would you use this response with customer?",
    )

    # Comments
    feedback_notes = Column(Text, nullable=True, comment="Reviewer comments")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tutor_pair = relationship("AITutorPair", back_populates="rlhf_scores")

    # Indexes
    __table_args__ = (
        Index("idx_rlhf_tutor", "tutor_pair_id"),
        Index("idx_rlhf_overall", "overall_score", "created_at"),
        Index("idx_rlhf_production", "would_use_in_production", "created_at"),
    )


class AIExportJob(Base):
    """
    Training Data Export Jobs

    Tracks batch exports of high-quality tutor pairs for fine-tuning.
    Runs nightly to generate JSONL files for model training.
    """

    __tablename__ = "ai_export_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Job details
    export_type = Column(String(50), nullable=False, comment="fine_tuning/evaluation/backup")
    status = Column(
        SQLEnum(ExportStatus),
        nullable=False,
        default=ExportStatus.PENDING,
        index=True,
    )

    # Export criteria
    min_similarity_score = Column(
        Float,
        nullable=False,
        default=0.85,
        comment="Minimum similarity threshold",
    )
    min_rlhf_score = Column(Float, nullable=True, comment="Minimum RLHF score if available")
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)

    # Results
    pairs_exported = Column(Integer, default=0, comment="Number of pairs exported")
    output_file_path = Column(String(500), nullable=True, comment="Path to JSONL file")
    output_file_size_mb = Column(Float, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Metadata
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(Integer, nullable=True, comment="Admin user who initiated")

    # Indexes
    __table_args__ = (
        Index("idx_export_status", "status", "created_at"),
        Index("idx_export_type", "export_type", "status"),
    )
