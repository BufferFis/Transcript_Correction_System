from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.api.routes import router as step1_router
from app.api.grammar_routes import router as step2_router
from app.api.pipeline_routes import router as pipeline_router


app = FastAPI(title="Transcript Correction Pipeline")
app.include_router(step1_router)
app.include_router(step2_router)
app.include_router(pipeline_router)
