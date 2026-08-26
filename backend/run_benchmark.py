import sys
import os

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.project import Project
from app.services.evaluation_service import evaluation_service

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).first()
        proj = db.query(Project).first()

        if not user or not proj:
            print("[ERROR] Please seed database first using `python backend/seed_data.py`")
            sys.exit(1)

        print(f"[*] Running Comparative VersionRAG Benchmark against Project: '{proj.name}'...")
        eval_run = evaluation_service.run_benchmark(
            db=db,
            workspace_id=proj.workspace_id,
            project_id=proj.id,
            user_id=user.id,
            run_name="CLI Evaluation Benchmark"
        )

        print("\n=======================================================")
        print("          VERSIONRAG EVALUATION BENCHMARK RESULTS      ")
        print("=======================================================")
        print(f"Total Scenarios Evaluated  : {eval_run.total_scenarios}")
        print(f"VersionRAG Accuracy        : {int(eval_run.versionrag_accuracy * 100)}%")
        print(f"Naive RAG Accuracy (Baseline): {int(eval_run.naive_rag_accuracy * 100)}%")
        print(f"VersionRAG Faithfulness    : {int(eval_run.versionrag_faithfulness * 100)}%")
        print(f"Retrieval Precision@k      : {int(eval_run.retrieval_precision * 100)}%")
        print(f"Retrieval Recall@k         : {int(eval_run.retrieval_recall * 100)}%")
        print(f"Silent Change Detection %  : {int(eval_run.silent_change_detection_rate * 100)}%")
        print(f"Average Execution Latency  : {eval_run.average_latency_ms} ms")
        print("=======================================================\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
