import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCriar
from app.services.auth_service import hash_senha, verificar_senha

# Logger nomeado por módulo — TASK-05 (B.1).
logger = logging.getLogger(__name__)

# Decisão de design (TASK-05): NÃO converter o HTTPException(status=400) de
# unicidade de e-mail para ConflictError. O plano sugere ConflictError em 409,
# mas o endpoint sempre devolveu 400 (preservado por RNF-02 e pelo helper
# garantir_unicidade). Mudar para 409 quebraria contrato público; mudar para
# ConflictError quebraria o status code visível. A escolha conservadora é
# manter HTTPException(400) intacto aqui.


def buscar_por_email(db: Session, email: str) -> Usuario | None:
    """Retorna o usuário com o e-mail informado ou None se não encontrado."""
    # Padrão SQLAlchemy 2.0: select() + db.scalars() para retorno do modelo
    stmt = select(Usuario).where(Usuario.email == email)
    return db.scalars(stmt).first()


def criar_usuario(db: Session, dados: UsuarioCriar) -> Usuario:
    """
    Cria um novo usuário no banco de dados.
    Levanta HTTPException 400 se o e-mail já estiver em uso.
    """
    if buscar_por_email(db, dados.email):
        # Não logar o email para evitar exposição de PII em arquivos de log.
        logger.warning("tentativa de cadastro com e-mail ja existente")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado.",
        )

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        role="default",  # todos os novos usuários começam sem privilégios de adm
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    logger.info("usuario criado id=%s role=%s", novo_usuario.id, novo_usuario.role)
    return novo_usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> Usuario | None:
    """
    Valida as credenciais do usuário.
    Retorna o objeto Usuario se válidas, ou None caso contrário.
    """
    usuario = buscar_por_email(db, email)
    if usuario is None:
        return None
    if not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario
