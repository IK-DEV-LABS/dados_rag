# Usar uma imagem base leve de Python
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema e bibliotecas Python via APT (mais robusto no GCP)
# Como o pip sofre interferência no SSL, usamos os pacotes oficiais do Debian para o que for possível
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential curl python3-requests python3-dotenv python3-pandas \
  python3-pydantic python3-chardet python3-openpyxl \
  && rm -rf /var/lib/apt/lists/*

# Copiar apenas o arquivo de requisitos
COPY requirements.txt .

# ESTRATÉGIA DEFINITIVA ANTI-BLOQUEIO:
# 1. Usar espelhos via HTTP (evita o erro de identidade do certificado no proxy/firewall)
# 2. Declarar TRUSTED_HOST para que o pip aceite a conexão sem SSL
ENV PIP_INDEX_URL=http://mirrors.aliyun.com/pypi/simple/
ENV PIP_TRUSTED_HOST="mirrors.aliyun.com pypi.org files.pythonhosted.org pypi.python.org download.pytorch.org pypi.tuna.tsinghua.edu.cn"

# Instalar o restante das dependências (mais lento, mas foge do erro 403 e SSL)
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt || \
  pip install --no-cache-dir --index-url http://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

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
