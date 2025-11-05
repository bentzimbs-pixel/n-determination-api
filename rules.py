from __future__ import annotations
from typing import Dict, Any, List
from .models import CriterionResult

# Simplified CMS-like criteria for demo purposes
CRITERIA = [
    {
        "id": "EN1",
        "label": "Impaired swallowing or GI dysfunction necessitating EN",
        "any": [
            {"fact": "dysphagia_evidence", "present": True},
            {
                "all": [
                    {"fact": "gi_dysfunction", "present": True},
                    {"fact": "failure_of_oral_intake", "present": True},
                ]
            },
        ],
    },
    {
        "id": "EN2",
        "label": "Nutritional risk (weight loss ≥10%/180d or BMI < 18.5)",
        "any": [
            {"fact": "weight_loss_pct", "gte": 10.0},
            {"fact": "bmi_value", "lt": 18.5},
        ],
    },
    {
        "id": "EN3",
        "label": "Physician order and nutrition plan documented",
        "all": [
            {"fact": "physician_order_present", "present": True},
            {"fact": "nutrition_plan_documented", "present": True},
        ],
    },
]

REQUIRED_FOR_MEETS = ["EN1", "EN3"]  # EN2 strengthens but not required


def _eval_predicate(facts: Dict[str, Any], pred: Dict[str, Any]) -> bool:
    name = pred.get("fact")
    if name is None:
        # composite
        if "all" in pred:
            return all(_eval_predicate(facts, p) for p in pred["all"])
        if "any" in pred:
            return any(_eval_predicate(facts, p) for p in pred["any"])
        return False

    val = facts.get(name)
    if isinstance(val, dict) and "present" in pred:
        return bool(val.get("present")) == bool(pred["present"])  # presence check
    if "gte" in pred and isinstance(val, (int, float)):
        return val >= float(pred["gte"])
    if "lt" in pred and isinstance(val, (int, float)):
        return val < float(pred["lt"])
    if "present" in pred:
        return bool(val) == bool(pred["present"])  # generic truthiness
    return bool(val)


def evaluate(facts: Dict[str, Any]) -> (str, List[CriterionResult], str):
    results: List[CriterionResult] = []
    passed = set()

    for c in CRITERIA:
        outcome = "PASS" if _eval_predicate(facts, c) else "FAIL"
        if outcome == "PASS":
            passed.add(c["id"])
        results.append(CriterionResult(id=c["id"], label=c["label"], outcome=outcome, evidence=[]))

    # Determine final status
    if all(req in passed for req in REQUIRED_FOR_MEETS):
        status = "MEETS"
        summary = "Criteria EN1 and EN3 satisfied; EN2 optional."
    else:
        # check if insufficient data (no signals at all)
        if not any(facts.values()):
            status = "INSUFFICIENT"
            summary = "Insufficient clinical facts provided to evaluate criteria."
        else:
            status = "NOT_MEETS"
            summary = "Required criteria not satisfied."

    return status, results, summary