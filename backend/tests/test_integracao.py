"""
Testes de integração end-to-end para o backend.

Usa StaticPool para garantir que o SQLite em memória seja compartilhado
entre conexões — requisito quando o TestClient executa em thread separada.

Fluxos cobertos:
1. Cadastro -> Login -> Criar contato -> Editar -> Excluir (papel adm)
2. Cadastro -> Login -> Tentativa de escrita bloqueada (papel default)
3. Token expirado / inválido bloqueado em rota protegida
4. Pesquisa de contatos após criação
5. Criação de contato com somente campos obrigatórios
6. Email duplicado em contato retorna 400
7. GET /auth/me reflete dados corretos do usuário logado
8. Cadastro de usuário com email duplicado retorna 400
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# Fixtures locais — usam StaticPool para compatibilidade com TestClient
# (o TestClient executa em thread separada; StaticPool garante uma única
#  conexão compartilhada, evitando o erro "no such table" com SQLite em memória)
# ---------------------------------------------------------------------------

@pytest.fixture()
def engine_integracao():
    """Engine SQLite em memória com StaticPool — banco único por teste."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


@pytest.fixture()
def db_integracao(engine_integracao):
    """Sessão SQLAlchemy para o banco de integração."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine_integracao)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client_integracao(db_integracao):
    """TestClient com override de get_db apontando para o banco de integração."""
    def override_get_db():
        try:
            yield db_integracao
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _registrar(client, nome, email, senha):
    return client.post("/usuarios/", json={"nome": nome, "email": email, "senha": senha})


def _elevar_para_adm(db_session, usuario_id):
    from app.models.usuario import Usuario
    usuario = db_session.query(Usuario).filter(Usuario.id == usuario_id).first()
    usuario.role = "adm"
    db_session.commit()
    db_session.refresh(usuario)


# ---------------------------------------------------------------------------
# Fluxo completo adm: cadastro -> login -> criar -> editar -> excluir
# ---------------------------------------------------------------------------

def test_fluxo_completo_adm(client_integracao, db_integracao):
    """
    Fluxo end-to-end:
      1. Cria usuario, eleva para adm
      2. Faz login e obtem token
      3. Cria um contato
      4. Verifica contato na listagem
      5. Edita o contato
      6. Verifica edicao no detalhe
      7. Exclui o contato
      8. Confirma que nao existe mais
    """
    client = client_integracao

    # 1. Registrar e elevar
    resp = _registrar(client, "Adm Fluxo", "adm_fluxo@test.com", "senha123")
    assert resp.status_code == 201
    _elevar_para_adm(db_integracao, resp.json()["id"])

    # 2. Login
    resp = client.post("/auth/login", json={"email": "adm_fluxo@test.com", "senha": "senha123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = _auth(token)

    # 3. Criar contato
    payload = {
        "nome": "Cliente Integracao",
        "email": "cli_int@empresa.com",
        "telefone": "11933334444",
        "empresa": "CorpInt",
        "observacoes": "Criado no fluxo E2E",
    }
    resp = client.post("/contatos/", json=payload, headers=headers)
    assert resp.status_code == 201
    contato_id = resp.json()["id"]
    assert resp.json()["nome"] == "Cliente Integracao"

    # 4. Verificar na listagem
    resp = client.get("/contatos/", headers=headers)
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert contato_id in ids

    # 5. Editar contato
    resp = client.put(
        f"/contatos/{contato_id}",
        json={"nome": "Cliente Editado", "empresa": "NovaCorp"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Cliente Editado"
    assert resp.json()["empresa"] == "NovaCorp"
    assert resp.json()["email"] == "cli_int@empresa.com"  # email inalterado

    # 6. Verificar no detalhe
    resp = client.get(f"/contatos/{contato_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Cliente Editado"

    # 7. Excluir
    resp = client.delete(f"/contatos/{contato_id}", headers=headers)
    assert resp.status_code == 204

    # 8. Confirmar exclusao
    resp = client.get(f"/contatos/{contato_id}", headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Fluxo default: cadastro -> login -> operacoes de escrita bloqueadas
# ---------------------------------------------------------------------------

def test_fluxo_default_operacoes_escrita_bloqueadas(client_integracao):
    """Usuario default consegue ler mas nao escrever."""
    client = client_integracao
    _registrar(client, "Default Fluxo", "def_fluxo@test.com", "senha123")
    resp = client.post("/auth/login", json={"email": "def_fluxo@test.com", "senha": "senha123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = _auth(token)

    payload = {"nome": "Tentativa", "email": "tentativa@test.com"}

    # POST bloqueado
    resp = client.post("/contatos/", json=payload, headers=headers)
    assert resp.status_code == 403

    # PUT bloqueado (403 vem antes de 404)
    resp = client.put("/contatos/1", json={"nome": "Hack"}, headers=headers)
    assert resp.status_code == 403

    # DELETE bloqueado
    resp = client.delete("/contatos/1", headers=headers)
    assert resp.status_code == 403

    # GET permitido
    resp = client.get("/contatos/", headers=headers)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Token invalido / expirado bloqueado em rotas protegidas
# ---------------------------------------------------------------------------

def test_token_invalido_bloqueado_em_listagem(client_integracao):
    """Token invalido deve retornar 401 na listagem."""
    resp = client_integracao.get("/contatos/", headers={"Authorization": "Bearer token.falso.aqui"})
    assert resp.status_code == 401


def test_sem_token_bloqueado_em_listagem(client_integracao):
    """Ausencia de token deve retornar 401 na listagem."""
    resp = client_integracao.get("/contatos/")
    assert resp.status_code == 401


def test_sem_token_bloqueado_em_criacao(client_integracao):
    """Ausencia de token deve retornar 401 em POST /contatos/."""
    resp = client_integracao.post("/contatos/", json={"nome": "X", "email": "x@x.com"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Fluxo de pesquisa apos criacao
# ---------------------------------------------------------------------------

def test_fluxo_criar_e_pesquisar_contato(client_integracao, db_integracao):
    """Cria dois contatos e verifica que a busca retorna apenas o correto."""
    client = client_integracao

    resp = _registrar(client, "Adm Busca", "adm_busca@test.com", "senha123")
    _elevar_para_adm(db_integracao, resp.json()["id"])
    resp = client.post("/auth/login", json={"email": "adm_busca@test.com", "senha": "senha123"})
    token = resp.json()["access_token"]
    headers = _auth(token)

    client.post("/contatos/", json={"nome": "Joana Silva", "email": "joana@alpha.com", "empresa": "AlphaCo"}, headers=headers)
    client.post("/contatos/", json={"nome": "Pedro Lima", "email": "pedro@beta.com", "empresa": "BetaCo"}, headers=headers)

    # Busca por empresa
    resp = client.get("/contatos/", params={"busca": "AlphaCo"}, headers=headers)
    assert resp.status_code == 200
    resultado = resp.json()
    assert len(resultado) == 1
    assert resultado[0]["empresa"] == "AlphaCo"

    # Busca por nome parcial
    resp = client.get("/contatos/", params={"busca": "Pedro"}, headers=headers)
    assert resp.status_code == 200
    resultado = resp.json()
    assert len(resultado) == 1
    assert resultado[0]["nome"] == "Pedro Lima"

    # Busca sem resultados
    resp = client.get("/contatos/", params={"busca": "TermoInexistente"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Fluxo: cadastro com email duplicado
# ---------------------------------------------------------------------------

def test_fluxo_cadastro_email_duplicado_retorna_400(client_integracao):
    """Dois cadastros com o mesmo email devem resultar em 400 no segundo."""
    client = client_integracao
    payload = {"nome": "Repetido", "email": "repetido@test.com", "senha": "senha123"}
    resp1 = client.post("/usuarios/", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/usuarios/", json=payload)
    assert resp2.status_code == 400


# ---------------------------------------------------------------------------
# Fluxo: verificar dados de /auth/me apos login
# ---------------------------------------------------------------------------

def test_fluxo_me_reflete_dados_do_usuario_logado(client_integracao):
    """GET /auth/me deve retornar os dados exatos do usuario que se logou."""
    client = client_integracao
    _registrar(client, "Verificar Me", "verificarme@test.com", "senha123")
    resp = client.post("/auth/login", json={"email": "verificarme@test.com", "senha": "senha123"})
    token = resp.json()["access_token"]

    resp = client.get("/auth/me", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "verificarme@test.com"
    assert data["nome"] == "Verificar Me"
    assert data["role"] == "default"


# ---------------------------------------------------------------------------
# Fluxo: criacao de contato com campos minimos obrigatorios
# ---------------------------------------------------------------------------

def test_fluxo_criar_contato_somente_campos_obrigatorios(client_integracao, db_integracao):
    """Contato criado apenas com nome e email deve ter campos opcionais como None."""
    client = client_integracao
    resp = _registrar(client, "Adm Min", "adm_min@test.com", "senha123")
    _elevar_para_adm(db_integracao, resp.json()["id"])
    resp = client.post("/auth/login", json={"email": "adm_min@test.com", "senha": "senha123"})
    token = resp.json()["access_token"]
    headers = _auth(token)

    resp = client.post("/contatos/", json={"nome": "Minimo", "email": "minimo@test.com"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome"] == "Minimo"
    assert data["email"] == "minimo@test.com"
    assert data["telefone"] is None
    assert data["empresa"] is None
    assert data["observacoes"] is None


# ---------------------------------------------------------------------------
# Fluxo: criacao de contato com email duplicado retorna 400
# ---------------------------------------------------------------------------

def test_fluxo_contato_email_duplicado_retorna_400(client_integracao, db_integracao):
    """Segundo contato com mesmo email deve retornar 400 via endpoint HTTP."""
    client = client_integracao
    resp = _registrar(client, "Adm Dup", "adm_dup@test.com", "senha123")
    _elevar_para_adm(db_integracao, resp.json()["id"])
    resp = client.post("/auth/login", json={"email": "adm_dup@test.com", "senha": "senha123"})
    token = resp.json()["access_token"]
    headers = _auth(token)

    client.post("/contatos/", json={"nome": "Primeiro", "email": "emaildup@test.com"}, headers=headers)
    resp = client.post("/contatos/", json={"nome": "Segundo", "email": "emaildup@test.com"}, headers=headers)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Fluxo: novo usuario nasce sempre com role default
# ---------------------------------------------------------------------------

def test_fluxo_novo_usuario_role_default(client_integracao):
    """Qualquer usuario recem-criado deve ter role 'default'."""
    client = client_integracao
    resp = _registrar(client, "Role Check", "rolecheck@test.com", "senha123")
    assert resp.status_code == 201
    assert resp.json()["role"] == "default"


# ---------------------------------------------------------------------------
# Fluxo: validacao de campo obrigatorio faltando em contato
# ---------------------------------------------------------------------------

def test_fluxo_criar_contato_sem_email_retorna_422(client_integracao, db_integracao):
    """POST /contatos/ sem email deve retornar 422 (validacao Pydantic)."""
    client = client_integracao
    resp = _registrar(client, "Adm Val", "adm_val@test.com", "senha123")
    _elevar_para_adm(db_integracao, resp.json()["id"])
    resp = client.post("/auth/login", json={"email": "adm_val@test.com", "senha": "senha123"})
    token = resp.json()["access_token"]
    headers = _auth(token)

    resp = client.post("/contatos/", json={"nome": "Sem Email"}, headers=headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Fluxo: busca por email case-insensitive
# ---------------------------------------------------------------------------

def test_fluxo_busca_case_insensitive(client_integracao, db_integracao):
    """Busca em maiusculas deve encontrar contato com nome em minusculas."""
    client = client_integracao
    resp = _registrar(client, "Adm CI", "adm_ci@test.com", "senha123")
    _elevar_para_adm(db_integracao, resp.json()["id"])
    resp = client.post("/auth/login", json={"email": "adm_ci@test.com", "senha": "senha123"})
    token = resp.json()["access_token"]
    headers = _auth(token)

    client.post("/contatos/", json={"nome": "zelia moura", "email": "zelia@ci.com"}, headers=headers)

    resp = client.get("/contatos/", params={"busca": "ZELIA"}, headers=headers)
    assert resp.status_code == 200
    resultado = resp.json()
    assert len(resultado) == 1
    assert resultado[0]["nome"] == "zelia moura"
