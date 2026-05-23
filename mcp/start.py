"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.getenv('PORT', '8000')}", flush=True)

try:
    from server import mcp

    if hasattr(mcp, "settings"):
        s = mcp.settings
        print(f"settings: host={getattr(s,'host','?')} port={getattr(s,'port','?')}", flush=True)

    mcp.run(transport="streamable-http")

except BaseException as e:
    print(f"ERRO: {type(e).__name__}: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.exit(1)
