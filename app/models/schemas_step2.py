from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from app.models.schemas import TranscriptSegment

class Step2Edit(BaseModel):
    type: Literal["entity", "grammar", "punct", "capitalization", "filler"]
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    why: Optional[str] = None

class Step2SegmentResult(BaseModel):
    text: str
    edits: List[Step2Edit] = []

class GrammarRequest(BaseModel):
    transcript: List[TranscriptSegment]
    metadata: Dict[str, Any]
    step1_changes: List[List[Dict[str, Any]]] = Field(..., alias="changes")

    class Config:
        populate_by_name = True

class GrammarResponse(BaseModel):
    transcript: List[TranscriptSegment]
    edits: List[List[Step2Edit]]
    warnings: List[str] = []
