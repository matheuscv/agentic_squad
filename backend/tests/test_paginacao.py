"""
Testes de paginação para o endpoint GET /contatos/ e para contato_service.listar_contatos.

Cobre os critérios de aceite da Fase 1 (PRD seção 13.4):
- RF-F1-03: resposta com campos `items` e `total`
- RN-F1-01: defaults skip=0/limit=20, máximo limit=200
"""

import pytest

from app.schemas.contato import ContatoCriar
from app.services import contato_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _criar_n_contatos(db_session, n: int) -> None:
    """Insere n contatos com nomes e e-mails únicos no banco."""
    for i in range(1, n + 1):
        contato_service.criar_contato(
            db_session,
            ContatoCriar(
                nome=f"Contato {i:03d}",
                email=f"contato{i:03d}@paginacao.com",
                empresa="PagCorp",
            ),
        )


# ===========================================================================
# Testes de integração HTTP — GET /contatos/
# ===========================================================================

class TestListarContatosRespostaShape:
    """Verifica que o endpoint sempre retorna { items, total }."""

    def test_sem_parametros_retorna_items_e_total(self, client, usuario_default_token):
        """GET /contatos/ sem params deve retornar objeto com chaves items e total."""
        resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data, "Resposta deve conter campo 'items'"
        assert "total" in data, "Resposta deve conter campo 'total'"
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

    def test_banco_vazio_retorna_items_vazio_e_total_zero(self, client, usuario_default_token):
        """Com banco vazio, items=[] e total=0."""
        resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_resposta_nao_e_lista_plana(self, client, usuario_default_token, contato_exemplo):
        """A resposta não deve ser uma lista plana (regressão — formato anterior)."""
        resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))
        assert resp.status_code == 200
        # Deve ser dict, não list
        assert isinstance(resp.json(), dict), (
            "O endpoint retornou lista em vez de ContatoListResponse — "
            "provável regressão ao formato anterior."
        )


class TestPaginacaoDefaults:
    """Verifica o comportamento com parâmetros padrão (skip=0, limit=20)."""

    def test_default_retorna_ate_20_items(self, client, db_session, usuario_default_token):
        """Sem params, o endpoint retorna no máximo 20 registros."""
        _criar_n_contatos(db_session, 25)
        resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 20

    def test_default_total_reflete_count_real(self, client, db_session, usuario_default_token):
        """Campo total deve ser 25 mesmo que items contenha apenas 20."""
        _criar_n_contatos(db_session, 25)
        resp = client.get("/contatos/", headers=_auth_header(usuario_default_token))
        data = resp.json()
        assert data["total"] == 25
        assert len(data["items"]) == 20  # apenas a primeira página

    def test_sem_params_equivale_a_skip0_limit20(
        self, client, db_session, usuario_default_token
    ):
        """GET /contatos/ e GET /contatos/?skip=0&limit=20 devem retornar o mesmo."""
        _criar_n_contatos(db_session, 10)
        resp_sem = client.get("/contatos/", headers=_auth_header(usuario_default_token))
        resp_com = client.get(
            "/contatos/",
            params={"skip": 0, "limit": 20},
            headers=_auth_header(usuario_default_token),
        )
        assert resp_sem.json() == resp_com.json()


class TestPaginacaoSkipLimit:
    """Verifica o comportamento dos parâmetros skip e limit."""

    def test_limit_5_retorna_no_maximo_5_items(
        self, client, db_session, usuario_default_token
    ):
        """GET /contatos/?skip=0&limit=5 deve retornar até 5 registros."""
        _criar_n_contatos(db_session, 10)
        resp = client.get(
            "/contatos/",
            params={"skip": 0, "limit": 5},
            headers=_auth_header(usuario_default_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5

    def test_total_nao_muda_com_limit(self, client, db_session, usuario_default_token):
        """total deve ser sempre o count real, independente do limit."""
        _criar_n_contatos(db_session, 10)
        resp = client.get(
            "/contatos/",
            params={"skip": 0, "limit": 5},
            headers=_auth_header(usuario_default_token),
        )
        assert resp.json()["total"] == 10

    def test_skip_pula_registros_corretamente(
        self, client, db_session, usuario_default_token
    ):
        """skip=5&limit=5 deve retornar registros 6-10 (segunda página de 5)."""
        _criar_n_contatos(db_session, 10)
        resp_p1 = client.get(
            "/contatos/",
            params={"skip": 0, "limit": 5},
            headers=_auth_header(usuario_default_token),
        )
        resp_p2 = client.get(
            "/contatos/",
            params={"skip": 5, "limit": 5},
            headers=_auth_header(usuario_default_token),
        )
        ids_p1 = {c["id"] for c in resp_p1.json()["items"]}
        ids_p2 = {c["id"] for c in resp_p2.json()["items"]}
        assert ids_p1.isdisjoint(ids_p2), "Páginas não devem ter registros em comum"

    def test_skip_maior_que_total_retorna_items_vazio(
        self, client, db_session, usuario_default_token
    ):
        """Quando skip >= total, items deve ser lista vazia mas total permanece correto."""
        _criar_n_contatos(db_session, 3)
        resp = client.get(
            "/contatos/",
            params={"skip": 100, "limit": 20},
            headers=_auth_header(usuario_default_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 3

    def test_limit_maior_que_total_retorna_todos(
        self, client, db_session, usuario_default_token
    ):
        """limit > total deve retornar todos os registros disponíveis."""
        _criar_n_contatos(db_session, 3)
        resp = client.get(
            "/contatos/",
            params={"skip": 0, "limit": 20},
            headers=_auth_header(usuario_default_token),
        )
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3


class TestLimiteMaximo:
    """Verifica o limite máximo de 200 registros (RN-F1-01)."""

    def test_limit_999_e_forcado_para_200(
        self, client, db_session, usuario_default_token
    ):
        """GET /contatos/?limit=999 não deve retornar mais de 200 registros."""
        _criar_n_contatos(db_session, 205)
        resp = client.get(
            "/contatos/",
            params={"limit": 999},
            headers=_auth_header(usuario_default_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 200, (
            f"Esperado <= 200 items, mas recebeu {len(data['items'])}"
        )

    def test_total_correto_mesmo_com_limit_forcado(
        self, client, db_session, usuario_default_token
    ):
        """Mesmo com limit=999 truncado para 200, total deve refletir o count real."""
        _criar_n_contatos(db_session, 205)
        resp = client.get(
            "/contatos/",
            params={"limit": 999},
            headers=_auth_header(usuario_default_token),
        )
        data = resp.json()
        assert data["total"] == 205

    def test_limit_200_retorna_ate_200(
        self, client, db_session, usuario_default_token
    ):
        """GET /contatos/?limit=200 deve funcionar normalmente (limite exato)."""
        _criar_n_contatos(db_session, 200)
        resp = client.get(
            "/contatos/",
            params={"limit": 200},
            headers=_auth_header(usuario_default_token),
        )
        data = resp.json()
        assert len(data["items"]) == 200
        assert data["total"] == 200


class TestPaginacaoComBusca:
    """Verifica que total reflete o filtro de busca, não o total geral."""

    def test_total_com_busca_reflete_apenas_matches(
        self, client, db_session, usuario_default_token
    ):
        """total deve contar apenas registros que atendem ao filtro."""
        _criar_n_contatos(db_session, 5)
        # Cria contatos fora do padrão "PagCorp" para garantir discriminação
        contato_service.criar_contato(
            db_session,
            ContatoCriar(nome="Zara Única", email="zara@outraempresa.com", empresa="OutraCo"),
        )
        resp = client.get(
            "/contatos/",
            params={"busca": "Zara"},
            headers=_auth_header(usuario_default_token),
        )
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_total_com_busca_sem_matches_e_zero(
        self, client, db_session, usuario_default_token
    ):
        """Busca sem correspondência deve retornar total=0 e items=[]."""
        _criar_n_contatos(db_session, 3)
        resp = client.get(
            "/contatos/",
            params={"busca": "TermoAbsolutamenteInexistente99XYZ"},
            headers=_auth_header(usuario_default_token),
        )
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_paginacao_com_busca_limita_items(
        self, client, db_session, usuario_default_token
    ):
        """Paginação deve funcionar junto com busca: limit=2 retorna apenas 2 items."""
        _criar_n_contatos(db_session, 10)  # todos têm empresa="PagCorp"
        resp = client.get(
            "/contatos/",
            params={"busca": "PagCorp", "skip": 0, "limit": 2},
            headers=_auth_header(usuario_default_token),
        )
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 10  # total de matches, não de items retornados


# ===========================================================================
# Testes unitários de serviço — contato_service.listar_contatos (tupla)
# ===========================================================================

class TestListarContatosServiceTupla:
    """
    Verifica que listar_contatos retorna (items, total) conforme nova assinatura.

    ATENÇÃO: test_services.py (existente) chama listar_contatos sem skip/limit
    e compara o resultado diretamente com uma lista (ex: assert resultado == []).
    Esse comportamento está INCOMPATÍVEL com a nova assinatura que retorna tuple.
    Os testes abaixo cobrem o comportamento CORRETO; os antigos devem ser corrigidos.
    """

    def test_retorna_tupla_com_dois_elementos(self, db_session):
        """listar_contatos deve retornar uma tupla (items, total)."""
        resultado = contato_service.listar_contatos(db_session)
        assert isinstance(resultado, tuple), (
            "listar_contatos deve retornar tuple (items, total)"
        )
        assert len(resultado) == 2

    def test_banco_vazio_retorna_lista_vazia_e_zero(self, db_session):
        """Com banco vazio: items=[] e total=0."""
        items, total = contato_service.listar_contatos(db_session)
        assert items == []
        assert total == 0

    def test_total_reflete_count_real_sem_paginacao(self, db_session):
        """total deve refletir o número total de registros no banco."""
        contato_service.criar_contato(db_session, ContatoCriar(nome="A", email="aa@example.com"))
        contato_service.criar_contato(db_session, ContatoCriar(nome="B", email="bb@example.com"))
        contato_service.criar_contato(db_session, ContatoCriar(nome="C", email="cc@example.com"))
        items, total = contato_service.listar_contatos(db_session)
        assert total == 3

    def test_limit_restringe_items_mas_nao_total(self, db_session):
        """limit=1 deve retornar 1 item mas total deve ser o count completo."""
        for i in range(5):
            contato_service.criar_contato(
                db_session, ContatoCriar(nome=f"N{i}", email=f"nn{i}@example.com")
            )
        items, total = contato_service.listar_contatos(db_session, limit=1)
        assert len(items) == 1
        assert total == 5

    def test_skip_desloca_pagina(self, db_session):
        """skip=2&limit=2 deve retornar itens 3 e 4 (0-based offset)."""
        emails = [f"email{i}@example.com" for i in range(5)]
        for i, email in enumerate(emails):
            contato_service.criar_contato(
                db_session, ContatoCriar(nome=f"Nome{i}", email=email)
            )
        items_p1, _ = contato_service.listar_contatos(db_session, skip=0, limit=2)
        items_p2, _ = contato_service.listar_contatos(db_session, skip=2, limit=2)
        ids_p1 = {c.id for c in items_p1}
        ids_p2 = {c.id for c in items_p2}
        assert ids_p1.isdisjoint(ids_p2)

    def test_busca_com_paginacao_total_e_filtrado(self, db_session):
        """total deve refletir o count filtrado, não o total geral do banco."""
        contato_service.criar_contato(
            db_session, ContatoCriar(nome="Alpha Corp", email="alpha@example.com", empresa="Alpha")
        )
        contato_service.criar_contato(
            db_session, ContatoCriar(nome="Beta Inc", email="beta@example.com", empresa="Beta")
        )
        contato_service.criar_contato(
            db_session, ContatoCriar(nome="Alpha Dois", email="alpha2@example.com", empresa="Alpha")
        )
        items, total = contato_service.listar_contatos(db_session, busca="Alpha")
        assert total == 2
        assert len(items) == 2

    def test_busca_vazia_retorna_tudo(self, db_session):
        """busca='' (falsy) deve retornar todos os registros."""
        contato_service.criar_contato(db_session, ContatoCriar(nome="X", email="xx@example.com"))
        contato_service.criar_contato(db_session, ContatoCriar(nome="Y", email="yy@example.com"))
        items, total = contato_service.listar_contatos(db_session, busca="")
        assert total == 2
        assert len(items) == 2

    def test_skip_alem_do_total_items_vazio_total_correto(self, db_session):
        """skip maior que total retorna items=[] mas total correto."""
        contato_service.criar_contato(db_session, ContatoCriar(nome="Z", email="zz@example.com"))
        items, total = contato_service.listar_contatos(db_session, skip=999, limit=20)
        assert items == []
        assert total == 1


# ===========================================================================
# Testes do schema ContatoListResponse
# ===========================================================================

class TestContatoListResponseSchema:
    """Verifica o schema Pydantic ContatoListResponse."""

    def test_schema_instancia_com_items_e_total(self):
        """ContatoListResponse deve ser instanciável com items=[] e total=0."""
        from app.schemas.contato import ContatoListResponse
        schema = ContatoListResponse(items=[], total=0)
        assert schema.items == []
        assert schema.total == 0

    def test_schema_total_deve_ser_inteiro(self):
        """total deve aceitar inteiro e rejeitar string."""
        from pydantic import ValidationError
        from app.schemas.contato import ContatoListResponse
        with pytest.raises((ValidationError, Exception)):
            ContatoListResponse(items=[], total="nao_e_numero")

    def test_schema_items_deve_ser_lista(self):
        """items deve ser lista; passar inteiro deve levantar ValidationError."""
        from pydantic import ValidationError
        from app.schemas.contato import ContatoListResponse
        with pytest.raises((ValidationError, Exception)):
            ContatoListResponse(items=42, total=0)

    def test_schema_total_negativo_e_aceito(self):
        """Pydantic não impede total negativo por padrão — registrar comportamento."""
        from app.schemas.contato import ContatoListResponse
        # Sem restrição ge=0 no schema, valores negativos são aceitos
        schema = ContatoListResponse(items=[], total=-1)
        assert schema.total == -1
