"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from server import mcp  # noqa: E402
import uvicorn          # noqa: E402

port = int(os.getenv("PORT", "8001"))

# Tenta os métodos conhecidos do FastMCP para obter o ASGI app
if hasattr(mcp, "streamable_http_app"):
    asgi_app = mcp.streamable_http_app()
elif hasattr(mcp, "http_app"):
    asgi_app = mcp.http_app()
elif hasattr(mcp, "get_asgi_app"):
    asgi_app = mcp.get_asgi_app()
else:
    print("ERRO: nenhum método ASGI encontrado no FastMCP.", flush=True)
    print(f"Métodos disponíveis: {[m for m in dir(mcp) if not m.startswith('_')]}", flush=True)
    sys.exit(1)

uvicorn.run(asgi_app, host="0.0.0.0", port=port)
