# app/api/pipeline_routes.py
from fastapi import APIRouter
from typing import List, Dict, Any
from app.models.schemas_pipeline import PipelineRequest
from app.models.schemas import TranscriptSegment
from app.core.fuzzy_matcher import correct_transcript_segment  # Step 1
from app.core.step2_orchestrator import run_step2               # Step 2 orchestrator
from app.core.gemini_client import Step2Gemini                  # Step 2 client

# HITL CSV triage helpers
from app.core.csv_store import append_row, should_review

router = APIRouter()
_gemini = Step2Gemini()  # ensure env is loaded before import/instantiation

@router.post("/run", response_model=List[TranscriptSegment])
def run_full_pipeline(req: PipelineRequest):
    # Copy input segments to plain dicts
    seg_dicts: List[Dict[str, Any]] = [seg.dict() for seg in req.transcript]

    # Step 1: entity-only pass
    stage1_texts: List[str] = []
    stage1_changes: List[List[Dict[str, Any]]] = []
    for seg in seg_dicts:
        s1 = correct_transcript_segment(
            seg, req.metadata, add_terminal_period=True, threshold=80.0
        )
        seg["text"] = s1["text"]         # update segment to Stage 1 text (input to Step 2)
        stage1_texts.append(s1["text"])
        stage1_changes.append(s1.get("_stage1_changes", []))

    # Step 2: LLM refinement (context + grammar/style)
    results, warnings = run_step2(
        gemini=_gemini,
        metadata=req.metadata,
        transcript_segments=seg_dicts,   # Stage 1 text in seg_dicts
        step1_texts=stage1_texts,
        step1_changes=stage1_changes,
    )

    # Triage + CSV dump per segment (review or accepted)
    had_warning = len(warnings) > 0
    final_segments: List[Dict[str, Any]] = []
    for idx, (seg, res) in enumerate(zip(seg_dicts, results)):
        # Final corrected segment (replace text only)
        final = {**seg, "text": res.text}
        final_segments.append(final)

        # Prepare HITL CSV fields
        edits_dicts = [e.model_dump(by_alias=True) for e in res.edits]
        review, reason = should_review(num_edits=len(edits_dicts), had_warning=had_warning)

        # "original_text" here means the text as seen by Step 2 (Stage 1 text)
        original_text_for_step2 = stage1_texts[idx]
        step1_text = stage1_texts[idx]
        step2_text = res.text
        speaker = seg.get("speaker", "")
        speaker_id = seg.get("speaker_id", 0)

        append_row(
            review=review,
            reason=reason,
            segment_index=idx,
            speaker=speaker,
            speaker_id=speaker_id,
            original_text=original_text_for_step2,
            step1_text=step1_text,
            step2_text=step2_text,
            edits=edits_dicts,
            warnings=warnings,
            metadata=req.metadata,
        )

    # Return only corrected segments array for downstream pipeline
    return final_segments
