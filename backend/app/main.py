import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter
from app.routers.auth import router as auth_router
from app.routers.usuarios import router as usuarios_router
from app.routers.contatos import router as contatos_router

app = FastAPI(
    title="API Manutenção de Contatos",
    version="1.0.0",
    description="Backend para gerenciamento de contatos de clientes.",
)

# -----------------------------------------------------------------------
# Rate limiting — slowapi
# O limiter é instanciado em app/limiter.py para evitar import circular.
# -----------------------------------------------------------------------

# Registrar o limiter no estado do app (exigido pelo slowapi)
app.state.limiter = limiter


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handler customizado para HTTP 429.
    Retorna mensagem em PT-BR e inclui o header Retry-After.
    """
    # Tenta calcular o tempo restante até o reset; usa 60 s como fallback
    try:
        retry_after = exc.limit.reset_time - int(time.time())
    except Exception:
        retry_after = 60

    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas tentativas. Tente novamente em 1 minuto."},
        headers={"Retry-After": str(max(retry_after, 1))},
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# CORS: permite apenas a origem do frontend em desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de autenticação e usuários (TASK-03)
app.include_router(auth_router)
app.include_router(usuarios_router)

app.include_router(contatos_router)


@app.get("/", tags=["health"])
def health_check():
    """Endpoint de verificação de saúde da API."""
    return {"status": "ok", "version": app.version}
