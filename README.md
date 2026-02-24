# RAG Data Service - Microsserviço de Contexto

Este projeto é um microsserviço especializado na **ingestão, indexação e recuperação (Retrieval)** de documentos corporativos. Ele utiliza uma abordagem de **Busca Híbrida** (ChromaDB para busca vetorial + BM25 para busca por palavras-chave).

## 🚀 Arquitetura de Microserviços

Este serviço faz parte de um ecossistema RAG distribuído:
1.  **Dados RAG (Este projeto):** Responsável por baixar arquivos do SharePoint, vetorizar e servir os trechos mais relevantes via API.
2.  **Backend (IA Agent):** Consome este serviço para obter contexto e gerar respostas usando LLMs (OpenAI/Ollama).

---

## 🛠️ Novas Funcionalidades: Inicialização Inteligente (Smart Start)

O sistema agora possui uma lógica de inicialização otimizada no `entrypoint.sh`:
- **Verificação Automática**: O container detecta se o banco de dados (`chroma_db`) e o índice (`bm25_index.pkl`) já existem.
- **Skip de Indexação**: Se os dados já estiverem presentes, o container pula o download e a indexação, iniciando a API instantaneamente.
- **Forçar Re-indexação**: Caso precise atualizar os documentos, basta definir a variável de ambiente `FORCE_REINDEX=true` no momento da execução.

---

## 🐳 Deploy e Execução (Docker)

Para que este serviço se comunique com o Backend em terminais ou containers separados, utilizamos uma **Rede Docker Externa**.

### 1. Criar a Rede (Uma única vez)
```powershell
docker network create rag-network-shared
```

### 2. Configurar o .env
Certifique-se de que o seu `.env` contém o token de segurança:
```ini
BACKEND_INTERNAL_TOKEN=seu_token_aqui
```

### 3. Iniciar o Serviço
```bash
docker-compose up --build
```
*A API estará disponível internamente na rede Docker como `rag-api-service:8002`.*

---

## 🔌 Documentação da API

### Endpoint: `/retrieve`
*   **Método:** `POST`
*   **Autenticação:** Header `Authorization: Bearer <BACKEND_INTERNAL_TOKEN>`.

#### Exemplo de Requisição
```json
{
  "query": "Como configurar o sistema?",
  "k": 7
}
```

---

## ⚙️ Variáveis de Ambiente Principais

| Variável | Descrição |
| :--- | :--- |
| `DOCUMENTS_PATH` | Caminho local dos documentos PDF. |
| `FORCE_REINDEX` | Se `true`, força o download e indexação no boot. |
| `BACKEND_INTERNAL_TOKEN` | Token para validar requisições do backend. |