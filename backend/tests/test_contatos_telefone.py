"""
Testes da validacao Pydantic do campo telefone — TASK-04 (Fase D / D.3 / RF-04).

Cobre:
- Schema ContatoCriar:
    * telefone=None aceito
    * telefone="" (vazio) aceito (normalizado para None)
    * telefone valido (XX) XXXXX-XXXX aceito
    * telefone invalido "123" rejeitado
    * telefone fixo (10 digitos) (XX) XXXX-XXXX rejeitado
    * telefone digits-only "11999999999" rejeitado
- Schema ContatoAtualizar (PUT): mesmas regras
- Schema ContatoPatch: mesmas regras + body vazio
- Integracao via API:
    * POST /contatos/ com telefone valido -> 201
    * POST /contatos/ com telefone invalido -> 422
    * POST /contatos/ sem telefone -> 201
    * PATCH /contatos/{id} com telefone fixo 10 digitos -> 422

Padrao: AAA (Arrange / Act / Assert).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.contato import ContatoAtualizar, ContatoCriar, ContatoPatch


# ===========================================================================
# Helpers
# ===========================================================================


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# ContatoCriar — testes de schema puro (sem HTTP)
# ===========================================================================


def test_contato_criar_telefone_none_aceito():
    """ContatoCriar com telefone=None deve ser aceito (campo opcional)."""
    dados = ContatoCriar(nome="Sem Tel", email="sem_tel@test.com", telefone=None)
    assert dados.telefone is None


def test_contato_criar_telefone_omitido_aceito():
    """ContatoCriar sem o campo telefone deve ser aceito (default = None)."""
    dados = ContatoCriar(nome="Sem Campo Tel", email="sem_campo_tel@test.com")
    assert dados.telefone is None


def test_contato_criar_telefone_vazio_normalizado_para_none():
    """ContatoCriar com telefone='' deve ser normalizado para None (TASK-04 docstring)."""
    dados = ContatoCriar(nome="Vazio", email="vazio@test.com", telefone="")
    assert dados.telefone is None


def test_contato_criar_telefone_so_espacos_normalizado_para_none():
    """ContatoCriar com telefone='   ' (espacos) deve virar None apos strip."""
    dados = ContatoCriar(nome="Esp", email="esp@test.com", telefone="   ")
    assert dados.telefone is None


def test_contato_criar_telefone_celular_valido_aceito():
    """ContatoCriar com telefone no formato celular (XX) XXXXX-XXXX -> aceito."""
    dados = ContatoCriar(
        nome="Cel Valido",
        email="cel_valido@test.com",
        telefone="(11) 91234-5678",
    )
    assert dados.telefone == "(11) 91234-5678"


def test_contato_criar_telefone_curto_rejeitado():
    """ContatoCriar com telefone='123' deve ser rejeitado com ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ContatoCriar(nome="Curto", email="curto@test.com", telefone="123")
    # A mensagem PT-BR documentada em _TELEFONE_ERRO deve aparecer no erro.
    assert "(XX) XXXXX-XXXX" in str(exc_info.value)


def test_contato_criar_telefone_fixo_10_digitos_rejeitado():
    """Telefone fixo (XX) XXXX-XXXX (10 digitos) NAO faz parte do contrato — rejeita."""
    # Decisao TASK-04: contrato unico aceita apenas celular (11 digitos
    # mascarado). Fixo deve falhar com 422 — alinhado ao Zod do frontend.
    with pytest.raises(ValidationError):
        ContatoCriar(
            nome="Fixo Rejeitado",
            email="fixo@test.com",
            telefone="(11) 1234-5678",
        )


def test_contato_criar_telefone_digits_only_rejeitado():
    """Telefone digits-only (sem mascara) deve ser rejeitado (TASK-04)."""
    with pytest.raises(ValidationError):
        ContatoCriar(
            nome="Digits Only",
            email="digits@test.com",
            telefone="11999999999",
        )


def test_contato_criar_telefone_sem_parenteses_rejeitado():
    """Telefone sem parenteses ao redor do DDD deve ser rejeitado."""
    with pytest.raises(ValidationError):
        ContatoCriar(
            nome="Sem Par",
            email="sempar@test.com",
            telefone="11 91234-5678",
        )


def test_contato_criar_telefone_com_letra_rejeitado():
    """Telefone com letra no meio dos digitos deve ser rejeitado."""
    with pytest.raises(ValidationError):
        ContatoCriar(
            nome="Letra",
            email="letra@test.com",
            telefone="(11) A1234-5678",
        )


# ===========================================================================
# ContatoAtualizar (PUT) — mesmas regras
# ===========================================================================


def test_contato_atualizar_telefone_none_aceito():
    """ContatoAtualizar com telefone=None deve ser aceito."""
    dados = ContatoAtualizar(telefone=None)
    assert dados.telefone is None


def test_contato_atualizar_telefone_valido():
    """ContatoAtualizar com telefone no formato celular -> aceito."""
    dados = ContatoAtualizar(telefone="(21) 98765-4321")
    assert dados.telefone == "(21) 98765-4321"


def test_contato_atualizar_telefone_invalido_rejeitado():
    """ContatoAtualizar com telefone fora do padrao -> ValidationError."""
    with pytest.raises(ValidationError):
        ContatoAtualizar(telefone="abc")


def test_contato_atualizar_telefone_fixo_rejeitado():
    """ContatoAtualizar tambem rejeita telefone fixo (10 digitos)."""
    with pytest.raises(ValidationError):
        ContatoAtualizar(telefone="(11) 1234-5678")


# ===========================================================================
# ContatoPatch — mesmas regras + body vazio
# ===========================================================================


def test_contato_patch_telefone_none_com_outro_campo_aceito():
    """ContatoPatch com telefone=None + outro campo -> aceito (campo opcional)."""
    dados = ContatoPatch(nome="Novo", telefone=None)
    assert dados.telefone is None
    assert dados.nome == "Novo"


def test_contato_patch_telefone_valido():
    """ContatoPatch com telefone celular valido -> aceito."""
    dados = ContatoPatch(telefone="(31) 99888-7766")
    assert dados.telefone == "(31) 99888-7766"


def test_contato_patch_telefone_vazio_normalizado_para_none_mas_so_isso_falha():
    """ContatoPatch com APENAS telefone='' deve falhar (todos None apos normalizacao)."""
    # telefone="" e normalizado para None; com todos os outros None,
    # o model_validator `ao_menos_um_campo` dispara ValidationError.
    with pytest.raises(ValidationError):
        ContatoPatch(telefone="")


def test_contato_patch_telefone_invalido_rejeitado():
    """ContatoPatch com telefone '123' -> ValidationError."""
    with pytest.raises(ValidationError):
        ContatoPatch(telefone="123")


# ===========================================================================
# Integracao via API — POST/PATCH cobertura HTTP
# ===========================================================================


def test_post_contato_com_telefone_valido_retorna_201(client, usuario_adm_token):
    """POST /contatos/ com telefone mascarado retorna 201."""
    payload = {
        "nome": "Tel Valido API",
        "email": "tel_valido_api@test.com",
        "telefone": "(11) 91234-5678",
    }
    resp = client.post(
        "/contatos/",
        json=payload,
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["telefone"] == "(11) 91234-5678"


def test_post_contato_sem_telefone_retorna_201(client, usuario_adm_token):
    """POST /contatos/ sem telefone (campo opcional) retorna 201."""
    payload = {
        "nome": "Sem Tel API",
        "email": "sem_tel_api@test.com",
    }
    resp = client.post(
        "/contatos/",
        json=payload,
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 201
    assert resp.json()["telefone"] is None


def test_post_contato_com_telefone_invalido_retorna_422(client, usuario_adm_token):
    """POST /contatos/ com telefone '123' deve retornar 422."""
    payload = {
        "nome": "Tel Invalido API",
        "email": "tel_invalido_api@test.com",
        "telefone": "123",
    }
    resp = client.post(
        "/contatos/",
        json=payload,
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 422


def test_post_contato_telefone_fixo_10_digitos_retorna_422(client, usuario_adm_token):
    """POST /contatos/ com telefone fixo (10 digitos) deve retornar 422."""
    payload = {
        "nome": "Fixo API",
        "email": "fixo_api@test.com",
        "telefone": "(11) 1234-5678",
    }
    resp = client.post(
        "/contatos/",
        json=payload,
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 422


def test_patch_contato_telefone_fixo_retorna_422(
    client, usuario_adm_token, contato_exemplo
):
    """PATCH /contatos/{id} com telefone fixo deve retornar 422."""
    resp = client.patch(
        f"/contatos/{contato_exemplo.id}",
        json={"telefone": "(11) 1234-5678"},
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 422


def test_patch_contato_telefone_valido_retorna_200(
    client, usuario_adm_token, contato_exemplo
):
    """PATCH /contatos/{id} com telefone celular mascarado retorna 200."""
    novo_tel = "(11) 95555-4444"
    resp = client.patch(
        f"/contatos/{contato_exemplo.id}",
        json={"telefone": novo_tel},
        headers=_auth_header(usuario_adm_token),
    )
    assert resp.status_code == 200
    assert resp.json()["telefone"] == novo_tel
