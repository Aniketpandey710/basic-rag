from typing import List, Optional
from pydantic import BaseModel

class IngestResponse(BaseModel):
    filename: str
    request_id: str
    message: str
    status: str = "success"
    chunks_created: int

class QueryRequest(BaseModel):
    question: str
    request_id: str
    top_k: Optional[int] = 3  # Number of document chunks to retrieve

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]  # To show which parts of the PDF were used