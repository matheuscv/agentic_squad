from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Contato(Base):
    """Modelo de contato de cliente."""

    __tablename__ = "contatos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    empresa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        # onupdate via SQLAlchemy ORM — será atualizado pelo service ao persistir
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # Soft delete: preenchido com o instante UTC da exclusão lógica; NULL = ativo
    deletado_em: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )
