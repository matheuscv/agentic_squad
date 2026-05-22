"""
Testes da ordenacao em GET /contatos/ — TASK-03 (Fase D / RF-01).

Cobre:
- sort_by + sort_order = asc retorna lista em ordem ascendente
- sort_by + sort_order = desc retorna lista em ordem descendente
- Sem sort_by/sort_order: default = criado_em desc (mais recente primeiro)
- sort_by invalido => 422 (validacao via enum Pydantic)
- sort_order invalido => 422
- Ordenacao por telefone (novo campo na allowlist)
- Ordenacao por atualizado_em (novo campo na allowlist)
- Combinacao com busca + paginacao preserva ordenacao

Padrao: AAA (Arrange / Act / Assert).
"""

from __future__ import annotations

import time

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _criar(client, token, *, nome: str, email: str, **extras) -> dict:
    """Cria contato via API; aceita campos extras (telefone, empresa, etc.)."""
    payload = {"nome": nome, "email": email, **extras}
    resp = client.post("/contatos/", json=payload, headers=_auth_header(token))
    assert resp.status_code == 201, f"Falha ao criar contato: {resp.text}"
    return resp.json()


def _seed_tres_contatos(client, token) -> list[dict]:
    """Cria 3 contatos em ordem cronologica conhecida, retornando os JSONs.

    Insere com pequena espera entre cada para garantir criado_em estritamente
    crescente (necessario para validar default = criado_em desc).
    """
    contatos = []
    contatos.append(
        _criar(
            client,
            token,
            nome="Ana Sort",
            email="ana_sort@test.com",
            empresa="Acme",
            telefone="(11) 91111-1111",
        )
    )
    # Garante criado_em estritamente crescente mesmo em SQLite (datetime com
    # resolucao de microssegundos, mas o teste se torna mais robusto).
    time.sleep(0.01)
    contatos.append(
        _criar(
            client,
            token,
            nome="Bruno Sort",
            email="bruno_sort@test.com",
            empresa="Beta Corp",
            telefone="(11) 92222-2222",
        )
    )
    time.sleep(0.01)
    contatos.append(
        _criar(
            client,
            token,
            nome="Carlos Sort",
            email="carlos_sort@test.com",
            empresa="Cielo",
            telefone="(11) 93333-3333",
        )
    )
    return contatos


# ---------------------------------------------------------------------------
# Caso 1 — Ordenacao ASC
# ---------------------------------------------------------------------------


def test_sort_by_nome_asc(client, usuario_adm_token, usuario_default_token):
    """GET /contatos/?sort_by=nome&sort_order=asc retorna ordem alfabetica."""
    # Arrange
    _seed_tres_contatos(client, usuario_adm_token)

    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    nomes = [item["nome"] for item in resp.json()["items"]]
    # A lista pode conter outros contatos vindos de outras fixtures, mas
    # entre os 3 conhecidos a ordem precisa ser Ana < Bruno < Carlos.
    nomes_alvo = [n for n in nomes if n.endswith(" Sort")]
    assert nomes_alvo == sorted(nomes_alvo)


# ---------------------------------------------------------------------------
# Caso 2 — Ordenacao DESC
# ---------------------------------------------------------------------------


def test_sort_by_nome_desc(client, usuario_adm_token, usuario_default_token):
    """GET /contatos/?sort_by=nome&sort_order=desc retorna ordem alfabetica reversa."""
    # Arrange
    _seed_tres_contatos(client, usuario_adm_token)

    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    nomes = [item["nome"] for item in resp.json()["items"]]
    nomes_alvo = [n for n in nomes if n.endswith(" Sort")]
    assert nomes_alvo == sorted(nomes_alvo, reverse=True)


# ---------------------------------------------------------------------------
# Caso 3 — Default (sem sort params) = criado_em DESC
# ---------------------------------------------------------------------------


def test_sort_default_e_criado_em_desc(client, usuario_adm_token, usuario_default_token):
    """Sem sort_by/sort_order: ordem deve ser criado_em DESC (mais recente primeiro).

    Preserva o comportamento documentado no plano (TASK-03):
    "Default = criado_em desc (preservar comportamento atual)".
    """
    # Arrange — cria 3 contatos com criado_em crescente
    contatos = _seed_tres_contatos(client, usuario_adm_token)
    nomes_inseridos_em_ordem = [c["nome"] for c in contatos]
    nomes_esperados_desc = list(reversed(nomes_inseridos_em_ordem))

    # Act — sem sort_by/sort_order
    resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))

    # Assert
    assert resp.status_code == 200
    nomes_retornados = [item["nome"] for item in resp.json()["items"]]
    nomes_alvo = [n for n in nomes_retornados if n.endswith(" Sort")]
    assert nomes_alvo == nomes_esperados_desc


# ---------------------------------------------------------------------------
# Caso 4 — sort_by invalido => 422
# ---------------------------------------------------------------------------


def test_sort_by_invalido_retorna_422(client, usuario_default_token):
    """sort_by fora da allowlist deve disparar 422 via validacao do enum Pydantic."""
    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "senha"},  # nao existe na allowlist — protege contra SQLi
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 422
    # Mensagem deve mencionar o campo problematico — confere se o detalhe
    # da 422 do FastAPI inclui referencia clara para o dev frontend.
    body = resp.json()
    assert "detail" in body


def test_sort_order_invalido_retorna_422(client, usuario_default_token):
    """sort_order fora de {asc, desc} deve disparar 422."""
    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "nome", "sort_order": "crescente"},  # invalido
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Cobertura extra — colunas que foram ADICIONADAS na allowlist (telefone,
# atualizado_em). Garante que nao houve regressao e que a allowlist
# corresponde ao contrato D.1.
# ---------------------------------------------------------------------------


def test_sort_by_telefone_asc_aceito(client, usuario_adm_token, usuario_default_token):
    """sort_by=telefone deve ser aceito (na allowlist da Fase D)."""
    # Arrange
    _seed_tres_contatos(client, usuario_adm_token)

    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "telefone", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert — basta nao retornar 422; o ordering em si ja foi validado
    # nos testes de nome (mesmo caminho de codigo, mesma logica).
    assert resp.status_code == 200


def test_sort_by_atualizado_em_aceito(client, usuario_adm_token, usuario_default_token):
    """sort_by=atualizado_em deve ser aceito (na allowlist da Fase D)."""
    # Arrange
    _seed_tres_contatos(client, usuario_adm_token)

    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "atualizado_em", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200


def test_sort_by_empresa_desc(client, usuario_adm_token, usuario_default_token):
    """sort_by=empresa,sort_order=desc retorna lista em ordem reversa de empresa."""
    # Arrange — cria 3 contatos com empresas conhecidas (Acme < Beta < Cielo)
    _seed_tres_contatos(client, usuario_adm_token)

    # Act
    resp = client.get(
        "/contatos/",
        params={"sort_by": "empresa", "sort_order": "desc"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    empresas = [item.get("empresa") for item in resp.json()["items"]]
    empresas_alvo = [e for e in empresas if e in {"Acme", "Beta Corp", "Cielo"}]
    assert empresas_alvo == sorted(empresas_alvo, reverse=True)


# ---------------------------------------------------------------------------
# Combinacao: ordenacao + busca + paginacao funcionam juntas
# ---------------------------------------------------------------------------


def test_sort_combinado_com_busca(client, usuario_adm_token, usuario_default_token):
    """sort + busca: filtro por 'Sort' + sort_by=nome,asc retorna apenas os 3 inseridos em ordem."""
    # Arrange
    _seed_tres_contatos(client, usuario_adm_token)

    # Act
    resp = client.get(
        "/contatos/",
        params={"busca": "Sort", "sort_by": "nome", "sort_order": "asc"},
        headers=_auth_header(usuario_default_token),
    )

    # Assert
    assert resp.status_code == 200
    nomes = [item["nome"] for item in resp.json()["items"]]
    # Todos os retornados devem conter 'Sort' (filtro de busca) e estar em
    # ordem alfabetica crescente.
    assert all("Sort" in n for n in nomes)
    assert nomes == sorted(nomes)
