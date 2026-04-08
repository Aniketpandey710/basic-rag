import os
import shutil
import uuid
import asyncio
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.models.schema import IngestResponse, QueryRequest, QueryResponse
from app.services.rag_services import rag_service
from app.core.mongodb_service import MongoDBService

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.post("/ingest", response_model=IngestResponse)
def ingest_data(file: UploadFile = File(...)):
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    
    tmp_file_name = f"data/{file.filename}"

    try:
        os.makedirs("data", exist_ok=True)
        with open(tmp_file_name, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Get file size
        file_size = os.path.getsize(tmp_file_name)
        
        # Generate request ID
        request_id = uuid.uuid4().hex
        
        # Process file and create chunks
        num_chunks = rag_service.process_file(tmp_file_name, request_id)
        
        # Delete the local file after processing
        os.remove(tmp_file_name)
        
        # Store metadata in MongoDB
        try:
            MongoDBService.insert_ingest_record(
                request_id=request_id,
                document_name=file.filename,
                file_size=file_size,
                total_chunks=num_chunks,
                status="success"
            )
        except Exception as db_error:
            print(f"Warning: Failed to store metadata in MongoDB: {db_error}")
            # Continue even if MongoDB fails - RAG data is already stored in Chroma
        
        return IngestResponse(
            filename=file.filename,
            request_id=request_id,
            message="Document successfully ingested and processed.",
            status="success",
            chunks_created=num_chunks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/chunks")
def get_chunks(request_id: str, limit: int = 10):
    """Retrieve chunks from Chroma DB"""
    try:
        # Query all documents from Chroma DB
        results = rag_service.vector_db.get(limit=limit, where={"request_id": request_id})
        
        if not results or not results.get("documents"):
            return {"message": "No chunks found in database", "chunks": []}
        
        chunks_data = []
        for i, doc in enumerate(results["documents"]):
            chunks_data.append({
                "id": results["ids"][i] if results.get("ids") else f"chunk_{i}",
                "content": doc,
                "metadata": results["metadatas"][i] if results.get("metadatas") else {}
            })
        
        return {
            "total_chunks": len(chunks_data),
            "chunks": chunks_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chunks: {str(e)}")
    
@router.post("/search",response_model=QueryResponse)
async def search_chunks(payload: QueryRequest):
    """Search RAG with retry logic for API rate limits"""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Call the RAG service to get the answer
            result = await rag_service.answer_question(
                payload.question, 
                payload.top_k,
                request_id=payload.request_id
            )
            
            return QueryResponse(
                question=payload.question,
                answer=result["answer"],
                sources=result["sources"]
            )
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a rate limit error (503)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️  API unavailable. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=503, 
                        detail="Google Gemini API is currently unavailable. Please try again in a few minutes."
                    )
            else:
                # For other errors, fail immediately
                raise HTTPException(status_code=500, detail=f"Search failed: {error_msg}")