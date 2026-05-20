"""
Testes do RequestContextMiddleware — TASK-06.

Cobre:
- Geração de X-Request-ID quando o cliente não envia o header.
- Propagação fiel do X-Request-ID quando o cliente envia.
- Disponibilidade do request_id via ContextVar (request_id_ctx) dentro
  do handler da rota.
- Emissão de log estruturado com extras: request_id, route, status_code,
  duration_ms.

Estratégia:
- Cada teste monta um FastAPI() mínimo isolado com o middleware aplicado
  e uma rota dummy. Não dependemos da fixture `client` (que carrega o app
  real) para evitar interferência de outros middlewares/routers da app.
- Sem fixtures de banco — middleware é stateless.

Padrão: AAA (Arrange / Act / Assert).
"""

import logging
import re
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.logging_config import request_id_ctx
from app.middleware.request_context import RequestContextMiddleware


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Aceita tanto UUID v4 canônico (com hífens) quanto o formato `hex` (32 chars
# sem hífen), porque o middleware usa `uuid.uuid4().hex`.
_UUID_HEX_RE = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)
_UUID_CANONICAL_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_uuid_like(value: str) -> bool:
    """True se o valor parece um UUID (forma hex ou canônica)."""
    if not isinstance(value, str):
        return False
    if _UUID_HEX_RE.match(value):
        return True
    if _UUID_CANONICAL_RE.match(value):
        # Sanity check com a stdlib — se o canônico passa no parser, é UUID.
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError, TypeError):
            return False
    return False


def _build_app() -> FastAPI:
    """Monta um FastAPI mínimo com o middleware e rotas dummy."""
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ping")
    def ping():
        # Rota simples que não interage com o ContextVar — usada para
        # validar header e log básico.
        return {"ok": True}

    @app.get("/whoami")
    def whoami():
        # Rota que devolve o request_id corrente lido do ContextVar.
        # Permite verificar que o middleware setou a variável ANTES de
        # despachar para o handler.
        return {"request_id": request_id_ctx.get()}

    return app


# ---------------------------------------------------------------------------
# Header de resposta — geração / propagação
# ---------------------------------------------------------------------------

def test_get_sem_header_gera_x_request_id_valido():
    """GET sem header X-Request-ID -> resposta contém um X-Request-ID UUID-like."""
    # Arrange
    app = _build_app()
    client = TestClient(app)

    # Act
    resp = client.get("/ping")

    # Assert
    assert resp.status_code == 200
    rid = resp.headers.get("X-Request-ID")
    assert rid is not None, "middleware deve sempre devolver X-Request-ID"
    assert _is_uuid_like(rid), f"X-Request-ID '{rid}' não parece UUID-like"


def test_get_com_header_x_request_id_propaga_valor():
    """GET com X-Request-ID: abc-123 -> response.headers['X-Request-ID'] == 'abc-123'."""
    # Arrange
    app = _build_app()
    client = TestClient(app)

    # Act
    resp = client.get("/ping", headers={"X-Request-ID": "abc-123"})

    # Assert
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == "abc-123"


# ---------------------------------------------------------------------------
# Propagação para o ContextVar (visível dentro do handler)
# ---------------------------------------------------------------------------

def test_request_id_ctx_disponivel_dentro_da_rota():
    """A rota dummy lê request_id_ctx.get() e devolve no body; valor bate com header."""
    # Arrange
    app = _build_app()
    client = TestClient(app)
    rid_enviado = "fixed-rid-001"

    # Act
    resp = client.get("/whoami", headers={"X-Request-ID": rid_enviado})

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert body["request_id"] == rid_enviado, (
        "request_id_ctx.get() dentro da rota deve devolver o mesmo "
        "valor que aparece no header de resposta"
    )
    assert resp.headers.get("X-Request-ID") == rid_enviado


def test_request_id_ctx_gerado_quando_header_ausente():
    """Sem header de entrada, o ContextVar deve conter o UUID gerado pelo middleware."""
    # Arrange
    app = _build_app()
    client = TestClient(app)

    # Act
    resp = client.get("/whoami")

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    rid_body = body["request_id"]
    rid_header = resp.headers.get("X-Request-ID")
    assert rid_body is not None
    assert _is_uuid_like(rid_body)
    # Header e ContextVar devem ser o mesmo valor.
    assert rid_body == rid_header


# ---------------------------------------------------------------------------
# Log estruturado emitido pelo middleware
# ---------------------------------------------------------------------------

def test_log_emitido_contem_extras_estruturados(caplog):
    """Ao bater na rota, o middleware emite log INFO com extras: request_id,
    route, status_code, duration_ms."""
    # Arrange
    app = _build_app()
    client = TestClient(app)

    # Capturamos a partir do logger do middleware. caplog instala um handler
    # propagando para o root, mas precisamos garantir nível INFO no logger
    # específico (alguns ambientes podem ter elevado o nível).
    logger_name = "app.middleware.request_context"
    with caplog.at_level(logging.INFO, logger=logger_name):
        # Act
        resp = client.get("/ping", headers={"X-Request-ID": "log-check-42"})

    # Assert — sanidade da resposta
    assert resp.status_code == 200

    # Filtra apenas os registros emitidos pelo middleware.
    middleware_records = [r for r in caplog.records if r.name == logger_name]
    assert middleware_records, (
        f"esperava ao menos 1 registro do logger '{logger_name}', "
        f"recebi: {[r.name for r in caplog.records]}"
    )

    # Pega o registro de finalização (mensagem fixa do middleware).
    finalizacao = [
        r for r in middleware_records if r.getMessage() == "request finalizada"
    ]
    assert finalizacao, "esperava registro 'request finalizada' do middleware"
    record = finalizacao[-1]

    # Extras estruturados promovidos a atributos do LogRecord.
    assert getattr(record, "request_id", None) == "log-check-42"
    assert getattr(record, "route", None) == "/ping"
    assert getattr(record, "status_code", None) == 200

    duration_ms = getattr(record, "duration_ms", None)
    assert duration_ms is not None
    assert isinstance(duration_ms, int)
    # Duração não pode ser negativa; pode ser 0 em hosts rápidos.
    assert duration_ms >= 0
