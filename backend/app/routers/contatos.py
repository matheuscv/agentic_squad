"""Router FastAPI para o recurso Contatos."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db

# Dependências de autenticação criadas pela TASK-03
from app.dependencies import get_current_user, require_adm

from app.schemas.contato import ContatoCriar, ContatoAtualizar, ContatoPatch, ContatoResposta, ContatoListResponse
from app.services import contato_service

router = APIRouter(prefix="/contatos", tags=["Contatos"])


@router.get("/", response_model=ContatoListResponse)
def listar(
    busca: str | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "nome",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    """Lista contatos com paginação, filtro opcional e ordenação por coluna.

    Parâmetros de query:
    - busca: texto livre filtrado em nome, email e empresa (LIKE icase)
    - skip: número de registros a pular (offset); padrão 0
    - limit: máximo de registros por página; padrão 20, máximo 200 (RN-F1-01)
    - sort_by: coluna de ordenação; valores aceitos: nome, email, empresa, criado_em (padrão: nome)
    - sort_order: direção de ordenação; valores aceitos: asc, desc (padrão: asc)
    """
    # Valores permitidos para ordenação (RF-F2-01)
    _SORT_BY_PERMITIDOS = {"nome", "email", "empresa", "criado_em"}
    _SORT_ORDER_PERMITIDOS = {"asc", "desc"}

    if sort_by not in _SORT_BY_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail=f"Valor inválido para sort_by: '{sort_by}'. Permitidos: {sorted(_SORT_BY_PERMITIDOS)}",
        )
    if sort_order not in _SORT_ORDER_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail=f"Valor inválido para sort_order: '{sort_order}'. Permitidos: asc, desc",
        )

    # Garante que limit não ultrapasse o máximo permitido (RN-F1-01)
    if limit > 200:
        limit = 200

    items, total = contato_service.listar_contatos(
        db,
        busca=busca,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ContatoListResponse(items=items, total=total)


@router.get("/lixeira", response_model=ContatoListResponse)
def lixeira(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _usuario=Depends(require_adm),
):
    """Lista contatos que sofreram soft delete, ordenados por data de exclusão DESC.

    Acesso restrito a administradores (role='adm').
    Usuários 'default' recebem 403; requisições sem token recebem 401.
    """
    items, total = contato_service.listar_lixeira(db, skip=skip, limit=limit)
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
    current_user=Depends(require_adm),
):
    """Cria um novo contato (restrito a administradores)."""
    # Passa o id do usuário autenticado para auditoria (RF-F3.2-01)
    return contato_service.criar_contato(db, dados, usuario_id=current_user.id)


@router.put("/{id}", response_model=ContatoResposta)
def atualizar(
    id: int,
    dados: ContatoAtualizar,
    db: Session = Depends(get_db),
    current_user=Depends(require_adm),
):
    """Atualiza um contato (restrito a administradores)."""
    # Passa o id do usuário autenticado para auditoria (RF-F3.2-01)
    return contato_service.atualizar_contato(db, id, dados, usuario_id=current_user.id)


@router.patch("/{id}", response_model=ContatoResposta)
def patch(
    id: int,
    dados: ContatoPatch,
    db: Session = Depends(get_db),
    current_user=Depends(require_adm),
):
    """Atualiza parcialmente um contato (restrito a administradores)."""
    # Passa o id do usuário autenticado para auditoria (RF-F3.2-01)
    return contato_service.patch_contato(db, id, dados, usuario_id=current_user.id)


@router.delete("/{id}", status_code=204)
def excluir(
    id: int,
    db: Session = Depends(get_db),
    _usuario=Depends(require_adm),
):
    """Exclui um contato (restrito a administradores). Retorna 204 sem corpo."""
    contato_service.excluir_contato(db, id)
    return Response(status_code=204)
