"""
Módulo dedicado ao Limiter do slowapi.

Isolado em módulo próprio para evitar import circular entre main.py e auth.py:
  main.py importa app do FastAPI e registra o limiter no app.state
  auth.py importa o limiter para aplicar o decorator @limiter.limit
  Se ambos importassem de main.py, haveria ciclo de importação.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Permite desabilitar o rate limiting via variável de ambiente.
# Usar RATELIMIT_ENABLED=false em ambientes de teste para não interferir
# nos testes de autenticação.
_enabled = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
