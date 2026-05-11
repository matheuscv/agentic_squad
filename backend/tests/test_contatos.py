"""Testes para os endpoints CRUD de /contatos/."""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONTATO_PAYLOAD = {
    "nome": "Contato Criado",
    "email": "criado@contatos.com",
    "telefone": "11988887777",
    "empresa": "Empresa X",
    "observacoes": "Obs teste",
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /contatos/ — listagem
# ---------------------------------------------------------------------------

def test_listar_contatos_autenticado(client, usuario_default_token):
    """GET /contatos/ com token válido deve retornar 200 e uma lista."""
    resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_listar_contatos_sem_token(client):
    """GET /contatos/ sem token deve retornar 401."""
    resp = client.get("/contatos/")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /contatos/ — busca
# ---------------------------------------------------------------------------

def test_busca_por_nome(client, usuario_default_token, contato_exemplo):
    """GET /contatos/?busca=<nome> deve retornar apenas contatos que batem."""
    resp = client.get(
        "/contatos/",
        params={"busca": contato_exemplo.nome},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    # Todos os resultados devem conter o nome buscado (case-insensitive)
    nome_lower = contato_exemplo.nome.lower()
    for item in data:
        campos = (
            item["nome"].lower()
            + item["email"].lower()
            + (item.get("empresa") or "").lower()
        )
        assert nome_lower in campos or contato_exemplo.nome.lower() in campos


def test_busca_case_insensitive(client, usuario_default_token, contato_exemplo):
    """Busca em maiúsculas deve retornar o contato mesmo com nome em minúsculas."""
    busca_maiuscula = contato_exemplo.nome.upper()
    resp = client.get(
        "/contatos/",
        params={"busca": busca_maiuscula},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    ids_retornados = [c["id"] for c in resp.json()]
    assert contato_exemplo.id in ids_retornados


# ---------------------------------------------------------------------------
# GET /contatos/{id} — detalhe
# ---------------------------------------------------------------------------

def test_detalhe_contato(client, usuario_default_token, contato_exemplo):
    """GET /contatos/{id} deve retornar 200 com os dados do contato."""
    resp = client.get(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == contato_exemplo.id
    assert data["email"] == contato_exemplo.email
    assert data["nome"] == contato_exemplo.nome


def test_detalhe_contato_inexistente(client, usuario_default_token):
    """GET /contatos/99999 deve retornar 404."""
    resp = client.get(
        "/contatos/99999",
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /contatos/ — criação
# ---------------------------------------------------------------------------

def test_criar_contato_adm(client, usuario_adm_token):
    """POST /contatos/ com token adm deve retornar 201."""
    resp = client.post(
        "/contatos/",
        json=_CONTATO_PAYLOAD,
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == _CONTATO_PAYLOAD["email"]
    assert data["nome"] == _CONTATO_PAYLOAD["nome"]
    assert "id" in data


def test_criar_contato_default(client, usuario_default_token):
    """POST /contatos/ com token default deve retornar 403."""
    resp = client.post(
        "/contatos/",
        json={**_CONTATO_PAYLOAD, "email": "default_nao_pode@test.com"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 403


def test_criar_contato_sem_token(client):
    """POST /contatos/ sem token deve retornar 401."""
    resp = client.post("/contatos/", json=_CONTATO_PAYLOAD)
    assert resp.status_code == 401


def test_criar_contato_email_duplicado(client, usuario_adm_token, contato_exemplo):
    """POST /contatos/ com e-mail já existente deve retornar 400."""
    payload = {
        "nome": "Outro Nome",
        "email": contato_exemplo.email,  # e-mail duplicado
    }
    resp = client.post(
        "/contatos/",
        json=payload,
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PUT /contatos/{id} — atualização
# ---------------------------------------------------------------------------

def test_atualizar_contato_adm(client, usuario_adm_token, contato_exemplo):
    """PUT /contatos/{id} com adm deve retornar 200 e dados atualizados."""
    novo_nome = "Nome Atualizado"
    resp = client.put(
        f"/contatos/{contato_exemplo.id}",
        json={"nome": novo_nome},
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nome"] == novo_nome
    # Demais campos devem ser preservados
    assert data["email"] == contato_exemplo.email


def test_atualizar_contato_default(client, usuario_default_token, contato_exemplo):
    """PUT /contatos/{id} com token default deve retornar 403."""
    resp = client.put(
        f"/contatos/{contato_exemplo.id}",
        json={"nome": "Tentativa Não Autorizada"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /contatos/{id} — exclusão
# ---------------------------------------------------------------------------

def test_excluir_contato_adm(client, usuario_adm_token, contato_exemplo):
    """DELETE /contatos/{id} com adm deve retornar 204."""
    resp = client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 204
    # Verificar que o contato foi de fato removido
    resp_get = client.get(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )
    assert resp_get.status_code == 404


def test_excluir_contato_default(client, usuario_default_token, contato_exemplo):
    """DELETE /contatos/{id} com token default deve retornar 403."""
    resp = client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 403


def test_excluir_contato_inexistente(client, usuario_adm_token):
    """DELETE /contatos/99999 com adm deve retornar 404."""
    resp = client.delete(
        "/contatos/99999",
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 404
