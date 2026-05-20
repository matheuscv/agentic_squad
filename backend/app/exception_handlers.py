"""Handlers globais de exceção para a aplicação FastAPI.

Este módulo expõe a função :func:`register_exception_handlers` que conecta a
hierarquia de erros de domínio definida em :mod:`app.exceptions` ao FastAPI,
convertendo cada classe na resposta HTTP semanticamente correta e emitindo
log estruturado correlacionado pelo ``request_id`` propagado em ContextVar.

Princípios:

- **Nenhum traceback é exposto ao cliente.** Stack trace só vai para o log
  (via ``exc_info=True``). O payload visível em ``Exception`` genérico é
  sempre ``{"detail": "Erro interno do servidor."}``.
- Cada handler delega a resolução do ``request_id`` ao
  :func:`app.logging_config.get_request_id` — não há leitura do header aqui.
- O módulo NÃO chama ``app.add_exception_handler`` em escopo de import; tudo
  acontece dentro de :func:`register_exception_handlers` para que o
  wiring permaneça explícito em ``main.py`` (TASK-04).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from app.logging_config import get_request_id

logger = logging.getLogger(__name__)


def _build_payload(exc: DomainError) -> dict[str, Any]:
    """Monta o payload de resposta a partir de uma exceção de domínio.

    Inclui a chave ``details`` apenas quando há conteúdo, evitando poluir o
    contrato HTTP com campos vazios.
    """
    payload: dict[str, Any] = {"detail": exc.message}
    if exc.details:
        payload["details"] = exc.details
    return payload


async def _handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    # 4xx esperado pelo cliente — nível warning (não é falha do servidor).
    logger.warning(
        "NotFoundError em %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(status_code=exc.http_status, content=_build_payload(exc))


async def _handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
    logger.warning(
        "ConflictError em %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(status_code=exc.http_status, content=_build_payload(exc))


async def _handle_validation(request: Request, exc: ValidationError) -> JSONResponse:
    logger.warning(
        "ValidationError em %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(status_code=exc.http_status, content=_build_payload(exc))


async def _handle_authentication(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    logger.warning(
        "AuthenticationError em %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(status_code=exc.http_status, content=_build_payload(exc))


async def _handle_authorization(
    request: Request, exc: AuthorizationError
) -> JSONResponse:
    logger.warning(
        "AuthorizationError em %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(status_code=exc.http_status, content=_build_payload(exc))


async def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    # DomainError "puro" (sem subclasse específica) indica uma violação de
    # regra de domínio não categorizada — registramos com stack trace porque
    # geralmente sinaliza ponto de modelagem que merece análise.
    logger.error(
        "DomainError em %s %s: %s",
        request.method,
        request.url.path,
        exc.message,
        exc_info=True,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(status_code=exc.http_status, content=_build_payload(exc))


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    # Qualquer exceção não capturada pelos handlers acima. Logamos com stack
    # trace completo, mas o cliente recebe APENAS uma mensagem genérica para
    # evitar vazamento de detalhes internos (paths, classes, tracebacks).
    logger.error(
        "Exceção não tratada em %s %s",
        request.method,
        request.url.path,
        exc_info=True,
        extra={"request_id": get_request_id()},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers globais de exceção na aplicação FastAPI.

    A ordem de registro segue do mais específico ao mais genérico. O FastAPI
    faz dispatch pela classe exata da exceção (com fallback para a
    superclasse mais próxima), então registrar ``DomainError`` depois das
    subclasses garante que apenas instâncias puras de ``DomainError``
    caem no handler-fallback de 400.
    """
    app.add_exception_handler(NotFoundError, _handle_not_found)
    app.add_exception_handler(ConflictError, _handle_conflict)
    app.add_exception_handler(ValidationError, _handle_validation)
    app.add_exception_handler(AuthenticationError, _handle_authentication)
    app.add_exception_handler(AuthorizationError, _handle_authorization)
    app.add_exception_handler(DomainError, _handle_domain_error)
    # Fallback geral — qualquer Exception não capturada acima vira 500.
    app.add_exception_handler(Exception, _handle_unexpected)


__all__ = ["register_exception_handlers"]
