from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Payload JSON para o endpoint POST /auth/login."""

    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    """Resposta do login com o JWT gerado."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Dados extraídos do payload do JWT após decodificação."""

    email: str | None = None
