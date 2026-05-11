"""Testes para os endpoints de autenticação: POST /auth/login e GET /auth/me."""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _criar_usuario_e_token(client, email="user@auth.com", senha="senha123", nome="User Auth"):
    """Cria um usuário e retorna o JWT de login."""
    client.post("/usuarios/", json={"nome": nome, "email": email, "senha": senha})
    resp = client.post("/auth/login", json={"email": email, "senha": senha})
    return resp.json().get("access_token")


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

def test_login_sucesso(client):
    """Login com credenciais válidas deve retornar 200 e campo 'access_token'."""
    client.post(
        "/usuarios/",
        json={"nome": "Teste Login", "email": "login@test.com", "senha": "senha123"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": "login@test.com", "senha": "senha123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_senha_errada(client):
    """Login com senha incorreta deve retornar 401."""
    client.post(
        "/usuarios/",
        json={"nome": "Teste Senha", "email": "senha@test.com", "senha": "correta123"},
    )
    resp = client.post(
        "/auth/login",
        json={"email": "senha@test.com", "senha": "errada999"},
    )
    assert resp.status_code == 401


def test_login_usuario_inexistente(client):
    """Login com e-mail não cadastrado deve retornar 401."""
    resp = client.post(
        "/auth/login",
        json={"email": "naoexiste@test.com", "senha": "qualquer123"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

def test_me_com_token(client):
    """GET /auth/me com token válido deve retornar 200 e os dados do usuário."""
    email = "me@test.com"
    nome = "Me User"
    client.post(
        "/usuarios/",
        json={"nome": nome, "email": email, "senha": "senha123"},
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "senha": "senha123"},
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email
    assert data["nome"] == nome
    assert "id" in data
    assert data["role"] == "default"


def test_me_sem_token(client):
    """GET /auth/me sem header Authorization deve retornar 401."""
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_token_invalido(client):
    """GET /auth/me com token mal-formado deve retornar 401."""
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalido"})
    assert resp.status_code == 401
