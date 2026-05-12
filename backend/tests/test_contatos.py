"""
Testes CRUD completo de /contatos/ — TASK-10 / RF-F3-01.

Cobre:
- GET /contatos/ (listagem, paginação, busca)
- GET /contatos/{id} (detalhe, 404)
- POST /contatos/ (criação, e-mail duplicado, role default 403, sem token 401)
- PUT /contatos/{id} (atualização total, role default 403)
- PATCH /contatos/{id} (atualização parcial: só telefone, só e-mail, body vazio 422, e-mail dup 400, 404, role default 403, sem token 401)
- DELETE /contatos/{id} (soft delete: 204, some de GET, GET/{id} vira 404, role default 403)
- GET /contatos/lixeira (adm vê contato deletado com deletado_em, default 403, sem token 401)

Padrão: AAA (Arrange / Act / Assert)
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONTATO_PAYLOAD = {
    "nome": "Contato Criado",
    "email": "criado@contatos.com",
    "empresa": "Empresa X",
    "observacoes": "Obs teste",
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _criar_contato(client, token, *, email="unico@criar.com", nome="Criado Via Helper") -> dict:
    """Cria contato via API e retorna JSON de resposta."""
    resp = client.post(
        "/contatos/",
        json={"nome": nome, "email": email},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, f"Helper falhou ao criar contato: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# GET /contatos/ — listagem
# ---------------------------------------------------------------------------

def test_listar_contatos_autenticado(client, usuario_default_token):
    """GET /contatos/ com token válido deve retornar 200 e objeto paginado."""
    # Act
    resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_listar_contatos_sem_token(client):
    """GET /contatos/ sem token deve retornar 401."""
    # Act
    resp = client.get("/contatos/")

    # Assert
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /contatos/ — busca
# ---------------------------------------------------------------------------

def test_busca_por_nome(client, usuario_default_token, contato_exemplo):
    """GET /contatos/?busca=<nome> deve retornar apenas contatos que batem."""
    # Act
    resp = client.get(
        "/contatos/",
        params={"busca": contato_exemplo.nome},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) >= 1
    nome_lower = contato_exemplo.nome.lower()
    for item in data:
        campos = (
            item["nome"].lower()
            + item["email"].lower()
            + (item.get("empresa") or "").lower()
        )
        assert nome_lower in campos


def test_busca_case_insensitive(client, usuario_default_token, contato_exemplo):
    """Busca em maiúsculas deve retornar o contato mesmo com nome em minúsculas."""
    # Arrange
    busca_maiuscula = contato_exemplo.nome.upper()

    # Act
    resp = client.get(
        "/contatos/",
        params={"busca": busca_maiuscula},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    ids_retornados = [c["id"] for c in resp.json()["items"]]
    assert contato_exemplo.id in ids_retornados


# ---------------------------------------------------------------------------
# GET /contatos/{id} — detalhe
# ---------------------------------------------------------------------------

def test_detalhe_contato(client, usuario_default_token, contato_exemplo):
    """GET /contatos/{id} deve retornar 200 com os dados do contato."""
    # Act
    resp = client.get(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == contato_exemplo.id
    assert data["email"] == contato_exemplo.email
    assert data["nome"] == contato_exemplo.nome


def test_detalhe_contato_inexistente(client, usuario_default_token):
    """GET /contatos/99999 deve retornar 404."""
    # Act
    resp = client.get("/contatos/99999", headers=_auth_header(usuario_default_token))

    # Assert
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /contatos/ — criação
# ---------------------------------------------------------------------------

def test_criar_contato_adm(client, usuario_adm_token):
    """POST /contatos/ com token adm deve retornar 201 e dados do contato criado."""
    # Act
    resp = client.post(
        "/contatos/",
        json=_CONTATO_PAYLOAD,
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == _CONTATO_PAYLOAD["email"]
    assert data["nome"] == _CONTATO_PAYLOAD["nome"]
    assert "id" in data


def test_criar_contato_default_retorna_403(client, usuario_default_token):
    """POST /contatos/ com token default deve retornar 403."""
    # Act
    resp = client.post(
        "/contatos/",
        json={**_CONTATO_PAYLOAD, "email": "default_nao_pode@test.com"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 403


def test_criar_contato_sem_token_retorna_401(client):
    """POST /contatos/ sem token deve retornar 401."""
    # Act
    resp = client.post("/contatos/", json=_CONTATO_PAYLOAD)

    # Assert
    assert resp.status_code == 401


def test_criar_contato_email_duplicado(client, usuario_adm_token, contato_exemplo):
    """POST /contatos/ com e-mail já existente deve retornar 400."""
    # Arrange
    payload = {"nome": "Outro Nome", "email": contato_exemplo.email}

    # Act
    resp = client.post(
        "/contatos/",
        json=payload,
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PUT /contatos/{id} — atualização total
# ---------------------------------------------------------------------------

def test_atualizar_contato_adm(client, usuario_adm_token, contato_exemplo):
    """PUT /contatos/{id} com adm deve retornar 200 e dados atualizados."""
    # Arrange
    novo_nome = "Nome Atualizado"

    # Act
    resp = client.put(
        f"/contatos/{contato_exemplo.id}",
        json={"nome": novo_nome},
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["nome"] == novo_nome
    assert data["email"] == contato_exemplo.email


def test_atualizar_contato_default_retorna_403(client, usuario_default_token, contato_exemplo):
    """PUT /contatos/{id} com token default deve retornar 403."""
    # Act
    resp = client.put(
        f"/contatos/{contato_exemplo.id}",
        json={"nome": "Tentativa Não Autorizada"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /contatos/{id} — atualização parcial
# ---------------------------------------------------------------------------

def test_patch_somente_telefone(client, usuario_adm_token):
    """PATCH com apenas telefone deve atualizar só esse campo, preservando os demais."""
    # Arrange
    contato = _criar_contato(
        client, usuario_adm_token, email="patch_tel@test.com", nome="Patch Telefone"
    )
    novo_tel = "(11) 99999-9999"

    # Act
    resp = client.patch(
        f"/contatos/{contato['id']}",
        json={"telefone": novo_tel},
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["telefone"] == novo_tel
    assert data["nome"] == contato["nome"]
    assert data["email"] == contato["email"]


def test_patch_somente_email(client, usuario_adm_token):
    """PATCH com apenas email deve atualizar só esse campo."""
    # Arrange
    contato = _criar_contato(
        client, usuario_adm_token, email="patch_email_old@test.com", nome="Patch Email"
    )
    novo_email = "patch_email_new@test.com"

    # Act
    resp = client.patch(
        f"/contatos/{contato['id']}",
        json={"email": novo_email},
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == novo_email
    assert data["nome"] == contato["nome"]


def test_patch_body_vazio_retorna_422(client, usuario_adm_token, contato_exemplo):
    """PATCH com body {} (sem campos) deve retornar 422 (RN-F3-02)."""
    # Act
    resp = client.patch(
        f"/contatos/{contato_exemplo.id}",
        json={},
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 422


def test_patch_email_duplicado_retorna_400(client, usuario_adm_token):
    """PATCH com e-mail já em uso por outro contato deve retornar 400."""
    # Arrange
    c1 = _criar_contato(client, usuario_adm_token, email="dup_a@test.com", nome="Dup A")
    c2 = _criar_contato(client, usuario_adm_token, email="dup_b@test.com", nome="Dup B")

    # Act — tenta roubar o e-mail de c1 para c2
    resp = client.patch(
        f"/contatos/{c2['id']}",
        json={"email": c1["email"]},
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 400


def test_patch_id_inexistente_retorna_404(client, usuario_adm_token):
    """PATCH em contato inexistente deve retornar 404."""
    # Act
    resp = client.patch(
        "/contatos/99999",
        json={"nome": "Ninguem"},
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 404


def test_patch_role_default_retorna_403(client, usuario_default_token, contato_exemplo):
    """PATCH /contatos/{id} com token default deve retornar 403."""
    # Act
    resp = client.patch(
        f"/contatos/{contato_exemplo.id}",
        json={"nome": "Invasão"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 403


def test_patch_sem_token_retorna_401(client, contato_exemplo):
    """PATCH /contatos/{id} sem token deve retornar 401."""
    # Act
    resp = client.patch(
        f"/contatos/{contato_exemplo.id}",
        json={"nome": "Sem Token"},
    )

    # Assert
    assert resp.status_code == 401


def test_patch_telefone_formato_invalido_retorna_422(client, usuario_adm_token, contato_exemplo):
    """PATCH com telefone sem máscara deve retornar 422 (validação Pydantic)."""
    # Act
    resp = client.patch(
        f"/contatos/{contato_exemplo.id}",
        json={"telefone": "11999999999"},  # sem máscara — inválido para ContatoPatch
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /contatos/{id} — soft delete
# ---------------------------------------------------------------------------

def test_soft_delete_retorna_204(client, usuario_adm_token, contato_exemplo):
    """DELETE /contatos/{id} com adm deve retornar 204."""
    # Act
    resp = client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 204


def test_contato_deletado_some_da_listagem(client, usuario_adm_token, contato_exemplo):
    """Contato com soft delete não deve aparecer em GET /contatos/."""
    # Arrange
    client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )

    # Act
    resp = client.get("/contatos/", headers=_auth_header(usuario_adm_token))

    # Assert
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()["items"]]
    assert contato_exemplo.id not in ids


def test_contato_deletado_retorna_404_no_detalhe(client, usuario_adm_token, contato_exemplo):
    """GET /contatos/{id} após soft delete deve retornar 404."""
    # Arrange
    client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )

    # Act
    resp = client.get(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )

    # Assert
    assert resp.status_code == 404


def test_excluir_contato_default_retorna_403(client, usuario_default_token, contato_exemplo):
    """DELETE /contatos/{id} com token default deve retornar 403."""
    # Act
    resp = client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 403


def test_excluir_contato_inexistente_retorna_404(client, usuario_adm_token):
    """DELETE /contatos/99999 deve retornar 404."""
    # Act
    resp = client.delete("/contatos/99999", headers=_auth_header(usuario_adm_token))

    # Assert
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /contatos/lixeira — endpoint exclusivo para adm
# ---------------------------------------------------------------------------

def test_lixeira_adm_ve_contato_deletado(client, usuario_adm_token, contato_exemplo):
    """GET /contatos/lixeira com adm deve listar contato após soft delete com deletado_em preenchido."""
    # Arrange — faz o soft delete
    client.delete(
        f"/contatos/{contato_exemplo.id}",
        headers=_auth_header(usuario_adm_token),
    )

    # Act
    resp = client.get("/contatos/lixeira", headers=_auth_header(usuario_adm_token))

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    ids_lixeira = [c["id"] for c in data["items"]]
    assert contato_exemplo.id in ids_lixeira
    # Garante que deletado_em está preenchido para o contato na lixeira
    contato_na_lixeira = next(c for c in data["items"] if c["id"] == contato_exemplo.id)
    assert contato_na_lixeira["deletado_em"] is not None


def test_lixeira_default_retorna_403(client, usuario_default_token):
    """GET /contatos/lixeira com token default deve retornar 403."""
    # Act
    resp = client.get("/contatos/lixeira", headers=_auth_header(usuario_default_token))

    # Assert
    assert resp.status_code == 403


def test_lixeira_sem_token_retorna_401(client):
    """GET /contatos/lixeira sem token deve retornar 401."""
    # Act
    resp = client.get("/contatos/lixeira")

    # Assert
    assert resp.status_code == 401


def test_lixeira_vazia_quando_nenhum_deletado(client, usuario_adm_token, contato_exemplo):
    """GET /contatos/lixeira sem nenhum soft delete deve retornar lista vazia."""
    # Arrange — contato_exemplo existe mas não foi deletado

    # Act
    resp = client.get("/contatos/lixeira", headers=_auth_header(usuario_adm_token))

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_lixeira_nao_inclui_contatos_ativos(client, usuario_adm_token):
    """Contatos ativos não devem aparecer na lixeira."""
    # Arrange — cria dois contatos, deleta apenas um
    c1 = _criar_contato(client, usuario_adm_token, email="ativo@lixeira.com", nome="Ativo")
    c2 = _criar_contato(client, usuario_adm_token, email="deletado@lixeira.com", nome="Deletado")
    client.delete(f"/contatos/{c2['id']}", headers=_auth_header(usuario_adm_token))

    # Act
    resp = client.get("/contatos/lixeira", headers=_auth_header(usuario_adm_token))

    # Assert
    assert resp.status_code == 200
    ids_lixeira = [c["id"] for c in resp.json()["items"]]
    assert c2["id"] in ids_lixeira
    assert c1["id"] not in ids_lixeira
