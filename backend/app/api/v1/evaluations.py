from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Tuple
from app.core.database import get_db
from app.core.deps import get_current_user, get_project_and_membership
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.project import Project
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.schemas.evaluation import EvaluationScenarioRunRequest, EvaluationRunRead
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/evaluations", tags=["Evaluations & Benchmarks"])

@router.post("/run", response_model=EvaluationRunRead, status_code=status.HTTP_201_CREATED)
def run_project_benchmark(
    req: EvaluationScenarioRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes the standard comparative benchmark suite comparing Naive RAG vs VersionRAG.
    """
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    eval_run = evaluation_service.run_benchmark(
        db=db,
        workspace_id=project.workspace_id,
        project_id=project.id,
        user_id=current_user.id,
        run_name=req.run_name or "Live Benchmark Run"
    )
    return EvaluationRunRead.model_validate(eval_run)

@router.get("/project/{project_id}", response_model=List[EvaluationRunRead])
def list_project_evaluations(
    project_id: str,
    db: Session = Depends(get_db)
):
    """List all benchmark evaluation runs for a project."""
    runs = (
        db.query(EvaluationRun)
        .filter(EvaluationRun.project_id == project_id)
        .order_by(EvaluationRun.created_at.desc())
        .all()
    )
    return [EvaluationRunRead.model_validate(r) for r in runs]

@router.get("/{run_id}", response_model=EvaluationRunRead)
def get_evaluation_run(run_id: str, db: Session = Depends(get_db)):
    """Get single evaluation run details with scenario breakdown."""
    run = db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvaluationRunRead.model_validate(run)

@router.post("/custom-scenario", response_model=EvaluationRunRead)
def add_custom_scenario_and_evaluate(
    project_id: str,
    question: str,
    target_version: str,
    ground_truth: str,
    archetype: str = "version_specific_query",
    db: Session = Depends(get_db)
):
    """
    Dynamically add a custom user-defined scenario to the benchmark and compute live score.
    """
    from app.services.evaluation_service import BENCHMARK_SCENARIOS
    BENCHMARK_SCENARIOS.append({
        "query_archetype": archetype,
        "question": question,
        "target_version": target_version,
        "ground_truth_answer": ground_truth,
        "target_keywords": [target_version, question.split()[0]]
    })

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = project.workspace.members[0].user if project.workspace.members else None

    eval_run = evaluation_service.run_benchmark(
        db=db,
        workspace_id=project.workspace_id,
        project_id=project.id,
        user_id=user.id if user else "system",
        run_name=f"Custom Scenario Benchmark ({question[:30]}...)"
    )
    return EvaluationRunRead.model_validate(eval_run)

