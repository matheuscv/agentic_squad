"""add_auditoria_contatos

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-12

Migration non-destructive: adiciona colunas de auditoria `criado_por_id` e
`atualizado_por_id` (INTEGER, NULL, FK -> usuarios.id ON DELETE SET NULL)
à tabela `contatos`. Registros existentes ficam com NULL nos dois campos.

Nota sobre SQLite: FK constraints são declaradas mas não executadas por padrão
no SQLite. O ON DELETE SET NULL está presente para documentar a intenção e
funcionar em bancos de produção que suportam FKs (PostgreSQL, MySQL).
"""

from alembic import op
import sqlalchemy as sa

# Identificadores da revisão
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table é necessário no SQLite, que não suporta ALTER TABLE nativo
    with op.batch_alter_table("contatos") as batch_op:
        batch_op.add_column(
            sa.Column(
                "criado_por_id",
                sa.Integer(),
                nullable=True,
                # FK declarada — registros existentes ficam com NULL
            )
        )
        batch_op.add_column(
            sa.Column(
                "atualizado_por_id",
                sa.Integer(),
                nullable=True,
            )
        )
        # Cria FK constraints após adicionar as colunas
        batch_op.create_foreign_key(
            "fk_contatos_criado_por_id",
            "usuarios",
            ["criado_por_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_contatos_atualizado_por_id",
            "usuarios",
            ["atualizado_por_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("contatos") as batch_op:
        batch_op.drop_constraint("fk_contatos_criado_por_id", type_="foreignkey")
        batch_op.drop_constraint("fk_contatos_atualizado_por_id", type_="foreignkey")
        batch_op.drop_column("atualizado_por_id")
        batch_op.drop_column("criado_por_id")
