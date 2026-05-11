"""
Testes unitários para os services do backend, sem camada HTTP.

Cobre:
- auth_service: hash_senha, verificar_senha, criar_token, decodificar_token
- usuario_service: criar_usuario, buscar_por_email, autenticar_usuario
- contato_service: criar_contato, listar_contatos, buscar_contato,
                   atualizar_contato, excluir_contato
- schemas Pydantic: ContatoCriar, ContatoAtualizar, UsuarioCriar, LoginRequest
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.services import auth_service, contato_service, usuario_service
from app.schemas.contato import ContatoCriar, ContatoAtualizar
from app.schemas.usuario import UsuarioCriar
from app.schemas.auth import LoginRequest


# ===========================================================================
# auth_service — hash e verificação de senha
# ===========================================================================

def test_hash_senha_gera_hash_diferente_do_original():
    """O hash gerado não deve ser igual à senha em texto puro."""
    senha = "minhasenha123"
    resultado = auth_service.hash_senha(senha)
    assert resultado != senha


def test_hash_senha_gera_hashes_distintos_para_mesma_senha():
    """Duas chamadas com a mesma senha devem gerar hashes diferentes (salt aleatório)."""
    senha = "mesmasenha"
    hash1 = auth_service.hash_senha(senha)
    hash2 = auth_service.hash_senha(senha)
    assert hash1 != hash2


def test_verificar_senha_retorna_true_para_senha_correta():
    """verificar_senha deve retornar True quando a senha bate com o hash."""
    senha = "correta456"
    hash_ = auth_service.hash_senha(senha)
    assert auth_service.verificar_senha(senha, hash_) is True


def test_verificar_senha_retorna_false_para_senha_errada():
    """verificar_senha deve retornar False para senha incorreta."""
    hash_ = auth_service.hash_senha("senha_original")
    assert auth_service.verificar_senha("senha_errada", hash_) is False


def test_verificar_senha_sensivel_a_maiusculas():
    """A verificação de senha deve ser case-sensitive."""
    senha = "SenhaMaiuscula"
    hash_ = auth_service.hash_senha(senha)
    assert auth_service.verificar_senha("senhaMaiuscula", hash_) is False


# ===========================================================================
# auth_service — criação e decodificação de token JWT
# ===========================================================================

def test_criar_token_retorna_string_nao_vazia():
    """criar_token deve retornar uma string com conteúdo."""
    token = auth_service.criar_token({"sub": "teste@test.com"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decodificar_token_retorna_email_correto():
    """O email no payload do token deve ser recuperado na decodificação."""
    email = "usuario@test.com"
    token = auth_service.criar_token({"sub": email})
    token_data = auth_service.decodificar_token(token)
    assert token_data.email == email


def test_decodificar_token_invalido_levanta_401():
    """Um token mal-formado deve levantar HTTPException com status 401."""
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decodificar_token("isso.nao.e.um.token")
    assert exc_info.value.status_code == 401


def test_decodificar_token_expirado_levanta_401():
    """Token com expiração negativa (já expirado) deve levantar HTTPException 401."""
    token = auth_service.criar_token(
        {"sub": "expirado@test.com"},
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decodificar_token(token)
    assert exc_info.value.status_code == 401


def test_criar_token_com_expires_delta_customizado():
    """Token criado com expires_delta explícito deve ser decodificável enquanto válido."""
    token = auth_service.criar_token(
        {"sub": "exp@test.com"},
        expires_delta=timedelta(minutes=30),
    )
    token_data = auth_service.decodificar_token(token)
    assert token_data.email == "exp@test.com"


def test_decodificar_token_sem_sub_levanta_401():
    """Token sem campo 'sub' no payload deve levantar HTTPException 401."""
    # Cria token sem 'sub' — decodificar_token exige o campo
    token = auth_service.criar_token({"outro_campo": "valor"})
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decodificar_token(token)
    assert exc_info.value.status_code == 401


# ===========================================================================
# usuario_service — criar_usuario e buscar_por_email
# ===========================================================================

def test_criar_usuario_persiste_e_retorna_role_default(db_session):
    """Novo usuário deve ter role 'default' e ser encontrado no banco."""
    dados = UsuarioCriar(nome="Fulano", email="fulano@test.com", senha="senha123")
    usuario = usuario_service.criar_usuario(db_session, dados)
    assert usuario.id is not None
    assert usuario.role == "default"
    assert usuario.email == "fulano@test.com"


def test_criar_usuario_armazena_hash_nao_senha_clara(db_session):
    """senha_hash do usuário criado não deve ser igual à senha original."""
    dados = UsuarioCriar(nome="Hash Test", email="hash@test.com", senha="senhaclara")
    usuario = usuario_service.criar_usuario(db_session, dados)
    assert usuario.senha_hash != "senhaclara"


def test_criar_usuario_email_duplicado_levanta_400(db_session):
    """Segundo usuário com mesmo email deve levantar HTTPException 400."""
    dados = UsuarioCriar(nome="Primeiro", email="dup@test.com", senha="senha123")
    usuario_service.criar_usuario(db_session, dados)

    dados2 = UsuarioCriar(nome="Segundo", email="dup@test.com", senha="outrasenha")
    with pytest.raises(HTTPException) as exc_info:
        usuario_service.criar_usuario(db_session, dados2)
    assert exc_info.value.status_code == 400


def test_buscar_por_email_encontra_usuario_existente(db_session):
    """buscar_por_email deve retornar o usuário correto."""
    dados = UsuarioCriar(nome="Busca", email="busca@test.com", senha="senha123")
    usuario_service.criar_usuario(db_session, dados)
    encontrado = usuario_service.buscar_por_email(db_session, "busca@test.com")
    assert encontrado is not None
    assert encontrado.email == "busca@test.com"


def test_buscar_por_email_retorna_none_para_email_inexistente(db_session):
    """buscar_por_email deve retornar None quando o email não existe."""
    resultado = usuario_service.buscar_por_email(db_session, "inexistente@test.com")
    assert resultado is None


# ===========================================================================
# usuario_service — autenticar_usuario
# ===========================================================================

def test_autenticar_usuario_credenciais_validas(db_session):
    """autenticar_usuario deve retornar o objeto Usuario para credenciais corretas."""
    dados = UsuarioCriar(nome="Autentica", email="auth@test.com", senha="senha123")
    usuario_service.criar_usuario(db_session, dados)
    resultado = usuario_service.autenticar_usuario(db_session, "auth@test.com", "senha123")
    assert resultado is not None
    assert resultado.email == "auth@test.com"


def test_autenticar_usuario_senha_errada_retorna_none(db_session):
    """autenticar_usuario deve retornar None para senha incorreta."""
    dados = UsuarioCriar(nome="SenhaErrada", email="wrong@test.com", senha="correta")
    usuario_service.criar_usuario(db_session, dados)
    resultado = usuario_service.autenticar_usuario(db_session, "wrong@test.com", "errada")
    assert resultado is None


def test_autenticar_usuario_email_inexistente_retorna_none(db_session):
    """autenticar_usuario deve retornar None para email não cadastrado."""
    resultado = usuario_service.autenticar_usuario(db_session, "nao@existe.com", "qualquer")
    assert resultado is None


# ===========================================================================
# contato_service — criar_contato
# ===========================================================================

def test_criar_contato_persiste_campos_obrigatorios(db_session):
    """criar_contato deve persistir nome e email corretamente."""
    dados = ContatoCriar(nome="Contato Novo", email="novo@contato.com")
    contato = contato_service.criar_contato(db_session, dados)
    assert contato.id is not None
    assert contato.nome == "Contato Novo"
    assert contato.email == "novo@contato.com"


def test_criar_contato_campos_opcionais_none_por_padrao(db_session):
    """Campos opcionais não fornecidos devem ser None no objeto persistido."""
    dados = ContatoCriar(nome="Sem Opcionais", email="senopc@test.com")
    contato = contato_service.criar_contato(db_session, dados)
    assert contato.telefone is None
    assert contato.empresa is None
    assert contato.observacoes is None


def test_criar_contato_com_todos_os_campos(db_session):
    """Todos os campos fornecidos devem ser persistidos corretamente."""
    dados = ContatoCriar(
        nome="Completo",
        email="completo@test.com",
        telefone="11912345678",
        empresa="ACME",
        observacoes="Cliente VIP",
    )
    contato = contato_service.criar_contato(db_session, dados)
    assert contato.telefone == "11912345678"
    assert contato.empresa == "ACME"
    assert contato.observacoes == "Cliente VIP"


def test_criar_contato_email_duplicado_levanta_400(db_session):
    """Segundo contato com mesmo email deve levantar HTTPException 400."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="Primeiro", email="dup@contato.com"))
    with pytest.raises(HTTPException) as exc_info:
        contato_service.criar_contato(db_session, ContatoCriar(nome="Segundo", email="dup@contato.com"))
    assert exc_info.value.status_code == 400


# ===========================================================================
# contato_service — listar_contatos
# ===========================================================================

def test_listar_contatos_retorna_lista_vazia_quando_banco_vazio(db_session):
    """listar_contatos deve retornar lista vazia quando não há registros."""
    resultado = contato_service.listar_contatos(db_session)
    assert resultado == []


def test_listar_contatos_retorna_todos_sem_filtro(db_session):
    """listar_contatos sem busca deve retornar todos os contatos inseridos."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="A", email="a@test.com"))
    contato_service.criar_contato(db_session, ContatoCriar(nome="B", email="b@test.com"))
    resultado = contato_service.listar_contatos(db_session)
    assert len(resultado) == 2


def test_listar_contatos_busca_por_nome(db_session):
    """Busca por nome deve retornar apenas contatos correspondentes."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="Ana Lima", email="ana@test.com"))
    contato_service.criar_contato(db_session, ContatoCriar(nome="Carlos Melo", email="carlos@test.com"))
    resultado = contato_service.listar_contatos(db_session, busca="Ana")
    assert len(resultado) == 1
    assert resultado[0].nome == "Ana Lima"


def test_listar_contatos_busca_por_email(db_session):
    """Busca pelo email deve retornar o contato correto."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="Teste Email", email="unico@empresa.com"))
    contato_service.criar_contato(db_session, ContatoCriar(nome="Outro", email="outro@outro.com"))
    resultado = contato_service.listar_contatos(db_session, busca="unico@empresa.com")
    assert len(resultado) == 1
    assert resultado[0].email == "unico@empresa.com"


def test_listar_contatos_busca_por_empresa(db_session):
    """Busca pelo nome da empresa deve retornar contatos correspondentes."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="F1", email="f1@test.com", empresa="TechCorp"))
    contato_service.criar_contato(db_session, ContatoCriar(nome="F2", email="f2@test.com", empresa="OldCo"))
    resultado = contato_service.listar_contatos(db_session, busca="TechCorp")
    assert len(resultado) == 1
    assert resultado[0].empresa == "TechCorp"


def test_listar_contatos_busca_case_insensitive(db_session):
    """Busca em maiúsculas deve encontrar registros com nome em minúsculas e vice-versa."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="zelia moura", email="zelia@test.com"))
    resultado = contato_service.listar_contatos(db_session, busca="ZELIA")
    assert len(resultado) == 1


def test_listar_contatos_busca_sem_resultados_retorna_lista_vazia(db_session):
    """Busca sem correspondência deve retornar lista vazia."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="Pessoa X", email="x@test.com"))
    resultado = contato_service.listar_contatos(db_session, busca="TermoInexistente99")
    assert resultado == []


def test_listar_contatos_busca_string_vazia_retorna_todos(db_session):
    """Busca com string vazia deve se comportar como sem filtro (retornar todos)."""
    contato_service.criar_contato(db_session, ContatoCriar(nome="Alpha", email="alpha@test.com"))
    contato_service.criar_contato(db_session, ContatoCriar(nome="Beta", email="beta@test.com"))
    # String vazia é falsy em Python, logo o service não aplica filtro
    resultado = contato_service.listar_contatos(db_session, busca="")
    assert len(resultado) == 2


# ===========================================================================
# contato_service — buscar_contato
# ===========================================================================

def test_buscar_contato_existente_retorna_objeto(db_session):
    """buscar_contato deve retornar o objeto correto pelo id."""
    criado = contato_service.criar_contato(db_session, ContatoCriar(nome="Buscado", email="buscado@test.com"))
    encontrado = contato_service.buscar_contato(db_session, criado.id)
    assert encontrado.id == criado.id
    assert encontrado.email == "buscado@test.com"


def test_buscar_contato_inexistente_levanta_404(db_session):
    """buscar_contato com id inexistente deve levantar HTTPException 404."""
    with pytest.raises(HTTPException) as exc_info:
        contato_service.buscar_contato(db_session, 99999)
    assert exc_info.value.status_code == 404


# ===========================================================================
# contato_service — atualizar_contato
# ===========================================================================

def test_atualizar_contato_somente_nome(db_session):
    """Atualização parcial deve alterar apenas o nome, mantendo os demais campos."""
    criado = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Original", email="orig@test.com", empresa="EmpresaX"),
    )
    dados = ContatoAtualizar(nome="Atualizado")
    atualizado = contato_service.atualizar_contato(db_session, criado.id, dados)
    assert atualizado.nome == "Atualizado"
    assert atualizado.email == "orig@test.com"
    assert atualizado.empresa == "EmpresaX"


def test_atualizar_contato_multiplos_campos(db_session):
    """Atualização com múltiplos campos deve persistir todos."""
    criado = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Multi", email="multi@test.com"),
    )
    dados = ContatoAtualizar(telefone="11999998888", empresa="NovaCo", observacoes="VIP")
    atualizado = contato_service.atualizar_contato(db_session, criado.id, dados)
    assert atualizado.telefone == "11999998888"
    assert atualizado.empresa == "NovaCo"
    assert atualizado.observacoes == "VIP"


def test_atualizar_contato_payload_vazio_mantem_dados(db_session):
    """Payload sem nenhum campo (todos None) não deve alterar o contato."""
    criado = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Inalterado", email="inal@test.com", empresa="CorpZ"),
    )
    dados = ContatoAtualizar()  # todos None
    atualizado = contato_service.atualizar_contato(db_session, criado.id, dados)
    assert atualizado.nome == "Inalterado"
    assert atualizado.empresa == "CorpZ"


def test_atualizar_contato_inexistente_levanta_404(db_session):
    """atualizar_contato com id inexistente deve levantar HTTPException 404."""
    with pytest.raises(HTTPException) as exc_info:
        contato_service.atualizar_contato(db_session, 99999, ContatoAtualizar(nome="X"))
    assert exc_info.value.status_code == 404


def test_atualizar_contato_atualiza_timestamp(db_session):
    """atualizar_contato deve atualizar o campo atualizado_em."""
    import time
    criado = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Timestamp", email="ts@test.com"),
    )
    ts_criacao = criado.atualizado_em
    time.sleep(0.01)  # garante diferença mínima de tempo
    atualizado = contato_service.atualizar_contato(
        db_session, criado.id, ContatoAtualizar(nome="Novo Nome")
    )
    assert atualizado.atualizado_em >= ts_criacao


# ===========================================================================
# contato_service — excluir_contato
# ===========================================================================

def test_excluir_contato_remove_do_banco(db_session):
    """excluir_contato deve remover o registro; busca posterior deve levantar 404."""
    criado = contato_service.criar_contato(db_session, ContatoCriar(nome="Deletar", email="del@test.com"))
    contato_service.excluir_contato(db_session, criado.id)
    with pytest.raises(HTTPException) as exc_info:
        contato_service.buscar_contato(db_session, criado.id)
    assert exc_info.value.status_code == 404


def test_excluir_contato_inexistente_levanta_404(db_session):
    """excluir_contato com id inexistente deve levantar HTTPException 404."""
    with pytest.raises(HTTPException) as exc_info:
        contato_service.excluir_contato(db_session, 88888)
    assert exc_info.value.status_code == 404


# ===========================================================================
# Schemas Pydantic — validações
# ===========================================================================

def test_contato_criar_nome_vazio_levanta_validation_error():
    """ContatoCriar com nome em branco deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        ContatoCriar(nome="   ", email="ok@test.com")


def test_contato_criar_email_invalido_levanta_validation_error():
    """ContatoCriar com email mal-formado deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        ContatoCriar(nome="Valido", email="nao-e-um-email")


def test_contato_criar_sem_nome_levanta_validation_error():
    """ContatoCriar sem campo nome deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        ContatoCriar(email="semnom@test.com")


def test_contato_criar_sem_email_levanta_validation_error():
    """ContatoCriar sem campo email deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        ContatoCriar(nome="Sem Email")


def test_contato_atualizar_todos_campos_none_valido():
    """ContatoAtualizar sem nenhum campo deve ser instanciado sem erros."""
    dados = ContatoAtualizar()
    assert dados.nome is None
    assert dados.email is None


def test_usuario_criar_senha_curta_levanta_validation_error():
    """UsuarioCriar com senha menor que 6 caracteres deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="Curta", email="curta@test.com", senha="abc")


def test_usuario_criar_email_invalido_levanta_validation_error():
    """UsuarioCriar com email inválido deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="X", email="invalido", senha="senha123")


def test_usuario_criar_sem_nome_levanta_validation_error():
    """UsuarioCriar sem nome deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        UsuarioCriar(email="test@test.com", senha="senha123")


def test_login_request_email_invalido_levanta_validation_error():
    """LoginRequest com email mal-formado deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        LoginRequest(email="nao_email", senha="123456")
