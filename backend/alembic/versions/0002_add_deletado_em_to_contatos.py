"""add_deletado_em_to_contatos

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-12

Migration non-destructive: adiciona coluna `deletado_em` (DATETIME, NULL, DEFAULT NULL)
à tabela `contatos`. Nenhum dado existente é removido ou alterado.
"""

from alembic import op
import sqlalchemy as sa

# Identificadores da revisão
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table é necessário no SQLite, que não suporta ALTER TABLE nativo
    with op.batch_alter_table("contatos") as batch_op:
        batch_op.add_column(
            sa.Column(
                "deletado_em",
                sa.DateTime(),
                nullable=True,
                # DEFAULT NULL explícito — linhas existentes ficam com NULL (ativas)
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("contatos") as batch_op:
        batch_op.drop_column("deletado_em")
