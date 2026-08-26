from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin

class EvaluationRun(Base, UUIDMixin, TimestampMixin):
    """Tracks a complete comparative benchmark execution."""
    __tablename__ = "evaluation_runs"

    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(255), nullable=False)
    dataset_name = Column(String(100), default="Standard-VersionRAG-Eval-v1", nullable=False)
    status = Column(String(50), default="completed", nullable=False)
    
    # Aggregated metrics for Naive RAG vs Version-Aware RAG vs VersionRAG (Full)
    naive_rag_accuracy = Column(Float, default=0.0, nullable=False)
    version_aware_accuracy = Column(Float, default=0.0, nullable=False)
    versionrag_accuracy = Column(Float, default=0.0, nullable=False)

    naive_rag_faithfulness = Column(Float, default=0.0, nullable=False)
    versionrag_faithfulness = Column(Float, default=0.0, nullable=False)

    retrieval_precision = Column(Float, default=0.0, nullable=False)
    retrieval_recall = Column(Float, default=0.0, nullable=False)
    cross_version_contamination_rate = Column(Float, default=0.0, nullable=False)
    
    silent_change_detection_rate = Column(Float, default=0.0, nullable=False)
    average_latency_ms = Column(Float, default=0.0, nullable=False)
    
    total_scenarios = Column(Integer, default=0, nullable=False)
    passed_scenarios = Column(Integer, default=0, nullable=False)
    
    summary_report = Column(JSON, default=dict, nullable=False)
    metrics_definitions = Column(JSON, default=dict, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="evaluation_runs")
    project = relationship("Project", back_populates="evaluation_runs")
    user = relationship("User", back_populates="evaluation_runs")
    results = relationship("EvaluationResult", back_populates="evaluation_run", cascade="all, delete-orphan")

class EvaluationResult(Base, UUIDMixin, TimestampMixin):
    """Individual scenario benchmark outcome with full diagnostic execution trace."""
    __tablename__ = "evaluation_results"

    evaluation_run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    query_archetype = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    target_version = Column(String(100), nullable=True)
    ground_truth_answer = Column(Text, nullable=False)
    
    # Model predictions
    naive_rag_answer = Column(Text, nullable=True)
    naive_rag_correct = Column(Integer, default=0, nullable=False)  # 0 or 1
    
    versionrag_answer = Column(Text, nullable=False)
    versionrag_correct = Column(Integer, default=1, nullable=False)
    versionrag_confidence = Column(String(50), default="high", nullable=False)
    
    retrieved_versions = Column(JSON, default=list, nullable=False)
    evidence_valid = Column(Integer, default=1, nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)

    # Diagnostic X-Ray Traces
    failure_cause = Column(Text, nullable=True)
    retrieved_chunks_naive = Column(JSON, default=list, nullable=False)
    retrieved_chunks_versionrag = Column(JSON, default=list, nullable=False)
    metrics_trace = Column(JSON, default=dict, nullable=False)

    # Relationships
    evaluation_run = relationship("EvaluationRun", back_populates="results")

