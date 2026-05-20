"""
Testes dos exception handlers globais — TASK-06.

Cobre, em um FastAPI() mínimo registrado via `register_exception_handlers`:

- NotFoundError       -> 404 {"detail": "x"}
- ConflictError       -> 409 {"detail": "y"}
- ValidationError     -> 422 {"detail": "z"}   (a de domínio, não a do Pydantic)
- AuthenticationError -> 401 {"detail": "a"}
- AuthorizationError  -> 403 {"detail": "b"}
- DomainError         -> 400 {"detail": "c"}
- RuntimeError        -> 500 {"detail": "Erro interno do servidor."}
                        (sem 'boom', sem 'Traceback' no body)
- 4xx adicional com details={"campo": "email"} exposto no payload.

Estratégia:
- Não importamos `app.main.app`: montamos um FastAPI() vazio só para o teste,
  evitando interferência de middlewares, routers e dependências reais.
- Cada subteste registra suas próprias rotas dummy num app dedicado para
  garantir isolamento.

Padrão: AAA (Arrange / Act / Assert).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exception_handlers import register_exception_handlers
from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Fixture: app mínimo com rotas dummy disparando cada exceção
# ---------------------------------------------------------------------------

@pytest.fixture()
def app_com_handlers():
    """FastAPI() mínimo com rotas que disparam cada classe de exceção.

    Registra todas as rotas dummy e o conjunto de handlers globais. Não há
    middleware, autenticação ou banco — foco exclusivo no comportamento dos
    handlers.
    """
    app = FastAPI()

    @app.get("/raise/not-found")
    def _r_not_found():
        raise NotFoundError("x")

    @app.get("/raise/conflict")
    def _r_conflict():
        raise ConflictError("y")

    @app.get("/raise/validation")
    def _r_validation():
        # Importante: é a ValidationError DE DOMÍNIO (app.exceptions),
        # não a do Pydantic. Disparada manualmente em código de service.
        raise ValidationError("z")

    @app.get("/raise/auth")
    def _r_auth():
        raise AuthenticationError("a")

    @app.get("/raise/authz")
    def _r_authz():
        raise AuthorizationError("b")

    @app.get("/raise/domain")
    def _r_domain():
        # DomainError "puro" (sem subclasse) — fallback 400.
        raise DomainError("c")

    @app.get("/raise/boom")
    def _r_boom():
        # Exceção totalmente externa à hierarquia de domínio — deve cair
        # no handler de Exception (500 com payload genérico).
        raise RuntimeError("boom")

    @app.get("/raise/with-details")
    def _r_with_details():
        # Caso 4xx adicional carregando details estruturado.
        raise ValidationError("campo inválido", {"campo": "email"})

    register_exception_handlers(app)
    return app


@pytest.fixture()
def cli(app_com_handlers):
    """TestClient sobre o app mínimo.

    `raise_server_exceptions=False` é essencial para o caso RuntimeError:
    sem isso o TestClient propaga a exceção para o teste em vez de deixar
    o handler global responder com 500.
    """
    return TestClient(app_com_handlers, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Subclasses de DomainError — mapeamento status code + payload
# ---------------------------------------------------------------------------

def test_not_found_error_responde_404(cli):
    """NotFoundError('x') -> 404 {'detail': 'x'}."""
    # Act
    resp = cli.get("/raise/not-found")

    # Assert
    assert resp.status_code == 404
    assert resp.json() == {"detail": "x"}


def test_conflict_error_responde_409(cli):
    """ConflictError('y') -> 409 {'detail': 'y'}."""
    # Act
    resp = cli.get("/raise/conflict")

    # Assert
    assert resp.status_code == 409
    assert resp.json() == {"detail": "y"}


def test_validation_error_de_dominio_responde_422(cli):
    """ValidationError('z') (de domínio) -> 422 {'detail': 'z'}."""
    # Act
    resp = cli.get("/raise/validation")

    # Assert
    assert resp.status_code == 422
    assert resp.json() == {"detail": "z"}


def test_authentication_error_responde_401(cli):
    """AuthenticationError('a') -> 401 {'detail': 'a'}."""
    # Act
    resp = cli.get("/raise/auth")

    # Assert
    assert resp.status_code == 401
    assert resp.json() == {"detail": "a"}


def test_authorization_error_responde_403(cli):
    """AuthorizationError('b') -> 403 {'detail': 'b'}."""
    # Act
    resp = cli.get("/raise/authz")

    # Assert
    assert resp.status_code == 403
    assert resp.json() == {"detail": "b"}


def test_domain_error_puro_responde_400(cli):
    """DomainError('c') sem subclasse -> 400 {'detail': 'c'}."""
    # Act
    resp = cli.get("/raise/domain")

    # Assert
    assert resp.status_code == 400
    assert resp.json() == {"detail": "c"}


# ---------------------------------------------------------------------------
# Exceção não tratada — payload genérico, sem vazamento
# ---------------------------------------------------------------------------

def test_runtime_error_responde_500_payload_generico(cli):
    """RuntimeError('boom') -> 500 com mensagem genérica e SEM vazar 'boom'/'Traceback'."""
    # Act
    resp = cli.get("/raise/boom")

    # Assert — status e payload
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Erro interno do servidor."}

    # O body não pode conter detalhes internos.
    body_text = resp.text
    assert "boom" not in body_text, (
        "mensagem original da exceção NUNCA pode vazar para o cliente"
    )
    assert "Traceback" not in body_text, (
        "stack trace NUNCA pode vazar no payload de resposta"
    )


# ---------------------------------------------------------------------------
# Campo `details` exposto quando presente
# ---------------------------------------------------------------------------

def test_4xx_com_details_expoe_no_payload(cli):
    """ValidationError('...', {'campo': 'email'}) -> payload inclui chave 'details'."""
    # Act
    resp = cli.get("/raise/with-details")

    # Assert
    assert resp.status_code == 422
    payload = resp.json()
    assert payload.get("detail") == "campo inválido"
    assert payload.get("details") == {"campo": "email"}


def test_4xx_sem_details_nao_inclui_chave(cli):
    """NotFoundError('x') sem details NÃO deve incluir a chave 'details' no payload."""
    # Act
    resp = cli.get("/raise/not-found")

    # Assert
    assert resp.status_code == 404
    payload = resp.json()
    # Contrato: chave 'details' só aparece quando há conteúdo, evitando
    # poluir respostas de erro com campos vazios.
    assert "details" not in payload
