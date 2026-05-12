from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
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
    # Auditoria RF-F3.2-01: rastreia quem criou/modificou o registro.
    # ON DELETE SET NULL: se o usuário for removido, o campo fica NULL (sem orfanizar o contato).
    # Nota: SQLite ignora FK constraints por padrão; nullable garante compatibilidade retroativa.
    criado_por_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, default=None
    )
    atualizado_por_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, default=None
    )
