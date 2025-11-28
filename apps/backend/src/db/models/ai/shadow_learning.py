"""
Shadow Learning Models - ai Schema

This module handles shadow learning (teacher-student AI training).

Business Requirements:
- Teacher-student response pairs (OpenAI vs Local model)
- RLHF (Reinforcement Learning from Human Feedback) scoring
- Training data export jobs
- Model performance comparison
- Production readiness evaluation

Schema: ai
Tables: ai_tutor_pairs, ai_rlhf_scores, ai_export_jobs

Industry Pattern: OpenAI/Anthropic fine-tuning pipelines
"""

from datetime import datetime
from enum import Enum

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
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

# MIGRATED: from models.base → ...base_class (3 levels up from ai/)
from ...base_class import Base


# ============================================================================
# ENUMS
# ============================================================================


class ModelType(str, Enum):
    """
    Model types for tutor pairs.

    Business Context:
    - TEACHER: OpenAI models (GPT-4, GPT-3.5) - Production quality
    - STUDENT: Local models (Llama-3-8B) - Cost savings target
    """

    TEACHER = "teacher"
    STUDENT = "student"


class ExportStatus(str, Enum):
    """
    Training data export job status.

    Business Context:
    - PENDING: Job queued, not started
    - IN_PROGRESS: Currently exporting data
    - COMPLETED: Export successful, file ready
    - FAILED: Export failed, check error_message
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# AI TUTOR PAIR MODEL
# ============================================================================


class AITutorPair(Base):
    """
    Teacher-Student Response Pairs for Shadow Learning.

    Schema: ai.ai_tutor_pairs

    Business Logic:
    1. Store parallel responses (OpenAI teacher vs Local student)
    2. Measure similarity (how close is student to teacher?)
    3. Track production usage (did we use student response?)
    4. Collect customer feedback (was student response good?)
    5. Build fine-tuning dataset (train student to match teacher)

    Shadow Learning Process:
    1. User sends prompt
    2. BOTH teacher (GPT-4) and student (Llama-3) generate responses
    3. Compare responses (cosine similarity of embeddings)
    4. If similarity >= threshold (0.85): Use student response (save $$$)
    5. If similarity < threshold: Use teacher response (quality)
    6. Store pair for training
    7. Human review (RLHF scoring)
    8. Export high-quality pairs for fine-tuning

    Key Metrics:
    - similarity_score: Embedding cosine similarity (0-1)
    - quality_score: Overall quality assessment (0-1)
    - used_in_production: Did we actually use student response?
    - customer_feedback: positive/negative/neutral

    Indexes:
    - Composite: (created_at) - Time-series analysis
    - Composite: (similarity_score) - Quality filtering
    - Composite: (agent_type, created_at) - Agent-specific analysis
    - Composite: (used_in_production, created_at) - Production usage trends

    Example Usage:
    ```python
    pair = AITutorPair(
        prompt="How do I book a hibachi chef?",
        context="Previous messages: ...",
        agent_type="booking_agent",
        teacher_model="gpt-4-turbo-preview",
        teacher_response="To book a hibachi chef, visit...",
        teacher_tokens=150,
        teacher_cost_usd=0.003,
        teacher_response_time_ms=1200,
        student_model="llama-3-8b-instruct",
        student_response="To book a hibachi chef, visit...",
        student_tokens=145,
        student_response_time_ms=800,
        similarity_score=0.92,  # High similarity
        quality_score=0.88,
        used_in_production=True,  # Used student (saved money!)
        customer_feedback="positive"
    )
    ```
    """

    __tablename__ = "ai_tutor_pairs"
    __table_args__ = (
        # Time-series analysis (most common query)
        Index("idx_tutor_created", "created_at"),
        # Quality filtering (find high-quality pairs for training)
        Index("idx_tutor_similarity", "similarity_score", "created_at"),
        Index("idx_tutor_quality", "quality_score", "created_at"),
        # Agent-specific analysis
        Index("idx_tutor_agent", "agent_type", "created_at"),
        # Production usage trends (ROI calculation)
        Index("idx_tutor_production", "used_in_production", "created_at"),
        # Customer feedback analysis
        Index("idx_tutor_feedback", "customer_feedback", "created_at"),
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Auto-incrementing ID (sequential)",
    )

    # ========================================================================
    # REQUEST CONTEXT
    # ========================================================================

    prompt = Column(Text, nullable=False, comment="User's original prompt (training input)")

    context = Column(
        Text,
        nullable=True,
        comment="""
        Conversation context/history (training context):
        - Previous messages
        - Customer preferences
        - Booking details
        - Session state
        """,
    )

    agent_type = Column(
        String(50),
        nullable=True,
        comment="""
        Which AI agent type handled this request:
        - booking_agent
        - menu_agent
        - support_agent
        - general_agent
        """,
    )

    # ========================================================================
    # TEACHER RESPONSE (OpenAI - Production Quality)
    # ========================================================================

    teacher_model = Column(
        String(50), nullable=False, comment="Teacher model name (gpt-4-turbo, gpt-3.5-turbo)"
    )

    teacher_response = Column(Text, nullable=False, comment="Teacher's response (gold standard)")

    teacher_tokens = Column(
        Integer, nullable=True, comment="Teacher tokens consumed (input + output)"
    )

    teacher_cost_usd = Column(
        Float, nullable=True, comment="Teacher cost in USD (GPT-4: ~$0.02/1K tokens)"
    )

    teacher_response_time_ms = Column(
        Integer, nullable=True, comment="Teacher response time in milliseconds"
    )

    # ========================================================================
    # STUDENT RESPONSE (Local Llama-3 - Cost Savings)
    # ========================================================================

    student_model = Column(
        String(50), nullable=False, comment="Student model name (llama-3-8b-instruct)"
    )

    student_response = Column(Text, nullable=False, comment="Student's response (training target)")

    student_tokens = Column(
        Integer, nullable=True, comment="Student tokens generated (output only, input is local)"
    )

    student_response_time_ms = Column(
        Integer, nullable=True, comment="Student response time in milliseconds (should be faster)"
    )

    # ========================================================================
    # SIMILARITY METRICS
    # ========================================================================

    similarity_score = Column(
        Float,
        nullable=True,
        comment="""
        Cosine similarity between teacher and student embeddings (0-1):
        - 1.0: Identical responses
        - 0.85+: Very similar (safe to use student)
        - 0.7-0.84: Similar (review needed)
        - <0.7: Different (use teacher)
        """,
    )

    quality_score = Column(
        Float,
        nullable=True,
        comment="""
        Overall quality assessment (0-1):
        Combines:
        - Similarity score
        - RLHF scores (if available)
        - Customer feedback
        - Resolution success
        """,
    )

    # ========================================================================
    # CUSTOMER IMPACT TRACKING
    # ========================================================================

    used_in_production = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="""
        Did we use student response in production?
        True = Used student (cost savings!)
        False = Used teacher (quality priority)
        """,
    )

    customer_feedback = Column(
        String(20),
        nullable=True,
        comment="""
        Customer feedback on response:
        - positive (thumbs up, 4-5 rating)
        - neutral (3 rating, no feedback)
        - negative (thumbs down, 1-2 rating)
        """,
    )

    # ========================================================================
    # METADATA
    # ========================================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Pair creation timestamp",
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp (feedback, RLHF scores)",
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    rlhf_scores = relationship(
        "AIRLHFScore", back_populates="tutor_pair", cascade="all, delete-orphan"
    )


# ============================================================================
# AI RLHF SCORE MODEL
# ============================================================================


class AIRLHFScore(Base):
    """
    Reinforcement Learning from Human Feedback (RLHF) Scores.

    Schema: ai.ai_rlhf_scores

    Business Logic:
    1. Human reviewers score student responses (1-5 scale)
    2. Multiple scoring dimensions (accuracy, helpfulness, tone, completeness)
    3. Overall assessment (would use in production?)
    4. Feedback notes for improvement
    5. Train student model to maximize human-approved responses

    RLHF Process:
    1. Admin reviews tutor pairs
    2. Scores student response on 4 dimensions (1-5 each)
    3. Overall score calculated (average of 4 dimensions)
    4. Production readiness flag (yes/no)
    5. Optional feedback notes
    6. High-scoring pairs exported for fine-tuning

    Scoring Dimensions:
    - Accuracy: Is response factually correct? (1-5)
    - Helpfulness: Does it help customer? (1-5)
    - Tone: Appropriate brand voice? (1-5)
    - Completeness: Addresses all aspects? (1-5)

    Indexes:
    - Composite: (tutor_pair_id) - Link to pair
    - Composite: (overall_score, created_at) - Quality trends
    - Composite: (would_use_in_production, created_at) - Production readiness

    Example Usage:
    ```python
    score = AIRLHFScore(
        tutor_pair_id=123,
        reviewer_id=456,
        accuracy_score=5,
        helpfulness_score=4,
        tone_score=5,
        completeness_score=4,
        overall_score=4.5,
        would_use_in_production=True,
        feedback_notes="Great response! Minor: Could mention pricing earlier."
    )
    ```
    """

    __tablename__ = "ai_rlhf_scores"
    __table_args__ = (
        # Tutor pair linkage
        Index("idx_rlhf_tutor", "tutor_pair_id"),
        # Quality trends
        Index("idx_rlhf_overall", "overall_score", "created_at"),
        # Production readiness
        Index("idx_rlhf_production", "would_use_in_production", "created_at"),
        # Reviewer analytics
        Index("idx_rlhf_reviewer", "reviewer_id", "created_at"),
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Auto-incrementing ID (sequential)",
    )

    # ========================================================================
    # REFERENCE TO TUTOR PAIR
    # ========================================================================

    tutor_pair_id = Column(
        Integer,
        ForeignKey("ai.ai_tutor_pairs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent tutor pair ID (CASCADE delete)",
    )

    # ========================================================================
    # HUMAN FEEDBACK
    # ========================================================================

    reviewer_id = Column(Integer, nullable=True, comment="Admin user ID who reviewed this pair")

    # ========================================================================
    # SCORING DIMENSIONS (1-5 scale)
    # ========================================================================

    accuracy_score = Column(
        Integer,
        nullable=False,
        comment="""
        How accurate is the student response? (1-5):
        5 = Fully accurate, no errors
        4 = Mostly accurate, minor issues
        3 = Somewhat accurate, some errors
        2 = Inaccurate, major errors
        1 = Completely wrong
        """,
    )

    helpfulness_score = Column(
        Integer,
        nullable=False,
        comment="""
        How helpful is the student response? (1-5):
        5 = Very helpful, solves problem
        4 = Helpful, good guidance
        3 = Somewhat helpful
        2 = Not very helpful
        1 = Not helpful at all
        """,
    )

    tone_score = Column(
        Integer,
        nullable=False,
        comment="""
        Appropriate tone for My Hibachi brand? (1-5):
        5 = Perfect brand voice
        4 = Good tone, minor adjustments
        3 = Acceptable tone
        2 = Off-brand tone
        1 = Wrong tone entirely
        """,
    )

    completeness_score = Column(
        Integer,
        nullable=False,
        comment="""
        Addresses all aspects of customer query? (1-5):
        5 = Fully complete answer
        4 = Mostly complete, minor gaps
        3 = Somewhat complete
        2 = Missing key information
        1 = Incomplete answer
        """,
    )

    # ========================================================================
    # OVERALL ASSESSMENT
    # ========================================================================

    overall_score = Column(Float, nullable=False, comment="Average of all scoring dimensions (1-5)")

    would_use_in_production = Column(
        Boolean,
        nullable=False,
        comment="""
        Would you use this student response with a real customer?
        True = Production-ready
        False = Needs improvement
        """,
    )

    # ========================================================================
    # COMMENTS
    # ========================================================================

    feedback_notes = Column(
        Text,
        nullable=True,
        comment="""
        Reviewer comments and suggestions:
        - What was good?
        - What needs improvement?
        - Specific examples
        """,
    )

    # ========================================================================
    # METADATA
    # ========================================================================

    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True, comment="Review timestamp"
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================

    tutor_pair = relationship("AITutorPair", back_populates="rlhf_scores")


# ============================================================================
# AI EXPORT JOB MODEL
# ============================================================================


class AIExportJob(Base):
    """
    Training Data Export Jobs.

    Schema: ai.ai_export_jobs

    Business Logic:
    1. Export high-quality tutor pairs for fine-tuning
    2. Filter by similarity score, RLHF score, date range
    3. Generate JSONL files (OpenAI fine-tuning format)
    4. Track export status and results
    5. Support multiple export types (fine-tuning, evaluation, backup)

    Export Process:
    1. Admin creates export job (criteria: min similarity, min RLHF, date range)
    2. Job status: PENDING
    3. Background worker processes job
    4. Job status: IN_PROGRESS
    5. Generate JSONL file with high-quality pairs
    6. Job status: COMPLETED (or FAILED)
    7. File ready for download/upload to OpenAI

    Export Types:
    - fine_tuning: For training student model
    - evaluation: For testing model performance
    - backup: Full backup of all pairs

    Indexes:
    - Composite: (status, created_at) - Active jobs
    - Composite: (export_type, status) - Job type analytics

    Example Usage:
    ```python
    job = AIExportJob(
        export_type="fine_tuning",
        status=ExportStatus.PENDING,
        min_similarity_score=0.85,
        min_rlhf_score=4.0,
        date_range_start=datetime(2025, 1, 1),
        date_range_end=datetime(2025, 11, 25),
        pairs_exported=0,
        created_by=admin_id
    )
    ```
    """

    __tablename__ = "ai_export_jobs"
    __table_args__ = (
        # Active jobs monitoring
        Index("idx_export_status", "status", "created_at"),
        # Job type analytics
        Index("idx_export_type", "export_type", "status"),
        # Creator tracking
        Index("idx_export_creator", "created_by", "created_at"),
        {"schema": "ai"},
    )

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Auto-incrementing ID (sequential)",
    )

    # ========================================================================
    # JOB DETAILS
    # ========================================================================

    export_type = Column(
        String(50), nullable=False, comment="Export type (fine_tuning/evaluation/backup)"
    )

    status = Column(
        SQLEnum(ExportStatus),
        nullable=False,
        default=ExportStatus.PENDING,
        index=True,
        comment="Job status (pending/in_progress/completed/failed)",
    )

    # ========================================================================
    # EXPORT CRITERIA
    # ========================================================================

    min_similarity_score = Column(
        Float, nullable=False, default=0.85, comment="Minimum similarity score threshold (0.0-1.0)"
    )

    min_rlhf_score = Column(
        Float, nullable=True, comment="Minimum RLHF score threshold (1.0-5.0) if available"
    )

    date_range_start = Column(
        DateTime, nullable=True, comment="Export pairs created after this date (NULL = all)"
    )

    date_range_end = Column(
        DateTime, nullable=True, comment="Export pairs created before this date (NULL = all)"
    )

    # ========================================================================
    # RESULTS
    # ========================================================================

    pairs_exported = Column(
        Integer, nullable=False, default=0, comment="Number of tutor pairs exported"
    )

    output_file_path = Column(String(500), nullable=True, comment="Path to generated JSONL file")

    output_file_size_mb = Column(Float, nullable=True, comment="File size in megabytes")

    # ========================================================================
    # ERROR HANDLING
    # ========================================================================

    error_message = Column(Text, nullable=True, comment="Error message if job failed")

    # ========================================================================
    # METADATA
    # ========================================================================

    started_at = Column(
        DateTime, nullable=True, comment="Job start timestamp (when worker began processing)"
    )

    completed_at = Column(
        DateTime, nullable=True, comment="Job completion timestamp (success or failure)"
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Job creation timestamp",
    )

    created_by = Column(Integer, nullable=True, comment="Admin user ID who created this job")
