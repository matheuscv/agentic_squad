"""
Smoke test end-to-end da Fase D (TASK-11).

Exercita o fluxo completo:
  1. Criar 10 contatos com dados variados (empresa, telefone)
  2. Listar sem filtros (default criado_em desc)
  3. Ordenar por nome ASC
  4. Filtrar por empresa
  5. Exportar CSV com filtro ativo

Criterios de aceite (TASK-11):
  - Smoke test passa em < 5 segundos.
  - Todos os endpoints retornam status correto.
  - Export CSV respeita filtro e ordenacao.
"""

from __future__ import annotations

import csv
import io


_SEED = [
    {"nome": "Alice Souza", "email": "alice@smoke.com", "empresa": "Alpha"},
    {"nome": "Bruno Lima", "email": "bruno@smoke.com", "empresa": "Beta Corp"},
    {"nome": "Carla Dias", "email": "carla@smoke.com", "empresa": "Alpha"},
    {"nome": "Diego Rocha", "email": "diego@smoke.com", "empresa": "Gamma SA"},
    {"nome": "Elena Costa", "email": "elena@smoke.com", "empresa": "Alpha", "telefone": "(11) 91111-1111"},
    {"nome": "Fabio Nunes", "email": "fabio@smoke.com", "empresa": "Delta"},
    {"nome": "Gabi Moura", "email": "gabi@smoke.com", "empresa": "Beta Corp"},
    {"nome": "Hugo Pires", "email": "hugo@smoke.com"},
    {"nome": "Iris Vaz", "email": "iris@smoke.com", "empresa": "Alpha"},
    {"nome": "Joao Melo", "email": "joao@smoke.com", "empresa": "Epsilon"},
]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_smoke_fase_d(client, usuario_adm_token, usuario_default_token):
    """Fluxo completo: criar -> listar -> ordenar -> filtrar -> exportar CSV."""
    headers_adm = _auth(usuario_adm_token)
    headers_default = _auth(usuario_default_token)

    # 1. Criar 10 contatos
    ids = []
    for seed in _SEED:
        r = client.post("/contatos/", json=seed, headers=headers_adm)
        assert r.status_code == 201, f"Falha ao criar contato: {r.text}"
        ids.append(r.json()["id"])
    assert len(ids) == 10

    # 2. Listar sem filtros — default criado_em desc, retorna todos
    r = client.get("/contatos/", headers=headers_default)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 10

    # 3. Ordenar por nome ASC
    r = client.get("/contatos/", params={"sort_by": "nome", "sort_order": "asc"}, headers=headers_default)
    assert r.status_code == 200
    nomes = [c["nome"] for c in r.json()["items"]]
    # Verifica que os nomes do seed estao em ordem crescente no resultado
    smoke_nomes = [n for n in nomes if any(n == s["nome"] for s in _SEED)]
    assert smoke_nomes == sorted(smoke_nomes)

    # 4. Filtrar por empresa "Alpha"
    r = client.get("/contatos/", params={"empresa": "Alpha"}, headers=headers_default)
    assert r.status_code == 200
    empresas = {c["empresa"] for c in r.json()["items"]}
    assert all("alpha" in (e or "").lower() for e in empresas)
    assert r.json()["total"] == 4

    # 5. Exportar CSV com filtro empresa="Alpha" e sort nome ASC
    r = client.get(
        "/contatos/export",
        params={"formato": "csv", "empresa": "Alpha", "sort_by": "nome", "sort_order": "asc"},
        headers=headers_default,
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "filename=" in r.headers.get("content-disposition", "")

    # Verifica headers PT-BR e conteudo
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    assert len(rows) == 4
    nomes_csv = [row["nome"] for row in rows]
    assert nomes_csv == sorted(nomes_csv), "CSV deve estar ordenado por nome ASC"
    assert all("Alpha" in (row.get("empresa") or "") for row in rows)
