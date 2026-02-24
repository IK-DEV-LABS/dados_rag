import os
import pickle
import glob
import chromadb
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

# Carrega variáveis de ambiente (caso existam configurações específicas no .env local)
load_dotenv()

# --- Configuração ---
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documentos_oficiais")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "./bm25_index.pkl")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")

def process_and_index_documents_in_batches():
    """
    Carrega, processa e indexa documentos em lotes para economizar memória.
    """
    # 1. Inicializar componentes
    print("Inicializando modelo de embedding e text splitter...")
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)

    print(f"Conectando ao ChromaDB local em {CHROMA_DB_PATH}...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    vector_store = Chroma(
        client=chroma_client,
        embedding_function=embedding_model
    )

    all_chunks = []
    processed_files = set()

    # 2. Encontrar todos os arquivos PDF
    pdf_files = glob.glob(os.path.join(DOCUMENTS_PATH, "**/*.pdf"), recursive=True)
    print(f"Encontrados {len(pdf_files)} arquivos PDF para processar.")

    # 3. Processar cada arquivo individualmente
    for i, file_path in enumerate(pdf_files):
        if file_path in processed_files:
            continue

        print(f"Processando arquivo {i+1}/{len(pdf_files)}: {os.path.basename(file_path)}")
        try:
            # Carrega um único arquivo
            loader = PyMuPDFLoader(file_path, extract_images=False)
            documents = loader.load()

            # Divide em chunks
            chunks = text_splitter.split_documents(documents)
            
            # Adiciona os chunks ao ChromaDB (o embedding acontece aqui)
            vector_store.add_documents(chunks)
            
            # Guarda os chunks para o índice BM25
            all_chunks.extend(chunks)
            processed_files.add(file_path)

        except Exception as e:
            print(f"  -> Erro ao processar o arquivo {file_path}: {e}")

    if not all_chunks:
        print("Nenhum documento foi processado. Encerrando.")
        return

    # 4. Criar e salvar o índice BM25 com todos os chunks
    print("Criando e salvando o índice de busca por palavra-chave (BM25)...")
    tokenized_docs = [doc.page_content.split(" ") for doc in all_chunks]
    bm25_index = BM25Okapi(tokenized_docs)
    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump((bm25_index, all_chunks), f)

    print("\nIndexação concluída com sucesso!")

if __name__ == "__main__":
    process_and_index_documents_in_batches()