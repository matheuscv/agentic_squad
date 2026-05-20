import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenData

# Logger nomeado por módulo — TASK-05 (B.1). Adicionado sem mudar comportamento.
logger = logging.getLogger(__name__)


def hash_senha(senha: str) -> str:
    """Gera o hash bcrypt da senha em texto puro."""
    # bcrypt.hashpw exige bytes; encode/decode para trabalhar com str
    senha_bytes = senha.encode("utf-8")
    hashed = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verificar_senha(senha: str, hash: str) -> bool:
    """Compara a senha em texto puro com o hash armazenado."""
    return bcrypt.checkpw(senha.encode("utf-8"), hash.encode("utf-8"))


def criar_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Cria um JWT assinado com a SECRET_KEY e ALGORITHM da config.
    Se expires_delta não for informado, usa ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    payload = data.copy()

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    payload.update({"exp": expire})
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token


def decodificar_token(token: str) -> TokenData:
    """
    Decodifica e valida o JWT.
    Levanta HTTPException 401 se o token for inválido ou expirado.
    """
    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str | None = payload.get("sub")
        if email is None:
            raise credenciais_exception
        return TokenData(email=email)
    except JWTError:
        raise credenciais_exception
