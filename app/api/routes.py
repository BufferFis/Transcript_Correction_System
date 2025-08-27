from fastapi import APIRouter
from typing import List, Dict, Any
from app.models.schemas import CorrectionRequest, CorrectionResponse
from app.core.fuzzy_matcher import correct_transcript_segment

router = APIRouter()

@router.post("/step1", response_model=CorrectionResponse)
def correct_entities(req: CorrectionRequest):
    corrected: List[Dict[str, Any]] = []
    changes_all: List[List[Dict[str, any]]] = []

    for seg in req.transcript:
        c = correct_transcript_segment(seg.dict(), req.metadata, add_terminal_period=True, threshold=80.0)
        corrected.append({**seg.dict(), "text": c["text"]})
        changes_all.append(c.get("_stage1_changes", []))
        
    return {"transcript": corrected, "changes": changes_all}