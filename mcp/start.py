"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.getenv('PORT', '8001')}", flush=True)

try:
    from server import mcp
    print("servidor importado com sucesso", flush=True)

    port = int(os.getenv("PORT", "8001"))
    print(f"iniciando mcp.run() na porta {port}...", flush=True)

    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)

except BaseException as e:
    # Imprime para stdout (não stderr) para aparecer nos logs do Render
    print(f"ERRO: {type(e).__name__}: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    sys.exit(1)
