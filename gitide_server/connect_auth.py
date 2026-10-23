"""Connect authentication, compatible with existing users, cookies and config files."""
import os, re, json, secrets, hashlib, hmac, base64
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from gitide_server.database import init_db, SessionLocal, User, get_db
init_db()
CONFIG_DIR = os.path.abspath(os.getenv("GITIDE_DATA_DIR", os.path.expanduser("~/.gitide")))
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def load_or_create_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                if "api_key" in config:
                    return config
        except Exception:
            pass
            
    # Se não existir ou estiver corrompido, gera uma chave nova
    new_key = secrets.token_hex(24)
    config = {"api_key": new_key}
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    return config

def get_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return load_or_create_config()

def save_config(new_config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(new_config, f, indent=4)

config = load_or_create_config()
API_KEY = config["api_key"]
SESSION_SECRET = config.get("session_secret")
if not SESSION_SECRET:
    SESSION_SECRET = secrets.token_hex(32)
    config["session_secret"] = SESSION_SECRET
    save_config(config)
ROOT_EMAIL = os.getenv("GITIDE_ROOT_EMAIL", "contato@builtt.com.br").strip().lower()
ROOT_PASSWORD_ENV = os.getenv("GITIDE_ROOT_PASSWORD")
ROOT_CREDENTIALS_PATH = os.path.join(CONFIG_DIR, "root_credentials.txt")

def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256${salt}${base64.b64encode(digest).decode('ascii')}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hash_password(password, salt).split("$", 2)[2]
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False

def sign_session(user_id: int) -> str:
    payload = str(user_id)
    signature = hmac.new(SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("ascii")

def read_session_user_id(token: Optional[str]) -> Optional[int]:
    if not token:
        return None
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        payload, signature = decoded.split(":", 1)
        expected = hmac.new(SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        return int(payload)
    except Exception:
        return None

def has_valid_bearer(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return False
    return hmac.compare_digest(auth.split(" ", 1)[1], API_KEY)

def get_current_user_from_request(request: Request) -> Optional[User]:
    user_id = read_session_user_id(request.cookies.get("gitide_session"))
    if not user_id:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return None
        db.expunge(user)
        return user
    finally:
        db.close()

def ensure_root_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ROOT_EMAIL).first()
        if existing:
            if ROOT_PASSWORD_ENV:
                existing.password_hash = hash_password(ROOT_PASSWORD_ENV)
                existing.is_active = True
                existing.role = "root"
                existing.updated_at = datetime.utcnow()
                db.commit()
                print(f"[Act IA Auth] Senha do usuário root atualizada via GITIDE_ROOT_PASSWORD: {ROOT_EMAIL}")
            return
        password = ROOT_PASSWORD_ENV or secrets.token_urlsafe(18)
        user = User(
            email=ROOT_EMAIL,
            password_hash=hash_password(password),
            role="root",
            is_active=True,
            must_change_password=False,
        )
        db.add(user)
        db.commit()
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(ROOT_CREDENTIALS_PATH, "w", encoding="utf-8") as f:
            f.write(
                "Act IA root user\n"
                "URL local: http://127.0.0.1:8000/login\n"
                f"Usuário: {ROOT_EMAIL}\n"
                f"Senha: {password if not ROOT_PASSWORD_ENV else '[definida via GITIDE_ROOT_PASSWORD]'}\n"
            )
        print(f"[Act IA Auth] Usuário root criado: {ROOT_EMAIL}")
        if ROOT_PASSWORD_ENV:
            print("[Act IA Auth] Senha inicial definida via GITIDE_ROOT_PASSWORD.")
        else:
            print(f"[Act IA Auth] Senha inicial salva em: {ROOT_CREDENTIALS_PATH}")
    finally:
        db.close()

ensure_root_user()


router = APIRouter()
class LoginRequest(BaseModel):
    email: str = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")

@router.get("/login", response_class=HTMLResponse, tags=["Autenticação"])
def get_login_page(request: Request):
    """Tela de autenticação do Act IA."""
    next_path = request.query_params.get("next", "")
    if not re.fullmatch(r"/oauth/consent\?ticket=[A-Za-z0-9_-]+", next_path):
        next_path = "/connect-device"
    if get_current_user_from_request(request):
        return RedirectResponse(url=next_path, status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse(
        content=f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Okestre Connect</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ min-height: 100vh; margin: 0; display: grid; place-items: center; background: #0b0b0c; color: #f8fafc; }}
    main {{ width: min(420px, calc(100vw - 32px)); padding: 28px; border: 1px solid rgba(255,255,255,.12); border-radius: 22px; background: #151517; box-shadow: 0 24px 70px rgba(0,0,0,.36); }}
    span {{ color: #9ca3af; font-size: 12px; }}
    h1 {{ margin: 4px 0 6px; font-size: 24px; }}
    p {{ margin: 0 0 22px; color: #a1a1aa; font-size: 13px; line-height: 1.45; }}
    label {{ display: block; margin: 14px 0 7px; color: #cbd5e1; font-size: 12px; font-weight: 700; }}
    input {{ width: 100%; min-height: 44px; padding: 0 13px; border: 1px solid rgba(255,255,255,.12); border-radius: 12px; background: #0f0f10; color: #f8fafc; outline: none; }}
    input:focus {{ border-color: rgba(255,107,138,.62); box-shadow: 0 0 0 3px rgba(255,107,138,.12); }}
    button {{ width: 100%; min-height: 46px; margin-top: 20px; border: 0; border-radius: 999px; background: #fff; color: #111827; font-weight: 800; cursor: pointer; }}
    #login-error {{ min-height: 18px; margin-top: 12px; color: #fb7185; font-size: 12px; }}
    .hint {{ margin-top: 18px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,.10); color: #71717a; font-size: 11px; }}
  </style>
</head>
<body>
  <main>
    <span>Okestre Connect</span>
    <h1>Conectar dispositivos</h1>
    <p>Informe o usuário root da instalação para acessar o ambiente.</p>
    <form id="login-form">
      <label for="email">Usuário</label>
      <input id="email" name="email" type="email" value="{ROOT_EMAIL}" autocomplete="username" required>
      <label for="password">Senha</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
      <button type="submit">Entrar</button>
      <div id="login-error"></div>
    </form>
    <div class="hint">Cadastro e redefinição pública de senha estão desativados.</div>
  </main>
  <script>
    document.getElementById('login-form').addEventListener('submit', async (event) => {{
      event.preventDefault();
      const error = document.getElementById('login-error');
      error.textContent = '';
      const response = await fetch('/api/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          email: document.getElementById('email').value,
          password: document.getElementById('password').value
        }})
      }});
      const data = await response.json().catch(() => ({{}}));
      if (!response.ok || data.status !== 'success') {{
        error.textContent = data.detail || 'Usuário ou senha inválidos.';
        return;
      }}
      window.location.href = {json.dumps(next_path)};
    }});
  </script>
</body>
</html>""",
        status_code=200,
    )

@router.post("/api/auth/login", tags=["Autenticação"])
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Autentica usuário local e cria cookie de sessão sem expiração por tempo."""
    user = db.query(User).filter(User.email == req.email.strip().lower(), User.is_active == True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")
    user.last_login_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    db.commit()
    response.set_cookie(
        "gitide_session",
        sign_session(user.id),
        httponly=True,
        samesite="lax",
        secure=os.getenv("GITIDE_PUBLIC_URL", "").startswith("https://"),
        path="/",
    )
    return {"status": "success", "user": {"email": user.email, "role": user.role}}

@router.post("/api/auth/logout", tags=["Autenticação"])
def logout(response: Response):
    response.delete_cookie("gitide_session", path="/")
    return {"status": "success"}

@router.get("/api/auth/me", tags=["Autenticação"])
def auth_me(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida.")
    return {"email": user.email, "role": user.role}

