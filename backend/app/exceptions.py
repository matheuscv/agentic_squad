"""Hierarquia de exceções de domínio do backend.

Este módulo define as exceções tipadas que representam erros de negócio
do sistema. Cada subclasse de :class:`DomainError` carrega o status HTTP
semanticamente correto via o atributo de classe ``http_status``, mas o
módulo permanece **agnóstico de framework**: nenhum import de FastAPI ou
``HTTPException`` deve ser adicionado aqui.

Os handlers globais que convertem essas exceções em respostas HTTP são
registrados em ``app.exception_handlers`` (TASK-03). Este módulo expõe
apenas a hierarquia.

Uso típico em services/routers::

    from app.exceptions import NotFoundError, ConflictError

    if contato is None:
        raise NotFoundError("contato")

    if email_ja_existe:
        raise ConflictError("email já cadastrado", {"campo": "email"})
"""

from __future__ import annotations

__all__ = [
    "DomainError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
]


class DomainError(Exception):
    """Erro de domínio base.

    Subclasses devem sobrescrever ``http_status`` com o código HTTP
    apropriado. O construtor aceita uma mensagem humana (``message``) e
    um dicionário opcional de detalhes estruturados (``details``) que os
    handlers globais podem incluir no payload de resposta.

    Exemplo::

        raise DomainError("estado inválido", {"estado": "X"})
    """

    # Status HTTP padrão para DomainError "puro" (fallback usado pelos
    # handlers em app.exception_handlers). Subclasses sobrescrevem.
    http_status: int = 400

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        # Normaliza para dict vazio quando não informado, simplificando
        # o consumo nos handlers (basta checar truthiness).
        self.details = details if details is not None else {}


class NotFoundError(DomainError):
    """Recurso de domínio não encontrado (HTTP 404).

    Exemplo::

        raise NotFoundError("contato")
    """

    http_status = 404


class ConflictError(DomainError):
    """Conflito com estado atual do recurso (HTTP 409).

    Tipicamente usado para violações de unicidade ou tentativas de criar
    algo que já existe.

    Exemplo::

        raise ConflictError("email já cadastrado", {"campo": "email"})
    """

    http_status = 409


class ValidationError(DomainError):
    """Dados violam regra de negócio do domínio (HTTP 422).

    Distinta da ``ValidationError`` do Pydantic — esta é levantada
    manualmente por services quando uma regra de domínio é violada.

    Exemplo::

        raise ValidationError("data de nascimento no futuro")
    """

    http_status = 422


class AuthenticationError(DomainError):
    """Falha de autenticação — credencial inválida ou ausente (HTTP 401).

    Exemplo::

        raise AuthenticationError("credenciais inválidas")
    """

    http_status = 401


class AuthorizationError(DomainError):
    """Falha de autorização — usuário autenticado sem permissão (HTTP 403).

    Exemplo::

        raise AuthorizationError("acesso negado ao recurso")
    """

    http_status = 403
