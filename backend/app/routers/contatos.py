"""Router FastAPI para o recurso Contatos."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db

# Dependências de autenticação criadas pela TASK-03
from app.dependencies import get_current_user, require_adm

from app.schemas.contato import ContatoCriar, ContatoAtualizar, ContatoResposta, ContatoListResponse
from app.services import contato_service

router = APIRouter(prefix="/contatos", tags=["Contatos"])


@router.get("/", response_model=ContatoListResponse)
def listar(
    busca: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    """Lista contatos com paginação e filtro opcional por nome, email ou empresa.

    Parâmetros de query:
    - busca: texto livre filtrado em nome, email e empresa (LIKE icase)
    - skip: número de registros a pular (offset); padrão 0
    - limit: máximo de registros por página; padrão 20, máximo 200 (RN-F1-01)
    """
    # Garante que limit não ultrapasse o máximo permitido (RN-F1-01)
    if limit > 200:
        limit = 200

    items, total = contato_service.listar_contatos(db, busca=busca, skip=skip, limit=limit)
    return ContatoListResponse(items=items, total=total)


@router.get("/{id}", response_model=ContatoResposta)
def obter(
    id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    """Retorna um contato pelo id ou 404."""
    return contato_service.buscar_contato(db, id)


@router.post("/", response_model=ContatoResposta, status_code=201)
def criar(
    dados: ContatoCriar,
    db: Session = Depends(get_db),
    _usuario=Depends(require_adm),
):
    """Cria um novo contato (restrito a administradores)."""
    return contato_service.criar_contato(db, dados)


@router.put("/{id}", response_model=ContatoResposta)
def atualizar(
    id: int,
    dados: ContatoAtualizar,
    db: Session = Depends(get_db),
    _usuario=Depends(require_adm),
):
    """Atualiza um contato (restrito a administradores)."""
    return contato_service.atualizar_contato(db, id, dados)


@router.delete("/{id}", status_code=204)
def excluir(
    id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_adm),
):
    """Exclui um contato (restrito a administradores). Retorna 204 sem corpo."""
    contato_service.excluir_contato(db, id)
    return Response(status_code=204)
