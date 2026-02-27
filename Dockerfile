# Usar uma imagem base leve de Python
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema e bibliotecas Python via APT (mais robusto no GCP)
# Como o pip está bloqueado com 403 para a API JSON, usamos pacotes oficiais do Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl python3-requests python3-dotenv python3-pandas \
  && rm -rf /var/lib/apt/lists/*

# Copiar apenas o arquivo de requisitos
COPY requirements.txt .

# Configurar pip para usar o espelho Aliyun e confiar nele
# O pip será usado apenas para pacotes que não existem no repositório do Debian
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST="mirrors.aliyun.com download.pytorch.org"

# Instalar o restante das dependências (pip tentará o espelho alternativo)
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt || \
  pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

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
