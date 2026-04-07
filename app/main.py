import warnings
from dotenv import load_dotenv

# Suppress Pydantic V1 compatibility warning
warnings.filterwarnings("ignore", message=".*Pydantic V1 functionality.*")

load_dotenv()

from fastapi import FastAPI
from app.api.endpoints import router as rag_router


app = FastAPI(title="RAG Backend API")
app.include_router(rag_router)

@app.get("/")
async def root():
    return {"message": "RAG Backend is running"}