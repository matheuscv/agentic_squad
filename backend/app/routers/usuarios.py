from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.usuario import UsuarioCriar, UsuarioResposta
from app.services.usuario_service import criar_usuario

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("/", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
def registrar_usuario(dados: UsuarioCriar, db: Session = Depends(get_db)):
    """
    Endpoint público para cadastro de novos usuários.
    Retorna 201 com os dados do usuário criado (sem senha).
    """
    return criar_usuario(db, dados)
