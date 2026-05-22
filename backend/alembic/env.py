import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Adiciona o diretório backend ao path para que os imports de app funcionem
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa Base e todos os modelos para que target_metadata seja populado
from app.database import Base  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402, F401
from app.models.contato import Contato  # noqa: E402, F401

# Objeto de configuração do alembic (lê alembic.ini)
config = context.config

# Sobrescreve a URL do alembic.ini com DATABASE_URL do ambiente (se definida).
# Necessário para que o Render/produção use PostgreSQL em vez do SQLite local.
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    config.set_main_option("sqlalchemy.url", _db_url)

# Configura logging a partir do alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata do SQLAlchemy — usado pelo autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações em modo offline (sem conexão ativa)."""
    url = config.get_main_option("sqlalchemy.url") or ""
    # render_as_batch só é necessário para SQLite (não suporta ALTER TABLE completo)
    render_as_batch = url.startswith("sqlite")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=render_as_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações em modo online (com conexão ativa)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    _url = config.get_main_option("sqlalchemy.url") or ""
    render_as_batch = _url.startswith("sqlite")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
