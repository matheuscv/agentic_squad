"""Infraestrutura de logging estruturado para o backend.

Este módulo centraliza:
- ContextVars para propagar `request_id` e `user_id` ao longo de uma requisição
  (preenchidos pelo middleware em `app.middleware.request_context`).
- Filtros de logging:
    * `ContextFilter`  -> injeta `request_id` e `user_id` em cada LogRecord.
    * `RedactionFilter` -> mascara valores de chaves sensíveis (`password`,
      `senha`, `token`, etc.) recursivamente em dicts/listas/tuplas que
      apareçam em `record.msg` ou `record.args`.
- `setup_logging(env)` -> ponto único de configuração, idempotente.

Importante: este módulo NÃO importa `app.main` para evitar ciclos.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Context propagation
# ---------------------------------------------------------------------------

# ContextVars são propagadas naturalmente em código async (incluindo tasks
# criadas com asyncio.create_task) e por isso são o mecanismo correto para
# carregar request_id/user_id por toda a vida de uma requisição.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id_ctx", default=None)


def get_request_id() -> str | None:
    """Retorna o request_id corrente (ou None se fora de contexto de request)."""
    return request_id_ctx.get()


def get_user_id() -> str | None:
    """Retorna o user_id corrente (ou None se anônimo / fora de request)."""
    return user_id_ctx.get()


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

# Chaves que NUNCA podem aparecer em log em texto claro. Comparação
# case-insensitive (a normalização é feita no filtro).
_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "senha",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "secret",
    }
)

_REDACTED = "***"


def _is_sensitive_key(key: Any) -> bool:
    """True se a chave (case-insensitive) está na lista de chaves a mascarar."""
    if not isinstance(key, str):
        return False
    return key.lower() in _SENSITIVE_KEYS


def _redact_value(value: Any) -> Any:
    """Aplica redaction recursivamente sobre estruturas comuns.

    - dict: substitui valor por '***' quando a chave é sensível, caso
      contrário desce recursivamente no valor.
    - list/tuple: aplica recursivamente a cada elemento, preservando o tipo.
    - Outros tipos: retorna como está (strings cruas não são inspecionadas
      para 'key=value' porque isso geraria parsing arbitrário e frágil;
      o contrato esperado é que dados estruturados venham em dict/args).
    """
    if isinstance(value, dict):
        return {
            k: (_REDACTED if _is_sensitive_key(k) else _redact_value(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(v) for v in value)
    return value


class RedactionFilter(logging.Filter):
    """Mascara dados sensíveis em LogRecord antes da serialização.

    Atua sobre:
    - `record.msg`  -> se for dict (logger.info({...})) aplica recursão.
    - `record.args` -> se for dict (logger.info("login=%(user)s", {...}))
      ou tuple/list (logger.info("a=%s b=%s", (a, b))), aplica recursão.
    - Atributos extras de chaves sensíveis no próprio LogRecord
      (ex.: `logger.info("x", extra={"password": ...})`) são também
      mascarados — apenas para as chaves listadas em `_SENSITIVE_KEYS`.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        # 1) record.msg como dict
        if isinstance(record.msg, dict):
            record.msg = _redact_value(record.msg)

        # 2) record.args
        if isinstance(record.args, dict):
            record.args = _redact_value(record.args)
        elif isinstance(record.args, (list, tuple)):
            redacted = _redact_value(record.args)
            # _redact_value preserva o tipo; garantimos tuple para logging
            record.args = tuple(redacted) if isinstance(redacted, list) else redacted

        # 3) extras promovidos ao LogRecord como atributos
        #    (logging copia chaves de `extra=` direto para o record).
        for key in list(vars(record).keys()):
            if _is_sensitive_key(key):
                setattr(record, key, _REDACTED)

        # Sempre deixa o log passar; apenas reescrevemos campos sensíveis.
        return True


# ---------------------------------------------------------------------------
# Context injection
# ---------------------------------------------------------------------------


class ContextFilter(logging.Filter):
    """Injeta `request_id` e `user_id` em cada LogRecord.

    Lê os ContextVars do módulo. Caso não haja contexto ativo (ex.: log
    durante startup), os campos ficam como None — o formatter cuidará
    de serializar como `null` no JSON ou string vazia no texto.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        # Só sobrescrevemos se o atributo ainda não veio explicitamente em
        # `extra=` (preserva uso avançado).
        if not hasattr(record, "request_id"):
            record.request_id = request_id_ctx.get()
        if not hasattr(record, "user_id"):
            record.user_id = user_id_ctx.get()
        return True


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


def _clear_root_handlers(root: logging.Logger) -> None:
    """Remove handlers prévios para garantir idempotência do setup."""
    for handler in list(root.handlers):
        root.removeHandler(handler)
        # Fecha handler para não vazar file descriptors em testes.
        try:
            handler.close()
        except Exception:  # noqa: BLE001
            # Fechar handler é best-effort; se falhar, seguimos.
            # NUNCA usar `pass` silencioso — registramos via stderr cru
            # (logger não está pronto neste ponto).
            sys.stderr.write("logging_config: falha ao fechar handler antigo\n")


def _attach_filters(handler: logging.Handler) -> None:
    """Anexa filtros padrão (context + redaction) ao handler dado."""
    handler.addFilter(ContextFilter())
    handler.addFilter(RedactionFilter())


def setup_logging(env: str) -> None:
    """Configura o logger raiz conforme o ambiente.

    - `production`: JSON estruturado em stdout (pythonjsonlogger).
    - qualquer outro valor (incluindo `development`): texto plano legível
      em stdout.

    Em ambos os modos:
    - Nível raiz INFO.
    - `ContextFilter` injeta request_id/user_id.
    - `RedactionFilter` mascara chaves sensíveis.
    - Idempotente: chamadas múltiplas não duplicam handlers.
    """
    root = logging.getLogger()
    _clear_root_handlers(root)
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(stream=sys.stdout)

    if env == "production":
        # Import local evita custo no boot em DEV e protege contra
        # ausência da lib em ambientes onde ela não foi instalada ainda
        # (a importação só ocorre quando efetivamente ativamos prod).
        from pythonjsonlogger import jsonlogger

        # Formato declarativo: nomes de campos que devem aparecer no JSON.
        # `request_id`, `user_id`, `route` e `duration_ms` vêm via filter
        # (ContextFilter) ou via `extra=` no log call.
        formatter: logging.Formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s "
            "%(request_id)s %(user_id)s %(route)s %(duration_ms)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )

    handler.setFormatter(formatter)
    _attach_filters(handler)
    root.addHandler(handler)


__all__: Iterable[str] = (
    "request_id_ctx",
    "user_id_ctx",
    "get_request_id",
    "get_user_id",
    "ContextFilter",
    "RedactionFilter",
    "setup_logging",
)
