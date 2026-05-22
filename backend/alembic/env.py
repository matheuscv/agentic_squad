import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, engine_from_config, pool

from alembic import context

# Adiciona o diretório backend ao path para que os imports de app funcionem
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa Base e todos os modelos para que target_metadata seja populado
from app.database import Base  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402, F401
from app.models.contato import Contato  # noqa: E402, F401

# Objeto de configuração do alembic (lê alembic.ini)
config = context.config

# Configura logging a partir do alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata do SQLAlchemy — usado pelo autogenerate
target_metadata = Base.metadata

# URL efetiva: DATABASE_URL do ambiente tem prioridade sobre alembic.ini.
# NÃO usamos config.set_main_option() pois o configparser do Python trata '%'
# como sintaxe de interpolação — URLs com senhas codificadas (%40, %23, etc.)
# causam ValueError. Lemos a URL diretamente do ambiente em cada função.
_env_db_url: str | None = os.environ.get("DATABASE_URL")


def run_migrations_offline() -> None:
    """Executa migrações em modo offline (sem conexão ativa)."""
    url = _env_db_url or config.get_main_option("sqlalchemy.url") or ""
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
    if _env_db_url:
        # Cria engine diretamente da variável de ambiente, bypassando o
        # configparser para evitar erros de interpolação com '%' na senha.
        connectable = create_engine(_env_db_url, poolclass=pool.NullPool)
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    _url = _env_db_url or config.get_main_option("sqlalchemy.url") or ""
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
