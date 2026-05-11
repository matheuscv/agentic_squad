"""Schemas Pydantic v2 para o recurso Contato."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class ContatoCriar(BaseModel):
    """Payload para criação de um novo contato."""

    nome: str
    email: EmailStr
    telefone: str | None = None
    empresa: str | None = None
    observacoes: str | None = None

    @field_validator("nome")
    @classmethod
    def nome_nao_vazio(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("nome não pode ser vazio")
        return v


class ContatoAtualizar(BaseModel):
    """Payload para atualização parcial (PATCH semantics) de um contato.

    Todos os campos são opcionais — apenas os fornecidos (não-None) serão
    aplicados pelo service.
    """

    nome: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None
    empresa: str | None = None
    observacoes: str | None = None


class ContatoResposta(BaseModel):
    """Schema de resposta — espelha o modelo ORM Contato."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    telefone: str | None
    empresa: str | None
    observacoes: str | None
    criado_em: datetime
    atualizado_em: datetime
