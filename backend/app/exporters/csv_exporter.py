"""Exportador CSV de Contatos (Fase D — TASK-06 / RF-07 a RF-10).

Gera linhas CSV via generator + stdlib `csv` de forma streaming-friendly,
usando um buffer in-memory (`io.StringIO`) reciclado por linha. O retorno
e um generator que produz `bytes` codificados em UTF-8 — pronto para ser
passado direto a `StreamingResponse`.

Decisao: usamos `csv.writer` para garantir conformidade com RFC 4180
(escape de aspas, separadores, quebras de linha dentro de campo). NAO
concatenamos strings manualmente para evitar corrupcao quando o conteudo
contiver virgula/aspa/quebra de linha (ex.: campo `observacoes`).
"""

from __future__ import annotations

import csv
import io
from typing import Iterable, Iterator

from app.models.contato import Contato

# Mime type oficial para CSV (RFC 7111). Inclui charset explicito porque
# Excel/LibreOffice usam o header para decidir a decodificacao quando
# nao ha BOM.
CONTATOS_CSV_MIME = "text/csv; charset=utf-8"

# Headers (PT-BR) — RF-07. Manter ordem alinhada com `_linha_de(contato)`.
CONTATOS_CSV_HEADERS: tuple[str, ...] = (
    "id",
    "nome",
    "email",
    "telefone",
    "empresa",
    "criado_em",
    "atualizado_em",
)


def _formatar_datetime(valor) -> str:
    """Serializa datetime como ISO 8601; None -> string vazia.

    Mantemos ISO 8601 (e.g. `2026-05-20T13:45:00`) por ser portavel e
    nao-ambiguo. Excel/LibreOffice interpretam corretamente.
    """
    if valor is None:
        return ""
    # Datetimes do modelo sao naive (SQLAlchemy DateTime sem timezone) — a
    # serializacao isoformat() devolve string sem offset, que e o que
    # queremos para nao induzir falsa precisao de timezone na planilha.
    return valor.isoformat()


def _linha_de(contato: Contato) -> tuple[str, ...]:
    """Converte um Contato em uma tupla de strings na ordem dos headers."""
    return (
        str(contato.id),
        contato.nome or "",
        contato.email or "",
        contato.telefone or "",
        contato.empresa or "",
        _formatar_datetime(contato.criado_em),
        _formatar_datetime(contato.atualizado_em),
    )


def gerar_csv_contatos(contatos: Iterable[Contato]) -> Iterator[bytes]:
    """Generator que produz o CSV em chunks (1 linha por iteracao).

    Uso:
        StreamingResponse(gerar_csv_contatos(items), media_type=CONTATOS_CSV_MIME)

    Implementacao: `csv.writer` precisa de um file-like; usamos um
    `StringIO` reciclado (truncate+seek) por linha para evitar alocar um
    buffer gigante quando a lista for grande. Cada chunk e codificado em
    UTF-8 antes de ser cedido ao FastAPI.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    # Cabecalho — primeira linha.
    writer.writerow(CONTATOS_CSV_HEADERS)
    yield buffer.getvalue().encode("utf-8")
    buffer.seek(0)
    buffer.truncate(0)

    # Dados — uma linha por contato. Reciclamos o buffer para nao
    # acumular memoria proporcional ao total de registros (RNF-02).
    for contato in contatos:
        writer.writerow(_linha_de(contato))
        yield buffer.getvalue().encode("utf-8")
        buffer.seek(0)
        buffer.truncate(0)
