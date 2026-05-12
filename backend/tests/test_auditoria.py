"""
Testes de auditoria de criação/modificação de contatos — TASK-11 / RF-F3.2-01.

Cobre:
- POST /contatos/ preenche criado_por_id e atualizado_por_id com o id do usuário autenticado
- PUT /contatos/{id} atualiza atualizado_por_id; criado_por_id permanece inalterado (RN-F3.2-01)
- PATCH /contatos/{id} atualiza atualizado_por_id; criado_por_id permanece inalterado
- GET /contatos/ e GET /contatos/{id} expõem criado_por_id e atualizado_por_id no payload
- Contatos criados com usuario_id=None mantêm NULL nos campos de auditoria (retrocompatibilidade)

Padrão: AAA (Arrange / Act / Assert)
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _obter_id_usuario_adm(client, token: str) -> int:
    """Retorna o id do usuário autenticado via GET /auth/me."""
    resp = client.get("/auth/me", headers=_auth_header(token))
    assert resp.status_code == 200
    return resp.json()["id"]


def _criar_contato(client, token: str, email: str = "auditoria@contato.com", nome: str = "Contato Auditoria") -> dict:
    """Cria contato via API e retorna JSON de resposta."""
    resp = client.post(
        "/contatos/",
        json={"nome": nome, "email": email},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201, f"Falha ao criar contato: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# RF-F3.2-01 — POST /contatos/ popula campos de auditoria
# ---------------------------------------------------------------------------

def test_criar_contato_preenche_criado_por_id(client, usuario_adm_token):
    """Arrange: usuário adm autenticado.
    Act: POST /contatos/.
    Assert: criado_por_id == id do usuário autenticado."""
    adm_id = _obter_id_usuario_adm(client, usuario_adm_token)

    contato = _criar_contato(client, usuario_adm_token)

    assert contato["criado_por_id"] == adm_id


def test_criar_contato_preenche_atualizado_por_id(client, usuario_adm_token):
    """Arrange: usuário adm autenticado.
    Act: POST /contatos/.
    Assert: atualizado_por_id == id do usuário autenticado."""
    adm_id = _obter_id_usuario_adm(client, usuario_adm_token)

    contato = _criar_contato(client, usuario_adm_token)

    assert contato["atualizado_por_id"] == adm_id


def test_criar_contato_campos_auditoria_presentes_no_payload(client, usuario_adm_token):
    """Arrange: usuário adm autenticado.
    Act: POST /contatos/.
    Assert: payload contém as chaves criado_por_id e atualizado_por_id."""
    contato = _criar_contato(client, usuario_adm_token)

    assert "criado_por_id" in contato
    assert "atualizado_por_id" in contato


# ---------------------------------------------------------------------------
# RF-F3.2-01 — PUT /contatos/{id} atualiza atualizado_por_id, preserva criado_por_id
# ---------------------------------------------------------------------------

def test_put_contato_atualiza_atualizado_por_id(client, usuario_adm_token):
    """Arrange: contato criado pelo adm.
    Act: PUT /contatos/{id} com mesmo adm.
    Assert: atualizado_por_id == id do adm."""
    adm_id = _obter_id_usuario_adm(client, usuario_adm_token)
    contato = _criar_contato(client, usuario_adm_token, email="put.auditoria@contato.com")

    resp = client.put(
        f"/contatos/{contato['id']}",
        json={"nome": "Nome Atualizado PUT", "email": contato["email"]},
        headers=_auth_header(usuario_adm_token),
    )

    assert resp.status_code == 200
    assert resp.json()["atualizado_por_id"] == adm_id


def test_put_contato_preserva_criado_por_id(client, usuario_adm_token):
    """Arrange: contato criado pelo adm.
    Act: PUT /contatos/{id}.
    Assert: criado_por_id permanece igual ao valor da criação (RN-F3.2-01)."""
    adm_id = _obter_id_usuario_adm(client, usuario_adm_token)
    contato = _criar_contato(client, usuario_adm_token, email="put.criado@contato.com")
    criado_por_id_original = contato["criado_por_id"]

    resp = client.put(
        f"/contatos/{contato['id']}",
        json={"nome": "Nome Modificado", "email": contato["email"]},
        headers=_auth_header(usuario_adm_token),
    )

    assert resp.status_code == 200
    assert resp.json()["criado_por_id"] == criado_por_id_original
    assert resp.json()["criado_por_id"] == adm_id


# ---------------------------------------------------------------------------
# RF-F3.2-01 — PATCH /contatos/{id} atualiza atualizado_por_id, preserva criado_por_id
# ---------------------------------------------------------------------------

def test_patch_contato_atualiza_atualizado_por_id(client, usuario_adm_token):
    """Arrange: contato criado pelo adm.
    Act: PATCH /contatos/{id} com campo parcial.
    Assert: atualizado_por_id == id do adm."""
    adm_id = _obter_id_usuario_adm(client, usuario_adm_token)
    contato = _criar_contato(client, usuario_adm_token, email="patch.audit@contato.com")

    resp = client.patch(
        f"/contatos/{contato['id']}",
        json={"empresa": "Empresa Patch"},
        headers=_auth_header(usuario_adm_token),
    )

    assert resp.status_code == 200
    assert resp.json()["atualizado_por_id"] == adm_id


def test_patch_contato_preserva_criado_por_id(client, usuario_adm_token):
    """Arrange: contato criado pelo adm.
    Act: PATCH /contatos/{id}.
    Assert: criado_por_id não é alterado pelo patch (RN-F3.2-01)."""
    contato = _criar_contato(client, usuario_adm_token, email="patch.criado@contato.com")
    criado_por_id_original = contato["criado_por_id"]

    resp = client.patch(
        f"/contatos/{contato['id']}",
        json={"observacoes": "Observação via patch"},
        headers=_auth_header(usuario_adm_token),
    )

    assert resp.status_code == 200
    assert resp.json()["criado_por_id"] == criado_por_id_original


# ---------------------------------------------------------------------------
# RF-F3.2-01 — GET expõe criado_por_id e atualizado_por_id
# ---------------------------------------------------------------------------

def test_get_listagem_expoe_campos_auditoria(client, usuario_adm_token):
    """Arrange: contato criado.
    Act: GET /contatos/.
    Assert: items contêm criado_por_id e atualizado_por_id."""
    _criar_contato(client, usuario_adm_token, email="list.audit@contato.com")

    resp = client.get("/contatos/", headers=_auth_header(usuario_adm_token))

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert "criado_por_id" in items[0]
    assert "atualizado_por_id" in items[0]


def test_get_detalhe_expoe_campos_auditoria(client, usuario_adm_token):
    """Arrange: contato criado.
    Act: GET /contatos/{id}.
    Assert: payload contém criado_por_id e atualizado_por_id com valores não-None."""
    adm_id = _obter_id_usuario_adm(client, usuario_adm_token)
    contato = _criar_contato(client, usuario_adm_token, email="detail.audit@contato.com")

    resp = client.get(f"/contatos/{contato['id']}", headers=_auth_header(usuario_adm_token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["criado_por_id"] == adm_id
    assert data["atualizado_por_id"] == adm_id


# ---------------------------------------------------------------------------
# RN-F3.2-02 — Contatos sem usuario_id ficam com NULL (retrocompatibilidade)
# ---------------------------------------------------------------------------

def test_contato_criado_sem_usuario_id_tem_campos_auditoria_null(db_session):
    """Arrange: criar contato via service sem usuario_id (simula dados anteriores à feature).
    Act: verificar campos de auditoria.
    Assert: criado_por_id e atualizado_por_id são None."""
    from app.services import contato_service
    from app.schemas.contato import ContatoCriar

    dados = ContatoCriar(nome="Contato Legado", email="legado@auditoria.com")
    # usuario_id=None simula registro criado antes da Fase 3.2
    contato = contato_service.criar_contato(db_session, dados, usuario_id=None)

    assert contato.criado_por_id is None
    assert contato.atualizado_por_id is None
