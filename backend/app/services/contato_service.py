"""Camada de serviço para operações CRUD de Contato."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contato import Contato
from app.schemas.contato import ContatoCriar, ContatoAtualizar


def listar_contatos(db: Session, busca: str | None = None) -> list[Contato]:
    """Retorna até 200 contatos.

    Se `busca` for fornecido, filtra com LIKE case-insensitive (ilike) nos
    campos nome, email e empresa (OR entre eles).
    """
    stmt = select(Contato)

    if busca:
        termo = f"%{busca}%"
        stmt = stmt.where(
            Contato.nome.ilike(termo)
            | Contato.email.ilike(termo)
            | Contato.empresa.ilike(termo)
        )

    stmt = stmt.limit(200)
    resultado = db.execute(stmt)
    return list(resultado.scalars().all())


def buscar_contato(db: Session, id: int) -> Contato:
    """Retorna o Contato pelo id ou levanta HTTPException 404."""
    stmt = select(Contato).where(Contato.id == id)
    contato = db.execute(stmt).scalar_one_or_none()
    if contato is None:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return contato


def criar_contato(db: Session, dados: ContatoCriar) -> Contato:
    """Persiste um novo Contato.

    Levanta HTTPException 400 se o e-mail já estiver cadastrado.
    """
    # Verifica duplicidade de e-mail
    existente = db.execute(
        select(Contato).where(Contato.email == dados.email)
    ).scalar_one_or_none()

    if existente is not None:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    contato = Contato(
        nome=dados.nome,
        email=dados.email,
        telefone=dados.telefone,
        empresa=dados.empresa,
        observacoes=dados.observacoes,
    )
    db.add(contato)
    db.commit()
    db.refresh(contato)
    return contato


def atualizar_contato(db: Session, id: int, dados: ContatoAtualizar) -> Contato:
    """Atualiza apenas os campos não-None do schema e persiste.

    Levanta HTTPException 404 se o contato não existir.
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

    db.commit()
    db.refresh(contato)
    return contato


def excluir_contato(db: Session, id: int) -> None:
    """Exclui o contato pelo id.

    Levanta HTTPException 404 se o contato não existir.
    """
    contato = buscar_contato(db, id)
    db.delete(contato)
    db.commit()
