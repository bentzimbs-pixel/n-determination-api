from __future__ import annotations
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import DeterminationRequest, DeterminationResult, ErrorResponse
from .extract import extract_facts
from . import rules
from .pdf import render_and_store_pdf

API_KEY = os.getenv("API_KEY", "dev-key")

app = FastAPI(title="EN Determination API (Vertical Slice)", version="0.1.0")

# Simple CORS for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# In-memory store (demo only)
DB: dict[str, DeterminationResult] = {}


def _check_auth(x_api_key: str | None) -> None:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/determinations", response_model=DeterminationResult, responses={401: {"model": ErrorResponse}})
def create_determination(req: DeterminationRequest, x_api_key: str | None = None):
    _check_auth(x_api_key)

    # Extract facts
    facts = extract_facts(req.bundle)

    # Evaluate rules
    status, criteria, summary = rules.evaluate(facts)

    det_id = str(uuid.uuid4())
    result = DeterminationResult(
        id=det_id,
        caseId=req.caseId,
        policy=f"{req.payerCode}:{req.policyVersion}",
        status=status,
        summary=summary,
        criteria=criteria,
        artifacts={
            "pdf": f"https://example.com/artifacts/{det_id}.pdf",
            "json": f"https://example.com/artifacts/{det_id}.json",
        },
    )
    
    try:
        pdf_url = render_and_store_pdf(result)
        result.artifacts["pdf"] = pdf_url
    except Exception as e:
        # In a real app, you'd use structured logging
        print(f"Could not generate or upload PDF: {e}")


    DB[det_id] = result
    return result


@app.get("/v1/determinations/{det_id}", response_model=DeterminationResult, responses={404: {"model": ErrorResponse}})
def get_determination(det_id: str, x_api_key: str | None = None):
    _check_auth(x_api_key)
    if det_id not in DB:
        raise HTTPException(status_code=404, detail="Not found")
    return DB[det_id]


# FHIR-style operation (stub)
@app.post("/fhir/Patient/{patient_id}/$determine-necessity", response_model=DeterminationResult)
def fhir_determine(patient_id: str, req: DeterminationRequest, x_api_key: str | None = None):
    _check_auth(x_api_key)
    return create_determination(req, x_api_key)