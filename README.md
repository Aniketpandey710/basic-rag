# Basic RAG (Retrieval-Augmented Generation) Backend

A FastAPI-based Retrieval-Augmented Generation (RAG) application that allows you to upload PDF documents, chunk them, embed them using Google's Generative AI, store them in Chroma DB, and query them with intelligent responses powered by the Gemini model.

## Features

- 📄 **PDF Upload & Processing**: Upload PDF files for processing
- 🔍 **Document Chunking**: Automatically split documents into manageable chunks
- 🧠 **Vector Embeddings**: Generate embeddings using Google's Generative AI
- 💾 **Vector Database**: Store and retrieve chunks using Chroma DB
- 🤖 **Intelligent Queries**: Ask questions about your documents and get context-aware answers
- 📊 **Chunk Retrieval**: View all processed chunks from the database

## Tech Stack

- **Backend Framework**: FastAPI
- **LLM Provider**: Google Generative AI (Gemini)
- **Vector Database**: Chroma DB
- **Embeddings**: Google Generative AI Embeddings
- **Document Processing**: LangChain
- **PDF Handling**: PyPDF

## Prerequisites

- Python 3.8+
- Google Generative AI API key (get it from [Google AI Studio](https://aistudio.google.com/app/apikey))

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aniketpandey710/basic-rag.git
   cd basic-rag/rag-backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the `rag-backend` directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   DATABASE_PATH=./chroma_db
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=100
   ```

## Running the Application

1. **Start the FastAPI server**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the API**
   - API Documentation (Swagger UI): http://localhost:8000/docs
   - Alternative Documentation (ReDoc): http://localhost:8000/redoc

## API Endpoints

### 1. Health Check
- **Endpoint**: `GET /health`
- **Description**: Check if the API is running
- **Response**:
  ```json
  {
    "status": "healthy"
  }
  ```

### 2. Ingest PDF
- **Endpoint**: `POST /ingest`
- **Description**: Upload and process a PDF file
- **Request**: 
  - Form data with file upload (PDF only)
- **Response**:
  ```json
  {
    "filename": "document.pdf",
    "message": "Document successfully ingested and processed.",
    "status": "success",
    "chunks_created": 15
  }
  ```

### 3. Retrieve Chunks
- **Endpoint**: `GET /chunks?limit=10`
- **Description**: Get chunks stored in Chroma DB
- **Parameters**:
  - `limit` (optional): Number of chunks to retrieve (default: 10)
- **Response**:
  ```json
  {
    "total_chunks": 10,
    "chunks": [
      {
        "id": "chunk_1",
        "content": "Lorem ipsum dolor sit amet...",
        "metadata": {
          "source": "document.pdf",
          "page": 1
        }
      }
    ]
  }
  ```

### 4. Query RAG
- **Endpoint**: `POST /query`
- **Description**: Ask a question about the uploaded documents
- **Request**:
  ```json
  {
    "question": "What is the main topic of the document?",
    "k": 3
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The main topic of the document is...",
    "sources": ["document.pdf"]
  }
  ```

## Project Structure

```
rag-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── api/
│   │   └── endpoints.py     # API route definitions
│   ├── models/
│   │   └── schema.py        # Pydantic models
│   ├── services/
│   │   └── rag_services.py  # RAG business logic
│   └── core/
├── data/                    # Uploaded PDFs
├── chroma_db/              # Vector database storage
├── requirements.txt
├── .env                    # Environment variables (not in git)
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Your Google Generative AI API key | Required |
| `DATABASE_PATH` | Path to Chroma DB storage | `./chroma_db` |
| `CHUNK_SIZE` | Size of document chunks | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `100` |

## Usage Example

```bash
# 1. Upload a PDF
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@document.pdf"

# 2. View chunks
curl "http://localhost:8000/chunks?limit=5"

# 3. Query the document
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the document about?",
    "k": 3
  }'
```

## How It Works

1. **PDF Upload**: User uploads a PDF file via the `/ingest` endpoint
2. **Text Extraction**: PDFs are parsed and converted to text
3. **Chunking**: Large documents are split into overlapping chunks
4. **Embedding**: Each chunk is converted to a vector embedding
5. **Storage**: Embeddings and chunks are stored in Chroma DB
6. **Query Processing**: User queries are converted to embeddings
7. **Retrieval**: Similar chunks are retrieved from the database
8. **Generation**: Retrieved chunks are passed to Gemini for response generation

## Models Used

- **Embedding Model**: `models/embedding-001`
- **LLM Model**: `gemini-pro`

## Dependencies

See `requirements.txt` for all dependencies. Key packages:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain` - LLM orchestration
- `langchain-google-genai` - Google Generative AI integration
- `chromadb` - Vector database
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

## Troubleshooting

### API Key Issues
- Ensure `GOOGLE_API_KEY` is set in `.env`
- Verify the API key is valid at [Google AI Studio](https://aistudio.google.com/app/apikey)

### Model Not Found Errors
- Check that the models are available for your API key
- Visit Google AI Studio to see available models

### Port Already in Use
- Change the port: `uvicorn app.main:app --reload --port 8001`

## Future Enhancements

- [ ] Support for multiple file formats (DOCX, TXT, etc.)
- [ ] User authentication and document management
- [ ] Advanced filtering and metadata search
- [ ] Conversation history tracking
- [ ] Performance analytics and monitoring
- [ ] Batch document processing
- [ ] Multiple language support

## Contributing

Contributions are welcome! Feel free to open issues and submit pull requests.

## License

This project is open source and available under the MIT License.

## Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, LangChain, and Google Generative AI**
