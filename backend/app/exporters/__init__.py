"""Pacote de exportadores (Fase D — TASK-06 / RF-07 a RF-10).

Contém implementações de exportação de dados de Contato em formatos
CSV (stdlib `csv`) e XLSX (`openpyxl`). Cada exportador devolve um
iterável/`BytesIO` adequado para `StreamingResponse` do FastAPI.
"""

from app.exporters.csv_exporter import (
    CONTATOS_CSV_HEADERS,
    CONTATOS_CSV_MIME,
    gerar_csv_contatos,
)
from app.exporters.xlsx_exporter import (
    CONTATOS_XLSX_MIME,
    gerar_xlsx_contatos,
)

__all__ = (
    "CONTATOS_CSV_HEADERS",
    "CONTATOS_CSV_MIME",
    "CONTATOS_XLSX_MIME",
    "gerar_csv_contatos",
    "gerar_xlsx_contatos",
)
