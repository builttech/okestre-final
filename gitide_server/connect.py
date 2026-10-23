"""VPS entrypoint: device management and authenticated relay only.

The Desktop continues to compose gitide_server.main independently.
"""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.gzip import GZipMiddleware

from gitide_server import connect_auth as auth
from gitide_server.database import SessionLocal, Project, User
from gitide_server.local_bridge import DeviceStore, LocalBridge
from gitide_server.mcp_oauth import MCPOAuth
from gitide_server.mcp_server import create_mcp, mount_mcp


def active_subject(subject):
    if not subject or not str(subject).isdigit():
        return False
    with SessionLocal() as db:
        user = db.get(User, int(subject))
        return bool(user and user.is_active and user.role == "root")


def consent_projects():
    with SessionLocal() as db:
        return [{"id": p.id, "name": p.name} for p in
                db.query(Project).filter(Project.storage_kind == "device").order_by(Project.name)]


def subject_name(subject):
    with SessionLocal() as db:
        user = db.get(User, int(subject)) if subject and str(subject).isdigit() else None
        return user.email if user else "Conta indisponível"


mcp_oauth = MCPOAuth(os.getenv("GITIDE_PUBLIC_URL", "https://ide.builtt.com.br"),
    os.path.join(auth.CONFIG_DIR, "mcp_oauth.db"), auth.SESSION_SECRET,
    auth.get_current_user_from_request, active_subject, consent_projects, subject_name)
local_bridge = LocalBridge(DeviceStore(os.path.join(auth.CONFIG_DIR, "local_devices.db")),
                           SessionLocal, mcp_oauth)


async def validate_bearer(request):
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return False
    return await mcp_oauth.load_access_token(authorization.split(" ", 1)[1])


mcp_server, transport, lifespan = create_mcp(validate_bearer, bridge=local_bridge,
    remote_only=True, audit=mcp_oauth.audit,
    metadata_url=mcp_oauth.base + "/.well-known/oauth-protected-resource/mcp/")
app = FastAPI(title="Okestre Connect", lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(auth.router)
app.router.routes.extend(mcp_oauth.routes())
app.router.routes.extend(local_bridge.routes())
mount_mcp(app, transport)


@app.middleware("http")
async def panel_session(request: Request, call_next):
    if request.url.path in {"/connect-device", "/local-devices"}:
        if not auth.get_current_user_from_request(request):
            return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.get("/")
def home():
    return RedirectResponse("/connect-device", status_code=303)


# Explicit assets: the workspace HTML/JS and editors are never mounted here.
@app.get("/static/{asset}")
def panel_asset(asset: str):
    from fastapi import HTTPException
    if asset not in {"local-devices.css", "local-devices.js"}:
        raise HTTPException(status_code=404)
    return FileResponse(Path(__file__).parent / "static" / asset)


@app.get("/health")
def health():
    return {"status": "ok", "service": "okestre-connect"}
