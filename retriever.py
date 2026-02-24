import os
import pickle
import chromadb
from typing import List, Any
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import Runnable

load_dotenv()

# Configurações
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "./bm25_index.pkl")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")

def reciprocal_rank_fusion(results: List[List], k=60) -> List[Document]:
    """Combina resultados usando Reciprocal Rank Fusion."""
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = str(doc.page_content) # Simplificado para usar conteúdo como chave
            if doc_str not in fused_scores:
                fused_scores[doc_str] = {'doc': doc, 'score': 0.0}
            fused_scores[doc_str]['score'] += 1 / (rank + k)
    
    reranked_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
    return [item['doc'] for item in reranked_results]

class RAGRetriever:
    def __init__(self):
        print("Carregando modelo de embedding (Dados RAG)...")
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'} # Geralmente CPU é suficiente para embedding de query
        )

        print(f"Conectando ao ChromaDB local em {CHROMA_DB_PATH}...")
        try:
            chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            self.vector_store = Chroma(
                client=chroma_client,
                embedding_function=self.embedding_model
            )
            self.vector_retriever = self.vector_store.as_retriever(
                search_type="similarity", 
                search_kwargs={'k': 10}
            )
        except Exception as e:
            print(f"Erro ao conectar no ChromaDB: {e}")
            raise e

        print("Carregando índice BM25...")
        if os.path.exists(BM25_INDEX_PATH):
            with open(BM25_INDEX_PATH, "rb") as f:
                self.bm25_index, self.bm25_docs = pickle.load(f)
        else:
            raise FileNotFoundError(f"Índice BM25 não encontrado em {BM25_INDEX_PATH}")

    def search(self, query: str) -> List[dict]:
        """Executa a busca híbrida e retorna lista de dicionários (serializável)."""
        
        # 1. Busca Vetorial
        print(f"Executando busca vetorial para: {query}")
        vector_docs = self.vector_retriever.invoke(query)

        # 2. Busca BM25
        print("Executando busca BM25...")
        tokenized_query = query.split(" ")
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        top_n_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:10]
        bm25_docs_result = [self.bm25_docs[i] for i in top_n_indices]

        # 3. Fusão
        combined_docs = reciprocal_rank_fusion([vector_docs, bm25_docs_result])
        
        # Remove duplicatas
        unique_docs = list({doc.page_content: doc for doc in combined_docs}.values())
        
        # Converte para formato JSON-friendly
        return [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in unique_docs
        ]
