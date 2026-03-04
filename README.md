# RAG Data Service - Microsserviço de Contexto (Otimizado 🚀)

Este projeto é um microsserviço especializado na **ingestão, indexação e recuperação (Retrieval)** de documentos corporativos, otimizado para rodar em ambientes com recursos limitados (GCP M2) e validado para estabilidade via Docker.

## ⚡ Destaques da Otimização
*   **Memória RAM**: Redução de ~2.5GB para **~470MB** (Economia de ~82%).
*   **Modelo de Embedding**: Transição para o `paraphrase-multilingual-MiniLM-L12-v2` (leve e preciso em Português).
*   **Smart Indexing**: Sistema de detecção de mudanças via **Hash MD5**. O container só processa arquivos novos ou alterados.
*   **Build Estabilizado**: Travado em `sentence-transformers==3.4.1` para evitar bugs de regressão em versões mais recentes.
*   **Busca Híbrida**: Combinação de busca semântica (ChromaDB) + busca por palavra-chave (BM25Okapi) via fusion RRF.

---

## 🚀 Arquitetura e Integração

O serviço opera de forma integrada com o ecossistema RAG:
1.  **Dados RAG (Este projeto):** Gerencia o banco vetorial e disponibiliza os chunks via API.
2.  **Backend (IA Agent):** Consome este serviço via porta `8002` para compor o contexto do LLM.

---

## 🐳 Como Executar (Docker)

O serviço agora é auto-suficiente e gerencia a rede `rag-network-shared` automaticamente.

### 1. Startup e Build
```bash
docker compose up -d --build
```
*O sistema instalará a versão otimizada da PyTorch CPU (aprox. 180MB) e o modelo leve de embedding no primeiro boot.*

### 2. Comandos Úteis
| Ação | Comando |
| :--- | :--- |
| Ver Logs | `docker logs -f rag-api-service` |
| Ver Recursos (RAM/CPU) | `docker stats rag-api-service` |
| Forçar Re-indexação | Altere `FORCE_REINDEX=true` no `.env` e reinicie |

---

## 🔌 Documentação da API

### Endpoint: `/retrieve`
*   **Método:** `POST`
*   **Headers:** `Authorization: Bearer <TOKEN_DE_SEGURANCA>`

#### Estrutura do JSON
```json
{
  "query": "procedimento de segurança",
  "k": 5
}
```

---

## ⚙️ Configurações (.env)

| Variável | Valor Recomendado | Descrição |
| :--- | :--- | :--- |
| `MASTER_TOKEN` | `[TOKEN_PARA_TESTES]` | Token alternativo para validação rápida via Postman. |
| `BACKEND_INTERNAL_TOKEN` | `[CHAVE_INTERNA]` | Token de comunicação oficial entre microsserviços. |
| `CHROMA_DB_PATH` | `./chroma_db` | Pasta de persistência (mapeada no volume Docker). |

---

## 🛠️ Troubleshooting (Resolução de Problemas)
- **Erro de Certificado/SSL no Build**: O Dockerfile já usa espelhos via HTTP (`mirrors.aliyun.com`) para contornar bloqueios de rede no servidor.
- **NameError 'nn' ou ImportErrors**: Se ocorrer erro no startup, verifique se a versão da `sentence-transformers` está fixa em `3.4.1` no `requirements.txt`. Versões superiores (como 5.2.x) podem apresentar instabilidades em ambientes CPU.
```