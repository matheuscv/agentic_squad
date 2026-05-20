"""Middleware que injeta `request_id` em ContextVars e mede duração da requisição.

Comportamento:
- Lê `X-Request-ID` do header; se ausente, gera um UUID4.
- Publica o valor em `request_id_ctx` (e `user_id_ctx` se `request.state.user_id`
  já tiver sido populado por uma dependência de autenticação anterior).
- Mede duração em milissegundos usando `time.perf_counter`.
- Emite UM log INFO ao final com extras estruturados.
- Sempre escreve o header `X-Request-ID` na resposta.
- Em caso de exceção dentro do app, ainda emite log de saída (status 500) e
  re-levanta — nunca engole silenciosamente.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import request_id_ctx, user_id_ctx

logger = logging.getLogger(__name__)

_HEADER_REQUEST_ID = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware HTTP que propaga request_id e loga métricas básicas."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 1) Resolução do request_id: header do cliente tem prioridade para
        #    permitir correlação ponta-a-ponta com sistemas upstream.
        incoming = request.headers.get(_HEADER_REQUEST_ID)
        rid = incoming if incoming else uuid.uuid4().hex

        # 2) Publica em ContextVars. Guardamos o token para um reset limpo
        #    no finally (boa prática para evitar vazamento entre requisições
        #    quando o servidor reusa worker tasks).
        rid_token = request_id_ctx.set(rid)

        # `request.state.user_id` é convenção: dependências de auth (quando
        # existirem) podem setar este atributo. Aqui apenas propagamos se já
        # estiver presente — não bloqueamos requisições anônimas.
        user_id_value = getattr(request.state, "user_id", None)
        uid_token = user_id_ctx.set(user_id_value) if user_id_value is not None else None

        start = time.perf_counter()
        status_code = 500  # default pessimista — sobrescrito em caso de sucesso
        response: Response | None = None
        error: BaseException | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except BaseException as exc:  # noqa: BLE001 — re-levantamos abaixo
            # Capturamos para emitir log de saída e devolver controle ao
            # handler de exceções do FastAPI (TASK-03/04). Não engolimos.
            error = exc
            raise
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)

            # Resolve a rota lógica (template) quando disponível; fallback no path bruto.
            route_obj = request.scope.get("route")
            route_path = getattr(route_obj, "path", None) or request.url.path

            extra = {
                "request_id": rid,
                "user_id": user_id_ctx.get(),
                "route": route_path,
                "method": request.method,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }

            if error is not None:
                # Log de erro com stack trace; o handler global ainda decide
                # o payload retornado ao cliente.
                logger.error(
                    "request finalizada com exceção", extra=extra, exc_info=error
                )
            else:
                logger.info("request finalizada", extra=extra)

            # Sempre devolve o header com o request_id (mesmo em erro, se
            # houver response). Em caso de exceção sem response, o handler
            # global cuidará da resposta — mas ainda assim setamos no objeto
            # caso ele exista.
            if response is not None:
                response.headers[_HEADER_REQUEST_ID] = rid

            # Reset dos ContextVars para não vazar entre requisições.
            request_id_ctx.reset(rid_token)
            if uid_token is not None:
                user_id_ctx.reset(uid_token)
