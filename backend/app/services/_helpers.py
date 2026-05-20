"""Helpers compartilhados entre os services.

Este módulo concentra utilitários transversais (cross-cutting) que apareciam
duplicados em diferentes services/routers — por exemplo, o padrão de
"verificar se já existe um registro com o mesmo valor em um campo único e,
em caso afirmativo, levantar HTTPException".

Mantendo a lógica em um único lugar reduzimos:

- Risco de divergência de mensagens de erro entre endpoints.
- Risco de drift de status code (400 vs. 409) entre rotas que validam o
  mesmo tipo de invariante.
- Duplicação de SQL ("select ... where campo = :valor" repetido N vezes).

Decisão de design: o helper é deliberadamente síncrono e recebe a `Session`
como argumento (ao invés de injetar via Depends). Isso permite reutilizá-lo
tanto a partir de routers quanto a partir de services unitários (sem o
contexto de request do FastAPI), facilitando os testes.
"""

import logging
from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

# Logger nomeado por módulo — TASK-05 (B.1). Adicionado sem mudar comportamento.
logger = logging.getLogger(__name__)

# Tipo genérico para o model SQLAlchemy passado como argumento.
# Mantém a assinatura tipada sem amarrar o helper a um modelo concreto.
T = TypeVar("T")


def garantir_unicidade(
    db: Session,
    model: Type[T],
    campo: str,
    valor: str,
    mensagem: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    excluir_id: int | None = None,
) -> None:
    """Garante que não exista outro registro de ``model`` com ``model.<campo> == valor``.

    Levanta ``HTTPException`` com ``status_code`` e ``mensagem`` se encontrar um
    conflito. Caso contrário, retorna ``None`` silenciosamente.

    Parameters
    ----------
    db : Session
        Sessão SQLAlchemy ativa.
    model : Type[T]
        Classe do model (declarativa) onde a unicidade será verificada.
    campo : str
        Nome do atributo do model a comparar (ex.: ``"email"``).
    valor : str
        Valor a procurar.
    mensagem : str
        Texto do ``detail`` enviado na resposta HTTP em caso de conflito.
    status_code : int, optional
        Status HTTP a retornar em caso de conflito. Default ``400`` — mantém
        compatibilidade com os endpoints existentes do projeto (não migrar
        para 409 sem revisar contratos públicos — RNF-02).
    excluir_id : int | None, optional
        Quando informado, o helper ignora qualquer registro cujo ``id`` seja
        igual a ``excluir_id``. Útil em PUT/PATCH onde o próprio registro já
        pode ter o valor que está sendo "revalidado".

    Examples
    --------
    >>> # POST de criação — sem excluir_id
    >>> garantir_unicidade(db, Usuario, "email", dados.email, "E-mail já cadastrado.")
    >>>
    >>> # PUT/PATCH de atualização — preserva o próprio registro
    >>> garantir_unicidade(
    ...     db, Usuario, "email", dados.email,
    ...     "Este e-mail já está em uso por outro usuário.",
    ...     excluir_id=usuario.id,
    ... )

    Notes
    -----
    Usa o padrão SQLAlchemy 2.0 (``select(...)`` + ``db.scalars(...)``).
    Não usa ``db.query(...)`` para evitar regredir após a migração TASK-17.
    """
    # getattr garante que a coluna seja resolvida em runtime — o campo é validado
    # implicitamente pelo SQLAlchemy se não existir no model (AttributeError).
    stmt = select(model).where(getattr(model, campo) == valor)

    if excluir_id is not None:
        # Exclui o próprio registro da comparação — só importam conflitos com OUTROS.
        stmt = stmt.where(getattr(model, "id") != excluir_id)

    existente = db.scalars(stmt).first()
    if existente is not None:
        raise HTTPException(status_code=status_code, detail=mensagem)
