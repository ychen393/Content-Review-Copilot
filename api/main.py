from __future__ import annotations

import logging
import os

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import DecisionRequest, ReviewCreateRequest, ReviewSessionViewModel
from .service import ReviewWorkflowService
from .workspace import WorkspaceRepository, ProjectCreate, TaskCreate, ItemCreate, VersionCreate
from .drafting import DraftGenerationService, GenerateRequest
from .idempotency import GenerationReservation
from backend.documents import DefaultDocumentParser
from .database import postgres_enabled

logger = logging.getLogger(__name__)
app = FastAPI(title="Content Review API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
service = ReviewWorkflowService()


def public(payload: dict) -> ReviewSessionViewModel:
    return ReviewSessionViewModel.model_validate(payload)


def load(review_id: str) -> dict:
    payload = service.store.get(review_id)
    if not payload: raise HTTPException(404, "Review session not found")
    return payload


def execute(operation):
    try:
        result = operation()
        # Linked content items retain review state and outputs; legacy sessions are unaffected.
        linked = globals().get("workspace")
        if linked is not None and result.get("id"):
            linked.sync_review(result["id"], result)
        return public(result)
    except ValueError as error: raise HTTPException(409, str(error)) from error
    except Exception as error:
        logger.exception("Review operation failed")
        raise HTTPException(500, "处理未完成。当前稿件和审核进度已保留。") from error


@app.get("/api/health")
def health(): return {"status": "ok"}


@app.post("/api/documents/parse")
async def parse_document(file: UploadFile = File(...)):
    parsed = DefaultDocumentParser().parse(file.filename or "document.txt", await file.read())
    if parsed.status != "parsed": raise HTTPException(422, "文档读取失败，请检查文件格式。")
    return {"filename": parsed.filename, "text": parsed.text}


@app.post("/api/reviews", response_model=ReviewSessionViewModel)
def create_review(request: ReviewCreateRequest): return execute(lambda: service.create(request))


@app.post("/api/reviews/{review_id}/first-review", response_model=ReviewSessionViewModel)
def first_review(review_id: str): return execute(lambda: service.first_review(load(review_id)))


@app.post("/api/reviews/{review_id}/decisions", response_model=ReviewSessionViewModel)
def save_decisions(review_id: str, request: DecisionRequest): return execute(lambda: service.decisions(load(review_id), request.stage, request.decisions))


@app.post("/api/reviews/{review_id}/rewrite", response_model=ReviewSessionViewModel)
def rewrite(review_id: str): return execute(lambda: service.rewrite(load(review_id)))


@app.post("/api/reviews/{review_id}/second-review", response_model=ReviewSessionViewModel)
def second_review(review_id: str): return execute(lambda: service.second_review(load(review_id)))


@app.post("/api/reviews/{review_id}/finalize", response_model=ReviewSessionViewModel)
def finalize(review_id: str, keep_current: bool = False): return execute(lambda: service.finalize(load(review_id), keep_current))


@app.get("/api/reviews/{review_id}", response_model=ReviewSessionViewModel)
def get_review(review_id: str): return public(load(review_id))


@app.get("/api/reviews", response_model=list[ReviewSessionViewModel])
def list_reviews(): return [public(row) for row in service.store.list()]


@app.post("/api/reviews/{review_id}/export/docx")
def export_docx(review_id: str):
    try: data = service.export_docx(load(review_id))
    except ValueError as error: raise HTTPException(409, str(error)) from error
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=final_content.docx"})


@app.get("/api/developer/reviews/{review_id}")
def developer_review(review_id: str): return load(review_id).get("technical", {})

# M2.1 content workspace: additive routes, preserving existing review API.
workspace = WorkspaceRepository()

@app.post("/api/projects")
def create_project(request: ProjectCreate):
    return workspace.create_project(request)

@app.get("/api/projects")
def list_projects():
    return workspace.list_projects()

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    result = workspace.get_project(project_id)
    if result is None: raise HTTPException(404, "Project not found")
    return result

@app.post("/api/tasks")
def create_task(request: TaskCreate):
    try: return workspace.create_task(request)
    except LookupError as error: raise HTTPException(404, str(error)) from error

@app.get("/api/projects/{project_id}/tasks")
def list_project_tasks(project_id: str):
    try: return workspace.list_tasks(project_id)
    except LookupError as error: raise HTTPException(404, str(error)) from error

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    result = workspace.get_task(task_id)
    if result is None: raise HTTPException(404, "Task not found")
    return result

@app.post("/api/tasks/{task_id}/items")
def create_content_item(task_id: str, request: ItemCreate):
    try: return workspace.create_item(task_id, request)
    except LookupError as error: raise HTTPException(404, str(error)) from error
    except ValueError as error: raise HTTPException(409, str(error)) from error

@app.get("/api/tasks/{task_id}/items")
def list_content_items(task_id: str):
    try: return workspace.list_items(task_id)
    except LookupError as error: raise HTTPException(404, str(error)) from error

@app.get("/api/items/{item_id}")
def get_content_item(item_id: str):
    result = workspace.get_item(item_id)
    if result is None: raise HTTPException(404, "Content item not found")
    return result

@app.post("/api/items/{item_id}/versions")
def create_content_version(item_id: str, request: VersionCreate):
    try: return workspace.add_version(item_id, request)
    except LookupError as error: raise HTTPException(404, str(error)) from error

@app.get("/api/items/{item_id}/versions")
def list_content_versions(item_id: str):
    try: return workspace.list_versions(item_id)
    except LookupError as error: raise HTTPException(404, str(error)) from error

@app.post("/api/items/{item_id}/review", response_model=ReviewSessionViewModel)
def start_item_review(item_id: str):
    item = workspace.get_item(item_id)
    if item is None:
        raise HTTPException(404, "Content item not found")
    if not item.get("body", "").strip():
        raise HTTPException(409, "Cannot review an empty content item")
    existing = item.get("review_session_id")
    if existing:
        return public(load(existing))
    task = workspace.get_task(item["task_id"])
    project = workspace.get_project(task["project_id"])
    request = ReviewCreateRequest(
        original_text=item["body"], source_filename=item.get("title", ""),
        brand=project.get("brand") or "示例品牌",
        product=project.get("product") or "示例产品",
    )
    result = service.create(request)
    workspace.attach_review(item_id, result["id"])
    return public(result)


@app.get("/api/health/storage")
def storage_health():
    """Check live DB connectivity without revealing database credentials."""
    if not postgres_enabled():
        return {"status": "unconfigured", "storage": "sqlite-local"}
    try:
        with workspace.connect() as db:
            row = db.execute("SELECT 1").fetchone()
        if row and row[0] == 1:
            return {"status": "ok", "storage": "postgresql"}
        raise RuntimeError("Unexpected database probe result")
    except Exception:
        logger.exception("Storage readiness check failed")
        raise HTTPException(503, "PostgreSQL connection unavailable")


@app.post("/api/tasks/{task_id}/generate-one")
def generate_task_draft(task_id: str, request: GenerateRequest):
    try:
        if os.getenv("VERCEL") and not model_configuration_status()["ready"]:
            raise ValueError("真实模型尚未配置；请先在 Vercel Preview 设置 LLM_PROVIDER、LLM_MODEL、LLM_API_KEY")
        if not request.request_key:
            raise ValueError("request_key required for safe generation")
        # Do not persist reservations for invalid tasks.
        task = workspace.get_task(task_id)
        if not task:
            raise LookupError("Task not found")
        if task["mode"] != "generate" or not task.get("brief", "").strip():
            raise ValueError("Valid Generate task with Brief required")
        reservation = GenerationReservation(workspace)
        status, item_id = reservation.claim(task_id, request.request_key)
        if status == "COMPLETE" and item_id:
            item = workspace.get_item(item_id)
            if item:
                return item
        if status == "CAPACITY":
            raise ValueError("Task generation quantity reached, including in-flight requests")
        if status != "CLAIMED":
            raise ValueError("This generation request is already running or failed; do not retry blindly")
        try:
            item = DraftGenerationService(workspace).generate_one(task_id, request.instruction, auto_review=request.auto_review, review_service=service)
            reservation.complete(task_id, request.request_key, item["id"])
            return item
        except Exception:
            reservation.fail(task_id, request.request_key)
            raise
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except Exception as error:
        logger.exception("Brief draft generation failed")
        raise HTTPException(503, "生成暂时不可用，请检查模型配置或稍后重试") from error

@app.get("/api/models/status")
def model_configuration_status():
    """Non-sensitive configuration summary, never expose keys."""
    enabled = os.getenv("LLM_PROVIDER", "mock").strip().lower() not in ("", "mock", "demo")
    model = os.getenv("LLM_MODEL", "").strip()
    configured = bool(enabled and model and os.getenv("LLM_API_KEY", "").strip())
    return {"mode": "live" if configured else "demo", "ready": configured,
            "model": model if configured else "mock-v1",
            "message": "真实模型已配置" if configured else "当前为 Mock 演示模式；请配置 LLM_PROVIDER、LLM_MODEL 和 LLM_API_KEY"}
