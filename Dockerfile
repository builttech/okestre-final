FROM python:3.11-slim

# Instala o Git, necessário para as operações do agente no repositório
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos do código
COPY . .

# Expõe a porta interna do servidor
EXPOSE 8000

# Executa o uvicorn apontando para o app do main.py
CMD ["uvicorn", "gitide_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
