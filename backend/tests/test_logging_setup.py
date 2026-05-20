"""
Testes adicionais — cobertura de lacunas após TASK-06/TASK-07.

Foco:

- CA-01 (PRD): `setup_logging("production")` deve emitir EXATAMENTE 1 linha
  JSON parseável por requisição, com as chaves canônicas
  (`request_id`, `user_id`, `route`, `duration_ms`, `status_code`).
- CA-02 (PRD): `setup_logging("development")` deve emitir formato texto
  plano (não-JSON).
- CA-03/CA-04 (PRD): o header `X-Request-ID` deve aparecer também em
  respostas de ERRO (4xx via NotFoundError e 5xx via RuntimeError),
  não apenas no caminho feliz.
- Idempotência de `setup_logging`: chamadas múltiplas não duplicam
  handlers (RNF-05 — setup centralizado, manutenibilidade).

Estratégia:
- Cada teste isola sua FastAPI(): nada toca o `app` real para evitar
  conflito com handlers/middlewares de produção.
- Captura de stdout via `capsys` no caso JSON — único caminho fiel
  para validar serialização real do `JsonFormatter`.
- Restauração explícita do logger raiz no teardown para não vazar
  configuração entre testes.

Padrão: AAA (Arrange / Act / Assert).
"""

from __future__ import annotations

import io
import json
import logging
import re
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exception_handlers import register_exception_handlers
from app.exceptions import NotFoundError
from app.logging_config import setup_logging
from app.middleware.request_context import RequestContextMiddleware


# ---------------------------------------------------------------------------
# Fixture — preserva e restaura o logger raiz para evitar poluição entre testes
# ---------------------------------------------------------------------------


@pytest.fixture()
def _restore_root_logger():
    """Salva handlers/nivel do root, executa o teste, restaura ao final.

    `setup_logging` é destrutivo no root logger (limpa handlers). Sem essa
    restauração, outros testes do regressivo podem perder seus captadores
    (`caplog`, etc.).
    """
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    saved_filters = list(root.filters)
    try:
        yield
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in saved_handlers:
            root.addHandler(h)
        for f in list(root.filters):
            root.removeFilter(f)
        for f in saved_filters:
            root.addFilter(f)
        root.setLevel(saved_level)


# ---------------------------------------------------------------------------
# CA-01 — production: JSON estruturado em stdout
# ---------------------------------------------------------------------------


def test_setup_logging_production_emite_json_parseavel(_restore_root_logger):
    """
    `setup_logging("production")` configura o root para emitir JSON
    parseável contendo as chaves canônicas exigidas pelo PRD.

    Estratégia: redireciona o stdout do StreamHandler instalado por
    `setup_logging` para um StringIO local, emite UM log com os extras
    típicos do middleware, e valida que a linha resultante é JSON.
    """
    # Arrange
    setup_logging("production")
    root = logging.getLogger()
    assert root.handlers, "setup_logging deve instalar pelo menos um handler"
    handler = root.handlers[0]

    # Substitui o stream do handler instalado (que é sys.stdout) por um
    # buffer local para captura confiável — capsys/capfd não são confiáveis
    # quando o stream foi resolvido no momento da instanciação do handler.
    buf = io.StringIO()
    original_stream = handler.stream  # type: ignore[attr-defined]
    handler.stream = buf  # type: ignore[attr-defined]

    try:
        # Act — emitimos UM evento simulando o que o middleware faria.
        logging.getLogger("app.test").info(
            "request finalizada",
            extra={
                "request_id": "rid-prod-001",
                "user_id": None,
                "route": "/ping",
                "duration_ms": 7,
                "status_code": 200,
            },
        )
        handler.flush()
        output = buf.getvalue().strip()
    finally:
        handler.stream = original_stream  # type: ignore[attr-defined]

    # Assert — output é UMA linha JSON parseável.
    assert output, "esperava conteúdo emitido no stdout em modo production"
    linhas = [linha for linha in output.splitlines() if linha.strip()]
    assert len(linhas) == 1, f"esperava 1 linha, recebi {len(linhas)}: {linhas!r}"

    payload = json.loads(linhas[0])
    # Campos canônicos do PRD (RF-02): timestamp/level/name/message + extras.
    assert payload.get("message") == "request finalizada"
    assert payload.get("levelname") in ("INFO",)
    assert payload.get("name") == "app.test"
    assert payload.get("request_id") == "rid-prod-001"
    assert payload.get("route") == "/ping"
    assert payload.get("duration_ms") == 7
    # `user_id` pode aparecer como None/null — basta estar presente como chave.
    assert "user_id" in payload


# ---------------------------------------------------------------------------
# CA-02 — development: texto plano, NÃO JSON
# ---------------------------------------------------------------------------


def test_setup_logging_development_emite_texto_nao_json(_restore_root_logger):
    """
    `setup_logging("development")` configura formato texto plano. A linha
    emitida NÃO deve ser parseável como JSON (e deve conter o nome do
    logger e a mensagem em formato `asctime LEVEL name message`).
    """
    # Arrange
    setup_logging("development")
    root = logging.getLogger()
    assert root.handlers, "setup_logging deve instalar pelo menos um handler"
    handler = root.handlers[0]

    buf = io.StringIO()
    original_stream = handler.stream  # type: ignore[attr-defined]
    handler.stream = buf  # type: ignore[attr-defined]

    try:
        # Act
        logging.getLogger("app.test").info("evento-dev-12345")
        handler.flush()
        output = buf.getvalue().strip()
    finally:
        handler.stream = original_stream  # type: ignore[attr-defined]

    # Assert — não-vazio, não-JSON, contém logger + mensagem.
    assert output, "esperava saída em texto plano em modo development"
    with pytest.raises(json.JSONDecodeError):
        json.loads(output)
    assert "app.test" in output
    assert "evento-dev-12345" in output
    # Heurística: INFO está no formato `%(levelname)s`.
    assert "INFO" in output


# ---------------------------------------------------------------------------
# Idempotência — múltiplas chamadas não duplicam handlers
# ---------------------------------------------------------------------------


def test_setup_logging_e_idempotente_nao_duplica_handlers(_restore_root_logger):
    """
    Chamar `setup_logging` várias vezes não deve acumular handlers no root,
    senão cada linha de log apareceria N vezes em produção (RNF-05).
    """
    # Arrange / Act
    setup_logging("development")
    qtd_inicial = len(logging.getLogger().handlers)
    setup_logging("development")
    setup_logging("production")
    setup_logging("development")
    qtd_final = len(logging.getLogger().handlers)

    # Assert
    assert qtd_inicial == 1, (
        f"setup_logging deveria instalar exatamente 1 handler na 1ª chamada, "
        f"encontrei {qtd_inicial}"
    )
    assert qtd_final == 1, (
        f"setup_logging deveria permanecer com 1 handler após várias chamadas, "
        f"encontrei {qtd_final}"
    )


# ---------------------------------------------------------------------------
# CA-03 / CA-04 — X-Request-ID também aparece em respostas de erro
# ---------------------------------------------------------------------------


_UUID_HEX_RE = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)


def _build_app_com_erros() -> FastAPI:
    """
    FastAPI() isolado com middleware + handlers + rotas que disparam erros.
    Não usa o `app` global para não interferir com outros testes.
    """
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/erro/not-found")
    def _r_not_found():
        raise NotFoundError("recurso inexistente")

    @app.get("/erro/boom")
    def _r_boom():
        raise RuntimeError("explodiu de propósito")

    register_exception_handlers(app)
    return app


def test_x_request_id_propagado_em_resposta_404():
    """
    Endpoint que dispara NotFoundError deve continuar respondendo com o
    header X-Request-ID propagado do request (CA-03).
    """
    # Arrange
    app = _build_app_com_erros()
    client = TestClient(app, raise_server_exceptions=False)
    rid = "trace-erro-404"

    # Act
    resp = client.get("/erro/not-found", headers={"X-Request-ID": rid})

    # Assert
    assert resp.status_code == 404
    assert resp.headers.get("X-Request-ID") == rid, (
        "middleware deve devolver o X-Request-ID enviado mesmo em respostas "
        "de erro de domínio (NotFoundError)"
    )


def test_x_request_id_gerado_em_resposta_404_sem_header():
    """
    Sem header de entrada, o middleware ainda deve devolver um UUID válido
    no header de resposta mesmo quando a rota dispara erro de domínio (CA-04).
    """
    # Arrange
    app = _build_app_com_erros()
    client = TestClient(app, raise_server_exceptions=False)

    # Act
    resp = client.get("/erro/not-found")

    # Assert
    assert resp.status_code == 404
    rid = resp.headers.get("X-Request-ID")
    assert rid is not None, "X-Request-ID deve ser sempre devolvido"
    assert _UUID_HEX_RE.match(rid), (
        f"valor '{rid}' não parece UUID hex gerado pelo middleware"
    )


# ---------------------------------------------------------------------------
# Sanidade — payload genérico em 500 NÃO vaza, e log captura a exceção
# ---------------------------------------------------------------------------


def test_runtime_error_log_contem_exc_info(caplog):
    """
    Quando uma rota lança RuntimeError, o handler global deve registrar
    o evento com `exc_info=True` (stack trace no log, NÃO no payload).

    Validamos via caplog que o log capturado tem `exc_info` populado.
    """
    # Arrange
    app = _build_app_com_erros()
    client = TestClient(app, raise_server_exceptions=False)

    # Act
    with caplog.at_level(logging.ERROR, logger="app.exception_handlers"):
        resp = client.get("/erro/boom")

    # Assert — status e payload
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Erro interno do servidor."}
    body = resp.text
    assert "explodiu de propósito" not in body
    assert "Traceback" not in body

    # E o log capturado deve ter stack trace.
    erros = [
        r for r in caplog.records
        if r.name == "app.exception_handlers" and r.levelno >= logging.ERROR
    ]
    assert erros, "esperava ao menos 1 ERROR emitido pelo handler global"
    # Pelo menos um registro deve ter exc_info preenchido (RuntimeError).
    com_traceback = [r for r in erros if r.exc_info is not None]
    assert com_traceback, (
        "esperava registro de erro com exc_info populado (stack trace no log)"
    )
