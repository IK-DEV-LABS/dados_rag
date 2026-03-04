import os
import pickle
import glob
import hashlib
import chromadb
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# --- Configuração ---
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documentos_oficiais")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "./bm25_index.pkl")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
METADATA_PATH = os.path.join(CHROMA_DB_PATH, "indexing_metadata.pkl")

def get_file_hash(file_path):
    """Gera um hash MD5 para verificar se o arquivo mudou."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_and_index_documents_in_batches():
    """
    Carrega, processa e indexa documentos de forma incremental para economizar CPU/RAM.
    """
    # 1. Carregar metadados de indexação anterior
    indexing_metadata = {}
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "rb") as f:
            indexing_metadata = pickle.load(f)

    # 2. Inicializar componentes
    print(f"Inicializando modelo de embedding: {EMBEDDING_MODEL_NAME}")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=300)

    print(f"Conectando ao ChromaDB em {CHROMA_DB_PATH}...")
    # Usando PersistentClient de forma direta
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    vector_store = Chroma(
        client=chroma_client,
        embedding_function=embedding_model
    )

    # 3. Encontrar arquivos e filtrar apenas os novos/alterados
    pdf_files = glob.glob(os.path.join(DOCUMENTS_PATH, "**/*.pdf"), recursive=True)
    files_to_process = []
    
    current_metadata = {}
    for f in pdf_files:
        f_hash = get_file_hash(f)
        current_metadata[f] = f_hash
        if indexing_metadata.get(f) != f_hash or os.getenv("FORCE_REINDEX") == "true":
            files_to_process.append(f)

    if not files_to_process and os.path.exists(BM25_INDEX_PATH) and os.getenv("FORCE_REINDEX") != "true":
        print("Nenhuma alteração detectada nos documentos. Pulando indexação.")
        return

    print(f"Processando {len(files_to_process)} arquivos novos ou alterados...")
    
    # IMPORTANTE: Se formos re-indexar algo novo, precisamos de TODOS os chunks para o BM25 
    # (O BM25 não é inerentemente incremental da mesma forma que o Chroma)
    all_chunks_for_bm25 = []
    
    # Para o BM25, se houver QUALQUER mudança, reconstruímos o índice global de termos
    # mas o Chroma só recebe os novos.
    
    # 4. Processar arquivos
    for i, file_path in enumerate(pdf_files):
        # Para o Chroma, só adicionamos se estiver na lista de processamento
        if file_path in files_to_process:
            print(f"Indexando no Chroma: {os.path.basename(file_path)}")
            try:
                loader = PyMuPDFLoader(file_path, extract_images=False)
                documents = loader.load()
                chunks = text_splitter.split_documents(documents)
                vector_store.add_documents(chunks)
                all_chunks_for_bm25.extend(chunks)
            except Exception as e:
                print(f"  -> Erro no arquivo {file_path}: {e}")
        else:
            # Para o BM25, precisamos recarregar os antigos para manter o índice completo
            # (Simplificado: Se houver mudança, recarregamos tudo para o BM25 garantir integridade)
            # Em uma escala maior, usaríamos um Search Engine real (Elastic/OpenSearch)
            try:
                loader = PyMuPDFLoader(file_path, extract_images=False)
                all_chunks_for_bm25.extend(text_splitter.split_documents(loader.load()))
            except: pass

    # 5. Salvar BM25 e Metadados
    if all_chunks_for_bm25:
        print("Atualizando índice BM25...")
        tokenized_docs = [doc.page_content.split(" ") for doc in all_chunks_for_bm25]
        bm25_index = BM25Okapi(tokenized_docs)
        with open(BM25_INDEX_PATH, "wb") as f:
            pickle.dump((bm25_index, all_chunks_for_bm25), f)
        
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(current_metadata, f)

    print("\nProcesso concluído.")

if __name__ == "__main__":
    process_and_index_documents_in_batches()
