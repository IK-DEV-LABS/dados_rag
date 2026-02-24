import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any
from retriever import RAGRetriever

# Carrega variáveis de ambiente
load_dotenv()

# Configurações de Segurança
security = HTTPBearer()
BACKEND_INTERNAL_TOKEN = os.getenv("BACKEND_INTERNAL_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != BACKEND_INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# --- Modelos ---
class RetrieveRequest(BaseModel):
    query: str

class DocumentModel(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

class RetrieveResponse(BaseModel):
    documents: List[DocumentModel]

# --- App ---
app = FastAPI(
    title="RAG Data Service",
    description="Microsserviço responsável pela recuperação de documentos (Chroma + BM25).",
    version="1.0.0"
)

# Inicializa o Retriever Globalmente
retriever_service = None

@app.on_event("startup")
async def startup_event():
    global retriever_service
    retriever_service = RAGRetriever()
    print("Serviço de Dados RAG pronto.")

@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(request: RetrieveRequest, token: str = Depends(verify_token)):
    if not retriever_service:
        raise HTTPException(status_code=503, detail="Serviço de busca não inicializado.")
    
    try:
        docs = retriever_service.search(request.query)
        return RetrieveResponse(documents=docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
