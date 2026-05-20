"""add_indices_contatos

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-19

Migration non-destructive: adiciona índices nas colunas `nome`, `email` e
`criado_em` da tabela `contatos`. Estas colunas são usadas em busca (LIKE/=),
ordenação (ORDER BY) e filtros — RF-06 (C.6) / TASK-19.

Operações:
    - CREATE INDEX ix_contatos_nome ON contatos (nome)
    - CREATE INDEX ix_contatos_email ON contatos (email)
    - CREATE INDEX ix_contatos_criado_em ON contatos (criado_em)

Observação sobre `email`: a coluna já possui constraint `UNIQUE`, que em
SQLite cria um índice único implícito (ex.: `sqlite_autoindex_contatos_*`).
O índice nomeado `ix_contatos_email` é criado adicionalmente para alinhar-se
ao mapeamento ORM (`index=True` no model) e permitir reutilização por consultas
que não dependam do nome do índice automático. Em ambientes Postgres, considerar
substituir por `op.create_index(..., postgresql_concurrently=True)` em tabelas
grandes (R-02) — não aplicável a SQLite.

Sem operações destrutivas. `downgrade()` apenas remove os índices criados.
"""

from alembic import op

# Identificadores da revisão
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cada índice é criado de forma independente; falha em um não corrompe os demais.
    op.create_index("ix_contatos_nome", "contatos", ["nome"])
    op.create_index("ix_contatos_email", "contatos", ["email"])
    op.create_index("ix_contatos_criado_em", "contatos", ["criado_em"])


def downgrade() -> None:
    # Drop em ordem reversa por simetria/legibilidade.
    op.drop_index("ix_contatos_criado_em", table_name="contatos")
    op.drop_index("ix_contatos_email", table_name="contatos")
    op.drop_index("ix_contatos_nome", table_name="contatos")
