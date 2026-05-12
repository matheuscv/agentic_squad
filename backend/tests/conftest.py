"""
Fixtures compartilhadas para os testes do backend.

Estratégia:
- engine_test: SQLite em memória, criado por função (isolamento total entre testes)
- db_session: cria todas as tabelas, yield session, drop all ao final
- client: TestClient com override de get_db apontando para db_session
- usuario_default_dados / usuario_adm_dados: dicts com dados de criação
- usuario_default_token: cria usuário default via API e devolve JWT
- usuario_adm_token: cria usuário, eleva role para "adm" diretamente no DB, devolve JWT
- contato_exemplo: insere um contato via service e devolve o objeto Contato
"""

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.services import contato_service
from app.schemas.contato import ContatoCriar


# ---------------------------------------------------------------------------
# Engine por função — garante banco limpo a cada teste
# ---------------------------------------------------------------------------

@pytest.fixture()
def engine_test():
    """Cria um engine SQLite em memória novo a cada função de teste.
    StaticPool garante que TestClient (thread separada) use a mesma conexão."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


# ---------------------------------------------------------------------------
# Sessão de banco por teste
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session(engine_test):
    """
    Sessão SQLAlchemy vinculada ao engine em memória.
    As tabelas são criadas no engine_test; aqui apenas abrimos e fechamos a sessão.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine_test
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# TestClient com override de dependência
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db_session):
    """
    TestClient do FastAPI usando o banco em memória via override de get_db.
    O override é limpo após cada teste para evitar vazamento entre testes.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # fechamento gerenciado pela fixture db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Dados de usuários para reuso
# ---------------------------------------------------------------------------

@pytest.fixture()
def usuario_default_dados():
    """Dict com dados do usuário comum (role default)."""
    return {"nome": "João Silva", "email": "joao@test.com", "senha": "senha123"}


@pytest.fixture()
def usuario_adm_dados():
    """Dict com dados do usuário administrador."""
    return {"nome": "Admin", "email": "admin@test.com", "senha": "admin123"}


# ---------------------------------------------------------------------------
# Tokens JWT por role
# ---------------------------------------------------------------------------

@pytest.fixture()
def usuario_default_token(client, usuario_default_dados):
    """
    Cria o usuário default via POST /usuarios/, faz login e retorna o JWT.
    Depende de client (que já injeta db_session).
    """
    # Criar usuário
    resp = client.post("/usuarios/", json=usuario_default_dados)
    assert resp.status_code == 201, f"Falha ao criar usuário default: {resp.text}"

    # Fazer login para obter token
    resp = client.post(
        "/auth/login",
        json={
            "email": usuario_default_dados["email"],
            "senha": usuario_default_dados["senha"],
        },
    )
    assert resp.status_code == 200, f"Falha ao logar usuário default: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture()
def usuario_adm_token(client, db_session, usuario_adm_dados):
    """
    Cria o usuário via POST /usuarios/, eleva o role para 'adm' diretamente
    no banco (db_session), faz login e retorna o JWT.
    """
    from app.models.usuario import Usuario

    # Criar usuário (nasce como default)
    resp = client.post("/usuarios/", json=usuario_adm_dados)
    assert resp.status_code == 201, f"Falha ao criar usuário adm: {resp.text}"

    usuario_id = resp.json()["id"]

    # Elevar role diretamente no banco
    usuario = db_session.query(Usuario).filter(Usuario.id == usuario_id).first()
    assert usuario is not None
    usuario.role = "adm"
    db_session.commit()
    db_session.refresh(usuario)

    # Fazer login para obter token com role já atualizado
    resp = client.post(
        "/auth/login",
        json={
            "email": usuario_adm_dados["email"],
            "senha": usuario_adm_dados["senha"],
        },
    )
    assert resp.status_code == 200, f"Falha ao logar usuário adm: {resp.text}"
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Contato de exemplo
# ---------------------------------------------------------------------------

@pytest.fixture()
def contato_exemplo(db_session):
    """
    Cria um contato diretamente via contato_service e retorna o objeto Contato.
    Não depende de autenticação — ideal para testes de leitura.
    """
    dados = ContatoCriar(
        nome="Maria Contato",
        email="maria@contato.com",
        telefone="11999999999",
        empresa="Empresa Teste",
        observacoes="Observação de teste",
    )
    return contato_service.criar_contato(db_session, dados)


# ---------------------------------------------------------------------------
# Isolamento do rate limiter entre testes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_limiter():
    """
    Reseta o storage interno do slowapi antes de cada teste.
    Evita que testes de autenticação falhem com HTTP 429 devido ao acúmulo
    de requisições de testes anteriores no mesmo processo.
    """
    from app.limiter import limiter

    # O storage padrão do slowapi é um MemoryStorage com método reset()
    # Se o storage não tiver reset (ex.: Redis), este bloco é seguro por ignorar o erro.
    try:
        limiter._storage.reset()
    except Exception:
        pass
    yield
