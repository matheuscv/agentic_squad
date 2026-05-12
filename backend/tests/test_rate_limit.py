"""
Testes de rate limiting no endpoint de login — TASK-12 / RF-F3.2-02.

Cobre:
- 5 requisições consecutivas ao POST /auth/login são processadas normalmente (200 ou 401)
- A 6ª requisição dentro da mesma janela retorna HTTP 429
- Body da resposta 429: {"detail": "Muitas tentativas. Tente novamente em 1 minuto."}
- Header Retry-After presente na resposta 429
- Outros endpoints (GET /contatos/) não são afetados pelo rate limiter
- Em ambiente de testes, o reset_limiter (autouse) evita 429 entre testes distintos

Padrão: AAA (Arrange / Act / Assert)

Nota: o fixture `reset_limiter` em conftest.py é autouse=True — reseta o storage
do slowapi antes de cada teste, garantindo isolamento entre testes.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LOGIN_URL = "/auth/login"
_CREDENCIAIS_INVALIDAS = {"email": "nao@existe.com", "senha": "qualquer"}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _fazer_login(client, email: str, senha: str) -> "Response":
    return client.post(_LOGIN_URL, json={"email": email, "senha": senha})


def _criar_usuario(client, email: str, senha: str, nome: str = "Teste RL") -> None:
    client.post("/usuarios/", json={"nome": nome, "email": email, "senha": senha})


# ---------------------------------------------------------------------------
# RF-F3.2-02 — 5 tentativas dentro do limite não retornam 429
# ---------------------------------------------------------------------------

def test_cinco_tentativas_nao_retornam_429(client):
    """Arrange: nenhum usuário real; credenciais inválidas.
    Act: 5 POSTs ao /auth/login.
    Assert: todas retornam 401 (credenciais inválidas), nunca 429."""
    for _ in range(5):
        resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)
        # 401 = credenciais inválidas; qualquer coisa exceto 429 é aceita aqui
        assert resp.status_code != 429, f"Não esperado 429 dentro do limite: {resp.text}"


def test_quinta_tentativa_retorna_401_nao_429(client):
    """Arrange: 4 tentativas anteriores.
    Act: 5ª tentativa com credenciais inválidas.
    Assert: retorna 401, não 429."""
    for _ in range(4):
        _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# RF-F3.2-02 — A 6ª requisição retorna 429
# ---------------------------------------------------------------------------

def test_sexta_tentativa_retorna_429(client):
    """Arrange: 5 tentativas anteriores esgotam a cota.
    Act: 6ª tentativa.
    Assert: HTTP 429."""
    for _ in range(5):
        _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code == 429


def test_body_429_contem_mensagem_pt_br(client):
    """Arrange: 5 tentativas consomem a cota.
    Act: 6ª tentativa.
    Assert: body JSON com detail em PT-BR."""
    for _ in range(5):
        _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code == 429
    body = resp.json()
    assert "detail" in body
    assert body["detail"] == "Muitas tentativas. Tente novamente em 1 minuto."


def test_header_retry_after_presente_no_429(client):
    """Arrange: 5 tentativas consomem a cota.
    Act: 6ª tentativa.
    Assert: header Retry-After presente na resposta."""
    for _ in range(5):
        _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code == 429
    assert "retry-after" in {k.lower() for k in resp.headers.keys()}, (
        f"Header Retry-After ausente. Headers recebidos: {dict(resp.headers)}"
    )


def test_header_retry_after_valor_positivo(client):
    """Arrange: 5 tentativas consomem a cota.
    Act: 6ª tentativa.
    Assert: Retry-After contém valor inteiro >= 1."""
    for _ in range(5):
        _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code == 429
    retry_after = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    assert retry_after is not None
    assert int(retry_after) >= 1


# ---------------------------------------------------------------------------
# RF-F3.2-02 — Login bem-sucedido também conta para a cota
# ---------------------------------------------------------------------------

def test_login_bem_sucedido_conta_para_cota(client):
    """Arrange: cria usuário válido; realiza 5 logins bem-sucedidos.
    Act: 6ª tentativa (com credenciais inválidas).
    Assert: HTTP 429 — logins válidos consomem a cota (RN-F3.2-04)."""
    email = "cota@ratelimit.com"
    senha = "senha123"
    _criar_usuario(client, email, senha, nome="Cota Rate Limit")

    for _ in range(5):
        resp = _fazer_login(client, email, senha)
        assert resp.status_code == 200

    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)
    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# RF-F3.2-02 — Outros endpoints não são afetados pelo rate limiter
# ---------------------------------------------------------------------------

def test_outros_endpoints_nao_afetados_por_rate_limit(client, usuario_default_token):
    """Arrange: 5 tentativas de login esgotam cota; usuário default autenticado.
    Act: GET /contatos/ (endpoint não limitado).
    Assert: retorna 200, nunca 429."""
    for _ in range(5):
        _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))

    assert resp.status_code == 200
    assert resp.status_code != 429


# ---------------------------------------------------------------------------
# RN-F3.2-05 — Isolamento entre testes (reset_limiter autouse garante isso)
# ---------------------------------------------------------------------------

def test_reset_limiter_entre_testes_primeira_chamada_nao_e_429(client):
    """Arrange: este teste começa com storage zerado (reset_limiter autouse).
    Act: 1ª chamada ao /auth/login.
    Assert: não retorna 429 — prova que o reset funcionou."""
    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code != 429


def test_reset_limiter_entre_testes_segunda_prova(client):
    """Segundo teste consecutivo — também começa com storage zerado.
    A 1ª chamada deve retornar 401, não 429."""
    resp = _fazer_login(client, **_CREDENCIAIS_INVALIDAS)

    assert resp.status_code == 401
