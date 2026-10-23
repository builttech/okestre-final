FROM python:3.11-slim

# Instala o Git, necessário para as operações do agente no repositório
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia somente o Connect e os contratos necessários ao relay
COPY gitide_server/connect.py gitide_server/connect_auth.py gitide_server/database.py gitide_server/local_bridge.py gitide_server/mcp_oauth.py gitide_server/mcp_connections.py gitide_server/mcp_audit.py gitide_server/mcp_server.py gitide_server/sdd_tasks.py ./gitide_server/
COPY gitide_server/static/local-devices.html gitide_server/static/local-devices.css gitide_server/static/local-devices.js ./gitide_server/static/
COPY okestre_local/__init__.py okestre_local/protocol.py ./okestre_local/

# Expõe a porta interna do servidor
EXPOSE 8000

# Inicia exclusivamente o painel Connect e a comunicação com os agentes
CMD ["uvicorn", "gitide_server.connect:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--ws-max-size", "8388608"]
