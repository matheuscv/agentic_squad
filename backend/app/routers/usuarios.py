from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import (
    RoleAtualizacao,
    UsuarioAtualizacao,
    UsuarioCriar,
    UsuarioResposta,
)
from app.services.usuario_service import criar_usuario

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


# ---------------------------------------------------------------------------
# Helper: busca usuário por ID ou levanta 404
# ---------------------------------------------------------------------------

def _get_or_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com id {usuario_id} não encontrado.",
        )
    return usuario


# ---------------------------------------------------------------------------
# POST /usuarios/ — cadastro público (sem autenticação)
# ---------------------------------------------------------------------------

@router.post("/", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
def registrar_usuario(dados: UsuarioCriar, db: Session = Depends(get_db)):
    """
    Endpoint público para cadastro de novos usuários.
    Retorna 201 com os dados do usuário criado (sem senha).
    """
    return criar_usuario(db, dados)


# ---------------------------------------------------------------------------
# GET /usuarios/ — listar todos (somente adm)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[UsuarioResposta])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna todos os usuários cadastrados.
    Requer role 'adm'; usuários 'default' recebem HTTP 403.
    """
    if current_user.role != "adm":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return db.query(Usuario).all()


# ---------------------------------------------------------------------------
# GET /usuarios/{id} — detalhar um usuário (adm ou próprio usuário)
# ---------------------------------------------------------------------------

@router.get("/{usuario_id}", response_model=UsuarioResposta)
def detalhar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna os dados de um usuário específico.
    Permitido para role 'adm' ou para o próprio usuário autenticado.
    HTTP 404 se o ID não existir; HTTP 403 se 'default' tentar acessar outro usuário.
    """
    usuario = _get_or_404(db, usuario_id)

    if current_user.role != "adm" and current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para visualizar dados de outro usuário.",
        )

    return usuario


# ---------------------------------------------------------------------------
# PUT /usuarios/{id} — atualizar nome e/ou email (adm ou próprio usuário)
# ---------------------------------------------------------------------------

@router.put("/{usuario_id}", response_model=UsuarioResposta)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioAtualizacao,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Atualiza nome e/ou email de um usuário.
    Permitido para role 'adm' ou para o próprio usuário autenticado.
    HTTP 400 se o novo email já estiver em uso por outro usuário.
    HTTP 404 se o ID não existir.
    """
    usuario = _get_or_404(db, usuario_id)

    if current_user.role != "adm" and current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para alterar dados de outro usuário.",
        )

    if dados.nome is not None:
        usuario.nome = dados.nome

    if dados.email is not None:
        # Verificar unicidade: ignorar o próprio registro na comparação
        conflito = (
            db.query(Usuario)
            .filter(Usuario.email == dados.email, Usuario.id != usuario_id)
            .first()
        )
        if conflito:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail já está em uso por outro usuário.",
            )
        usuario.email = dados.email

    db.commit()
    db.refresh(usuario)
    return usuario


# ---------------------------------------------------------------------------
# DELETE /usuarios/{id} — remover usuário (somente adm)
# ---------------------------------------------------------------------------

@router.delete("/{usuario_id}", status_code=status.HTTP_200_OK)
def remover_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Remove um usuário pelo ID.
    Requer role 'adm'.
    HTTP 400 se o admin tentar excluir a si mesmo (RN-F2-02).
    HTTP 404 se o ID não existir.
    """
    if current_user.role != "adm":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )

    # Regra de negócio: admin não pode excluir a si mesmo
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrador não pode excluir a própria conta.",
        )

    usuario = _get_or_404(db, usuario_id)

    db.delete(usuario)
    db.commit()
    return {"detail": f"Usuário {usuario_id} removido com sucesso."}


# ---------------------------------------------------------------------------
# PATCH /usuarios/{id}/role — alterar role (somente adm)
# ---------------------------------------------------------------------------

@router.patch("/{usuario_id}/role", response_model=UsuarioResposta)
def atualizar_role(
    usuario_id: int,
    dados: RoleAtualizacao,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Altera a role de um usuário ('default' ou 'adm').
    Requer role 'adm'.
    HTTP 400 se o admin tentar rebaixar a si mesmo (RN-F2-02).
    HTTP 404 se o ID não existir.
    """
    if current_user.role != "adm":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )

    # Regra de negócio: admin não pode alterar a própria role
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrador não pode alterar a própria role.",
        )

    usuario = _get_or_404(db, usuario_id)

    usuario.role = dados.role
    db.commit()
    db.refresh(usuario)
    return usuario
