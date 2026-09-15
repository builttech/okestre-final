"""Session-root management API; never accepts MCP credentials as administrator."""
import hmac
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.concurrency import run_in_threadpool
from gitide_server.integrations import DatabaseDiagnostic
from gitide_server.supabase_oauth import SupabaseOAuthError


def routes(oauth, integrations):
    async def manage(request):
        headers = {"Cache-Control": "no-store"}
        user = oauth.current_user(request)
        if not user or user.role != "root":
            return JSONResponse({"detail": "Acesso restrito ao root."}, 403 if user else 401, headers=headers)
        csrf = oauth.management_csrf(request, user)
        if request.method != "GET" and not hmac.compare_digest(request.headers.get("x-csrf-token", ""), csrf):
            return JSONResponse({"detail": "Atualize a pagina antes de continuar."}, 403, headers=headers)
        try:
            identifier = request.path_params.get("identifier")
            action = request.path_params.get("action")
            if request.method == "GET":
                return JSONResponse({"items": integrations.list(), "projects": oauth.list_projects(),
                    "approvals": integrations.pending(), "csrf_token": csrf,
                    "supabase_oauth": integrations.supabase.metadata(user.id) if integrations.supabase else {"configured": False, "accounts": []}}, headers=headers)
            if request.method == "DELETE":
                await run_in_threadpool(integrations.delete, identifier)
                return JSONResponse({"status": "deleted"}, headers=headers)
            if action == "test":
                result = await run_in_threadpool(integrations.test, identifier)
                return JSONResponse(result, headers=headers)
            if action in {"approve", "reject"}:
                if not integrations.decide(identifier, action == "approve"):
                    return JSONResponse({"detail": "Solicitacao expirada ou ja decidida."}, 409, headers=headers)
                return JSONResponse({"status": "approved" if action == "approve" else "rejected"}, headers=headers)
            if len(await request.body()) > 32000:
                return JSONResponse({"detail": "Formulario muito grande."}, 413, headers=headers)
            data = await request.json()
            result = await run_in_threadpool(integrations.save, data, {p["id"] for p in oauth.list_projects()}, identifier)
            return JSONResponse(result, headers=headers)
        except DatabaseDiagnostic as error:
            return JSONResponse({"detail": str(error), "code": error.code}, 502, headers=headers)
        except SupabaseOAuthError as error:
            return JSONResponse({"detail": str(error), "code": "supabase_oauth_error"}, 502, headers=headers)
        except Exception:
            return JSONResponse({"detail": "Operacao recusada. Verifique campos, host Supabase, projetos, senha e conexao SSL."}, 400, headers=headers)
    return [Route("/api/integrations", manage, methods=["GET", "POST"]),
            Route("/api/integrations/{identifier}", manage, methods=["PUT", "DELETE"]),
            Route("/api/integrations/{identifier}/{action}", manage, methods=["POST"])]
