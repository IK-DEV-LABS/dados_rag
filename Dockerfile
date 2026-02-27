# Usar uma imagem base leve de Python
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema e ferramentas de diagnóstico
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl \
  && rm -rf /var/lib/apt/lists/*

# Copiar apenas o arquivo de requisitos
COPY requirements.txt .

# Configurar pip para usar o espelho Aliyun (bypass 403 do CDN Fastly/GRU)
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST="mirrors.aliyun.com download.pytorch.org"

# Instalar dependências básicas
RUN pip install --no-cache-dir requests python-dotenv

# Instalar Torch CPU
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 \
  torch --index-url https://download.pytorch.org/whl/cpu

# Instalar o restante das dependências
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

# Copiar o restante do código do projeto
COPY . .

# Dar permissão de execução ao entrypoint
RUN chmod +x entrypoint.sh

# Expor a porta da API
EXPOSE 8002

# Usar o entrypoint para gerenciar os comandos
ENTRYPOINT ["./entrypoint.sh"]

# Comando padrão para iniciar tudo (Download -> Index -> API)
CMD ["start"]
