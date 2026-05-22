"""Camada de serviço para operações CRUD de Contato."""

import logging
from datetime import date, datetime, time, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.contato import Contato
from app.schemas.contato import (
    ContatoAtualizar,
    ContatoCriar,
    ContatoPatch,
    SortByContato,
    SortOrder,
)
from app.services._helpers import garantir_unicidade

# Allowlist EXPLICITA de colunas ordenaveis (TASK-03 / RF-01).
# Manter como tupla derivada do enum para reduzir risco de divergencia entre
# router e service. Qualquer coluna fora deste conjunto e rejeitada como 422
# pelo Pydantic no router antes de chegar aqui — esta validacao em service
# atua como defesa em profundidade contra erros futuros de refactor.
_COLUNAS_ORDENACAO_PERMITIDAS: frozenset[str] = frozenset(
    item.value for item in SortByContato
)

# Logger nomeado por módulo — TASK-05 (B.1).
logger = logging.getLogger(__name__)


def listar_contatos(
    db: Session,
    busca: str | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: SortByContato | str = SortByContato.criado_em,
    sort_order: SortOrder | str = SortOrder.desc,
    # TASK-05 — Filtros avancados (RF-06). Todos opcionais; combinaveis com
    # `busca`, sort e paginacao. Quando None/False, o filtro nao e aplicado.
    empresa: str | None = None,
    criado_desde: date | None = None,
    criado_ate: date | None = None,
    sem_email: bool | None = None,
    sem_telefone: bool | None = None,
) -> tuple[list[Contato], int]:
    """Retorna uma tupla (items, total) com paginação, ordenação e filtros.

    - items: registros da página, aplicando ORDER BY, OFFSET skip, LIMIT limit
    - total: contagem total de registros que atendem aos filtros e a `busca`

    Se `busca` for fornecido, filtra com LIKE case-insensitive (ilike) nos
    campos nome, email e empresa (OR entre eles).

    Parâmetros de ordenação (TASK-03 / RF-01):
    - sort_by: coluna; default = `criado_em`. Allowlist em `SortByContato`:
      nome, email, empresa, telefone, criado_em, atualizado_em.
    - sort_order: direcao; default = `desc` (preserva ordenacao
      cronologica reversa que era o comportamento atual).

    Parâmetros de filtro avancado (TASK-05 / RF-06):
    - empresa: busca parcial case-insensitive (ilike) sobre `contatos.empresa`.
    - criado_desde: data inicial inclusiva (>= 00:00:00 do dia).
    - criado_ate: data final inclusiva (<= 23:59:59.999999 do dia). Convertido
      para `datetime` no fim do dia para garantir inclusao do dia inteiro
      mesmo quando `criado_em` armazena timestamps com horas.
    - sem_email: True -> apenas registros com email NULL OU string vazia.
    - sem_telefone: True -> apenas registros com telefone NULL OU string vazia.

    A validacao de coerencia (criado_desde > criado_ate) e feita no router
    via `ContatoFilterParams` (Pydantic -> HTTP 422). Aqui assumimos que o
    intervalo, se ambos fornecidos, ja e valido.

    Defesa em profundidade: o router ja valida via Pydantic enums (HTTP 422
    para valor invalido). Aqui revalidamos contra `_COLUNAS_ORDENACAO_PERMITIDAS`
    para impedir SQL injection caso a funcao seja chamada por outro caller
    (ex.: endpoint de export — TASK-06) com input ainda nao validado.
    """
    # Normaliza para string (aceita Enum ou str — facilita chamadas internas
    # e testes que ainda passam str literal).
    sort_by_str = sort_by.value if isinstance(sort_by, SortByContato) else str(sort_by)
    sort_order_str = (
        sort_order.value if isinstance(sort_order, SortOrder) else str(sort_order)
    )

    # Validacao defensiva contra allowlist — impede SQL injection caso a
    # funcao seja chamada com input nao validado pelo Pydantic.
    if sort_by_str not in _COLUNAS_ORDENACAO_PERMITIDAS:
        raise ValueError(
            f"sort_by invalido: {sort_by_str!r}. "
            f"Permitidos: {sorted(_COLUNAS_ORDENACAO_PERMITIDAS)}"
        )
    if sort_order_str not in {"asc", "desc"}:
        raise ValueError(
            f"sort_order invalido: {sort_order_str!r}. Permitidos: asc, desc"
        )

    # Predicado de filtro reutilizado tanto no COUNT quanto na consulta paginada.
    # Registros com soft delete (deletado_em IS NOT NULL) são excluídos da listagem normal.
    stmt_base = select(Contato).where(Contato.deletado_em == None)  # noqa: E711

    if busca:
        termo = f"%{busca}%"
        filtro = (
            Contato.nome.ilike(termo)
            | Contato.email.ilike(termo)
            | Contato.empresa.ilike(termo)
        )
        stmt_base = stmt_base.where(filtro)

    # ------------------------------------------------------------------
    # Filtros avancados (TASK-05 / RF-06)
    # ------------------------------------------------------------------
    # Aplicados como AND adicional sobre `stmt_base`. Cada filtro e
    # idempotente: se o parametro for None/False, o `where` nao e
    # adicionado e a consulta segue inalterada.

    # `empresa` — busca parcial case-insensitive. Normalizamos o termo
    # aqui (defesa em profundidade; o schema ContatoFilterParams ja
    # remove espacos em branco quando chamado pelo router).
    if empresa:
        termo_empresa = empresa.strip()
        if termo_empresa:
            stmt_base = stmt_base.where(
                Contato.empresa.ilike(f"%{termo_empresa}%")
            )

    # Datas inclusivas. Convertemos `date` -> `datetime` (00:00:00 e
    # 23:59:59.999999 respectivamente) para garantir que registros
    # cujo `criado_em` armazena hora/minuto sejam incluidos quando
    # caem no mesmo dia das bordas do intervalo.
    if criado_desde is not None:
        # Inclusivo: >= 00:00:00 do dia.
        limite_inferior = datetime.combine(criado_desde, time.min)
        stmt_base = stmt_base.where(Contato.criado_em >= limite_inferior)

    if criado_ate is not None:
        # Inclusivo: <= 23:59:59.999999 do dia.
        limite_superior = datetime.combine(criado_ate, time.max)
        stmt_base = stmt_base.where(Contato.criado_em <= limite_superior)

    # `sem_email` / `sem_telefone`: registros sem o respectivo campo.
    # Tratamos NULL OU string vazia como "ausente" — alinhado com a
    # validacao do schema que normaliza "" para None ao persistir, mas
    # historicamente alguns registros podem ter "" no banco.
    if sem_email:
        stmt_base = stmt_base.where(
            or_(Contato.email == None, Contato.email == "")  # noqa: E711
        )

    if sem_telefone:
        stmt_base = stmt_base.where(
            or_(Contato.telefone == None, Contato.telefone == "")  # noqa: E711
        )

    # COUNT com o mesmo filtro (incluindo os filtros avancados) para calcular total real
    stmt_count = select(func.count()).select_from(stmt_base.subquery())
    total: int = db.execute(stmt_count).scalar_one()

    # Ordenacao via getattr — apos validacao contra allowlist (RNF-03:
    # proibida concatenacao de string em SQL; `getattr` resolve para um
    # InstrumentedAttribute do SQLAlchemy, nao para SQL bruto).
    coluna = getattr(Contato, sort_by_str)
    ordem = coluna.asc() if sort_order_str == "asc" else coluna.desc()

    # Consulta paginada com ordenação
    stmt_paginada = stmt_base.order_by(ordem).offset(skip).limit(limit)
    items = list(db.execute(stmt_paginada).scalars().all())

    return items, total


def listar_contatos_para_export(
    db: Session,
    busca: str | None = None,
    sort_by: SortByContato | str = SortByContato.criado_em,
    sort_order: SortOrder | str = SortOrder.desc,
    empresa: str | None = None,
    criado_desde: date | None = None,
    criado_ate: date | None = None,
    sem_email: bool | None = None,
    sem_telefone: bool | None = None,
) -> list[Contato]:
    """Versao SEM paginacao da listagem — usada pelo endpoint de export
    (TASK-06 / RF-07 a RF-10).

    Reutiliza EXATAMENTE os mesmos predicados (busca, filtros avancados,
    ordenacao, exclusao de soft-deleted) da `listar_contatos`, mas
    deliberadamente IGNORA `skip` e `limit` (RF-08: exporta todos os
    registros que casam com a query atual).

    Soft-deleted nao entra (RF-09) — herdado do filtro base
    `deletado_em IS NULL` da `listar_contatos` (definido na propria
    funcao via `Contato.deletado_em == None`).

    Estrategia: chamamos `listar_contatos` com `limit` muito grande para
    nao duplicar logica. Esta abordagem mantem 1 unico ponto de
    construcao da query (DRY) — qualquer ajuste futuro em filtros/sort
    fica refletido automaticamente no export.
    """
    # 2_000_000 e um teto muito superior ao RNF-02 (50k linhas), evitando
    # truncar exports legitimos. Caso o ambiente cresca alem desse limite,
    # a melhor abordagem futura sera substituir esta chamada por um
    # generator que faz cursor server-side — registrar como item de
    # backlog se aparecer.
    items, _total = listar_contatos(
        db,
        busca=busca,
        skip=0,
        limit=2_000_000,
        sort_by=sort_by,
        sort_order=sort_order,
        empresa=empresa,
        criado_desde=criado_desde,
        criado_ate=criado_ate,
        sem_email=sem_email,
        sem_telefone=sem_telefone,
    )
    return items


def buscar_contato(db: Session, id: int) -> Contato:
    """Retorna o Contato ativo (não deletado) pelo id ou levanta HTTPException 404.

    Contatos com deletado_em preenchido são tratados como inexistentes para o
    fluxo normal — retornam 404 tal como registros que nunca existiram.
    """
    stmt = select(Contato).where(Contato.id == id, Contato.deletado_em == None)  # noqa: E711
    contato = db.execute(stmt).scalar_one_or_none()
    if contato is None:
        logger.warning("contato inexistente acessado id=%s", id)
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return contato


def criar_contato(db: Session, dados: ContatoCriar, usuario_id: int | None = None) -> Contato:
    """Persiste um novo Contato.

    Levanta HTTPException 400 se o e-mail já estiver cadastrado.

    usuario_id (RF-F3.2-01): id do usuário autenticado que está criando o registro.
    Preenchido em criado_por_id e atualizado_por_id. Pode ser None em contextos de teste/seed.
    """
    # Verifica duplicidade de e-mail via helper compartilhado (DRY).
    # Status 400 e mensagem preservados — qualquer ajuste futuro deve passar pelo helper.
    garantir_unicidade(db, Contato, "email", dados.email, "E-mail já cadastrado")

    contato = Contato(
        nome=dados.nome,
        email=dados.email,
        telefone=dados.telefone,
        empresa=dados.empresa,
        observacoes=dados.observacoes,
        criado_por_id=usuario_id,
        atualizado_por_id=usuario_id,
    )
    db.add(contato)
    db.commit()
    db.refresh(contato)
    # Log apenas ids/ação — nunca payload bruto (pode conter dados pessoais).
    logger.info("contato criado id=%s por usuario_id=%s", contato.id, usuario_id)
    return contato


def atualizar_contato(
    db: Session, id: int, dados: ContatoAtualizar, usuario_id: int | None = None
) -> Contato:
    """Atualiza apenas os campos não-None do schema e persiste.

    Levanta HTTPException 404 se o contato não existir.

    usuario_id (RF-F3.2-01): atualiza atualizado_por_id sem tocar em criado_por_id (RN-F3.2-01).
    """
    contato = buscar_contato(db, id)

    # Atualiza somente os campos explicitamente fornecidos (não-None)
    campos_atualizaveis = ("nome", "email", "telefone", "empresa", "observacoes")
    for campo in campos_atualizaveis:
        valor = getattr(dados, campo)
        if valor is not None:
            setattr(contato, campo, valor)

    # Atualiza o timestamp manualmente (o onupdate do modelo cuida disso via ORM,
    # mas é bom ser explícito para garantir o comportamento em todos os drivers)
    contato.atualizado_em = datetime.now(timezone.utc)
    # Auditoria: registra quem fez a atualização; criado_por_id é preservado
    if usuario_id is not None:
        contato.atualizado_por_id = usuario_id

    db.commit()
    db.refresh(contato)
    logger.info("contato atualizado id=%s por usuario_id=%s", contato.id, usuario_id)
    return contato


def patch_contato(
    db: Session, id: int, dados: ContatoPatch, usuario_id: int | None = None
) -> Contato:
    """Atualiza parcialmente um contato — apenas os campos não-None do schema.

    Levanta HTTPException 404 se o contato não existir.
    Levanta HTTPException 400 se o novo e-mail já pertencer a outro contato.

    usuario_id (RF-F3.2-01): atualiza atualizado_por_id sem tocar em criado_por_id (RN-F3.2-01).
    """
    contato = buscar_contato(db, id)

    # Valida unicidade de e-mail antes de aplicar qualquer mudança.
    # excluir_id=id preserva o próprio registro ao revalidar o e-mail no PATCH.
    if dados.email is not None:
        garantir_unicidade(
            db,
            Contato,
            "email",
            dados.email,
            "E-mail já cadastrado por outro contato",
            excluir_id=id,
        )

    # Aplica somente os campos presentes no body (não-None)
    campos_atualizaveis = ("nome", "email", "telefone", "empresa", "observacoes")
    for campo in campos_atualizaveis:
        valor = getattr(dados, campo)
        if valor is not None:
            setattr(contato, campo, valor)

    contato.atualizado_em = datetime.now(timezone.utc)
    # Auditoria: registra quem fez o patch; criado_por_id é preservado
    if usuario_id is not None:
        contato.atualizado_por_id = usuario_id

    db.commit()
    db.refresh(contato)
    logger.info("contato patch aplicado id=%s por usuario_id=%s", contato.id, usuario_id)
    return contato


def excluir_contato(db: Session, id: int) -> None:
    """Soft delete: marca deletado_em com o instante atual (UTC) em vez de remover a linha.

    Levanta HTTPException 404 se o contato não existir (ou já estiver deletado).
    """
    contato = buscar_contato(db, id)
    contato.deletado_em = datetime.now(timezone.utc)
    db.commit()
    logger.info("contato excluido (soft) id=%s", id)


def listar_lixeira(
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Contato], int]:
    """Retorna contatos que passaram por soft delete (deletado_em IS NOT NULL).

    - Ordenados por deletado_em DESC (mais recentes primeiro).
    - Retorna tupla (items, total) no mesmo padrão de listar_contatos.
    - Exclusivo para administradores (o controle de acesso é feito no router).
    """
    stmt_base = select(Contato).where(Contato.deletado_em != None)  # noqa: E711

    # Contagem total de registros na lixeira
    stmt_count = select(func.count()).select_from(stmt_base.subquery())
    total: int = db.execute(stmt_count).scalar_one()

    # Mais recentemente deletado primeiro
    stmt_paginada = (
        stmt_base.order_by(Contato.deletado_em.desc()).offset(skip).limit(limit)
    )
    items = list(db.execute(stmt_paginada).scalars().all())

    return items, total
