# Backend — API Manutenção de Contatos

API REST construída com FastAPI, SQLAlchemy e autenticação JWT.

---

## Pré-requisitos

- Python 3.11+
- pip

---

## Instalação e execução

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

A documentação interativa estará disponível em: http://localhost:8000/docs

---

## Executar testes

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

Meta de cobertura: >= 80%.

---

## Análise estática de segurança (Bandit)

O backend usa [Bandit](https://bandit.readthedocs.io/) para detectar padrões inseguros em código Python (uso de `eval`, `exec`, hashes fracos, SQL por concatenação, etc.).

**Executar localmente:**

```bash
bandit -c .bandit -r app/
```

**Falha do CI:** findings com severidade `MEDIUM` ou `HIGH` quebram o pipeline.

```bash
# Comando exato usado pelo CI (não falha em findings LOW)
bandit -c .bandit -r app/ --severity-level medium --confidence-level medium
```

Configuração em `backend/.bandit`. Diretórios excluídos: `tests/` e `alembic/versions/`.

---

## Variáveis de ambiente

O arquivo `.env` na raiz de `backend/` deve conter:

| Variável                     | Descrição                                             | Exemplo                        |
|------------------------------|-------------------------------------------------------|--------------------------------|
| `SECRET_KEY`                 | Chave secreta para assinar os tokens JWT (min. 32 chars) | `changeme_secret_key_256bits` |
| `ALGORITHM`                  | Algoritmo de assinatura JWT                           | `HS256`                        |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Tempo de expiração do token em minutos                | `60`                           |
| `DATABASE_URL`               | URL de conexão com o banco de dados SQLite            | `sqlite:///./contatos.db`      |

> Em produção, substitua `SECRET_KEY` por um valor aleatório e seguro (ex: `openssl rand -hex 32`).

---

## Endpoints principais

| Método | Rota             | Autenticação | Descrição                              |
|--------|------------------|--------------|----------------------------------------|
| POST   | `/auth/login`    | Não          | Autentica usuário e retorna token JWT  |
| GET    | `/auth/me`       | Bearer token | Retorna dados do usuário autenticado   |
| GET    | `/usuarios/`     | adm          | Lista todos os usuários                |
| POST   | `/usuarios/`     | Não          | Cadastra novo usuário (role: default)  |
| GET    | `/contatos/`     | Bearer token | Lista contatos (com pesquisa)          |
| POST   | `/contatos/`     | adm          | Cria novo contato                      |
| GET    | `/contatos/{id}` | Bearer token | Detalha um contato                     |
| PUT    | `/contatos/{id}` | adm          | Atualiza contato                       |
| DELETE | `/contatos/{id}` | adm          | Remove contato                         |

---

## Usuários e roles

- Ao se cadastrar, todo usuário recebe `role = "default"` (somente leitura).
- Para promover um usuário a administrador, acesse o banco SQLite diretamente:

```bash
sqlite3 contatos.db
UPDATE usuarios SET role = 'adm' WHERE email = 'seu@email.com';
.quit
```

- Apenas usuários com `role = "adm"` podem criar, editar e excluir contatos.
