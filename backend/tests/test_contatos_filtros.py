"""
Testes dos filtros avancados em GET /contatos/ — TASK-05 (Fase D / D.4 / RF-06).

Cobre:
- empresa (ilike parcial, case-insensitive)
- criado_desde / criado_ate (inclusivos)
- sem_email / sem_telefone (NULL ou "")
- Combinacoes entre filtros
- Combinacao com busca + sort
- range invertido (criado_desde > criado_ate) -> 422
- empresa vazia/whitespace normalizada para "sem filtro"

Padrao: AAA (Arrange / Act / Assert).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.contato import Contato
from app.schemas.contato import ContatoCriar
from app.services import contato_service


# ===========================================================================
# Helpers
# ===========================================================================


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _criar(client, token, *, nome: str, email: str, **extras) -> dict:
    payload = {"nome": nome, "email": email, **extras}
    resp = client.post("/contatos/", json=payload, headers=_auth_header(token))
    assert resp.status_code == 201, f"Falha ao criar contato: {resp.text}"
    return resp.json()


def _seed_basico(client, token):
    """Cria 4 contatos distintos cobrindo cenarios dos filtros."""
    # Empresa Alfa, com email e telefone
    a = _criar(
        client,
        token,
        nome="Alfa Pessoa",
        email="alfa@test.com",
        empresa="Alfa Industria",
        telefone="(11) 91111-1111",
    )
    # Empresa Beta, com email mas sem telefone
    b = _criar(
        client,
        token,
        nome="Beta Pessoa",
        email="beta@test.com",
        empresa="Beta SA",
    )
    # Empresa Gamma, com email mas sem telefone
    g = _criar(
        client,
        token,
        nome="Gamma Pessoa",
        email="gamma@test.com",
        empresa="Gamma LTDA",
    )
    # Empresa Acme, com telefone mas sem email armazenado como "" (forcado depois)
    d = _criar(
        client,
        token,
        nome="Delta Pessoa",
        email="delta@test.com",
        empresa="Acme Corp",
        telefone="(11) 94444-4444",
    )
    return {"alfa": a, "beta": b, "gamma": g, "delta": d}


# ===========================================================================
# Filtro: empresa
# ===========================================================================


def test_filtro_empresa_match_parcial(client, usuario_adm_token, usuario_default_token):
    """GET /contatos/?empresa=Alfa retorna apenas registros cuja empresa contem 'Alfa'."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"empresa": "Alfa"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    empresas = [c["empresa"] for c in resp.json()["items"]]
    # Todos os retornados devem conter "Alfa" no nome da empresa.
    assert all("Alfa" in e for e in empresas)
    # E ao menos o seed Alfa esta presente
    assert any("Alfa" in e for e in empresas)


def test_filtro_empresa_case_insensitive(client, usuario_adm_token, usuario_default_token):
    """Filtro empresa e case-insensitive (ilike)."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"empresa": "alfa"},  # minusculas
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    empresas = [c["empresa"] for c in resp.json()["items"]]
    assert any(e and "Alfa" in e for e in empresas)


def test_filtro_empresa_vazia_e_ignorada(client, usuario_adm_token, usuario_default_token):
    """empresa='' (vazia) deve ser ignorada pelo schema (normaliza para None)."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"empresa": ""},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    # Sem filtro: deve retornar pelo menos os 4 contatos do seed.
    assert resp.json()["total"] >= 4


def test_filtro_empresa_so_espacos_e_ignorada(
    client, usuario_adm_token, usuario_default_token
):
    """empresa='   ' (so espacos) tambem deve ser normalizada para None."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"empresa": "   "},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    # Sem filtro real: pelo menos os 4 do seed.
    assert resp.json()["total"] >= 4


# ===========================================================================
# Filtros: criado_desde / criado_ate (inclusivos)
# ===========================================================================


def test_filtro_criado_desde_inclui_dia(client, usuario_adm_token, usuario_default_token):
    """criado_desde no dia atual deve incluir contatos criados hoje (inclusivo)."""
    _criar(
        client,
        usuario_adm_token,
        nome="Recente",
        email="recente@test.com",
        empresa="Recentes SA",
    )
    hoje = date.today().isoformat()

    resp = client.get(
        "/contatos/",
        params={"criado_desde": hoje},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    # Deve incluir contatos cujo criado_em >= 00:00:00 de hoje.
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert "Recente" in nomes


def test_filtro_criado_ate_inclui_dia(client, usuario_adm_token, usuario_default_token):
    """criado_ate no dia atual deve incluir contatos criados hoje (inclusivo)."""
    _criar(
        client,
        usuario_adm_token,
        nome="Hoje",
        email="hoje@test.com",
    )
    hoje = date.today().isoformat()

    resp = client.get(
        "/contatos/",
        params={"criado_ate": hoje},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert "Hoje" in nomes


def test_filtro_range_invertido_retorna_422(client, usuario_default_token):
    """criado_desde > criado_ate deve retornar 422 (RNF-05 / RF-05)."""
    resp = client.get(
        "/contatos/",
        params={"criado_desde": "2026-12-31", "criado_ate": "2026-01-01"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 422


def test_filtro_intervalo_fora_passado_retorna_vazio(
    client, usuario_adm_token, usuario_default_token
):
    """Intervalo de datas no passado distante deve retornar zero registros."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"criado_desde": "1990-01-01", "criado_ate": "1990-12-31"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_filtro_data_intervalo_amplo_inclui_seed(
    client, usuario_adm_token, usuario_default_token
):
    """Intervalo amplo cobrindo hoje deve incluir todos os contatos do seed."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"criado_desde": "2000-01-01", "criado_ate": "2099-12-31"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    # >= 4 (seed completo); nada eh excluido por data.
    assert resp.json()["total"] >= 4


# ===========================================================================
# Filtros: sem_email / sem_telefone
# ===========================================================================


def test_filtro_sem_telefone_isolado(
    client, usuario_adm_token, usuario_default_token
):
    """sem_telefone=true retorna apenas contatos com telefone NULL/vazio."""
    seed = _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"sem_telefone": "true"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    # Todos retornados devem ter telefone None/vazio
    for c in items:
        assert c["telefone"] in (None, "")
    # Os seeds Beta e Gamma (sem telefone) devem estar; Alfa e Delta (com)
    # nao devem aparecer.
    ids_retornados = {c["id"] for c in items}
    assert seed["beta"]["id"] in ids_retornados
    assert seed["gamma"]["id"] in ids_retornados
    assert seed["alfa"]["id"] not in ids_retornados
    assert seed["delta"]["id"] not in ids_retornados


def test_filtro_sem_email_isolado_com_setup_direto(db_session, client, usuario_default_token):
    """sem_email=true retorna apenas contatos com email vazio.

    Como o schema rejeita email vazio na criacao, criamos um contato
    diretamente via ORM com email="" para simular dado legado.
    """
    # Cria contato com email no service (regra normal) e DEPOIS forca email=""
    # no banco para simular registro legado (cenario que o filtro deve cobrir).
    c = contato_service.criar_contato(
        db_session,
        ContatoCriar(nome="Legado", email="legado@test.com"),
    )
    # Forca email vazio diretamente no ORM (cenario migrado de base antiga).
    c.email = ""
    db_session.commit()

    resp = client.get(
        "/contatos/",
        params={"sem_email": "true"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    assert "Legado" in nomes
    # Todos retornados devem ter email vazio/None
    for item in resp.json()["items"]:
        assert item["email"] in (None, "")


def test_filtro_sem_telefone_false_e_ignorado(
    client, usuario_adm_token, usuario_default_token
):
    """sem_telefone=false NAO deve filtrar — comportamento boolean truthy."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"sem_telefone": "false"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    # Sem filtro real — deve retornar todos os contatos.
    assert resp.json()["total"] >= 4


# ===========================================================================
# Combinacoes
# ===========================================================================


def test_filtro_empresa_e_sem_telefone_combinados(
    client, usuario_adm_token, usuario_default_token
):
    """Filtros combinados: empresa contendo 'Beta' + sem_telefone."""
    seed = _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"empresa": "Beta", "sem_telefone": "true"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    # Apenas o seed Beta atende ambos os criterios.
    ids = [c["id"] for c in items]
    assert seed["beta"]["id"] in ids
    assert seed["alfa"]["id"] not in ids
    assert seed["delta"]["id"] not in ids


def test_filtro_combinado_com_busca_e_sort(
    client, usuario_adm_token, usuario_default_token
):
    """Combinacao: busca + filtro empresa + sort_by nome asc."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={
            "busca": "Pessoa",
            "empresa": "a",  # bate em Alfa, Beta, Gamma, Acme (todas tem 'a')
            "sort_by": "nome",
            "sort_order": "asc",
        },
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    nomes = [c["nome"] for c in resp.json()["items"]]
    # Todos devem conter 'Pessoa' (busca) E o nome alfabetico crescente.
    assert all("Pessoa" in n for n in nomes)
    assert nomes == sorted(nomes)


def test_filtro_sem_telefone_e_sem_email_combinados_retorna_zero(
    client, usuario_adm_token, usuario_default_token
):
    """Sem telefone E sem email simultaneamente — nenhum seed atende."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        params={"sem_email": "true", "sem_telefone": "true"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    # Nenhum dos seeds tem AMBOS vazios — todos tem email valido.
    assert resp.json()["total"] == 0


# ===========================================================================
# Filtros sem regressao na listagem normal
# ===========================================================================


def test_filtros_omitidos_mantem_comportamento_padrao(
    client, usuario_adm_token, usuario_default_token
):
    """Sem nenhum filtro, listagem retorna todos os contatos (regressivo)."""
    _seed_basico(client, usuario_adm_token)

    resp = client.get(
        "/contatos/",
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 4


def test_filtros_nao_incluem_soft_deleted(
    client, usuario_adm_token, usuario_default_token
):
    """Contatos soft-deleted nao devem aparecer mesmo com filtros."""
    seed = _seed_basico(client, usuario_adm_token)
    # Deleta o Alfa (que tem telefone)
    resp_del = client.delete(
        f"/contatos/{seed['alfa']['id']}",
        headers=_auth_header(usuario_adm_token),
    )
    assert resp_del.status_code == 204

    resp = client.get(
        "/contatos/",
        params={"empresa": "Alfa"},
        headers=_auth_header(usuario_default_token),
    )
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()["items"]]
    assert seed["alfa"]["id"] not in ids
