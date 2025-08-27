from typing import List, Dict, Any
from pydantic import BaseModel
from app.models.schemas import TranscriptSegment

class PipelineRequest(BaseModel):
    transcript: List[TranscriptSegment]
    metadata: Dict[str, Any]
