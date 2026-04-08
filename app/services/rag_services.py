import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

MODEL = os.getenv("model", "gemini-2.5-flash")  # Default to a more recent model if not set
api_key = os.getenv("GOOGLE_API_KEY")


class RAGService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
        self.vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.llm = None

    def process_pdf(self, file_path: str, request_id: str):
        # load pdf
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        print(f"Loaded {len(pages)} pages from PDF.")
        for page in pages:
            page.metadata["request_id"] = request_id  # Add request_id to metadata for tracking
        print("Pages:", [page.metadata for page in pages])
        # split text into chunks
        chunks = self.text_splitter.split_documents(pages)
        print("Chunks:", chunks)
        # add to Chroma DB
        self.vector_db.add_documents(chunks)

        return len(chunks)
    
    def get_loader(self, file_path: str):
        if file_path.lower().endswith(".pdf"):
            return PyPDFLoader(file_path)
        elif file_path.lower().endswith(".docx"):
            return Docx2txtLoader(file_path)
        else:
            raise ValueError("Unsupported file type. Only PDF and DOCX are supported.")
    
    def process_file(self, file_path: str, request_id: str):
        # loader
        loader = self.get_loader(file_path)
        pages = loader.load()
        print(f"Loaded {len(pages)} pages from PDF.")
        for page in pages:
            page.metadata["request_id"] = request_id  # Add request_id to metadata for tracking
        # split text into chunks
        chunks = self.text_splitter.split_documents(pages)
        print("Chunks:", chunks)
        # add to Chroma DB
        self.vector_db.add_documents(chunks)
        return len(chunks)
    
    async def answer_question(self, question: str, k: int, request_id: str = None):
        # Create the retriever from our ChromaDB with optional metadata filtering
        search_kwargs = {"k": k}
        self.llm = ChatGoogleGenerativeAI(
            model=MODEL,
            temperature=0.3, # Keep it deterministic for RAG
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=api_key,
        )
        print(f"LLM initialized with model: {MODEL}")
        
        # Add metadata filter if request_id is provided
        if request_id:
            search_kwargs["filter"] = {"request_id": request_id}
        
        retriever = self.vector_db.as_retriever(search_kwargs=search_kwargs)
        
        # Retrieve relevant documents (already filtered by request_id if provided)
        docs = retriever.invoke(question)
        
        # Format context from documents
        context = "\n".join([doc.page_content for doc in docs])
        
        # Create a simple prompt and invoke the LLM
        prompt = f"""Answer the question based on the following context:

                Context:
                {context}

                Question: {question}

                Answer:"""
        
        response = self.llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        # Extract the text and source filenames/page numbers
        sources = [doc.metadata.get("source", "Unknown") for doc in docs]
        
        return {
            "answer": answer,
            "sources": list(set(sources)) # Unique sources only
        }
    
# Create a singleton instance
rag_service = RAGService()