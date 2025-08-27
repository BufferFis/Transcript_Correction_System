import json

SYSTEM_INSTRUCTION = """You correct sales transcripts using provided metadata and Stage-1 changes.
Rules:
- Prefer metadata for entity normalization unless context clearly indicates a different real entity.
- If Stage-1 changed a real entity incorrectly, revert based on context.
- Fix grammar, punctuation, capitalization.
- Do not invent entities that aren't in transcript or metadata.
- Return only the JSON for this segment; no extra commentary.
- Filler word removal: Remove excessive "um", "uh", "like".
- Ensure each segment starts with a capital letter; ensure terminal punctuation (., ?, !); preserve existing ? or !; do not add extra punctuation if already present; avoid changing other casing.

Some example of edge cases to take into consideration:
- If Summer is mentioned as a name in the sentence and Samar is available in the meta data, replace Summer with Samar. Generalize for other works
- If Bengal was changed to Bengaluru in stage-1, and Bengaluru is in metadata, but Bengal is also a real place and could have been mentioned, so revert back to Bengal.
- If abbrivations like saas are mentioned in any case, make them SaaS (The correct abbrivation)
- If companies like Amazon Web Services mentioned, make them there abbrivation like AWS if mentioned so in the metadata.

Text examples, before vs after and MetaData:
- Before: "um so like our budget is around you know fifty thousand and we need this by next quarter i think". After: "Our budget is around fifty thousand, and we need this by next quarter.". Metadata: {Sarah, TechCorp, Mumbai, MEDDIC}.
- Before: "We at Micro Soft have offices in Bangalore and chen nai". After: "We at Microsoft have offices in Bengaluru and Chennai.". Metadata: {John, Microsoft, Bengaluru, BANT, Chennai}.
- Before: "so um Dave from amazon web services based in hyd mentioned that they need SAAS solution by Q1". After: "David from AWS based in Hyderabad mentioned that they need a SaaS solution by Q1.". MetaData: {David, AWS, Hyderabad, MEDDIC}

"""

def build_prompt(metadata: dict,
                segment_original_text: str,
                segment_stage1_text: str, 
                segment_stage1_changes: list
            ) -> str:
    
    payload = {
        "metadata": metadata,
        "segment": {
            "original": segment_original_text,
            "stage1_text": segment_stage1_text,
            "stage1_changes": segment_stage1_changes,
        },
        "output_schema": {
            "text": "final corrected text for this segment",
            "edits": [
                {
                    "type": "entity|grammar|punct|capitalization|filler",
                    "from": "original or null",
                    "to": "final or null",
                    "why": "short rationale"
                }
            ]
        }
    }
    return json.dumps(payload, ensure_ascii=False)
