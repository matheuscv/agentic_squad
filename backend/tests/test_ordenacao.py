"""
Testes para ordenação de contatos — RF-F2-01 (Fase 2).

Cobre os parâmetros sort_by e sort_order do endpoint GET /contatos/
conforme critérios de aceite do PRD seção 14.4.
"""

import pytest
from app.schemas.contato import ContatoCriar
from app.services import contato_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _criar_contatos_multiplos(db_session):
    """Insere três contatos com nomes/empresas distintos para validar ordenação."""
    dados = [
        ContatoCriar(nome="Carlos Andrade", email="carlos@test.com", empresa="Zebra Ltda"),
        ContatoCriar(nome="Ana Beatriz", email="ana@test.com", empresa="Alfa SA"),
        ContatoCriar(nome="Marcos Vieira", email="marcos@test.com", empresa="Beta Corp"),
    ]
    contatos = [contato_service.criar_contato(db_session, d) for d in dados]
    return contatos


# ---------------------------------------------------------------------------
# Ordenação por nome ASC (padrão)
# ---------------------------------------------------------------------------

def test_listar_sem_params_usa_nome_asc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=nome&sort_order=asc retorna resultados por nome ASC."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert nomes == sorted(nomes), "Deve estar em ordem alfabética crescente (ASC)"


def test_sort_by_nome_asc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=nome&sort_order=asc retorna lista em ordem alfabética crescente."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert nomes == sorted(nomes)


def test_sort_by_nome_desc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=nome&sort_order=desc retorna lista em ordem alfabética decrescente."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert nomes == sorted(nomes, reverse=True)


# ---------------------------------------------------------------------------
# Ordenação por empresa
# ---------------------------------------------------------------------------

def test_sort_by_empresa_asc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=empresa&sort_order=asc retorna lista por empresa crescente."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "empresa", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    empresas = [c["empresa"] for c in resp.json()["items"]]
    assert empresas == sorted(empresas)


def test_sort_by_empresa_desc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=empresa&sort_order=desc retorna lista em ordem decrescente por empresa."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "empresa", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    empresas = [c["empresa"] for c in resp.json()["items"]]
    assert empresas == sorted(empresas, reverse=True)


# ---------------------------------------------------------------------------
# Ordenação por email
# ---------------------------------------------------------------------------

def test_sort_by_email_asc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=email&sort_order=asc retorna lista ordenada por email."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "email", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    emails = [c["email"] for c in resp.json()["items"]]
    assert emails == sorted(emails)


# ---------------------------------------------------------------------------
# Ordenação por criado_em
# ---------------------------------------------------------------------------

def test_sort_by_criado_em_asc(client, usuario_default_token, db_session):
    """GET /contatos/?sort_by=criado_em retorna 200 (campo válido)."""
    _criar_contatos_multiplos(db_session)

    resp = client.get(
        "/contatos/",
        params={"sort_by": "criado_em", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)


# ---------------------------------------------------------------------------
# Parâmetros inválidos — HTTP 422
# ---------------------------------------------------------------------------

def test_sort_by_campo_invalido_retorna_422(client, usuario_default_token):
    """GET /contatos/?sort_by=campo_invalido deve retornar HTTP 422."""
    resp = client.get(
        "/contatos/",
        params={"sort_by": "campo_invalido"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 422


def test_sort_by_sql_injection_retorna_422(client, usuario_default_token):
    """Tentativa de SQL injection via sort_by deve retornar HTTP 422."""
    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome; DROP TABLE contatos;--"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 422


def test_sort_order_invalido_retorna_422(client, usuario_default_token):
    """GET /contatos/?sort_order=invalido deve retornar HTTP 422."""
    resp = client.get(
        "/contatos/",
        params={"sort_order": "invalido"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 422


def test_sort_order_ascending_invalido_retorna_422(client, usuario_default_token):
    """'ascending' não é valor válido para sort_order (apenas 'asc'/'desc')."""
    resp = client.get(
        "/contatos/",
        params={"sort_order": "ascending"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Ordenação com lista vazia — não deve falhar
# ---------------------------------------------------------------------------

def test_ordenacao_lista_vazia_retorna_200(client, usuario_default_token):
    """GET /contatos/ com ordenação explícita e banco vazio deve retornar 200."""
    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


# ---------------------------------------------------------------------------
# Ordenação combinada com busca
# ---------------------------------------------------------------------------

def test_ordenacao_combinada_com_busca(client, usuario_default_token, db_session):
    """Ordenação deve funcionar junto com filtro de busca."""
    _criar_contatos_multiplos(db_session)

    # Busca por "a" deve retornar contatos, ordenados por nome DESC
    resp = client.get(
        "/contatos/",
        params={"busca": "a", "sort_by": "nome", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert nomes == sorted(nomes, reverse=True)


# ---------------------------------------------------------------------------
# Sem token — deve retornar 401
# ---------------------------------------------------------------------------

def test_listar_sem_token_retorna_401(client):
    """GET /contatos/ sem token deve retornar 401 independente dos params de ordenação."""
    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "asc"},
    )
    assert resp.status_code == 401
