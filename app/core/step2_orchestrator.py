from typing import List, Dict, Any
from app.core.gemini_client import Step2Gemini
from app.models.schemas_step2 import Step2SegmentResult, Step2Edit


def run_step2(gemini: Step2Gemini,
                metadata: Dict[str, Any],
                transcript_segments: List[Dict[str, Any]],
                step1_texts: List[str],
                step1_changes: List[List[Dict[str, Any]]]    
        ):
    
    results: List[Step2SegmentResult] = []
    warnings: List[str] = []

    for idx, seg in enumerate(transcript_segments):
        og_text = seg.get("text", "")
        s1_text = step1_texts[idx]
        s1_changes = step1_changes[idx] if idx < len(step1_changes) else []

        try:
            data = gemini.refine_segment(metadata, og_text, s1_text, s1_changes)
            edits = [Step2Edit.model_validate(e) for e in data.get("edits", [])]
            results.append(Step2SegmentResult(text=data["text"], edits=edits))

        except Exception as e:
            warnings.append(f"segment {idx}: {e}")
            results.append(Step2SegmentResult(text=s1_text, edits=[]))
    return results, warnings