from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date

class WeightEntry(BaseModel):
    date: date
    kg: float

class Note(BaseModel):
    id: str
    text: str

class Observation(BaseModel):
    code: str
    value: Optional[float] = None
    unit: Optional[str] = None
    effectiveDate: Optional[date] = None

class Patient(BaseModel):
    id: str
    birthDate: Optional[date] = None
    sex: Optional[str] = Field(None, regex=r"^(male|female|other|unknown)$")

class Bundle(BaseModel):
    patient: Patient
    notes: List[Note] = []
    weights: List[WeightEntry] = []
    observations: List[Observation] = []
    bmi: Optional[float] = None
    facts: Dict[str, Any] = {}

class DeterminationRequest(BaseModel):
    caseId: str
    payerCode: str = Field(..., examples=["CMS", "UHC", "AETNA"])
    policyVersion: Optional[str] = "2025.1"
    bundle: Bundle

class CriterionResult(BaseModel):
    id: str
    label: str
    outcome: str  # PASS / FAIL / UNKNOWN
    evidence: List[Dict[str, Any]] = []

class DeterminationResult(BaseModel):
    id: str
    caseId: str
    policy: str
    status: str  # MEETS / NOT_MEETS / INSUFFICIENT
    summary: str
    criteria: List[CriterionResult]
    artifacts: Dict[str, str] = {}

class ErrorResponse(BaseModel):
    message: str