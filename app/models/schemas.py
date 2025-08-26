from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any, Dict, Tuple

class TranscriptSegment(BaseModel):
    end_timestamp: float
    is_seller: bool
    language: Optional[str]
    speaker: str
    speaker_id: int
    start_timestamp: float
    text: str


class CorrectionRequest(BaseModel):
    transcript: List[TranscriptSegment]
    metadata: Dict[str, Any]


class CorrectionResponse(BaseModel):
    transcript: List[TranscriptSegment]
    changes: List[List[Dict[str, Any]]]