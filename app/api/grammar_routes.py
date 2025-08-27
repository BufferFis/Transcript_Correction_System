from fastapi import APIRouter
from typing import List, Dict, Any
from app.models.schemas_step2 import GrammarRequest, GrammarResponse
from app.core.step2_orchestrator import run_step2
from app.core.gemini_client import Step2Gemini
from app.core.csv_store import append_row, should_review

router = APIRouter()
_gemini = Step2Gemini()

@router.post("/step2", response_model=GrammarResponse)
def refine_grammar(req: GrammarRequest):
    step1_texts = [seg.text for seg in req.transcript]
    seg_dicts: List[Dict[str, Any]] = [seg.dict() for seg in req.transcript]
    
    results, warnings = run_step2(
        gemini = _gemini,
        metadata = req.metadata,
        transcript_segments=seg_dicts,
        step1_texts=step1_texts,
        step1_changes=req.step1_changes
    )

    corrected: List[Dict[str, Any]] = []
    edits_all: List[List[Dict[str, Any]]] = []

    had_warning = len(warnings) > 0
    for idx, (seg, res) in enumerate(zip(seg_dicts, results)):
        corrected.append({**seg, "text": res.text})
        edits_dicts = [e.model_dump(by_alias=True) for e in res.edits]
        edits_all.append(edits_dicts)

        # Heuristic triage
        review, reason = should_review(num_edits=len(edits_dicts), had_warning=had_warning)

        # Build fields for CSV
        original_text = seg.get("text", "")
        step1_text = step1_texts[idx]
        step2_text = res.text
        speaker = seg.get("speaker", "")
        speaker_id = seg.get("speaker_id", 0)

        # Append to CSV (review or accepted)
        append_row(
            review=review,
            reason=reason,
            segment_index=idx,
            speaker=speaker,
            speaker_id=speaker_id,
            original_text=original_text,
            step1_text=step1_text,
            step2_text=step2_text,
            edits=edits_dicts,
            warnings=warnings,
            metadata=req.metadata,
        )


    for seg, res in zip(seg_dicts, results):
        corrected.append({**seg, "text": res.text})
        edits_all.append([e.model_dump(by_alias=True) for e in res.edits])

    return GrammarResponse(transcript=corrected, edits=edits_all, warnings=warnings)
