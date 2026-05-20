"""
Testes do `RedactionFilter` — TASK-07 (B.1, RF-08, RNF-04, CA-10).

Garantem que valores associados a chaves sensíveis (`password`, `senha`,
`token`, `authorization`, etc.) são mascarados como `"***"` antes da
serialização final do log, tanto em estruturas planas quanto aninhadas, e
que a string clara de uma senha sintética não aparece em nenhum log
emitido durante uma chamada real ao endpoint `/auth/login`.

Padrão: AAA (Arrange / Act / Assert).

NOTAS de segurança:
- Strings sintéticas curtas, propositalmente óbvias (ex.: "segredo123").
- Nenhum PAN/CVV — este projeto não é CDE.
- Não modifica o `conftest.py` global; usa apenas a fixture `client`
  e fixtures locais a este arquivo.
"""

from __future__ import annotations

import json
import logging

import pytest

from app.logging_config import (
    ContextFilter,
    RedactionFilter,
    setup_logging,
)


# ---------------------------------------------------------------------------
# Helpers locais
# ---------------------------------------------------------------------------


def _make_record(
    msg: str,
    args,
    *,
    name: str = "test.redaction",
    level: int = logging.INFO,
) -> logging.LogRecord:
    """
    Constrói um `LogRecord` cru, sem passar pelo logger global.
    Evita efeitos colaterais (handlers/filtros raiz) no teste unitário.
    """
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=args,
        exc_info=None,
    )


# ---------------------------------------------------------------------------
# Unit 1 — chave `password` em dict plano via record.args
# ---------------------------------------------------------------------------


def test_redaction_mascarar_password_em_args_plano():
    """
    Cenário do plano TASK-07: args={"password": "minha-senha", "user": "joao"}.
    Após filter.filter(record), record.args["password"] == "***" e
    record.args["user"] permanece "joao".
    """
    # Arrange
    filter_ = RedactionFilter()
    # args envelopado em tupla 1-elemento: o stdlib `logging.LogRecord`
    # desempacota automaticamente quando é (mapping,), preservando
    # record.args como dict para as asserções abaixo. Necessário em
    # Python 3.13, que rejeita mapping direto quando msg tem %s posicional.
    record = _make_record(
        msg="login=%s",
        args=({"password": "minha-senha", "user": "joao"},),
    )

    # Act
    resultado = filter_.filter(record)

    # Assert
    assert resultado is True, "RedactionFilter sempre deve deixar o log passar"
    assert isinstance(record.args, dict)
    assert record.args["password"] == "***"
    assert record.args["user"] == "joao"
    # Garantia extra: o valor original NUNCA pode estar no record final.
    assert "minha-senha" not in json.dumps(record.args)


# ---------------------------------------------------------------------------
# Unit 2 — estrutura aninhada com chave `token`
# ---------------------------------------------------------------------------


def test_redaction_mascarar_token_em_estrutura_aninhada():
    """
    Recursão: {"data": {"token": "abc"}} deve virar {"data": {"token": "***"}}.
    Chaves irmãs não-sensíveis permanecem intactas.
    """
    # Arrange
    filter_ = RedactionFilter()
    payload = {"data": {"token": "abc", "user_id": 42}}
    # Envelopa payload em tupla 1-elemento — ver nota em
    # test_redaction_mascarar_password_em_args_plano sobre Python 3.13.
    record = _make_record(msg="payload=%s", args=(payload,))

    # Act
    filter_.filter(record)

    # Assert
    assert record.args == {"data": {"token": "***", "user_id": 42}}
    assert "abc" not in json.dumps(record.args)


# ---------------------------------------------------------------------------
# Unit 3 — múltiplas chaves + case-insensitive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "chave_sensivel",
    ["password", "Password", "PASSWORD", "senha", "SENHA",
     "authorization", "Authorization", "AUTHORIZATION",
     "token", "access_token", "refresh_token", "secret"],
)
def test_redaction_chaves_sensiveis_case_insensitive(chave_sensivel: str):
    """
    Toda chave declarada como sensível em `_SENSITIVE_KEYS` deve ser
    mascarada independentemente do casing (PCI DSS Req 3.3.1 — segredos
    nunca em log claro).
    """
    # Arrange
    filter_ = RedactionFilter()
    valor_secreto = "valor-secreto-X"
    # Envelopa em tupla 1-elemento por compat com Python 3.13 (ver outras notas).
    record = _make_record(
        msg="evento=%s",
        args=({chave_sensivel: valor_secreto, "campo_publico": "ok"},),
    )

    # Act
    filter_.filter(record)

    # Assert
    assert record.args[chave_sensivel] == "***", (
        f"Chave '{chave_sensivel}' deveria ter sido mascarada"
    )
    assert record.args["campo_publico"] == "ok"
    assert valor_secreto not in json.dumps(record.args)


# ---------------------------------------------------------------------------
# Unit 4 — fallback puramente unitário do cenário de integração
# (garante que mesmo sem subir o app, a string clara da senha some)
# ---------------------------------------------------------------------------


def test_redaction_payload_login_unitario_nao_vaza_senha():
    """
    Fallback do cenário de integração: simula o payload típico de POST
    /auth/login passando-o como `args` de um LogRecord. A string clara
    `"segredo123"` NÃO pode permanecer no record após o filtro.
    """
    # Arrange
    filter_ = RedactionFilter()
    # Envelopa em tupla 1-elemento por compat com Python 3.13 (ver outras notas).
    record = _make_record(
        msg="login payload=%s",
        args=({"email": "x@y.com", "password": "segredo123"},),
    )

    # Act
    filter_.filter(record)

    # Assert
    # Serialização defensiva: cobre dict, list, tuple, str.
    serializado = json.dumps(record.args)
    assert "segredo123" not in serializado
    assert record.args["password"] == "***"
    # E-mail não é chave sensível listada — permanece como está.
    assert record.args["email"] == "x@y.com"


# ---------------------------------------------------------------------------
# Unit 5 — extras promovidos ao LogRecord (logger.x("msg", extra={...}))
# ---------------------------------------------------------------------------


def test_redaction_mascarar_extras_promovidos_ao_record():
    """
    `logging` copia chaves de `extra=` direto como atributos do LogRecord.
    O `RedactionFilter` deve mascarar atributos cujo nome esteja na lista
    de chaves sensíveis (ex.: logger.info("x", extra={"password": "..."} )).
    """
    # Arrange
    filter_ = RedactionFilter()
    record = _make_record(msg="evento", args=None)
    # Simula o que `logging` faz com `extra={"password": ..., "token": ...}`.
    record.password = "abc123"           # type: ignore[attr-defined]
    record.token = "tok-xyz"             # type: ignore[attr-defined]
    record.user_id = "42"                # type: ignore[attr-defined]  (não sensível)

    # Act
    filter_.filter(record)

    # Assert
    assert record.password == "***"      # type: ignore[attr-defined]
    assert record.token == "***"         # type: ignore[attr-defined]
    assert record.user_id == "42"        # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Integração — POST /auth/login não vaza a senha sintética em nenhum log
# ---------------------------------------------------------------------------


@pytest.fixture()
def _logging_configurado():
    """
    Garante que `setup_logging` foi chamado em modo `development` e que o
    `RedactionFilter` está anexado ao handler do logger raiz. Idempotente
    por design.
    """
    setup_logging("development")
    yield


def test_redaction_endpoint_login_nao_vaza_senha_em_caplog(
    client, _logging_configurado, caplog
):
    """
    Faz POST /auth/login com uma senha sintética e garante que NENHUM
    registro capturado por `caplog` (LogRecord.getMessage e args) contém
    a string clara `"segredo123"`.

    Decisão conservadora: o teste não falha se o endpoint retornar 401
    (o objetivo aqui é apenas garantir que a senha não vaze em log,
    não validar a autenticação em si). Cobertura de auth feliz/triste
    é responsabilidade de `test_auth.py`.
    """
    # Arrange
    senha_sintetica = "segredo123"
    # Criamos primeiro o usuário com a senha sintética, para que o login
    # exercite tanto o caminho feliz quanto o caminho de log mais rico
    # (ex.: "login realizado usuario_id=...").
    client.post(
        "/usuarios/",
        json={
            "nome": "Redact User",
            "email": "redact@test.com",
            "senha": senha_sintetica,
        },
    )

    caplog.clear()
    # Captura desde INFO; o nível raiz definido por setup_logging é INFO.
    with caplog.at_level(logging.INFO):
        # Act
        resp = client.post(
            "/auth/login",
            json={"email": "redact@test.com", "senha": senha_sintetica},
        )

    # Assert
    # Sanidade: a chamada foi processada (200 happy path; 401 ainda é
    # aceitável para a meta deste teste — não vazar a senha).
    assert resp.status_code in (200, 401), (
        f"Status inesperado: {resp.status_code} body={resp.text}"
    )

    # NENHUM record capturado pode conter a string clara da senha.
    # Verificamos em três superfícies: mensagem formatada, args crus e
    # atributos promovidos do record (extras).
    for record in caplog.records:
        # 1) Mensagem final formatada.
        mensagem_formatada = record.getMessage()
        assert senha_sintetica not in mensagem_formatada, (
            f"Senha vazou em record.getMessage(): {mensagem_formatada!r}"
        )

        # 2) record.args como dict/tupla — checamos via JSON defensivo.
        if record.args is not None:
            try:
                args_serializados = json.dumps(record.args, default=str)
            except (TypeError, ValueError):
                args_serializados = repr(record.args)
            assert senha_sintetica not in args_serializados, (
                f"Senha vazou em record.args: {args_serializados!r}"
            )

        # 3) Atributos promovidos via `extra=` (ex.: record.password).
        for atributo in ("password", "senha", "token", "authorization", "secret"):
            valor = getattr(record, atributo, None)
            if valor is not None:
                assert valor == "***", (
                    f"Atributo sensível '{atributo}' não foi mascarado: {valor!r}"
                )


# ---------------------------------------------------------------------------
# Sanidade — ContextFilter não interfere no redaction
# ---------------------------------------------------------------------------


def test_context_filter_nao_quebra_redaction():
    """
    Quando ambos os filtros estão ativos (ContextFilter + RedactionFilter),
    a mascaração continua sendo aplicada e os campos de contexto não
    introduzem chaves sensíveis no record.
    """
    # Arrange
    ctx = ContextFilter()
    red = RedactionFilter()
    # Envelopa em tupla 1-elemento por compat com Python 3.13 (ver outras notas).
    record = _make_record(
        msg="evento=%s",
        args=({"password": "abc", "ok": 1},),
    )

    # Act — ordem importa pouco aqui pois os filtros atuam em campos
    # disjuntos, mas testamos a sequência usada pelo handler real.
    ctx.filter(record)
    red.filter(record)

    # Assert
    assert record.args["password"] == "***"
    assert record.args["ok"] == 1
    # ContextFilter sempre define request_id / user_id (podem ser None
    # quando não há contexto ativo).
    assert hasattr(record, "request_id")
    assert hasattr(record, "user_id")
