"""Session-only, QA-scoped pairing for Chromium extensions on loopback."""
import re
import secrets
from starlette.responses import JSONResponse, Response

class QABridge:
    def __init__(self, runtime):
        self.runtime = runtime
        self.code = None
        self.tokens = {}

    def issue(self):
        self.code = secrets.token_urlsafe(32)
        return {'ok': True, 'data': {'pairing': {'url': self.runtime.origin, 'code': self.code}}}

    def revoke(self):
        self.code = None
        self.tokens.clear()
        return {'ok': True, 'data': {'revoked': True}}

    async def handle(self, request, call_next):
        origin = request.headers.get('origin', '')
        # Chromium extension origins are explicit; never grant browser websites CORS.
        valid_origin = bool(re.fullmatch(r'chrome-extension://[a-p]{32}', origin))
        def reply(data, status=200):
            return cors(JSONResponse(data, status))
        def cors(response):
            if valid_origin:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Vary'] = 'Origin'
            response.headers['Cache-Control'] = 'no-store'
            return response
        if origin and not valid_origin:
            return reply({'detail': 'qa_extension_origin_required'}, 403)
        if request.method == 'OPTIONS':
            if not valid_origin:
                return reply({'detail': 'qa_extension_origin_required'}, 403)
            return cors(Response(status_code=204, headers={'Access-Control-Allow-Methods':'GET, POST, OPTIONS', 'Access-Control-Allow-Headers':'Authorization, Content-Type'}))
        path = request.url.path
        if path == '/desktop/qa/pair' and request.method == 'POST':
            if not valid_origin:
                return reply({'detail':'qa_extension_origin_required'},403)
            body = await request.body()
            if len(body)>2048:
                return reply({'detail':'request_too_large'},413)
            try:
                data = await request.json()
                code = data.get('code', '')
                if not isinstance(code,str) or not self.code or not secrets.compare_digest(code,self.code):
                    return reply({'detail':'Código inválido, já usado ou revogado. Gere outro no Desktop.'},401)
            except (ValueError, AttributeError):
                return reply({'detail':'invalid_request'},400)
            self.code = None
            token = secrets.token_urlsafe(32)
            self.tokens[token] = origin
            return reply({'token':token, 'scope':'qa', 'apiBase':self.runtime.origin+'/desktop/qa'})
        token = request.headers.get('authorization','').removeprefix('Bearer ')
        bound = self.tokens.get(token)
        if not bound or (origin and bound != origin):
            return reply({'detail':'Pareamento expirado. Reconecte a extensão ao Desktop.'},401)
        if path == '/desktop/qa/projects' and request.method == 'GET':
            dbmod = self.runtime.existing
            with dbmod.SessionLocal() as db:
                projects = db.query(dbmod.Project).all()
                return reply([{'id':p.id,'name':p.name} for p in projects if p.storage_kind!='device'])
        match = re.fullmatch(r'/desktop/qa/api/projects/(\d+)/qa/(annotations|text/polish)',path)
        if not match or request.method not in (('GET','POST') if match[2]=='annotations' else ('POST',)):
            return reply({'detail':'qa_scope_denied'},403)
        # Only the allowlisted QA routes receive the internal API credential.
        request.scope['path'] = '/api/projects/'+match[1]+'/qa/'+match[2]
        request.scope['raw_path'] = request.scope['path'].encode()
        request.scope['headers'] = [(k,v) for k,v in request.scope['headers'] if k not in (b'authorization',b'cookie',b'origin')]+[(b'authorization',('Bearer '+self.runtime.existing.API_KEY).encode())]
        return cors(await call_next(request))
