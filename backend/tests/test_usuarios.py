"""Testes para o endpoint POST /usuarios/."""

import pytest


# ---------------------------------------------------------------------------
# POST /usuarios/
# ---------------------------------------------------------------------------

def test_criar_usuario(client):
    """Criação de usuário deve retornar 201 e role='default'."""
    resp = client.post(
        "/usuarios/",
        json={"nome": "Novo Usuario", "email": "novo@test.com", "senha": "senha123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "novo@test.com"
    assert data["nome"] == "Novo Usuario"
    assert data["role"] == "default"
    # Senha não deve ser exposta na resposta
    assert "senha" not in data
    assert "senha_hash" not in data
    assert "id" in data


def test_criar_usuario_email_duplicado(client):
    """Segundo POST com mesmo e-mail deve retornar 400."""
    payload = {"nome": "Duplicado", "email": "dup@test.com", "senha": "senha123"}
    resp1 = client.post("/usuarios/", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/usuarios/", json=payload)
    assert resp2.status_code == 400


def test_criar_usuario_senha_curta(client):
    """Senha com menos de 6 caracteres deve falhar na validação Pydantic (422)."""
    resp = client.post(
        "/usuarios/",
        json={"nome": "Curta", "email": "curta@test.com", "senha": "abc"},
    )
    assert resp.status_code == 422
