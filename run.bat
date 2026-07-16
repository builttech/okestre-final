@echo off
title GitIDE Local Server
chcp 65001 > nul
cls

echo ======================================================================
echo                     GitIDE - Servidor de Desenvolvimento
echo ======================================================================
echo.

:: 1. Verifica se o Python está disponível
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não foi encontrado no sistema. Por favor, instale o Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

:: 2. Configura e ativa o ambiente virtual (.venv)
if not exist .venv (
    echo [INFO] Criando ambiente virtual Python - venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo [INFO] Ambiente virtual criado com sucesso.
)

echo [INFO] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

:: 3. Instala/atualiza dependências
echo [INFO] Verificando e instalando dependências (pip)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar as dependências do requirements.txt.
    pause
    exit /b 1
)

:: 4. Executa a inicialização lógica da chave de segurança
echo [INFO] Configurando credenciais e banco de dados local...
python -c "from gitide_server.main import load_or_create_config; print('Configuração carregada:', load_or_create_config())"

echo.
echo ======================================================================
echo    O servidor local do GitIDE está prestes a iniciar!
echo.
echo    1. Abra o Dashboard no seu navegador:
echo       -^> http://127.0.0.1:8000
echo.
echo    2. Para conectar à GPT Action:
echo       Exponha a porta 8000 usando Ngrok ou Cloudflare Tunnel:
echo       ngrok http 8000  OU  cloudflared tunnel --url http://localhost:8000
echo.
echo    3. Copie o Token de API exibido no topo do Dashboard e use-o
echo       como Bearer Token na configuração de autenticação do GPT.
echo ======================================================================
echo.

:: 5. Inicia o Uvicorn
python -m uvicorn gitide_server.main:app --host 127.0.0.1 --port 8000 --reload
pause
