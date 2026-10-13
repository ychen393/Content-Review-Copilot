from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .models import DecisionRequest, ReviewCreateRequest, ReviewSessionViewModel
from .service import ReviewWorkflowService
from backend.documents import DefaultDocumentParser

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
    try: return public(operation())
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
