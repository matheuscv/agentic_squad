"""
Testes de autenticação — TASK-10 / RF-F3-01.

Cobre:
- Login bem-sucedido (happy path)
- Credenciais inválidas: senha errada, e-mail inexistente
- Token inválido / malformado
- Cadastro com e-mail duplicado
- Cadastro com senha curta (< 6 chars)
- GET /auth/me com token válido e sem token

Padrão: AAA (Arrange / Act / Assert)
"""

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
# POST /auth/login — caminho feliz
# ---------------------------------------------------------------------------

def test_login_bem_sucedido(client):
    """Login com credenciais válidas deve retornar 200 e campo 'access_token' não vazio."""
    # Arrange
    client.post(
        "/usuarios/",
        json={"nome": "Teste Login", "email": "login@test.com", "senha": "senha123"},
    )

    # Act
    resp = client.post(
        "/auth/login",
        json={"email": "login@test.com", "senha": "senha123"},
    )

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_sucesso(client):
    """Alias de caminho feliz — garante que token_type está presente (se retornado)."""
    # Arrange
    client.post(
        "/usuarios/",
        json={"nome": "Teste Login2", "email": "login2@test.com", "senha": "senha123"},
    )

    # Act
    resp = client.post("/auth/login", json={"email": "login2@test.com", "senha": "senha123"})

    # Assert
    assert resp.status_code == 200
    assert "access_token" in resp.json()


# ---------------------------------------------------------------------------
# POST /auth/login — credenciais inválidas
# ---------------------------------------------------------------------------

def test_login_senha_incorreta(client):
    """Login com senha incorreta deve retornar 401."""
    # Arrange
    client.post(
        "/usuarios/",
        json={"nome": "Teste Senha", "email": "senha@test.com", "senha": "correta123"},
    )

    # Act
    resp = client.post(
        "/auth/login",
        json={"email": "senha@test.com", "senha": "errada999"},
    )

    # Assert
    assert resp.status_code == 401


def test_login_email_inexistente(client):
    """Login com e-mail não cadastrado deve retornar 401."""
    # Arrange — nenhum usuário cadastrado com este e-mail

    # Act
    resp = client.post(
        "/auth/login",
        json={"email": "naoexiste@test.com", "senha": "qualquer123"},
    )

    # Assert
    assert resp.status_code == 401


def test_login_senha_errada(client):
    """Login com senha incorreta deve retornar 401 (variante de teste_login_senha_incorreta)."""
    # Arrange
    client.post(
        "/usuarios/",
        json={"nome": "Dupla Senha", "email": "dupla@test.com", "senha": "certa456"},
    )

    # Act
    resp = client.post("/auth/login", json={"email": "dupla@test.com", "senha": "errada456"})

    # Assert
    assert resp.status_code == 401


def test_login_usuario_inexistente(client):
    """Login com e-mail não cadastrado deve retornar 401."""
    # Act
    resp = client.post(
        "/auth/login",
        json={"email": "inexistente99@test.com", "senha": "qualquer123"},
    )

    # Assert
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Cadastro — casos de borda
# ---------------------------------------------------------------------------

def test_cadastro_email_duplicado(client):
    """POST /usuarios/ com e-mail já cadastrado deve retornar 400."""
    # Arrange
    payload = {"nome": "Primeiro", "email": "dup@test.com", "senha": "senha123"}
    client.post("/usuarios/", json=payload)

    # Act
    resp = client.post(
        "/usuarios/",
        json={"nome": "Segundo", "email": "dup@test.com", "senha": "outrasenha"},
    )

    # Assert
    assert resp.status_code == 400


def test_cadastro_senha_curta(client):
    """POST /usuarios/ com senha menor que 6 chars deve retornar 422."""
    # Arrange
    payload = {"nome": "Curta", "email": "curta@test.com", "senha": "abc"}

    # Act
    resp = client.post("/usuarios/", json=payload)

    # Assert
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Token inválido
# ---------------------------------------------------------------------------

def test_token_invalido_retorna_401(client):
    """GET /contatos/ com token malformado deve retornar 401."""
    # Arrange
    headers = {"Authorization": "Bearer token.invalido.aqui"}

    # Act
    resp = client.get("/contatos/", headers=headers)

    # Assert
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

def test_me_com_token(client):
    """GET /auth/me com token válido deve retornar 200 e dados do usuário."""
    # Arrange
    email = "me@test.com"
    nome = "Me User"
    client.post("/usuarios/", json={"nome": nome, "email": email, "senha": "senha123"})
    login_resp = client.post("/auth/login", json={"email": email, "senha": "senha123"})
    token = login_resp.json()["access_token"]

    # Act
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email
    assert data["nome"] == nome
    assert "id" in data
    assert data["role"] == "default"


def test_me_sem_token(client):
    """GET /auth/me sem header Authorization deve retornar 401."""
    # Act
    resp = client.get("/auth/me")

    # Assert
    assert resp.status_code == 401


def test_me_token_invalido(client):
    """GET /auth/me com token mal-formado deve retornar 401."""
    # Act
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalido"})

    # Assert
    assert resp.status_code == 401
