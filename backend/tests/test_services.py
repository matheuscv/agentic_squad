"""
Testes unitários diretos nas funções de serviço — TASK-10 / RF-F3-01.

Cobre (sem camada HTTP):
- auth_service: hash_senha, verificar_senha, criar_token, decodificar_token
- usuario_service: criar_usuario, buscar_por_email, autenticar_usuario
- contato_service: criar_contato, listar_contatos, buscar_contato,
                   atualizar_contato, patch_contato, excluir_contato (soft delete),
                   listar_lixeira
- Schemas Pydantic: ContatoCriar, ContatoAtualizar, ContatoPatch, UsuarioCriar, LoginRequest

Padrão: AAA (Arrange / Act / Assert)
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.services import auth_service, contato_service, usuario_service
from app.schemas.contato import ContatoCriar, ContatoAtualizar, ContatoPatch
from app.schemas.usuario import UsuarioCriar
from app.schemas.auth import LoginRequest


# ===========================================================================
# auth_service — hash e verificação de senha
# ===========================================================================

def test_hash_senha_gera_hash_diferente_do_original():
    """O hash gerado não deve ser igual à senha em texto puro."""
    # Arrange
    senha = "minhasenha123"

    # Act
    resultado = auth_service.hash_senha(senha)

    # Assert
    assert resultado != senha


def test_hash_senha_gera_hashes_distintos_para_mesma_senha():
    """Duas chamadas com a mesma senha devem gerar hashes diferentes (salt aleatório)."""
    # Arrange
    senha = "mesmasenha"

    # Act
    hash1 = auth_service.hash_senha(senha)
    hash2 = auth_service.hash_senha(senha)

    # Assert
    assert hash1 != hash2


def test_verificar_senha_retorna_true_para_senha_correta():
    """verificar_senha deve retornar True quando a senha bate com o hash."""
    # Arrange
    senha = "correta456"
    hash_ = auth_service.hash_senha(senha)

    # Act / Assert
    assert auth_service.verificar_senha(senha, hash_) is True


def test_verificar_senha_retorna_false_para_senha_errada():
    """verificar_senha deve retornar False para senha incorreta."""
    # Arrange
    hash_ = auth_service.hash_senha("senha_original")

    # Act / Assert
    assert auth_service.verificar_senha("senha_errada", hash_) is False


def test_verificar_senha_sensivel_a_maiusculas():
    """A verificação de senha deve ser case-sensitive."""
    # Arrange
    senha = "SenhaMaiuscula"
    hash_ = auth_service.hash_senha(senha)

    # Act / Assert
    assert auth_service.verificar_senha("senhaMaiuscula", hash_) is False


# ===========================================================================
# auth_service — criação e decodificação de token JWT
# ===========================================================================

def test_criar_token_retorna_string_nao_vazia():
    """criar_token deve retornar uma string com conteúdo."""
    # Act
    token = auth_service.criar_token({"sub": "teste@test.com"})

    # Assert
    assert isinstance(token, str)
    assert len(token) > 0


def test_decodificar_token_retorna_email_correto():
    """O email no payload do token deve ser recuperado na decodificação."""
    # Arrange
    email = "usuario@test.com"
    token = auth_service.criar_token({"sub": email})

    # Act
    token_data = auth_service.decodificar_token(token)

    # Assert
    assert token_data.email == email


def test_decodificar_token_invalido_levanta_401():
    """Um token mal-formado deve levantar HTTPException com status 401."""
    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decodificar_token("isso.nao.e.um.token")
    assert exc_info.value.status_code == 401


def test_decodificar_token_expirado_levanta_401():
    """Token com expiração negativa (já expirado) deve levantar HTTPException 401."""
    # Arrange
    token = auth_service.criar_token(
        {"sub": "expirado@test.com"},
        expires_delta=timedelta(seconds=-1),
    )

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decodificar_token(token)
    assert exc_info.value.status_code == 401


def test_criar_token_com_expires_delta_customizado():
    """Token criado com expires_delta explícito deve ser decodificável enquanto válido."""
    # Arrange / Act
    token = auth_service.criar_token(
        {"sub": "exp@test.com"},
        expires_delta=timedelta(minutes=30),
    )
    token_data = auth_service.decodificar_token(token)

    # Assert
    assert token_data.email == "exp@test.com"


def test_decodificar_token_sem_sub_levanta_401():
    """Token sem campo 'sub' no payload deve levantar HTTPException 401."""
    # Arrange
    token = auth_service.criar_token({"outro_campo": "valor"})

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        auth_service.decodificar_token(token)
    assert exc_info.value.status_code == 401


# ===========================================================================
# usuario_service — criar_usuario e buscar_por_email
# ===========================================================================

def test_criar_usuario_persiste_e_retorna_role_default(db_session):
    """Novo usuário deve ter role 'default' e ser encontrado no banco."""
    # Arrange
    dados = UsuarioCriar(nome="Fulano", email="fulano@test.com", senha="senha123")

    # Act
    usuario = usuario_service.criar_usuario(db_session, dados)

    # Assert
    assert usuario.id is not None
    assert usuario.role == "default"
    assert usuario.email == "fulano@test.com"


def test_criar_usuario_armazena_hash_nao_senha_clara(db_session):
    """senha_hash do usuário criado não deve ser igual à senha original."""
    # Arrange
    dados = UsuarioCriar(nome="Hash Test", email="hash@test.com", senha="senhaclara")

    # Act
    usuario = usuario_service.criar_usuario(db_session, dados)

    # Assert
    assert usuario.senha_hash != "senhaclara"


def test_criar_usuario_email_duplicado_levanta_400(db_session):
    """Segundo usuário com mesmo email deve levantar HTTPException 400."""
    # Arrange
    dados = UsuarioCriar(nome="Primeiro", email="dup@test.com", senha="senha123")
    usuario_service.criar_usuario(db_session, dados)
    dados2 = UsuarioCriar(nome="Segundo", email="dup@test.com", senha="outrasenha")

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        usuario_service.criar_usuario(db_session, dados2)
    assert exc_info.value.status_code == 400


def test_buscar_por_email_encontra_usuario_existente(db_session):
    """buscar_por_email deve retornar o usuário correto."""
    # Arrange
    dados = UsuarioCriar(nome="Busca", email="busca@test.com", senha="senha123")
    usuario_service.criar_usuario(db_session, dados)

    # Act
    encontrado = usuario_service.buscar_por_email(db_session, "busca@test.com")

    # Assert
    assert encontrado is not None
    assert encontrado.email == "busca@test.com"


def test_buscar_por_email_retorna_none_para_email_inexistente(db_session):
    """buscar_por_email deve retornar None quando o email não existe."""
    # Act
    resultado = usuario_service.buscar_por_email(db_session, "inexistente@test.com")

    # Assert
    assert resultado is None


# ===========================================================================
# usuario_service — autenticar_usuario
# ===========================================================================

def test_autenticar_usuario_credenciais_validas(db_session):
    """autenticar_usuario deve retornar o objeto Usuario para credenciais corretas."""
    # Arrange
    dados = UsuarioCriar(nome="Autentica", email="auth@test.com", senha="senha123")
    usuario_service.criar_usuario(db_session, dados)

    # Act
    resultado = usuario_service.autenticar_usuario(db_session, "auth@test.com", "senha123")

    # Assert
    assert resultado is not None
    assert resultado.email == "auth@test.com"


def test_autenticar_usuario_senha_errada_retorna_none(db_session):
    """autenticar_usuario deve retornar None para senha incorreta."""
    # Arrange
    dados = UsuarioCriar(nome="SenhaErrada", email="wrong@test.com", senha="correta")
    usuario_service.criar_usuario(db_session, dados)

    # Act
    resultado = usuario_service.autenticar_usuario(db_session, "wrong@test.com", "errada")

    # Assert
    assert resultado is None


def test_autenticar_usuario_email_inexistente_retorna_none(db_session):
    """autenticar_usuario deve retornar None para email não cadastrado."""
    # Act
    resultado = usuario_service.autenticar_usuario(db_session, "nao@existe.com", "qualquer")

    # Assert
    assert resultado is None


# ===========================================================================
# contato_service — criar_contato
# ===========================================================================

def test_criar_contato_service(db_session):
    """criar_contato deve persistir nome e email corretamente (caminho feliz)."""
    # Arrange
    dados = ContatoCriar(nome="Contato Novo", email="novo@contato.com")

    # Act
    contato = contato_service.criar_contato(db_session, dados)

    # Assert
    assert contato.id is not None
    assert contato.nome == "Contato Novo"
    assert contato.email == "novo@contato.com"


def test_criar_contato_email_duplicado_service(db_session):
    """criar_contato com e-mail duplicado deve levantar HTTPException 400."""
    # Arrange
    contato_service.criar_contato(db_session, ContatoCriar(nome="Primeiro", email="dup@contato.com"))

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        contato_service.criar_contato(db_session, ContatoCriar(nome="Segundo", email="dup@contato.com"))
    assert exc_info.value.status_code == 400


def test_criar_contato_campos_opcionais_none_por_padrao(db_session):
    """Campos opcionais não fornecidos devem ser None no objeto persistido."""
    # Arrange
    dados = ContatoCriar(nome="Sem Opcionais", email="senopc@test.com")

    # Act
    contato = contato_service.criar_contato(db_session, dados)

    # Assert
    assert contato.telefone is None
    assert contato.empresa is None
    assert contato.observacoes is None


# ===========================================================================
# contato_service — buscar_contato
# ===========================================================================

def test_buscar_contato_existente_retorna_objeto(db_session):
    """buscar_contato deve retornar o objeto correto pelo id."""
    # Arrange
    criado = contato_service.criar_contato(db_session, ContatoCriar(nome="Buscado", email="buscado@test.com"))

    # Act
    encontrado = contato_service.buscar_contato(db_session, criado.id)

    # Assert
    assert encontrado.id == criado.id
    assert encontrado.email == "buscado@test.com"


def test_buscar_contato_inexistente_service(db_session):
    """buscar_contato com id inexistente deve levantar HTTPException 404."""
    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        contato_service.buscar_contato(db_session, 99999)
    assert exc_info.value.status_code == 404


# ===========================================================================
# contato_service — listar_contatos
# ===========================================================================

def test_listar_contatos_retorna_lista_vazia_quando_banco_vazio(db_session):
    """listar_contatos deve retornar lista vazia quando não há registros."""
    # Act
    items, total = contato_service.listar_contatos(db_session)

    # Assert
    assert items == []
    assert total == 0


def test_listar_contatos_retorna_todos_sem_filtro(db_session):
    """listar_contatos sem busca deve retornar todos os contatos inseridos."""
    # Arrange
    contato_service.criar_contato(db_session, ContatoCriar(nome="A", email="a@test.com"))
    contato_service.criar_contato(db_session, ContatoCriar(nome="B", email="b@test.com"))

    # Act
    items, total = contato_service.listar_contatos(db_session)

    # Assert
    assert len(items) == 2
    assert total == 2


def test_listar_contatos_nao_inclui_deletados(db_session):
    """listar_contatos não deve retornar contatos com soft delete aplicado."""
    # Arrange
    c1 = contato_service.criar_contato(db_session, ContatoCriar(nome="Ativo", email="ativo@test.com"))
    c2 = contato_service.criar_contato(db_session, ContatoCriar(nome="Deletado", email="del@test.com"))
    contato_service.excluir_contato(db_session, c2.id)

    # Act
    items, total = contato_service.listar_contatos(db_session)

    # Assert
    ids = [c.id for c in items]
    assert c1.id in ids
    assert c2.id not in ids
    assert total == 1


# ===========================================================================
# contato_service — atualizar_contato
# ===========================================================================

def test_atualizar_contato_somente_nome(db_session):
    """Atualização parcial deve alterar apenas o nome, mantendo os demais campos."""
    # Arrange
    criado = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Original", email="orig@test.com", empresa="EmpresaX"),
    )
    dados = ContatoAtualizar(nome="Atualizado")

    # Act
    atualizado = contato_service.atualizar_contato(db_session, criado.id, dados)

    # Assert
    assert atualizado.nome == "Atualizado"
    assert atualizado.email == "orig@test.com"
    assert atualizado.empresa == "EmpresaX"


def test_atualizar_contato_inexistente_levanta_404(db_session):
    """atualizar_contato com id inexistente deve levantar HTTPException 404."""
    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        contato_service.atualizar_contato(db_session, 99999, ContatoAtualizar(nome="X"))
    assert exc_info.value.status_code == 404


# ===========================================================================
# contato_service — patch_contato (TASK-08)
# ===========================================================================

def test_patch_contato_service(db_session):
    """patch_contato deve atualizar apenas o campo fornecido."""
    # Arrange
    criado = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Patch Me", email="patch@test.com", empresa="OldCo"),
    )
    dados = ContatoPatch(empresa="NewCo")

    # Act
    atualizado = contato_service.patch_contato(db_session, criado.id, dados)

    # Assert
    assert atualizado.empresa == "NewCo"
    assert atualizado.nome == "Patch Me"
    assert atualizado.email == "patch@test.com"


def test_patch_contato_email_duplicado_levanta_400(db_session):
    """patch_contato com e-mail já usado por outro contato deve levantar HTTPException 400."""
    # Arrange
    c1 = contato_service.criar_contato(db_session, ContatoCriar(nome="C1", email="c1@test.com"))
    c2 = contato_service.criar_contato(db_session, ContatoCriar(nome="C2", email="c2@test.com"))
    dados = ContatoPatch(email=c1.email)

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        contato_service.patch_contato(db_session, c2.id, dados)
    assert exc_info.value.status_code == 400


def test_patch_contato_inexistente_levanta_404(db_session):
    """patch_contato com id inexistente deve levantar HTTPException 404."""
    # Arrange
    dados = ContatoPatch(nome="X")

    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        contato_service.patch_contato(db_session, 99999, dados)
    assert exc_info.value.status_code == 404


# ===========================================================================
# contato_service — excluir_contato (soft delete, TASK-09)
# ===========================================================================

def test_excluir_contato_soft_delete_service(db_session):
    """excluir_contato deve preencher deletado_em em vez de remover a linha."""
    # Arrange
    criado = contato_service.criar_contato(
        db_session, ContatoCriar(nome="Soft Del", email="softdel@test.com")
    )
    assert criado.deletado_em is None

    # Act
    contato_service.excluir_contato(db_session, criado.id)

    # Assert — busca_contato levanta 404 (registro existe mas deletado_em preenchido)
    with pytest.raises(HTTPException) as exc_info:
        contato_service.buscar_contato(db_session, criado.id)
    assert exc_info.value.status_code == 404

    # Confirma diretamente no banco que deletado_em foi preenchido
    db_session.refresh(criado)
    assert criado.deletado_em is not None


def test_excluir_contato_inexistente_levanta_404(db_session):
    """excluir_contato com id inexistente deve levantar HTTPException 404."""
    # Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        contato_service.excluir_contato(db_session, 88888)
    assert exc_info.value.status_code == 404


# ===========================================================================
# contato_service — listar_lixeira (TASK-09)
# ===========================================================================

def test_listar_lixeira_service(db_session):
    """listar_lixeira deve retornar apenas contatos com deletado_em preenchido."""
    # Arrange
    c_ativo = contato_service.criar_contato(
        db_session, ContatoCriar(nome="Ativo", email="ativo@lixeira.com")
    )
    c_del = contato_service.criar_contato(
        db_session, ContatoCriar(nome="Deletado", email="del@lixeira.com")
    )
    contato_service.excluir_contato(db_session, c_del.id)

    # Act
    items, total = contato_service.listar_lixeira(db_session)

    # Assert
    assert total == 1
    ids = [c.id for c in items]
    assert c_del.id in ids
    assert c_ativo.id not in ids


def test_listar_lixeira_vazia_quando_nenhum_deletado(db_session):
    """listar_lixeira deve retornar lista vazia quando não há soft deletes."""
    # Arrange
    contato_service.criar_contato(db_session, ContatoCriar(nome="Ativo", email="ativo2@lixeira.com"))

    # Act
    items, total = contato_service.listar_lixeira(db_session)

    # Assert
    assert items == []
    assert total == 0


def test_listar_lixeira_item_contem_deletado_em(db_session):
    """Cada item na lixeira deve ter deletado_em preenchido."""
    # Arrange
    criado = contato_service.criar_contato(
        db_session, ContatoCriar(nome="Del Check", email="delcheck@test.com")
    )
    contato_service.excluir_contato(db_session, criado.id)

    # Act
    items, _ = contato_service.listar_lixeira(db_session)

    # Assert
    assert all(c.deletado_em is not None for c in items)


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


def test_contato_patch_body_vazio_levanta_validation_error():
    """ContatoPatch sem nenhum campo deve levantar ValidationError (RN-F3-02)."""
    with pytest.raises(ValidationError):
        ContatoPatch()


def test_contato_patch_telefone_invalido_levanta_validation_error():
    """ContatoPatch com telefone sem máscara deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        ContatoPatch(telefone="11999999999")


def test_contato_patch_telefone_valido_celular():
    """ContatoPatch com telefone no formato celular deve ser aceito."""
    dados = ContatoPatch(telefone="(11) 99999-9999")
    assert dados.telefone == "(11) 99999-9999"


def test_contato_patch_telefone_valido_fixo():
    """ContatoPatch com telefone no formato fixo deve ser aceito."""
    dados = ContatoPatch(telefone="(11) 3456-7890")
    assert dados.telefone == "(11) 3456-7890"


def test_usuario_criar_senha_curta_levanta_validation_error():
    """UsuarioCriar com senha menor que 6 caracteres deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="Curta", email="curta@test.com", senha="abc")


def test_usuario_criar_email_invalido_levanta_validation_error():
    """UsuarioCriar com email inválido deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="X", email="invalido", senha="senha123")


def test_login_request_email_invalido_levanta_validation_error():
    """LoginRequest com email mal-formado deve levantar ValidationError."""
    with pytest.raises(ValidationError):
        LoginRequest(email="nao_email", senha="123456")
