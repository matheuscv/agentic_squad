"""Bootstrap HTTP para deploy no Render — não usado em modo stdio local."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from server import mcp  # noqa: E402

port = int(os.getenv("PORT", "8001"))

# host="0.0.0.0" configura TrustedHostMiddleware com allowed_hosts=["*"]
# permitindo qualquer domínio externo (necessário para o Render)
mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
