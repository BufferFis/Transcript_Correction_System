import os, json
from typing import Any, Dict
from google import genai
from app.core.prompt_step2 import SYSTEM_INSTRUCTION, build_prompt

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

class Step2Gemini:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = api_key or os.getenv("GEMINI_API_KEY")

        if not key:
            raise RuntimeError("GEMINI_API_KEY NOT FOUND")
        
        self.client = genai.Client(api_key=key)
        self.model = model or GEMINI_MODEL

    def _parse_or_repair(self, txt:str) -> Dict[str, Any]:
        try:
            return json.loads(txt)
        
        except Exception:
            s, e = txt.find("{"), txt.rfind("}")
            if s != -1 and e != -1 and e > s:
                return json.loads(txt[s:e+1])
            raise

    def refine_segment(self, metadata: Dict[str, Any], original_text: str, step1_text: str, step1_changes: list) -> Dict[str, Any]:
        user_payload = build_prompt(metadata, original_text, step1_text, step1_changes)
        prompt = f"{SYSTEM_INSTRUCTION}\n\n{user_payload}"

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,  # a string, not a list of dicts
            config={"temperature": 0.2, "top_p": 0.9, "max_output_tokens": 1024},
        )
        txt = getattr(resp, "text", None) or getattr(resp, "output_text", "")
        data = self._parse_or_repair(txt)

        if not isinstance(data, dict) or "text" not in data or "edits" not in data:
            raise ValueError("Phase 2: invalid model output schema")
        return data
    
