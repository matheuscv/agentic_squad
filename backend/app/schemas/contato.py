"""Schemas Pydantic v2 para o recurso Contato."""

import re
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums de ordenação (Fase D — TASK-03 / RF-01)
# ---------------------------------------------------------------------------
#
# Estes enums sao usados pelo endpoint GET /contatos/ para validar `sort_by`
# e `sort_order` via Pydantic/FastAPI. Valores fora da allowlist resultam em
# HTTP 422 automaticamente.
#
# A allowlist segue o plano D.1: nome, email, empresa, telefone, criado_em,
# atualizado_em. Qualquer expansao futura deve passar por revisao (RNF-03 —
# proibida concatenacao de string em SQL para `order_by`).


class SortByContato(str, Enum):
    """Colunas permitidas para ordenacao na listagem de contatos."""

    nome = "nome"
    email = "email"
    empresa = "empresa"
    telefone = "telefone"
    criado_em = "criado_em"
    atualizado_em = "atualizado_em"


class SortOrder(str, Enum):
    """Direcao de ordenacao aceita pelo endpoint de listagem."""

    asc = "asc"
    desc = "desc"


# ---------------------------------------------------------------------------
# Filtros avancados (Fase D — TASK-05 / RF-06)
# ---------------------------------------------------------------------------
#
# Schema dedicado aos filtros combinaveis do endpoint GET /contatos/:
#   - empresa: busca parcial case-insensitive (ilike)
#   - criado_desde: data inicial (inclusiva)
#   - criado_ate: data final (inclusiva)
#   - sem_email: True -> retorna registros com email NULL (ou string vazia)
#   - sem_telefone: True -> retorna registros com telefone NULL (ou string vazia)
#
# A validacao cruzada (criado_desde > criado_ate -> 422) e feita aqui via
# model_validator. Manter o schema isolado facilita reuso futuro (export D.5).


class ContatoFilterParams(BaseModel):
    """Parametros opcionais de filtro avancado para a listagem de contatos.

    Todos os campos sao opcionais e combinaveis entre si, alem de combinaveis
    com `busca`, `sort_by`/`sort_order` e paginacao.
    """

    empresa: Optional[str] = None
    criado_desde: Optional[date] = None
    criado_ate: Optional[date] = None
    sem_email: Optional[bool] = None
    sem_telefone: Optional[bool] = None

    @field_validator("empresa")
    @classmethod
    def normaliza_empresa(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza string vazia/branca para None (filtro inexistente)."""
        if v is None:
            return None
        v_strip = v.strip()
        if v_strip == "":
            return None
        return v_strip

    @model_validator(mode="after")
    def valida_intervalo_datas(self) -> "ContatoFilterParams":
        """Garante intervalo coerente: criado_desde <= criado_ate.

        Quando ambos sao fornecidos e o limite inferior e maior que o
        superior, o intervalo e impossivel — devolvemos 422 via Pydantic
        em vez de retornar uma lista silenciosamente vazia (RNF-05).
        """
        if (
            self.criado_desde is not None
            and self.criado_ate is not None
            and self.criado_desde > self.criado_ate
        ):
            raise ValueError(
                "criado_desde nao pode ser posterior a criado_ate."
            )
        return self


# Regex unica de telefone para a Fase D (TASK-04 — RF-04).
# Contrato unico desta entrega: formato (XX) XXXXX-XXXX (celular brasileiro,
# 11 digitos com mascara). Alinhado com a regex Zod do frontend (TASK-08).
# Telefone permanece OPCIONAL no contrato: None ou string vazia sao aceitos
# e devolvidos como None pelo validador (normalizacao para o service).
_TELEFONE_REGEX = re.compile(r"^\(\d{2}\) \d{5}-\d{4}$")
_TELEFONE_ERRO = (
    "Telefone deve estar no formato (XX) XXXXX-XXXX, ex: (11) 91234-5678."
)


def _validar_telefone_opcional(v: Optional[str]) -> Optional[str]:
    """Valida telefone opcional contra a regex BR (XX) XXXXX-XXXX.

    Regras (TASK-04):
    - None -> aceito, retorna None.
    - String vazia (apos strip) -> aceito, normalizado para None.
    - String preenchida que casa com a regex -> aceito, retorna o valor.
    - Qualquer outro formato -> ValueError (HTTP 422 via Pydantic).
    """
    if v is None:
        return None
    # String vazia (ou so espacos) e tratada como ausencia de telefone.
    if isinstance(v, str) and v.strip() == "":
        return None
    if not _TELEFONE_REGEX.match(v):
        raise ValueError(_TELEFONE_ERRO)
    return v


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

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, v: Optional[str]) -> Optional[str]:
        return _validar_telefone_opcional(v)


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

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, v: Optional[str]) -> Optional[str]:
        return _validar_telefone_opcional(v)


class ContatoPatch(BaseModel):
    """Payload para atualização parcial via PATCH /contatos/{id}.

    Todos os campos são opcionais. Pelo menos um campo deve ser fornecido
    (não-None); caso contrário, o validador levanta ValueError → HTTP 422.

    Validação de formato de telefone usa a regex unica da Fase D
    (TASK-04 — RF-04): (XX) XXXXX-XXXX. Telefone continua opcional —
    None ou string vazia sao aceitos.
    """

    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    empresa: Optional[str] = None
    observacoes: Optional[str] = None

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, v: Optional[str]) -> Optional[str]:
        return _validar_telefone_opcional(v)

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
