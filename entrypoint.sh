#!/bin/bash
set -e

# Detectar qual comando python usar (python ou python3)
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "Erro: Python não encontrado. Certifique-se de que o Python está no seu PATH."
    exit 1
fi

if [ "$1" = 'download' ]; then
    echo "Executando download de arquivos do SharePoint..."
    $PYTHON_CMD download_all_files_to_local_folder.py
elif [ "$1" = 'index' ]; then
    echo "Executando indexação de documentos..."
    $PYTHON_CMD index_documents.py
elif [ "$1" = 'api' ]; then
    echo "Iniciando API FastAPI..."
    exec uvicorn api:app --host 0.0.0.0 --port 8002
elif [ "$1" = 'start' ]; then
    echo "Iniciando verificação de banco vetorial..."
    
    # Caminhos dos índices (devem bater com o .env ou valores default do script python)
    CHROMA_DB="./chroma_db/chroma.sqlite3"
    BM25_INDEX="./bm25_index.pkl"

    if [ "$FORCE_REINDEX" = "true" ]; then
        echo "FORCE_REINDEX=true detectado. Forçando nova indexação..."
        NEED_INDEX="true"
    elif [ ! -f "$CHROMA_DB" ] || [ ! -f "$BM25_INDEX" ]; then
        echo "Banco vetorial ou índice BM25 não encontrados."
        NEED_INDEX="true"
    else
        echo "Banco vetorial e índice encontrados. Pulando download e indexação."
        NEED_INDEX="false"
    fi

    if [ "$NEED_INDEX" = "true" ]; then
        echo "Executando fluxo completo de inicialização..."
        echo "1/2: Baixando arquivos..."
        $PYTHON_CMD download_all_files_to_local_folder.py
        echo "2/2: Indexando documentos..."
        $PYTHON_CMD index_documents.py
    fi

    echo "Iniciando API..."
    exec uvicorn api:app --host 0.0.0.0 --port 8002
else
    echo "Comando não reconhecido. Use: download, index, api ou start."
    exec "$@"
fi
