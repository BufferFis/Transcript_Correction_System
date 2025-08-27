import os, json
from typing import Any, Dict
from google import genai
from app.core.prompt_step2 import SYSTEM_INSTRUCTION, build_prompt
from google.genai import types
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


        schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "text": types.Schema(type=types.Type.STRING),
                "edits": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "type": types.Schema(type=types.Type.STRING),
                            "from": types.Schema(type=types.Type.STRING, nullable=True),
                            "to": types.Schema(type=types.Type.STRING, nullable=True),
                            "why": types.Schema(type=types.Type.STRING, nullable=True),
                        },
                        required=["type"],
                    ),
                ),
            },
            required=["text", "edits"]
        )

        # First attempt with structured output
        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
                top_p=0.9,
                max_output_tokens=1024
            ),
        )
        txt = getattr(resp, "text", None) or getattr(resp, "output_text", "")
        
        try:
            data = self._parse_or_repair(txt)
            if not isinstance(data, dict) or "text" not in data or "edits" not in data:
                raise ValueError("schema_miss")
            return data
        
        except Exception:
            # One strict retry that reiterates constraints
            strict_prompt = (
                f"{SYSTEM_INSTRUCTION}\n\n"
                "Return a single JSON object only with keys 'text' and 'edits'; "
                "do not include markdown, prose, or extra keys.\n\n"
                f"{user_payload}"
            )
            resp2 = self.client.models.generate_content(
                model=self.model,
                contents=strict_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1,
                    top_p=0.9,
                    max_output_tokens=1024,
                ),
            )
            txt2 = getattr(resp2, "text", None) or getattr(resp2, "output_text", "")
            data2 = self._parse_or_repair(txt2)
            if not isinstance(data2, dict) or "text" not in data2 or "edits" not in data2:
                raise ValueError("Phase 2: invalid model output schema (after retry)")
            return data2


    
