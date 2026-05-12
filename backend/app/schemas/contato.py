"""Schemas Pydantic v2 para o recurso Contato."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator


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


class ContatoPatch(BaseModel):
    """Payload para atualização parcial via PATCH /contatos/{id}.

    Todos os campos são opcionais. Pelo menos um campo deve ser fornecido
    (não-None); caso contrário, o validador levanta ValueError → HTTP 422.

    Validação de formato de telefone reutiliza a mesma regex de ContatoCriar:
    (DD) DDDD-DDDD  (fixo, 10 dígitos) ou (DD) DDDDD-DDDD (celular, 11 dígitos).
    """

    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    empresa: Optional[str] = None
    observacoes: Optional[str] = None

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v is None:
            return v
        padrao = r"^\(\d{2}\) \d{4,5}-\d{4}$"
        if not re.match(padrao, v):
            raise ValueError(
                "Formato de telefone inválido. Use (99) 9999-9999 ou (99) 99999-9999."
            )
        return v

    @model_validator(mode="after")
    def ao_menos_um_campo(self) -> "ContatoPatch":
        """Garante que pelo menos um campo seja fornecido no body."""
        campos = (self.nome, self.email, self.telefone, self.empresa, self.observacoes)
        if all(v is None for v in campos):
            raise ValueError("Nenhum campo fornecido para atualização.")
        return self


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
    deletado_em: datetime | None = None
    # Campos de auditoria — NULL para registros anteriores à migration (RF-F3.2-01)
    criado_por_id: int | None = None
    atualizado_por_id: int | None = None


class ContatoListResponse(BaseModel):
    """Schema de resposta paginada para listagem de contatos.

    - items: registros da página atual
    - total: contagem total de registros que atendem ao filtro de busca
    """

    items: list[ContatoResposta]
    total: int
