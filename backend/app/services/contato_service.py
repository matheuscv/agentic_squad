"""Camada de serviço para operações CRUD de Contato."""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.contato import Contato
from app.schemas.contato import ContatoCriar, ContatoAtualizar, ContatoPatch
from app.services._helpers import garantir_unicidade

# Logger nomeado por módulo — TASK-05 (B.1).
logger = logging.getLogger(__name__)


def listar_contatos(
    db: Session,
    busca: str | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "nome",
    sort_order: str = "asc",
) -> tuple[list[Contato], int]:
    """Retorna uma tupla (items, total) com paginação e ordenação.

    - items: registros da página, aplicando ORDER BY, OFFSET skip, LIMIT limit
    - total: contagem total de registros que atendem ao filtro de busca

    Se `busca` for fornecido, filtra com LIKE case-insensitive (ilike) nos
    campos nome, email e empresa (OR entre eles).

    Parâmetros de ordenação (validados no router antes de chegar aqui):
    - sort_by: nome da coluna — "nome", "email", "empresa", "criado_em"
    - sort_order: "asc" ou "desc"
    """
    # Mapeamento explícito de nomes de campo para colunas SQLAlchemy.
    # Usar dicionário fechado evita SQL injection por substituição de coluna.
    colunas_ordenacao = {
        "nome": Contato.nome,
        "email": Contato.email,
        "empresa": Contato.empresa,
        "criado_em": Contato.criado_em,
    }

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

    # COUNT com o mesmo filtro para calcular total real
    stmt_count = select(func.count()).select_from(stmt_base.subquery())
    total: int = db.execute(stmt_count).scalar_one()

    # Ordenação no banco (RN-F2-01) — aplicada antes do offset/limit
    coluna = colunas_ordenacao[sort_by]
    ordem = coluna.asc() if sort_order == "asc" else coluna.desc()

    # Consulta paginada com ordenação
    stmt_paginada = stmt_base.order_by(ordem).offset(skip).limit(limit)
    items = list(db.execute(stmt_paginada).scalars().all())

    return items, total


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
