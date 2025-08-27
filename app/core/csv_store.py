import csv, json, os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

REVIEW_CSV_PATH = os.getenv("HITL_REVIEW_CSV", "./hitl_reviews.csv")
ACCEPTED_CSV_PATH = os.getenv("HITL_ACCEPTED_CSV", "./hitl_accepted.csv")

EDITS_REVIEW_THRESHOLD = int(os.getenv("HITL_EDITS_THRESHOLD", "3"))

CSV_HEADERS = [
    "timestamp",
    "review",          # true/false
    "reason",          # e.g., "warnings", "many_edits", "warnings+many_edits"
    "segment_index",
    "speaker",
    "speaker_id",
    "original_text",   # original segment text as received by Step 2
    "step1_text",
    "step2_text",
    "num_edits",
    "edits_json",
    "warnings_json",
    "metadata_json",
]


def _ensure_file(path: str):
    is_new = not os.path.exists(path)
    if is_new:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def should_review(num_edits: int, had_warning: bool) -> tuple[bool, str]:
    reasons = []
    if had_warning:
        reasons.append("warnings")
    if num_edits >= EDITS_REVIEW_THRESHOLD:
        reasons.append("many_edits")
    if not reasons:
        return False, ""
    return True, "+".join(reasons)

def append_row(
    review: bool,
    reason: str,
    segment_index: int,
    speaker: str,
    speaker_id: int,
    original_text: str,
    step1_text: str,
    step2_text: str,
    edits: List[Dict[str, Any]],
    warnings: List[str],
    metadata: Dict[str, Any],
):
    path = REVIEW_CSV_PATH if review else ACCEPTED_CSV_PATH
    _ensure_file(path)
    row = [
        datetime.utcnow().isoformat(),
        str(review).lower(),
        reason,
        segment_index,
        speaker,
        speaker_id,
        original_text,
        step1_text,
        step2_text,
        len(edits),
        json.dumps(edits, ensure_ascii=False),
        json.dumps(warnings, ensure_ascii=False),
        json.dumps(metadata, ensure_ascii=False),
    ]
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)