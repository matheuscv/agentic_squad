from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioResposta
from app.services.auth_service import criar_token
from app.services.usuario_service import autenticar_usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, dados: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica o usuário via e-mail e senha (JSON body).
    Retorna um JWT Bearer token em caso de sucesso.
    """
    usuario = autenticar_usuario(db, dados.email, dados.senha)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # O campo 'sub' (subject) do JWT armazena o e-mail como identificador
    token = criar_token(data={"sub": usuario.email})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioResposta)
def me(usuario=Depends(get_current_user)):
    """Retorna os dados do usuário autenticado pelo token JWT."""
    return usuario
