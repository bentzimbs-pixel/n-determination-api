from __future__ import annotations
from typing import Dict, Any, List
from datetime import date, timedelta
from .models import Bundle

NEGATIONS = ["no ", "denies ", "without ", "not "]

KEYWORDS_DYSPHAGIA = ["dysphagia", "aspiration risk", "difficulty swallowing", "unable to swallow"]
KEYWORDS_GI = ["malabsorption", "ileus", "bowel obstruction", "severe gastroparesis"]
KEYWORDS_INTAKE_FAIL = [
    "unable to meet", "< 50%", "less than 50%", "insufficient oral intake", "failed oral supplements"
]


def _contains_keyword(text: str, keywords: List[str]) -> bool:
    t = text.lower()
    for kw in keywords:
        idx = t.find(kw)
        if idx != -1:
            # naive negation check in a small window before the keyword
            window = t[max(0, idx-12):idx]
            if not any(n in window for n in NEGATIONS):
                return True
    return False


def compute_weight_loss_pct(bundle: Bundle, lookback_days: int = 180) -> Dict[str, Any]:
    if not bundle.weights:
        return {"available": False}
    lbs = sorted(bundle.weights, key=lambda w: w.date)
    cutoff = lbs[-1].date - timedelta(days=lookback_days)
    window = [w for w in lbs if w.date >= cutoff]
    if len(window) < 2:
        return {"available": False}
    start = window[0].kg
    end = window[-1].kg
    if start <= 0:
        return {"available": False}
    pct = (start - end) / start * 100.0
    return {"available": True, "pct": round(pct, 2), "start": start, "end": end}


def extract_facts(bundle: Bundle) -> Dict[str, Any]:
    facts: Dict[str, Any] = {}

    # Dysphagia / GI evidence from notes
    dys = any(_contains_keyword(n.text, KEYWORDS_DYSPHAGIA) for n in bundle.notes)
    gi = any(_contains_keyword(n.text, KEYWORDS_GI) for n in bundle.notes)
    intake_fail = any(_contains_keyword(n.text, KEYWORDS_INTAKE_FAIL) for n in bundle.notes)

    facts["dysphagia_evidence"] = {"present": dys, "confidence": 0.8 if dys else 0.2}
    facts["gi_dysfunction"] = {"present": gi, "confidence": 0.7 if gi else 0.2}
    facts["failure_of_oral_intake"] = {"present": intake_fail, "confidence": 0.7 if intake_fail else 0.2}

    # Weight loss
    wl = compute_weight_loss_pct(bundle)
    if wl.get("available"):
        facts["weight_loss_pct"] = wl["pct"]
    if bundle.bmi is not None:
        facts["bmi_value"] = bundle.bmi

    # Physician order / nutrition plan (super naive)
    plan = any("nutrition plan" in n.text.lower() or "dietitian" in n.text.lower() for n in bundle.notes)
    order = any("peg" in n.text.lower() or "tube" in n.text.lower() or "nutrition order" in n.text.lower() for n in bundle.notes)
    facts["nutrition_plan_documented"] = plan
    facts["physician_order_present"] = order

    # Merge user supplied facts, if any (user-provided facts take precedence)
    facts.update(bundle.facts or {})
    return facts