# Plano de Execução — Manutenção de Contatos de Clientes

## Stack Confirmada

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2, python-jose, bcrypt, Pytest + httpx
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Banco de dados**: SQLite (arquivo local)
- **Autenticação**: JWT (Bearer token)
- **Testes**: Pytest + pytest-cov (cobertura >= 80%)
- **Portas**: frontend :3000 | backend :8000

---

## Estrutura de Diretórios

```
projeto/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                  # redireciona para /login ou /contatos
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── cadastro/
│   │   │   │   └── page.tsx
│   │   │   └── contatos/
│   │   │       ├── page.tsx              # listagem + pesquisa
│   │   │       ├── [id]/
│   │   │       │   └── page.tsx          # detalhes do contato
│   │   │       └── novo/
│   │   │           └── page.tsx          # formulário de inclusão (adm)
│   │   ├── components/
│   │   │   ├── ui/                       # shadcn/ui (gerado automaticamente)
│   │   │   ├── ContatoTable.tsx
│   │   │   ├── ContatoForm.tsx
│   │   │   ├── ContatoDetalhe.tsx
│   │   │   ├── ConfirmacaoModal.tsx
│   │   │   ├── Navbar.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── services/
│   │   │   ├── api.ts                    # instância axios + interceptors JWT
│   │   │   ├── auth.service.ts
│   │   │   └── contatos.service.ts
│   │   ├── hooks/
│   │   │   └── useAuth.ts
│   │   ├── types/
│   │   │   └── index.ts                  # interfaces TypeScript
│   │   └── lib/
│   │       └── utils.ts
│   ├── .env.local
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
└── backend/
    ├── app/
    │   ├── main.py
    │   ├── database.py
    │   ├── config.py                     # variáveis de ambiente (pydantic-settings)
    │   ├── dependencies.py               # get_db, get_current_user, require_adm
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── usuario.py
    │   │   └── contato.py
    │   ├── schemas/
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── usuario.py
    │   │   └── contato.py
    │   ├── routers/
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── usuarios.py
    │   │   └── contatos.py
    │   └── services/
    │       ├── __init__.py
    │       ├── auth_service.py
    │       ├── usuario_service.py
    │       └── contato_service.py
    ├── tests/
    │   ├── conftest.py
    │   ├── test_auth.py
    │   ├── test_usuarios.py
    │   └── test_contatos.py
    ├── alembic/
    │   ├── env.py
    │   └── versions/
    │       └── 0001_initial.py
    ├── alembic.ini
    ├── .env
    └── requirements.txt
```

---

## Fases

### Fase 1 — Fundacao

> Setup inicial dos dois projetos (backend e frontend). Independentes entre si — podem rodar em paralelo.

---

- **TASK-01** [paralelo: com TASK-02] — Setup do projeto Backend

  - **Arquivos a criar/modificar**:
    - `backend/requirements.txt`
    - `backend/.env`
    - `backend/alembic.ini`
    - `backend/alembic/env.py`
    - `backend/alembic/versions/0001_initial.py`
    - `backend/app/__init__.py`
    - `backend/app/config.py`
    - `backend/app/database.py`
    - `backend/app/main.py`
    - `backend/app/models/__init__.py`
    - `backend/app/models/usuario.py`
    - `backend/app/models/contato.py`
    - `backend/app/schemas/__init__.py`
    - `backend/app/routers/__init__.py`
    - `backend/app/services/__init__.py`
    - `backend/tests/conftest.py`

  - **Stack**: Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2, python-jose, bcrypt, Pytest

  - **Dependencias de tasks**: nenhuma

  - **Descricao detalhada**:

    1. Criar `backend/requirements.txt` com as dependencias:
       ```
       fastapi>=0.111
       uvicorn[standard]
       sqlalchemy>=2.0
       alembic
       pydantic>=2.0
       pydantic-settings
       python-jose[cryptography]
       bcrypt
       pytest
       pytest-cov
       httpx
       python-multipart
       ```

    2. Criar `backend/.env` com variaveis:
       ```
       SECRET_KEY=changeme_secret_key_256bits
       ALGORITHM=HS256
       ACCESS_TOKEN_EXPIRE_MINUTES=60
       DATABASE_URL=sqlite:///./contatos.db
       ```

    3. Criar `backend/app/config.py` usando `pydantic-settings` para carregar as variaveis de ambiente acima como atributos tipados.

    4. Criar `backend/app/database.py` com a engine SQLAlchemy apontando para `DATABASE_URL`, a `SessionLocal` e a base declarativa `Base`.

    5. Criar `backend/app/models/usuario.py` com o modelo `Usuario`:
       - Campos: `id` (PK, int, autoincrement), `nome` (str, not null), `email` (str, unique, not null), `senha_hash` (str, not null), `role` (str, not null, default="default"), `criado_em` (datetime, default=now)

    6. Criar `backend/app/models/contato.py` com o modelo `Contato`:
       - Campos: `id` (PK, int, autoincrement), `nome` (str, not null), `email` (str, unique, not null), `telefone` (str, nullable), `empresa` (str, nullable), `observacoes` (text, nullable), `criado_em` (datetime, default=now), `atualizado_em` (datetime, default=now, onupdate=now)

    7. Configurar Alembic: `alembic.ini` aponta para `backend/`, `alembic/env.py` importa `Base` e os modelos para que o autogenerate funcione. Criar migracao inicial `0001_initial.py` que cria as tabelas `usuarios` e `contatos`.

    8. Criar `backend/app/main.py` instanciando o `FastAPI`, configurando CORS (permitir origem `http://localhost:3000`), e registrando os routers (vazios por ora, apenas importados).

    9. Criar `backend/tests/conftest.py` com fixture de banco em memória (`sqlite:///:memory:`), fixture de `TestClient`, e fixture de usuario adm e usuario default pré-criados para os testes.

  - **Criterio de pronto**:
    - `cd backend && pip install -r requirements.txt` sem erros
    - `alembic upgrade head` cria o arquivo `contatos.db` com as tabelas `usuarios` e `contatos`
    - `uvicorn app.main:app --reload` sobe sem erros e `/docs` responde 200
    - `pytest tests/` executa sem erros de importacao (mesmo sem testes reais ainda)

---

- **TASK-02** [paralelo: com TASK-01] — Setup do projeto Frontend

  - **Arquivos a criar/modificar**:
    - `frontend/package.json`
    - `frontend/tsconfig.json`
    - `frontend/next.config.ts`
    - `frontend/tailwind.config.ts`
    - `frontend/.env.local`
    - `frontend/src/app/layout.tsx`
    - `frontend/src/app/page.tsx`
    - `frontend/src/types/index.ts`
    - `frontend/src/lib/utils.ts`
    - `frontend/src/services/api.ts`

  - **Stack**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, axios

  - **Dependencias de tasks**: nenhuma

  - **Descricao detalhada**:

    1. Inicializar projeto Next.js 14 com App Router e TypeScript. Instalar dependencias adicionais: `axios`, `shadcn/ui` (via CLI), `lucide-react`.

    2. Criar `frontend/.env.local`:
       ```
       NEXT_PUBLIC_API_URL=http://localhost:8000
       ```

    3. Configurar Tailwind CSS (`tailwind.config.ts`) com tema claro (light), cores neutras e paths corretos (`./src/**/*.{ts,tsx}`).

    4. Criar `frontend/src/types/index.ts` com as interfaces TypeScript:
       ```typescript
       export interface Usuario {
         id: number;
         nome: string;
         email: string;
         role: 'default' | 'adm';
       }

       export interface Contato {
         id: number;
         nome: string;
         email: string;
         telefone?: string;
         empresa?: string;
         observacoes?: string;
         criado_em: string;
         atualizado_em: string;
       }

       export interface ContatoForm {
         nome: string;
         email: string;
         telefone?: string;
         empresa?: string;
         observacoes?: string;
       }

       export interface LoginForm {
         email: string;
         senha: string;
       }

       export interface CadastroForm {
         nome: string;
         email: string;
         senha: string;
       }

       export interface TokenResponse {
         access_token: string;
         token_type: string;
       }

       export interface AuthContextType {
         usuario: Usuario | null;
         token: string | null;
         login: (token: string, usuario: Usuario) => void;
         logout: () => void;
         isAdm: boolean;
       }
       ```

    5. Criar `frontend/src/lib/utils.ts` com helper `cn()` do shadcn/ui (merge de classnames com `clsx` + `tailwind-merge`).

    6. Criar `frontend/src/services/api.ts` com instancia Axios apontando para `NEXT_PUBLIC_API_URL`. Adicionar interceptor de request que le o token do `localStorage` (chave `token`) e injeta o header `Authorization: Bearer <token>`. Adicionar interceptor de response que, ao receber 401, limpa o localStorage e redireciona para `/login`.

    7. Criar `frontend/src/app/layout.tsx` com `<html lang="pt-BR">`, importacao do Tailwind e estrutura basica. Incluir `<Navbar />` (componente sera criado na TASK-07, deixar importacao comentada por ora).

    8. Criar `frontend/src/app/page.tsx` que redireciona para `/login` por padrao (usando `redirect()` do Next.js ou `useEffect`).

  - **Criterio de pronto**:
    - `cd frontend && npm install` sem erros
    - `npm run dev` sobe em `http://localhost:3000` sem erros de compilacao
    - Acessar `/` redireciona para `/login`
    - `npx tsc --noEmit` sem erros de tipagem

---

### Fase 2 — Backend Core

> Implementacao da logica de negocio, endpoints REST e testes. Tasks podem ser parcialmente paralelizadas conforme indicado.

---

- **TASK-03** [paralelo: com TASK-04] — Backend: Autenticacao e usuarios (schemas + service + router)

  - **Arquivos a criar/modificar**:
    - `backend/app/schemas/auth.py`
    - `backend/app/schemas/usuario.py`
    - `backend/app/services/auth_service.py`
    - `backend/app/services/usuario_service.py`
    - `backend/app/routers/auth.py`
    - `backend/app/routers/usuarios.py`
    - `backend/app/dependencies.py`
    - `backend/app/main.py` (modificar: registrar routers)

  - **Stack**: FastAPI, SQLAlchemy, Pydantic v2, python-jose, bcrypt

  - **Dependencias de tasks**: TASK-01

  - **Descricao detalhada**:

    1. **`backend/app/schemas/usuario.py`** — Schemas Pydantic:
       - `UsuarioCriar`: `nome` (str), `email` (EmailStr), `senha` (str, min_length=6)
       - `UsuarioResposta`: `id`, `nome`, `email`, `role` — `model_config = ConfigDict(from_attributes=True)`

    2. **`backend/app/schemas/auth.py`** — Schemas Pydantic:
       - `LoginRequest`: `email` (EmailStr), `senha` (str)
       - `TokenResponse`: `access_token` (str), `token_type` (str, default="bearer")
       - `TokenData`: `email` (str | None)

    3. **`backend/app/services/auth_service.py`** — Funcoes:
       - `hash_senha(senha: str) -> str` usando `bcrypt`
       - `verificar_senha(senha: str, hash: str) -> bool`
       - `criar_token(data: dict, expires_delta: timedelta | None) -> str` usando `python-jose`
       - `decodificar_token(token: str) -> TokenData` — levanta `HTTPException(401)` se invalido ou expirado

    4. **`backend/app/services/usuario_service.py`** — Funcoes:
       - `criar_usuario(db, dados: UsuarioCriar) -> Usuario` — verifica e-mail duplicado (levanta 400), faz hash da senha, persiste com `role="default"`
       - `buscar_por_email(db, email: str) -> Usuario | None`
       - `autenticar_usuario(db, email: str, senha: str) -> Usuario | None`

    5. **`backend/app/dependencies.py`** — Dependencias FastAPI:
       - `get_db()`: gerador de sessao SQLAlchemy
       - `get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)) -> Usuario`: decodifica token, busca usuario, levanta 401 se nao encontrado
       - `require_adm(usuario = Depends(get_current_user)) -> Usuario`: levanta 403 se `usuario.role != "adm"`

    6. **`backend/app/routers/auth.py`** — Endpoints:
       - `POST /auth/login` — recebe `LoginRequest`, autentica, retorna `TokenResponse`
       - `GET /auth/me` — requer token, retorna `UsuarioResposta` do usuario logado

    7. **`backend/app/routers/usuarios.py`** — Endpoints:
       - `POST /usuarios/` — publico (sem autenticacao), cria novo usuario, retorna `UsuarioResposta` com status 201

    8. **`backend/app/main.py`** — Registrar os dois routers com prefixos `/auth` e `/usuarios`.

  - **Criterio de pronto**:
    - `POST /usuarios/` cria usuario com role "default" e retorna 201
    - `POST /auth/login` retorna token JWT valido
    - `GET /auth/me` retorna dados do usuario com token valido, retorna 401 sem token
    - `POST /usuarios/` com e-mail duplicado retorna 400 com mensagem clara

---

- **TASK-04** [paralelo: com TASK-03] — Backend: CRUD de Contatos (schemas + service + router)

  - **Arquivos a criar/modificar**:
    - `backend/app/schemas/contato.py`
    - `backend/app/services/contato_service.py`
    - `backend/app/routers/contatos.py`
    - `backend/app/main.py` (modificar: registrar router de contatos)

  - **Stack**: FastAPI, SQLAlchemy, Pydantic v2

  - **Dependencias de tasks**: TASK-01

  - **Descricao detalhada**:

    1. **`backend/app/schemas/contato.py`** — Schemas Pydantic:
       - `ContatoCriar`: `nome` (str, not empty), `email` (EmailStr), `telefone` (str | None), `empresa` (str | None), `observacoes` (str | None)
       - `ContatoAtualizar`: todos os campos opcionais (PATCH semantics)
       - `ContatoResposta`: todos os campos + `id`, `criado_em`, `atualizado_em` — `from_attributes=True`

    2. **`backend/app/services/contato_service.py`** — Funcoes:
       - `listar_contatos(db, busca: str | None = None) -> list[Contato]`: retorna ate 200 registros. Se `busca` fornecido, filtra por `LIKE` case-insensitive em `nome`, `email` e `empresa`.
       - `buscar_contato(db, id: int) -> Contato`: levanta 404 se nao encontrado
       - `criar_contato(db, dados: ContatoCriar) -> Contato`: verifica e-mail duplicado (400), persiste
       - `atualizar_contato(db, id: int, dados: ContatoAtualizar) -> Contato`: busca pelo id (404), atualiza campos nao-nulos, persiste
       - `excluir_contato(db, id: int) -> None`: busca pelo id (404), deleta

    3. **`backend/app/routers/contatos.py`** — Endpoints (todos requerem autenticacao via `get_current_user`):
       - `GET /contatos/` — parametro query `busca: str | None`. Acessivel por qualquer usuario autenticado. Retorna `list[ContatoResposta]`
       - `GET /contatos/{id}` — retorna `ContatoResposta` ou 404. Qualquer usuario autenticado.
       - `POST /contatos/` — requer `require_adm`. Retorna `ContatoResposta` com status 201.
       - `PUT /contatos/{id}` — requer `require_adm`. Retorna `ContatoResposta`.
       - `DELETE /contatos/{id}` — requer `require_adm`. Retorna 204 No Content.

    4. **`backend/app/main.py`** — Registrar router de contatos com prefixo `/contatos`.

  - **Criterio de pronto**:
    - `GET /contatos/` sem token retorna 401
    - `POST /contatos/` com token de usuario `default` retorna 403
    - `POST /contatos/` com token adm cria contato e retorna 201
    - `GET /contatos/?busca=joao` filtra corretamente (case-insensitive)
    - `DELETE /contatos/{id}` com id inexistente retorna 404

---

- **TASK-05** [paralelo: nao] — Backend: Testes automatizados

  - **Arquivos a criar/modificar**:
    - `backend/tests/conftest.py` (modificar: adicionar fixtures completas)
    - `backend/tests/test_auth.py`
    - `backend/tests/test_usuarios.py`
    - `backend/tests/test_contatos.py`

  - **Stack**: Pytest, httpx (TestClient do FastAPI), pytest-cov

  - **Dependencias de tasks**: TASK-03, TASK-04

  - **Descricao detalhada**:

    1. **`backend/tests/conftest.py`** — Completar fixtures:
       - `db_session`: banco SQLite em memoria, cria todas as tabelas, yield session, drop all
       - `client`: `TestClient` do FastAPI usando `db_session` sobrescrita via `app.dependency_overrides`
       - `usuario_default_token`: cria usuario com role "default" via service, retorna JWT
       - `usuario_adm_token`: cria usuario, altera role para "adm" diretamente no banco, retorna JWT
       - `contato_exemplo`: cria um contato de exemplo no banco

    2. **`backend/tests/test_auth.py`**:
       - `test_login_sucesso`: POST /auth/login com credenciais validas retorna 200 e token
       - `test_login_senha_errada`: retorna 401
       - `test_login_usuario_inexistente`: retorna 401
       - `test_me_com_token`: GET /auth/me retorna dados do usuario
       - `test_me_sem_token`: retorna 401
       - `test_me_token_invalido`: retorna 401

    3. **`backend/tests/test_usuarios.py`**:
       - `test_criar_usuario`: POST /usuarios/ cria com role "default"
       - `test_criar_usuario_email_duplicado`: retorna 400
       - `test_criar_usuario_senha_curta`: retorna 422 (validacao Pydantic)

    4. **`backend/tests/test_contatos.py`**:
       - `test_listar_contatos_autenticado`: GET /contatos/ retorna lista
       - `test_listar_contatos_sem_token`: retorna 401
       - `test_busca_por_nome`: GET /contatos/?busca=... filtra corretamente
       - `test_busca_case_insensitive`: busca com letras maiusculas retorna resultado
       - `test_detalhe_contato`: GET /contatos/{id} retorna contato
       - `test_detalhe_contato_inexistente`: retorna 404
       - `test_criar_contato_adm`: POST /contatos/ com adm retorna 201
       - `test_criar_contato_default`: POST /contatos/ com default retorna 403
       - `test_criar_contato_email_duplicado`: retorna 400
       - `test_atualizar_contato_adm`: PUT /contatos/{id} altera e retorna dados atualizados
       - `test_atualizar_contato_default`: retorna 403
       - `test_excluir_contato_adm`: DELETE /contatos/{id} retorna 204
       - `test_excluir_contato_default`: retorna 403
       - `test_excluir_contato_inexistente`: retorna 404

  - **Criterio de pronto**:
    - `pytest tests/ --cov=app --cov-report=term-missing` com cobertura >= 80%
    - Todos os testes passam (verde)
    - Nenhum teste depende de ordem de execucao

---

### Fase 3 — Frontend Core

> Implementacao de paginas, componentes e servicos do frontend. TASK-06 e TASK-07 sao independentes entre si.

---

- **TASK-06** [paralelo: com TASK-07] — Frontend: Autenticacao (login, cadastro, contexto)

  - **Arquivos a criar/modificar**:
    - `frontend/src/hooks/useAuth.ts`
    - `frontend/src/components/ProtectedRoute.tsx`
    - `frontend/src/app/login/page.tsx`
    - `frontend/src/app/cadastro/page.tsx`

  - **Stack**: Next.js 14, TypeScript, React Context API, axios, shadcn/ui, Tailwind CSS

  - **Dependencias de tasks**: TASK-02

  - **Descricao detalhada**:

    1. **`frontend/src/hooks/useAuth.ts`** — Hook e Context de autenticacao:
       - Criar `AuthContext` com `createContext` usando `AuthContextType` (definido em `types/index.ts`)
       - `AuthProvider` component: gerencia estado `usuario` e `token`. No mount, le `localStorage` (`token` e `usuario`) para restaurar sessao. Expoe funcoes `login(token, usuario)` (salva no localStorage) e `logout()` (limpa localStorage e redireciona para `/login`). Calcula `isAdm = usuario?.role === 'adm'`.
       - Exportar `useAuth()` hook que consome o context
       - Adicionar `AuthProvider` no `layout.tsx`

    2. **`frontend/src/components/ProtectedRoute.tsx`** — Componente wrapper:
       - Verifica se ha token no localStorage. Se nao, redireciona para `/login`.
       - Enquanto verifica (montagem), exibe spinner de carregamento.
       - Se autenticado, renderiza `children`.

    3. **`frontend/src/app/login/page.tsx`** — Pagina de login:
       - Formulario com campos: `E-mail` e `Senha` (labels e placeholders em PT-BR)
       - Validacao client-side: campos obrigatorios
       - Ao submeter: chama `POST /auth/login` via `auth.service.ts` (criar na mesma task)
       - Em caso de sucesso: chama `login(token, usuario)` do context e redireciona para `/contatos`
       - Em caso de erro: exibe mensagem "E-mail ou senha invalidos" em PT-BR
       - Link para `/cadastro`
       - Estado de loading no botao durante requisicao

    4. **`frontend/src/app/cadastro/page.tsx`** — Pagina de cadastro:
       - Formulario com campos: `Nome`, `E-mail`, `Senha` (labels em PT-BR)
       - Validacao client-side: nome e e-mail obrigatorios, senha >= 6 caracteres
       - Ao submeter: chama `POST /usuarios/` via `auth.service.ts`
       - Sucesso: exibe mensagem "Conta criada com sucesso! Faca login." e redireciona para `/login`
       - Erro de e-mail duplicado: exibe mensagem clara em PT-BR
       - Link para `/login`

    5. **`frontend/src/services/auth.service.ts`** (criar junto nesta task):
       - `login(email, senha) -> TokenResponse`
       - `cadastrar(nome, email, senha) -> UsuarioResposta`
       - `getMe() -> Usuario` — chama `GET /auth/me` com token

  - **Criterio de pronto**:
    - Login com credenciais validas redireciona para `/contatos`
    - Login com credenciais invalidas exibe mensagem de erro em PT-BR
    - Cadastro cria usuario e redireciona para `/login`
    - Acessar `/contatos` sem estar logado redireciona para `/login`
    - Token persiste no `localStorage` apos login

---

- **TASK-07** [paralelo: com TASK-06] — Frontend: Componentes de UI compartilhados e Navbar

  - **Arquivos a criar/modificar**:
    - `frontend/src/components/Navbar.tsx`
    - `frontend/src/components/ContatoTable.tsx`
    - `frontend/src/components/ConfirmacaoModal.tsx`
    - `frontend/src/components/ContatoForm.tsx`
    - `frontend/src/components/ContatoDetalhe.tsx`
    - `frontend/src/app/layout.tsx` (modificar: adicionar Navbar e AuthProvider)

  - **Stack**: Next.js 14, TypeScript, shadcn/ui, Tailwind CSS

  - **Dependencias de tasks**: TASK-02

  - **Descricao detalhada**:

    1. **`frontend/src/components/Navbar.tsx`**:
       - Exibe nome da aplicacao ("Contatos de Clientes") a esquerda
       - Se usuario logado: exibe "Ola, {nome}" e botao "Sair" a direita
       - Botao "Sair" chama `logout()` do `useAuth`
       - Responsivo (mobile-friendly)
       - Tema claro com Tailwind

    2. **`frontend/src/components/ContatoTable.tsx`**:
       - Props: `contatos: Contato[]`, `isAdm: boolean`, `onEditar: (id) => void`, `onExcluir: (id) => void`, `loading: boolean`
       - Renderiza tabela com colunas: Nome, E-mail, Telefone, Empresa, Acoes
       - Coluna "Acoes" exibe botoes "Editar" e "Excluir" apenas se `isAdm === true`
       - Se `loading`, exibe skeleton ou spinner
       - Se lista vazia, exibe "Nenhum contato encontrado." em PT-BR
       - Cada linha e clicavel para ver detalhes (navega para `/contatos/{id}`)

    3. **`frontend/src/components/ConfirmacaoModal.tsx`**:
       - Props: `aberto: boolean`, `titulo: string`, `mensagem: string`, `onConfirmar: () => void`, `onCancelar: () => void`, `loading?: boolean`
       - Dialog/Modal (usar shadcn/ui `Dialog`)
       - Botoes "Confirmar" (vermelho) e "Cancelar"
       - Textos em PT-BR

    4. **`frontend/src/components/ContatoForm.tsx`**:
       - Props: `valorInicial?: ContatoForm`, `onSubmit: (dados: ContatoForm) => void`, `loading: boolean`, `erro?: string`
       - Campos: Nome Completo (obrigatorio), E-mail (obrigatorio), Telefone, Empresa, Observacoes (textarea)
       - Validacao client-side dos campos obrigatorios
       - Labels e mensagens de erro em PT-BR
       - Botao de submit com estado de loading

    5. **`frontend/src/components/ContatoDetalhe.tsx`**:
       - Props: `contato: Contato`, `isAdm: boolean`, `onEditar: () => void`, `onExcluir: () => void`
       - Exibe todos os campos do contato em layout de cartao/card
       - Botoes "Editar" e "Excluir" visiveis apenas se `isAdm`
       - Labels em PT-BR

    6. **`frontend/src/app/layout.tsx`** — Atualizar para incluir:
       - `AuthProvider` envolvendo o conteudo
       - `<Navbar />` acima do `{children}`

  - **Criterio de pronto**:
    - `ContatoTable` renderiza corretamente com e sem botoes de adm
    - `ConfirmacaoModal` abre e fecha corretamente com os dois botoes funcionando
    - `ContatoForm` valida campos obrigatorios e exibe erros em PT-BR
    - `Navbar` exibe nome do usuario e botao de logout quando autenticado
    - `npx tsc --noEmit` sem erros de tipagem nos componentes

---

### Fase 4 — Frontend Paginas e Integracao

> Paginas de listagem, detalhe e formularios conectados ao backend.

---

- **TASK-08** [paralelo: com TASK-09] — Frontend: Pagina de Listagem e Pesquisa de Contatos

  - **Arquivos a criar/modificar**:
    - `frontend/src/app/contatos/page.tsx`
    - `frontend/src/services/contatos.service.ts`

  - **Stack**: Next.js 14, TypeScript, React hooks, axios

  - **Dependencias de tasks**: TASK-06, TASK-07

  - **Descricao detalhada**:

    1. **`frontend/src/services/contatos.service.ts`** (criar junto):
       - `listarContatos(busca?: string) -> Promise<Contato[]>`: GET /contatos/?busca=...
       - `buscarContato(id: number) -> Promise<Contato>`: GET /contatos/{id}
       - `criarContato(dados: ContatoForm) -> Promise<Contato>`: POST /contatos/
       - `atualizarContato(id: number, dados: ContatoForm) -> Promise<Contato>`: PUT /contatos/{id}
       - `excluirContato(id: number) -> Promise<void>`: DELETE /contatos/{id}

    2. **`frontend/src/app/contatos/page.tsx`** — Pagina protegida (usar `ProtectedRoute`):
       - Campo de pesquisa (input) com placeholder "Pesquisar por nome, e-mail ou empresa..."
       - Debounce de 400ms na pesquisa para evitar excesso de requisicoes
       - Ao digitar, chama `listarContatos(busca)` e atualiza a tabela
       - Renderiza `<ContatoTable>` com os resultados
       - Se `isAdm`: exibe botao "Novo Contato" que navega para `/contatos/novo`
       - Ao clicar "Editar": navega para `/contatos/{id}/editar` (pagina a ser criada na TASK-09)
       - Ao clicar "Excluir": abre `<ConfirmacaoModal>`. Confirmado: chama `excluirContato(id)`, remove da lista local, exibe toast de sucesso.
       - Estado de loading durante carregamento inicial e durante exclusao
       - Mensagem de erro em PT-BR se a API retornar erro

  - **Criterio de pronto**:
    - Listagem carrega contatos do backend ao acessar `/contatos`
    - Campo de busca filtra contatos em tempo real (com debounce)
    - "Nenhum contato encontrado." exibido quando lista vazia
    - Botao "Novo Contato" visivel apenas para adm
    - Botoes "Editar" e "Excluir" visiveis apenas para adm
    - Modal de confirmacao aparece antes da exclusao
    - Exclusao remove o contato da lista sem recarregar a pagina

---

- **TASK-09** [paralelo: com TASK-08] — Frontend: Paginas de Detalhe, Inclusao e Edicao de Contato

  - **Arquivos a criar/modificar**:
    - `frontend/src/app/contatos/[id]/page.tsx`
    - `frontend/src/app/contatos/novo/page.tsx`
    - `frontend/src/app/contatos/[id]/editar/page.tsx` (criar estrutura de pasta)

  - **Stack**: Next.js 14, TypeScript, React hooks, axios

  - **Dependencias de tasks**: TASK-06, TASK-07

  - **Descricao detalhada**:

    1. **`frontend/src/app/contatos/[id]/page.tsx`** — Pagina de detalhe:
       - Pagina protegida (`ProtectedRoute`)
       - Ao montar: chama `buscarContato(id)` e exibe `<ContatoDetalhe>`
       - Estado de loading durante carregamento
       - Se 404: exibe "Contato nao encontrado." com link para voltar
       - Botoes "Editar" e "Excluir" condicionais ao `isAdm` (vem do `useAuth`)
       - "Excluir" abre `<ConfirmacaoModal>`, ao confirmar chama `excluirContato(id)` e redireciona para `/contatos`
       - Botao "Voltar" navega para `/contatos`

    2. **`frontend/src/app/contatos/novo/page.tsx`** — Formulario de inclusao:
       - Pagina protegida. Se `!isAdm`, redireciona para `/contatos` com mensagem de acesso negado.
       - Renderiza `<ContatoForm>` sem valores iniciais
       - Ao submeter: chama `criarContato(dados)`
       - Sucesso: exibe toast "Contato criado com sucesso!" e redireciona para `/contatos`
       - Erro de e-mail duplicado: exibe mensagem clara em PT-BR no formulario
       - Outros erros: exibe mensagem generica em PT-BR
       - Botao "Cancelar" navega para `/contatos`

    3. **`frontend/src/app/contatos/[id]/editar/page.tsx`** — Formulario de edicao:
       - Pagina protegida. Se `!isAdm`, redireciona para `/contatos`.
       - Ao montar: chama `buscarContato(id)` para pre-preencher o formulario
       - Renderiza `<ContatoForm valorInicial={contato}>`
       - Ao submeter: chama `atualizarContato(id, dados)`
       - Sucesso: exibe toast "Contato atualizado com sucesso!" e redireciona para `/contatos/{id}`
       - Erro: exibe mensagem em PT-BR
       - Botao "Cancelar" navega para `/contatos/{id}`

  - **Criterio de pronto**:
    - `/contatos/{id}` exibe todos os campos do contato
    - `/contatos/novo` cria contato e redireciona apos sucesso (apenas adm)
    - `/contatos/{id}/editar` pre-preenche formulario e salva alteracoes (apenas adm)
    - Usuario `default` que acessa `/contatos/novo` e redirecionado
    - Mensagens de sucesso e erro em PT-BR

---

### Fase 5 — Refinamentos e Verificacao Final

---

- **TASK-10** [paralelo: nao] — Verificacao de controle de acesso, CORS e variaveis de ambiente

  - **Arquivos a criar/modificar**:
    - `backend/app/main.py` (verificar CORS)
    - `backend/.env` (verificar todas as variaveis)
    - `frontend/.env.local` (verificar todas as variaveis)
    - `backend/README.md` (instrucoes de execucao — apenas se nao existir)
    - `frontend/README.md` (instrucoes de execucao — apenas se nao existir)

  - **Stack**: FastAPI, Next.js

  - **Dependencias de tasks**: TASK-05, TASK-08, TASK-09

  - **Descricao detalhada**:

    1. Verificar que o CORS do backend aceita apenas `http://localhost:3000` (nao `*`).

    2. Verificar que todas as rotas de escrita (`POST`, `PUT`, `DELETE`) em `/contatos/` retornam 403 quando chamadas com token de usuario `default`.

    3. Verificar que a interface nao exibe botoes de escrita para usuarios `default` (teste manual com dois usuarios de roles diferentes).

    4. Verificar que token expirado (simular com tempo curto em `.env`) redireciona para `/login`.

    5. Verificar que `SECRET_KEY` e `DATABASE_URL` sao lidas corretamente de variaveis de ambiente e nao estao hardcoded no codigo.

    6. Executar `pytest tests/ --cov=app --cov-report=term-missing` e confirmar cobertura >= 80%.

    7. Documentar comandos de execucao (inicio do backend com `uvicorn`, inicio do frontend com `npm run dev`, migracao com `alembic upgrade head`) em arquivos README de cada subprojeto.

  - **Criterio de pronto**:
    - Fluxo completo funciona: cadastro -> login -> listagem -> CRUD (adm) -> logout
    - Usuario `default` nao consegue criar/editar/excluir via API nem via interface
    - Cobertura de testes >= 80%
    - Nenhuma chave secreta hardcoded no codigo-fonte

---

## Resumo de Paralelismo

| Task    | Fase | Pode rodar em paralelo com |
|---------|------|---------------------------|
| TASK-01 | 1    | TASK-02                   |
| TASK-02 | 1    | TASK-01                   |
| TASK-03 | 2    | TASK-04                   |
| TASK-04 | 2    | TASK-03                   |
| TASK-05 | 2    | nenhuma (depende de 03+04)|
| TASK-06 | 3    | TASK-07                   |
| TASK-07 | 3    | TASK-06                   |
| TASK-08 | 4    | TASK-09                   |
| TASK-09 | 4    | TASK-08                   |
| TASK-10 | 5    | nenhuma (verificacao final)|

## Requisitos Cobertos por Task

| Requisito | Tasks |
|-----------|-------|
| RF-01 (tela de login) | TASK-06 |
| RF-02 (cadastro de usuario) | TASK-03, TASK-06 |
| RF-03 (JWT + redirect) | TASK-03, TASK-06 |
| RF-04 (validar token, 401) | TASK-03, TASK-06 |
| RF-05 (nome + logout na UI) | TASK-07 |
| RF-06 (listagem de contatos) | TASK-04, TASK-08 |
| RF-07 (pesquisa textual) | TASK-04, TASK-08 |
| RF-08 (detalhe do contato) | TASK-04, TASK-09 |
| RF-09 (incluir contato - adm) | TASK-04, TASK-09 |
| RF-10 (alterar contato - adm) | TASK-04, TASK-09 |
| RF-11 (excluir com confirmacao) | TASK-04, TASK-07, TASK-08 |
| RF-12 (ocultar acoes para default) | TASK-07, TASK-08, TASK-09 |
| RNF-02 (bcrypt + JWT secreto) | TASK-03 |
| RNF-06 (cobertura 80%) | TASK-05, TASK-10 |
| RNF-08 (CORS restrito) | TASK-01, TASK-10 |
