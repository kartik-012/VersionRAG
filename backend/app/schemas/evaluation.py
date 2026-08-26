from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvaluationScenarioRunRequest(BaseModel):
    project_id: str
    dataset_name: Optional[str] = "Standard-VersionRAG-Eval-v1"
    run_name: Optional[str] = "VersionRAG Live Reproduction Benchmark"

class RetrievedChunkSnippet(BaseModel):
    chunk_id: str
    version_tag: str
    similarity_score: float
    section_title: Optional[str] = None
    snippet: str
    is_contamination: bool = False

class EvaluationResultRead(BaseModel):
    id: str
    query_archetype: str
    question: str
    target_version: Optional[str] = None
    ground_truth_answer: str
    naive_rag_answer: Optional[str] = None
    naive_rag_correct: int
    versionrag_answer: str
    versionrag_correct: int
    versionrag_confidence: str
    retrieved_versions: List[str] = []
    evidence_valid: int
    execution_time_ms: int
    failure_cause: Optional[str] = None
    retrieved_chunks_naive: List[Dict[str, Any]] = []
    retrieved_chunks_versionrag: List[Dict[str, Any]] = []
    metrics_trace: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

class EvaluationRunRead(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    name: str
    dataset_name: str
    status: str
    naive_rag_accuracy: float
    version_aware_accuracy: float
    versionrag_accuracy: float
    naive_rag_faithfulness: float
    versionrag_faithfulness: float
    retrieval_precision: float
    retrieval_recall: float
    cross_version_contamination_rate: float = 0.0
    silent_change_detection_rate: float
    average_latency_ms: float
    total_scenarios: int
    passed_scenarios: int
    summary_report: Dict[str, Any] = {}
    metrics_definitions: Dict[str, Any] = {}
    created_at: datetime
    results: List[EvaluationResultRead] = []

    model_config = ConfigDict(from_attributes=True)
