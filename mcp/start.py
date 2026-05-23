"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys
import traceback

# Configurar FastMCP ANTES de importar server.py (que instancia FastMCP)
# FastMCP lê settings via pydantic-settings com prefixo FASTMCP_
port_str = os.getenv("PORT", "8001")
os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
os.environ.setdefault("FASTMCP_PORT", port_str)

sys.path.insert(0, os.path.dirname(__file__))

print(f"Python: {sys.version}", flush=True)
print(f"PORT (Render): {port_str}", flush=True)
print(f"FASTMCP_HOST: {os.environ['FASTMCP_HOST']}", flush=True)
print(f"FASTMCP_PORT: {os.environ['FASTMCP_PORT']}", flush=True)

try:
    from server import mcp
    print("mcp importado", flush=True)

    if hasattr(mcp, "settings"):
        s = mcp.settings
        print(f"settings: host={getattr(s,'host','?')} port={getattr(s,'port','?')}", flush=True)

    print("chamando mcp.run(transport=streamable-http)...", flush=True)
    mcp.run(transport="streamable-http")

except BaseException as e:
    print(f"ERRO: {type(e).__name__}: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.exit(1)
