Initial Structure
``` transcript_enhancer/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── fuzzy_matcher.py    # Stage 1: Fuzzy string matching
│   │   ├── gemini_processor.py # Stage 2: Gemini corrections
│   │   ├── active_learning.py  # Stage 3: Confidence & human review
│   │   └── pipeline.py         # Main processing orchestrator
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models for request/response
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── metrics.py          # Evaluation metrics
│   │   └── helpers.py          # Common utilities
│   └── config/
│       ├── __init__.py
│       ├── settings.py         # Configuration
│       └── metadata.py         # Metadata storage & management
├── tests/
├── requirements.txt
├── .env                        # Environment variables
└── README.md
```
