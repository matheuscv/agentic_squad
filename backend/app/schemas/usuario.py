from pydantic import BaseModel, EmailStr, ConfigDict


class UsuarioCriar(BaseModel):
    """Dados necessários para criar um novo usuário."""

    nome: str
    email: EmailStr
    senha: str  # mínimo 6 caracteres validado no service; Pydantic v2 usa Field para min_length

    # Validação de tamanho mínimo da senha via field_validator seria alternativa,
    # mas optamos por Field para manter o schema declarativo e limpo.
    from pydantic import field_validator

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres.")
        return v


class UsuarioResposta(BaseModel):
    """Dados retornados ao cliente — nunca expõe senha_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    role: str
