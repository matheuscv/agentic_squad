"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.getenv('PORT', '8000')}", flush=True)

try:
    import uvicorn
    from starlette.responses import Response as StarletteResponse
    from server import mcp

    MCP_API_KEY = os.getenv("MCP_API_KEY")

    if MCP_API_KEY:
        print("API key auth ativada.", flush=True)
    else:
        print("AVISO: MCP_API_KEY não definida — endpoint público!", flush=True)

    class _APIKeyMiddleware:
        """ASGI middleware que exige Bearer token quando MCP_API_KEY está definida."""

        def __init__(self, app):
            self._app = app

        async def __call__(self, scope, receive, send):
            if MCP_API_KEY and scope["type"] == "http":
                headers = {k.lower(): v for k, v in scope.get("headers", [])}
                auth = headers.get(b"authorization", b"").decode()
                if auth != f"Bearer {MCP_API_KEY}":
                    response = StarletteResponse("Unauthorized", status_code=401)
                    await response(scope, receive, send)
                    return
            await self._app(scope, receive, send)

    starlette_app = mcp.streamable_http_app()
    app = _APIKeyMiddleware(starlette_app)

    port = int(os.getenv("PORT", "8000"))
    print(f"Iniciando uvicorn em 0.0.0.0:{port}", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port)

except BaseException as e:
    print(f"ERRO: {type(e).__name__}: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.exit(1)
