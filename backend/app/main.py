import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.exception_handlers import register_exception_handlers
from app.limiter import limiter
from app.logging_config import setup_logging
from app.middleware.request_context import RequestContextMiddleware
from app.routers.auth import router as auth_router
from app.routers.contatos import router as contatos_router
from app.routers.usuarios import router as usuarios_router

# Inicializa o logging estruturado ANTES de criar o app, para que qualquer
# logger obtido logo abaixo já herde a configuração (handlers, filtros de
# redaction e injeção de contexto). É idempotente — pode ser chamado mais
# de uma vez sem efeitos colaterais.
setup_logging(settings.env)
logger = logging.getLogger(__name__)

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
    # Tenta calcular o tempo restante até o reset; usa 60 s como fallback.
    # Estreitamos para as exceções realmente esperadas (atributo ausente
    # em `exc.limit` ou tipo inesperado em `reset_time`); qualquer outra
    # exceção deve propagar para o handler global em vez de ser engolida.
    try:
        retry_after = exc.limit.reset_time - int(time.time())
    except (AttributeError, TypeError) as exc_calc:
        logger.warning("não foi possível calcular retry_after: %s", exc_calc)
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

# RequestContextMiddleware DEVE ser registrado APÓS o CORSMiddleware.
# FastAPI/Starlette executam middlewares em ordem LIFO (último adicionado
# é o mais externo). Como queremos que o RequestContextMiddleware envolva
# TODO o ciclo da requisição — inclusive a resposta do CORS e qualquer
# erro propagado por outros middlewares — ele é o último a ser adicionado
# e, portanto, o mais externo na cadeia de execução.
app.add_middleware(RequestContextMiddleware)

# Routers de autenticação e usuários (TASK-03)
app.include_router(auth_router)
app.include_router(usuarios_router)

app.include_router(contatos_router)

# Handlers globais de exceções de domínio.
# Registrados APÓS os routers para garantir que qualquer rota registrada
# até aqui seja coberta pelos handlers (NotFoundError, ConflictError, etc.).
register_exception_handlers(app)


@app.get("/", tags=["health"])
def health_check():
    """Endpoint de verificação de saúde da API."""
    return {"status": "ok", "version": app.version}
