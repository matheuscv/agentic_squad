from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.services.auth_service import decodificar_token
from app.services.usuario_service import buscar_por_email

# tokenUrl aponta para o endpoint de login; usado apenas para documentação OpenAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependência que extrai e valida o JWT do header Authorization.
    Retorna o usuário autenticado ou levanta 401.
    """
    token_data = decodificar_token(token)  # levanta 401 se inválido/expirado

    usuario = buscar_por_email(db, token_data.email)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def require_adm(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependência que garante que apenas administradores acessem o endpoint.
    Levanta HTTPException 403 para usuários sem role 'adm'.
    """
    if usuario.role != "adm":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return usuario
