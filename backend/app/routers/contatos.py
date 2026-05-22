"""Router FastAPI para o recurso Contatos."""

import logging
import time
from datetime import date, datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.database import get_db

# Dependências de autenticação criadas pela TASK-03
from app.dependencies import get_current_user, require_adm

from app.exporters import (
    CONTATOS_CSV_MIME,
    CONTATOS_XLSX_MIME,
    gerar_csv_contatos,
    gerar_xlsx_contatos,
)
from app.logging_config import get_request_id

from app.schemas.contato import (
    ContatoAtualizar,
    ContatoCriar,
    ContatoFilterParams,
    ContatoListResponse,
    ContatoPatch,
    ContatoResposta,
    SortByContato,
    SortOrder,
)
from app.services import contato_service


# --------------------------------------------------------------------------
# Enum do formato de export (TASK-06 / RF-07).
# Manter como Enum FastAPI valida automaticamente em 422 para valores fora
# da allowlist — alinhado com a abordagem usada em SortByContato/SortOrder.
# --------------------------------------------------------------------------


class FormatoExportContato(str, Enum):
    """Formatos suportados pelo endpoint /contatos/export."""

    csv = "csv"
    xlsx = "xlsx"


def _safe_validation_errors(errors: list) -> list:
    """Remove campos nao serializaveis dos erros Pydantic v2 (date, Exception no ctx)."""
    result = []
    for err in errors:
        safe = {k: v for k, v in err.items() if k not in ("input", "url")}
        if "ctx" in safe and isinstance(safe["ctx"], dict):
            safe["ctx"] = {
                k: str(v) if isinstance(v, Exception) else v
                for k, v in safe["ctx"].items()
            }
        result.append(safe)
    return result


# Logger nomeado por módulo — TASK-05 (B.1). Não substitui prints (nenhum
# existia neste arquivo); habilita rastreamento estruturado via handlers globais.
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contatos", tags=["Contatos"])


@router.get("/", response_model=ContatoListResponse)
def listar(
    busca: str | None = None,
    skip: int = 0,
    limit: int = 20,
    # TASK-03 — Ordenacao (RF-01 / RNF-03).
    # Enums Pydantic: valor fora da allowlist resulta em HTTP 422 automatico
    # via mecanismo de validacao do FastAPI (sem necessidade de checagem
    # manual / HTTPException). Default = criado_em desc (preserva listagem
    # cronologica reversa).
    sort_by: SortByContato = SortByContato.criado_em,
    sort_order: SortOrder = SortOrder.desc,
    # TASK-05 — Filtros avancados (RF-06).
    # Cada parametro e opcional e combinavel com `busca` + sort + paginacao.
    # A validacao cruzada (criado_desde > criado_ate -> 422) e feita abaixo
    # via ContatoFilterParams (Pydantic). Mantemos os parametros como query
    # params nominais para que o OpenAPI exiba cada um individualmente
    # (instanciar ContatoFilterParams como dependencia esconderia os nomes
    # no Swagger UI).
    empresa: str | None = None,
    criado_desde: date | None = None,
    criado_ate: date | None = None,
    sem_email: bool | None = None,
    sem_telefone: bool | None = None,
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    """Lista contatos com paginação, filtro opcional, ordenação e filtros avancados.

    Parâmetros de query:
    - busca: texto livre filtrado em nome, email e empresa (LIKE icase)
    - skip: número de registros a pular (offset); padrão 0
    - limit: máximo de registros por página; padrão 20, máximo 200 (RN-F1-01)
    - sort_by: coluna de ordenacao; allowlist: nome, email, empresa, telefone,
      criado_em, atualizado_em (padrao: criado_em)
    - sort_order: direção de ordenação; valores aceitos: asc, desc (padrão: desc)
    - empresa: busca parcial case-insensitive sobre o campo empresa (TASK-05 / RF-06)
    - criado_desde: data inicial inclusiva (YYYY-MM-DD)
    - criado_ate: data final inclusiva (YYYY-MM-DD)
    - sem_email: quando true, retorna apenas contatos sem email preenchido
    - sem_telefone: quando true, retorna apenas contatos sem telefone preenchido
    """
    # Garante que limit não ultrapasse o máximo permitido (RN-F1-01)
    if limit > 200:
        limit = 200

    # Validacao + normalizacao centralizada dos filtros (TASK-05).
    # ContatoFilterParams:
    #   - normaliza `empresa` (strip, "" -> None)
    #   - rejeita intervalo invertido (criado_desde > criado_ate -> 422)
    #
    # Como instanciamos o modelo manualmente (fora do mecanismo automatico
    # do FastAPI), o ValidationError do Pydantic NAO e capturado pelo
    # handler de RequestValidationError. Convertemos para HTTPException 422
    # explicitamente, preservando os erros estruturados originais para que
    # o cliente possa identificar qual campo falhou.
    try:
        filtros = ContatoFilterParams(
            empresa=empresa,
            criado_desde=criado_desde,
            criado_ate=criado_ate,
            sem_email=sem_email,
            sem_telefone=sem_telefone,
        )
    except PydanticValidationError as exc:
        # exc.errors() devolve lista de dicts no mesmo formato que o
        # FastAPI usa para 422 — mantemos contrato consistente.
        raise HTTPException(status_code=422, detail=_safe_validation_errors(exc.errors())) from exc

    # Log estruturado da operacao de listagem (B.1 — herda request_id/user_id
    # via ContextFilter). Incluir sort_by/sort_order e flags de filtro
    # ajuda a diagnosticar consultas lentas e a auditar uso (RF-01 / RF-06).
    # Importante: NAO logamos o valor textual de `busca` ou `empresa` (PII).
    logger.info(
        "contatos.listar sort_by=%s sort_order=%s busca=%s skip=%s limit=%s "
        "tem_filtro_empresa=%s tem_criado_desde=%s tem_criado_ate=%s "
        "sem_email=%s sem_telefone=%s",
        sort_by.value,
        sort_order.value,
        bool(busca),
        skip,
        limit,
        filtros.empresa is not None,
        filtros.criado_desde is not None,
        filtros.criado_ate is not None,
        bool(filtros.sem_email),
        bool(filtros.sem_telefone),
        extra={
            "sort_by": sort_by.value,
            "sort_order": sort_order.value,
            "tem_filtro_empresa": filtros.empresa is not None,
            "tem_criado_desde": filtros.criado_desde is not None,
            "tem_criado_ate": filtros.criado_ate is not None,
            "sem_email": bool(filtros.sem_email),
            "sem_telefone": bool(filtros.sem_telefone),
        },
    )

    items, total = contato_service.listar_contatos(
        db,
        busca=busca,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        empresa=filtros.empresa,
        criado_desde=filtros.criado_desde,
        criado_ate=filtros.criado_ate,
        sem_email=filtros.sem_email,
        sem_telefone=filtros.sem_telefone,
    )
    return ContatoListResponse(items=items, total=total)


# --------------------------------------------------------------------------
# Endpoint de exportacao (TASK-06 / RF-07 a RF-10).
#
# Aceita os MESMOS parametros de busca/filtros/ordenacao da listagem, MAS
# IGNORA `skip` e `limit` (RF-08: exporta todos os registros que casam com
# a query). Soft-deleted nao entra (RF-09 — herdado do filtro base do
# `listar_contatos`). Log estruturado emitido com request_id, user_id,
# formato e total_rows (RF-10 / B.1).
#
# NOTA: rota declarada ANTES de `/{id}` na ordem do arquivo nao seria
# necessario para FastAPI (paths estaticos tem prioridade), mas
# mantemos a posicao apos `/` (listar) e antes de `/lixeira` por
# coerencia organizacional.
# --------------------------------------------------------------------------


@router.get("/export", summary="Exporta contatos em CSV ou XLSX")
def exportar(
    formato: FormatoExportContato = FormatoExportContato.csv,
    busca: str | None = None,
    sort_by: SortByContato = SortByContato.criado_em,
    sort_order: SortOrder = SortOrder.desc,
    empresa: str | None = None,
    criado_desde: date | None = None,
    criado_ate: date | None = None,
    sem_email: bool | None = None,
    sem_telefone: bool | None = None,
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    """Exporta contatos como CSV ou XLSX (RF-07 a RF-10).

    Parametros de query (todos opcionais):
    - formato: `csv` (default) ou `xlsx`. Qualquer outro valor -> 422.
    - busca, sort_by, sort_order, empresa, criado_desde, criado_ate,
      sem_email, sem_telefone: mesma semantica da listagem em `GET /contatos/`.

    Importante:
    - skip/limit NAO sao aceitos: o endpoint exporta TODOS os registros que
      casam com a query (RF-08).
    - Soft-deleted nao entra (RF-09 — exclusao via filtro base do service).
    - Resposta usa `StreamingResponse` com `Content-Disposition: attachment`.
    """
    # Aceita o parametro do FastAPI como query string `format` (sinonimo
    # mais natural) mas mantemos a variavel `formato` em PT-BR no codigo.
    # Como `format` e palavra reservada do Python, usar alias direto via
    # `Query(alias="format")` aumentaria boilerplate; o nome `formato`
    # ja e descritivo no Swagger UI.

    # Validacao cruzada dos filtros (criado_desde > criado_ate -> 422),
    # mesma logica do endpoint de listagem.
    try:
        filtros = ContatoFilterParams(
            empresa=empresa,
            criado_desde=criado_desde,
            criado_ate=criado_ate,
            sem_email=sem_email,
            sem_telefone=sem_telefone,
        )
    except PydanticValidationError as exc:
        raise HTTPException(status_code=422, detail=_safe_validation_errors(exc.errors())) from exc

    inicio = time.perf_counter()

    # Coleta TODOS os registros (sem paginacao). A funcao reutiliza a
    # query base de `listar_contatos` — inclui exclusao de soft-deleted.
    items = contato_service.listar_contatos_para_export(
        db,
        busca=busca,
        sort_by=sort_by,
        sort_order=sort_order,
        empresa=filtros.empresa,
        criado_desde=filtros.criado_desde,
        criado_ate=filtros.criado_ate,
        sem_email=filtros.sem_email,
        sem_telefone=filtros.sem_telefone,
    )

    total_rows = len(items)
    duration_ms = int((time.perf_counter() - inicio) * 1000)

    # Nome do arquivo com timestamp para evitar overwrite no client
    # (RF-07): contatos_YYYYMMDD_HHMMSS.<ext>.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_base = f"contatos_{timestamp}"

    # Log estruturado (B.1 — herda request_id/user_id via ContextFilter,
    # mas tambem repetimos no extra para garantir captura mesmo se o
    # ContextFilter nao estiver ativo em algum ambiente).
    request_id = get_request_id()
    user_id = getattr(usuario, "id", None)

    logger.info(
        "contatos.export formato=%s total_rows=%s duration_ms=%s user_id=%s",
        formato.value,
        total_rows,
        duration_ms,
        user_id,
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "formato": formato.value,
            "total_rows": total_rows,
            "duration_ms": duration_ms,
            "tem_busca": bool(busca),
            "tem_filtro_empresa": filtros.empresa is not None,
            "tem_criado_desde": filtros.criado_desde is not None,
            "tem_criado_ate": filtros.criado_ate is not None,
            "sem_email": bool(filtros.sem_email),
            "sem_telefone": bool(filtros.sem_telefone),
            "sort_by": sort_by.value,
            "sort_order": sort_order.value,
        },
    )

    # Despacho por formato. Cada branch monta o iteravel/buffer + headers
    # corretos. Mantemos `Content-Disposition: attachment; filename=...`
    # exigido pelo PRD (RF-07).
    if formato == FormatoExportContato.csv:
        filename = f"{nome_base}.csv"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return StreamingResponse(
            gerar_csv_contatos(items),
            media_type=CONTATOS_CSV_MIME,
            headers=headers,
        )

    # XLSX — gera o workbook em memoria (BytesIO) e devolve via
    # StreamingResponse. O BytesIO ja vem com seek(0).
    filename = f"{nome_base}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    buffer = gerar_xlsx_contatos(items)
    return StreamingResponse(
        buffer,
        media_type=CONTATOS_XLSX_MIME,
        headers=headers,
    )


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
