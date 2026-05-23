"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.getenv('PORT', '8001')}", flush=True)

try:
    from server import mcp
    port = int(os.getenv("PORT", "8001"))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
except Exception:
    traceback.print_exc()
    sys.exit(1)
