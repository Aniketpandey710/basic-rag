import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

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
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0, # Keep it deterministic for RAG
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=api_key,
        )
    def process_pdf(self, file_path: str):
        # load pdf
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        print(f"Loaded {len(pages)} pages from PDF.")

        # split text into chunks
        chunks = self.text_splitter.split_documents(pages)

        # add to Chroma DB
        self.vector_db.add_documents(chunks)

        return len(chunks)
    
    async def answer_question(self, question: str, k: int):
        # Create the retriever from our ChromaDB
        retriever = self.vector_db.as_retriever(search_kwargs={"k": k})
        
        # Retrieve relevant documents
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