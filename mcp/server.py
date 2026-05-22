"""MCP Server — Contatos (wraps FastAPI REST API)."""

import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

API_URL = os.getenv("API_URL", "http://localhost:8000")
_token: Optional[str] = None

mcp = FastMCP("contatos-mcp")


def _login() -> str:
    resp = httpx.post(
        f"{API_URL}/auth/login",
        json={
            "email": os.getenv("MCP_USERNAME"),
            "senha": os.getenv("MCP_PASSWORD"),
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers() -> dict:
    global _token
    if not _token:
        _token = _login()
    return {"Authorization": f"Bearer {_token}"}


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    global _token
    resp = httpx.request(method, f"{API_URL}{path}", headers=_headers(), timeout=15, **kwargs)
    if resp.status_code == 401:
        _token = _login()
        resp = httpx.request(method, f"{API_URL}{path}", headers=_headers(), timeout=15, **kwargs)
    return resp


@mcp.tool()
def listar_contatos() -> list[dict]:
    """Lista todos os contatos cadastrados na base de dados."""
    resp = _request("GET", "/contatos/", params={"limit": 1000})
    resp.raise_for_status()
    return resp.json()["items"]


@mcp.tool()
def criar_contato(
    nome: str,
    email: str,
    telefone: Optional[str] = None,
    empresa: Optional[str] = None,
    observacoes: Optional[str] = None,
) -> dict:
    """Cria um novo contato na base.

    Args:
        nome: Nome completo do contato (obrigatório).
        email: E-mail único do contato (obrigatório).
        telefone: Telefone no formato (XX) XXXXX-XXXX (opcional).
        empresa: Nome da empresa (opcional).
        observacoes: Observações livres (opcional).
    """
    payload: dict = {"nome": nome, "email": email}
    if telefone is not None:
        payload["telefone"] = telefone
    if empresa is not None:
        payload["empresa"] = empresa
    if observacoes is not None:
        payload["observacoes"] = observacoes

    resp = _request("POST", "/contatos/", json=payload)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def atualizar_contato(
    id: int,
    nome: Optional[str] = None,
    email: Optional[str] = None,
    telefone: Optional[str] = None,
    empresa: Optional[str] = None,
    observacoes: Optional[str] = None,
) -> dict:
    """Atualiza parcialmente os dados de um contato existente.

    Apenas os campos informados (não-None) serão alterados.

    Args:
        id: ID do contato a atualizar (obrigatório).
        nome: Novo nome (opcional).
        email: Novo e-mail (opcional).
        telefone: Novo telefone no formato (XX) XXXXX-XXXX (opcional).
        empresa: Nova empresa (opcional).
        observacoes: Novas observações (opcional).
    """
    payload = {
        k: v
        for k, v in {
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "empresa": empresa,
            "observacoes": observacoes,
        }.items()
        if v is not None
    }

    if not payload:
        raise ValueError("Informe pelo menos um campo para atualizar.")

    resp = _request("PATCH", f"/contatos/{id}", json=payload)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def excluir_contato(id: int) -> str:
    """Exclui (soft delete) um contato pelo ID.

    O contato não é removido fisicamente — apenas marcado como excluído.

    Args:
        id: ID do contato a excluir (obrigatório).
    """
    resp = _request("DELETE", f"/contatos/{id}")
    resp.raise_for_status()
    return f"Contato {id} excluído com sucesso."


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8001")),
        )
    else:
        mcp.run()
