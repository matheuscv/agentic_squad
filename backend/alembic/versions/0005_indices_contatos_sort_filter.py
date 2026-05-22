"""indices_contatos_sort_filter

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-20

TASK-01 (Fase 0, plano D parcial): garantir indices nao-unicos em colunas
frequentemente usadas para ORDER BY (D.1 — sort) e WHERE (D.4 — filtros
`empresa`, `criado_de`, `criado_ate`) no endpoint `GET /contatos/`.

Colunas-alvo segundo o plano: `nome`, `email`, `empresa`, `criado_em`.

Decisao conservadora (registrada aqui em vez de em CHANGELOG/PR para que
fique versionada com a propria migration):

    A revisao anterior `0004_add_indices_contatos` ja criou:
        - ix_contatos_nome
        - ix_contatos_email
        - ix_contatos_criado_em

    Faltava apenas `ix_contatos_empresa`. Recriar indices ja existentes faria
    `alembic upgrade head` falhar com "index already exists" em bases que
    aplicaram a 0004 (criterio de aceite explicito da TASK-01: "aplica a
    revisao sem erro em base existente"). Portanto esta revisao adiciona
    SOMENTE o indice ausente. Os demais permanecem cobertos pela 0004 e
    juntos satisfazem o escopo da TASK-01 (RNF-01: p95 < 300 ms ate 50k linhas).

A migration nao altera `backend/app/models/contato.py` (instrucao explicita
da TASK-01: "indices via migration pura, para minimizar conflito com tasks
paralelas").

Validacao manual (SQLite) apos `alembic upgrade head`:

    sqlite> PRAGMA index_list('contatos');
    -- deve listar: ix_contatos_nome, ix_contatos_email,
    --              ix_contatos_criado_em, ix_contatos_empresa,
    --              alem do indice unico implicito do `email`.

Sem operacoes destrutivas. `downgrade()` remove apenas o indice criado aqui.
"""

from alembic import op

# Identificadores da revisao
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Indice nao-unico em `empresa` — usado em ILIKE (filtro D.4) e ordenacao.
    # Os indices `ix_contatos_nome`, `ix_contatos_email` e `ix_contatos_criado_em`
    # ja foram criados pela revisao 0004 e nao sao recriados aqui (ver docstring).
    op.create_index("ix_contatos_empresa", "contatos", ["empresa"])


def downgrade() -> None:
    # Reverte apenas o que esta revisao criou; demais indices permanecem sob 0004.
    op.drop_index("ix_contatos_empresa", table_name="contatos")
