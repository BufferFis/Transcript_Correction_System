# Transcript Correction
This project provides a single endpoint based service which runs in 2 stages, first stage follows an entity normalization via a fuzzy search and then a second stage LLM refinement, then there are prospects of active learning but soo far, the results are then segregated into two csv files, one containing high confidence changes and other low confidence for human review, this data can be used later to train a local model after an year of deployment like BART to remove the old api based service LLM to reduce latency further and increase self sustenance

## Quick Start

- Prerequisites: Python 3.10+ and a valid GEMINI_API_KEY in the environment.
- Install dependencies: pip install -r requirement.txt.
- Set env:  GEMINI_API_KEY="YOUR_KEY" and optionally GEMINI_MODEL="gemini-2.5-flash-lite"
- Run `fastapi dev main.py` to start the server and the service
- Test run can be seen at `app\scripts\evaluate_pipeline.py`


### Environment variables
- GEMINI_API_KEY: Required API key for the LLM client.
- GEMINI_MODEL: Optional model name, defaults to gemini-2.5-flash-lite when not set.

## Project Structure

```
transcript_enhancer/

├── __pycache__/

├── .env

├── .env.example # Store all the configs here

├── .gitignore

├── LICENSE

├── README.md

├── app/

│ ├── __init__.py

│ ├── api/

│ │ ├── __init__.py

│ │ ├── grammar_routes.py # Route to the Gemini API for grammer correction

│ │ ├── pipeline_routes.py # Route to Endpoint for full pipeline

│ │ └── routes.py # Route to Fuzzy Search

│ ├── core/

│ │ ├── __init__.py

│ │ ├── csv_store.py # Stores CSV for human in the loop(Accepted/Not Acc.)

│ │ ├── fuzzy_matcher.py # Fuzzy match algorithm

│ │ ├── gemini_client.py # Gemini client to invoke the LLM

│ │ ├── prompt_step2.py # Creates the prompt which will be taken in by LLM

│ │ └── step2_orchestrator.py # Uses LLM on the output of Fuzzy match

│ ├── models/

│ │ ├── __init__.py

│ │ ├── schemas.py # Pydantic models for step1

│ │ └── schemas_step2.py # Pydantic models for step2

│ ├── utils/ # Future use

│ │ ├── __init__.py

├── hitl_accepted.csv # Accepted captions

├── hitl_reviews.csv # Marked captions

├── main.py # Fast API entery point

├── requirements.txt

├── scripts/

│ ├── eval_results.csv # Evaluation results

│ └── evaluate_pipeline.py # Evaluate the entire pipeline

└── tests/

├── __init__.py

└── test_pipeline.py # Test pipeline on some results

```


## Demo Examples

-  Example A 
	- Input text: “uh like the SaaS platform needs an SSO integration you know” → Output text: “The SaaS platform needs an SSO integration.” 
	- where Metadata: {"people": [], "companies": [], "locations": [], "frameworks": []}
- Example B
	- Input text: “our delivery teams are in blr and hyd” → Output text: “Our delivery teams are in Bengaluru and Hyderabad.”
	- where Metadata: {"people": [], "companies": [], "locations": ["Bengaluru", "Hyderabad"], "frameworks": []}
- Example C
	- Input text: "Hello. Hello. Thank you. Am I audible? Hi, Mohit.: → Output text: "Hello. Hello. Thank you. Am I audible? Hi, Rohit."
	- where Metadata: {"people": ["Rohit"], "companies": ["Pepsales"], "locations": ["Bengaluru"], "frameworks": ["BANT"]}

- Example D
	- Input text: “so um Dave from amazon web services based in hyd mentioned that they need SAAS solution by Q1” → Output text: “David from AWS based in Hyderabad mentioned that they need a SaaS solution by Q1.”
	- Where MetaData: {"people": ["David"], "companies": ["AWS"], "locations": ["Hyderabad"], "frameworks": ["MEDDIC"]}

- Example E
	- Input text: “Pepsi is the organization we are working in. It is located in Bengu” → Output text: “Pepsales is the organization we are working in. It is located in Bengaluru.”
	- Where metadata: {"people": ["Rohit"], "companies": ["Pepsales"], "locations": ["Bengaluru"], "frameworks": ["BANT"]}

## Example Request

{
  "transcript": [
    {
      "end_timestamp": 42.0,
      "is_seller": false,
      "language": null,
      "speaker": "Analyst",
      "speaker_id": 303,
      "start_timestamp": 37.0,
      "text": "uh like the SaaS platform needs an SSO integration you know"
    }
  ],
  "metadata": {
    "people": [],
    "companies": [],
    "locations": [],
    "frameworks": []
  }
}


## Notes

- Stage‑1 can optionally append a terminal period when the text ends alphanumerically to stabilize sentence boundaries before Stage‑2 refinement.
- The pipeline’s evaluation script can compute processing time per segment and multiple readability metrics for before/after comparisons, if desired for regression tracking.
- Prospects of Active learning in the future with the current setup

	

