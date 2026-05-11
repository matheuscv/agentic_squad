# PRD — Manutenção de Contatos de Clientes

## 1. Visão Geral

Aplicação web local para gerenciamento de contatos de clientes, composta por frontend (Next.js + TypeScript) e backend (FastAPI + Python) executados em servidores separados na máquina do usuário. O acesso é protegido por autenticação JWT com dois perfis de usuário: **default** (somente leitura) e **adm** (leitura e escrita). Toda a interface é em português (PT-BR).

---

## 2. Objetivo

Permitir que equipes internas cadastrem, consultem, alterem e removam contatos de clientes de forma organizada, com controle de acesso baseado em perfil de usuário, sem necessidade de infraestrutura externa.

---

## 3. Público-Alvo

Usuários internos de uma organização que precisam consultar ou manter uma base de contatos de clientes em ambiente local (sem exposição à internet).

---

## 4. Premissas e Decisões

- A aplicação roda **exclusivamente em localhost** (sem deploy em servidor remoto).
- O banco de dados é **SQLite** (arquivo local), sem necessidade de servidor de banco de dados separado.
- A alteração do perfil (role) de um usuário é feita **diretamente no banco de dados** — não há interface para isso.
- Todo novo cadastro de usuário recebe automaticamente a role **default**.
- Não há funcionalidade de recuperação de senha nesta versão (fora de escopo do MVP).
- O token JWT terá expiração configurável via variável de ambiente (padrão: 60 minutos).
- O frontend consome a API REST do backend via HTTP (localhost).
- Os campos de contato de cliente são: nome completo, e-mail, telefone, empresa e observações.
- Não há paginação complexa no MVP; listagem retorna até 200 registros por padrão.

---

## 5. Requisitos Funcionais

### Autenticação e Usuários

- **RF-01**: O sistema deve exibir uma tela de login com campos de e-mail e senha.
- **RF-02**: O sistema deve permitir que qualquer visitante crie uma nova conta informando nome, e-mail e senha. A role atribuída deve ser sempre **default**.
- **RF-03**: Após login bem-sucedido, o sistema deve emitir um token JWT e redirecioná-lo para a tela principal.
- **RF-04**: O sistema deve validar o token JWT em todas as requisições protegidas; tokens inválidos ou expirados devem retornar HTTP 401 e redirecionar o usuário para a tela de login.
- **RF-05**: O sistema deve exibir o nome do usuário logado e um botão de logout na interface.

### Consulta de Contatos (roles: default e adm)

- **RF-06**: O sistema deve exibir uma listagem de todos os contatos cadastrados, com colunas: nome, e-mail, telefone e empresa.
- **RF-07**: O sistema deve permitir pesquisar contatos por nome, e-mail ou empresa (busca textual, case-insensitive).
- **RF-08**: O sistema deve permitir visualizar os detalhes completos de um contato (todos os campos).

### Manutenção de Contatos (role: adm)

- **RF-09**: O sistema deve permitir ao usuário **adm** incluir um novo contato com os campos: nome completo (obrigatório), e-mail (obrigatório, único), telefone, empresa e observações.
- **RF-10**: O sistema deve permitir ao usuário **adm** alterar qualquer campo de um contato existente.
- **RF-11**: O sistema deve permitir ao usuário **adm** excluir um contato, com confirmação antes da exclusão.
- **RF-12**: O sistema deve ocultar ou desabilitar os botões/ações de inclusão, alteração e exclusão para usuários com role **default**.

---

## 6. Requisitos Não-Funcionais

- **RNF-01 — Desempenho**: A listagem de contatos deve ser retornada em menos de 1 segundo para bases de até 5.000 registros em hardware comum.
- **RNF-02 — Segurança**: Senhas devem ser armazenadas com hash (bcrypt). Tokens JWT devem ser assinados com chave secreta configurável via variável de ambiente.
- **RNF-03 — Usabilidade**: A interface deve ter layout responsivo, tema claro (light theme), tipografia legível e feedback visual para ações (loading, sucesso, erro).
- **RNF-04 — Idioma**: Toda a interface (labels, mensagens de erro, placeholders, notificações) deve estar em português (PT-BR).
- **RNF-05 — Isolamento**: Frontend e backend devem rodar em portas distintas (sugestão: frontend em 3000, backend em 8000) e se comunicar via API REST.
- **RNF-06 — Manutenibilidade**: O código backend deve ter cobertura mínima de 80% por testes unitários (Pytest).
- **RNF-07 — Persistência**: O banco SQLite deve ser armazenado em arquivo local com caminho configurável via variável de ambiente.
- **RNF-08 — CORS**: O backend deve configurar CORS para aceitar requisições apenas do endereço do frontend (localhost:3000) em ambiente de desenvolvimento.

---

## 7. Stack Tecnológica

| Camada       | Tecnologia                        |
|--------------|-----------------------------------|
| Frontend     | Next.js 14+ com TypeScript        |
| UI / Estilo  | Tailwind CSS + shadcn/ui          |
| Backend      | Python 3.11+ com FastAPI          |
| Persistência | SQLite via SQLAlchemy (ORM)       |
| Autenticação | JWT (python-jose) + bcrypt        |
| Testes       | Pytest + httpx (TestClient)       |
| Migrations   | Alembic                           |
| Validação    | Pydantic v2                       |

---

## 8. Arquitetura Macro

```
┌─────────────────────────────────────────────────────┐
│                  Máquina Local                      │
│                                                     │
│  ┌──────────────────┐      HTTP/REST (JSON)         │
│  │  Frontend        │ ◄──────────────────────────►  │
│  │  Next.js :3000   │                               │
│  └──────────────────┘      ┌──────────────────┐    │
│                             │  Backend         │    │
│                             │  FastAPI :8000   │    │
│                             │                  │    │
│                             │  ┌────────────┐  │    │
│                             │  │  SQLite DB │  │    │
│                             │  │  (arquivo) │  │    │
│                             │  └────────────┘  │    │
│                             └──────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Estrutura de Diretórios Sugerida

```
projeto/
├── frontend/          # Next.js + TypeScript
│   ├── src/
│   │   ├── app/       # App Router (Next.js 14)
│   │   ├── components/
│   │   └── services/  # Funções de chamada à API
│   └── package.json
│
└── backend/           # FastAPI + Python
    ├── app/
    │   ├── main.py
    │   ├── models/    # SQLAlchemy models
    │   ├── schemas/   # Pydantic schemas
    │   ├── routers/   # Endpoints (auth, contatos, usuarios)
    │   ├── services/  # Lógica de negócio
    │   └── database.py
    ├── tests/
    ├── alembic/
    └── requirements.txt
```

---

## 9. Histórias de Usuário

- **US-01**: Como visitante, quero criar uma conta com nome, e-mail e senha para acessar o sistema.
- **US-02**: Como usuário cadastrado, quero fazer login com e-mail e senha para acessar minhas funcionalidades.
- **US-03**: Como usuário **default**, quero visualizar a lista de contatos para consultar informações de clientes.
- **US-04**: Como usuário **default**, quero pesquisar contatos por nome, e-mail ou empresa para encontrar rapidamente um cliente.
- **US-05**: Como usuário **default**, quero ver os detalhes completos de um contato para ter todas as informações disponíveis.
- **US-06**: Como usuário **adm**, quero incluir novos contatos para manter a base atualizada.
- **US-07**: Como usuário **adm**, quero alterar dados de um contato existente para corrigir ou atualizar informações.
- **US-08**: Como usuário **adm**, quero excluir um contato, com confirmação, para remover registros desnecessários.
- **US-09**: Como qualquer usuário logado, quero fazer logout para encerrar minha sessão com segurança.

---

## 10. Regras de Negócio

- **RN-01**: Todo usuário recém-cadastrado recebe automaticamente a role **default**; a alteração para **adm** é feita somente via banco de dados.
- **RN-02**: O e-mail de contato deve ser único na base; tentativas de cadastro com e-mail duplicado devem retornar erro com mensagem clara.
- **RN-03**: O e-mail de usuário (login) deve ser único na base; tentativas de cadastro duplicado devem retornar erro.
- **RN-04**: Usuários com role **default** não podem executar operações de escrita (POST, PUT, DELETE) em contatos; o backend deve rejeitar a requisição com HTTP 403.
- **RN-05**: A exclusão de um contato requer confirmação explícita do usuário na interface antes de enviar a requisição ao backend.
- **RN-06**: Campos obrigatórios para contato: nome completo e e-mail. Demais campos são opcionais.
- **RN-07**: O token JWT deve ser armazenado no lado cliente (localStorage ou cookie httpOnly) e enviado no header `Authorization: Bearer <token>` em todas as requisições autenticadas.
- **RN-08**: Senhas devem ter no mínimo 6 caracteres.

---

## 11. Critérios de Aceite por Funcionalidade

### Login
- [ ] Exibe formulário com campos e-mail e senha em PT-BR
- [ ] Redireciona para tela principal após login bem-sucedido
- [ ] Exibe mensagem de erro em PT-BR para credenciais inválidas
- [ ] Redireciona para login ao acessar rota protegida sem token

### Cadastro de Usuário
- [ ] Formulário com campos: nome, e-mail, senha
- [ ] Exibe erro se e-mail já estiver cadastrado
- [ ] Exibe erro se senha tiver menos de 6 caracteres
- [ ] Role atribuída é sempre "default" — confirmado via banco de dados

### Listagem de Contatos
- [ ] Exibe tabela com nome, e-mail, telefone e empresa
- [ ] Funciona para roles default e adm
- [ ] Botões de editar/excluir visíveis apenas para adm

### Pesquisa de Contatos
- [ ] Campo de busca filtra por nome, e-mail ou empresa
- [ ] Busca é case-insensitive
- [ ] Exibe mensagem "Nenhum contato encontrado" quando sem resultado

### Inclusão de Contato (adm)
- [ ] Formulário valida campos obrigatórios (nome, e-mail)
- [ ] Exibe erro para e-mail duplicado
- [ ] Contato aparece na listagem após inclusão bem-sucedida

### Alteração de Contato (adm)
- [ ] Formulário pré-preenchido com dados atuais
- [ ] Alterações persistem após salvar
- [ ] Exibe mensagem de sucesso após salvar

### Exclusão de Contato (adm)
- [ ] Exibe modal/diálogo de confirmação antes de excluir
- [ ] Contato removido da listagem após exclusão confirmada
- [ ] Exclusão cancelada não remove o contato

### Controle de Acesso
- [ ] Usuário default recebe HTTP 403 ao tentar POST/PUT/DELETE via API
- [ ] Interface não exibe botões de escrita para usuário default

### Testes Backend
- [ ] Cobertura >= 80% medida com pytest-cov
- [ ] Testes cobrem: autenticação, CRUD de contatos, validação de roles

---

## 12. Fora de Escopo (MVP)

- Recuperação ou redefinição de senha
- Interface para alterar a role de usuários
- Deploy em servidor remoto ou nuvem
- Exportação de contatos (CSV, Excel, etc.)
- Importação em massa de contatos
- Histórico de alterações / auditoria
- Paginação avançada (cursor-based)
- Notificações por e-mail
- Autenticação via OAuth / redes sociais
- Testes de integração end-to-end (E2E) no frontend

---

## 13. Fase 1 — Correções Imediatas

> **Data de referência:** 2026-05-11
> Conjunto de correções de baixa complexidade que eliminam bloqueadores de usabilidade identificados no MVP entregue.

---

### 13.1 Visão Geral da Fase 1

Três defeitos impedem o uso pleno da aplicação: ausência da barra de navegação em todas as telas, listagem sem paginação (risco de sobrecarga com bases maiores) e feedback visual de erro indistinguível de sucesso. Esta fase corrige os três pontos sem alterar funcionalidades existentes.

---

### 13.2 Requisitos Funcionais — Fase 1

- **RF-F1-01 — Navbar presente em todas as telas**: O componente `Navbar.tsx` deve ser incluído no arquivo `frontend/src/app/layout.tsx`, tornando a barra de navegação visível em todas as páginas da aplicação, incluindo a opção de logout e identificação do usuário logado.

- **RF-F1-02 — Navbar não exibida na tela de login**: A `Navbar` deve ser renderizada condicionalmente: não deve aparecer na rota `/login` nem em `/cadastro`, evitando elementos de navegação em telas públicas.

- **RF-F1-03 — Paginação no backend de contatos**: O endpoint `GET /contatos/` deve aceitar os parâmetros de query `skip: int = 0` e `limit: int = 20`. A resposta deve incluir o campo `total` (contagem total de registros que atendem ao filtro), além da lista `items` com os registros da página atual.

- **RF-F1-04 — Paginação no frontend de contatos**: O componente `ContatoTable` (ou a página `contatos/page.tsx`) deve exibir controles de paginação "Anterior" e "Próxima", refletindo a página atual e desabilitando o botão correspondente quando não houver página anterior ou próxima. O número da página atual e o total de registros devem ser exibidos ao usuário.

- **RF-F1-05 — Toast com tipos visuais distintos**: O estado de toast em `frontend/src/app/contatos/page.tsx` deve suportar o tipo `'sucesso' | 'erro'`. Toasts de sucesso devem usar estilo verde (comportamento atual). Toasts de erro devem usar estilo vermelho/destrutivo, claramente diferenciado do sucesso.

- **RF-F1-06 — Uso do toast de erro em todas as falhas**: Toda chamada à API que resultar em erro (catch de exceção ou resposta HTTP >= 400) deve acionar o toast com tipo `'erro'`, substituindo qualquer uso atual de toast de sucesso para cobrir cenários de falha.

---

### 13.3 Regras de Negócio — Fase 1

- **RN-F1-01**: O valor padrão de `limit` no backend é 20 registros por página; o valor máximo permitido é 200 (para manter compatibilidade com clientes existentes que não enviam parâmetros).
- **RN-F1-02**: A paginação do frontend deve resetar para a primeira página sempre que o usuário alterar o filtro de busca.
- **RN-F1-03**: A Navbar não deve ser exibida para usuários não autenticados (rotas públicas: `/login`, `/cadastro`).

---

### 13.4 Critérios de Aceite — Fase 1

#### RF-F1-01 / RF-F1-02 — Navbar
- [ ] Acessar `/contatos` exibe a Navbar com nome do usuário e botão de logout
- [ ] Acessar `/login` não exibe a Navbar
- [ ] Clicar em logout na Navbar encerra a sessão e redireciona para `/login`

#### RF-F1-03 / RF-F1-04 — Paginação
- [ ] `GET /contatos/?skip=0&limit=20` retorna JSON com campos `items` (array) e `total` (inteiro)
- [ ] `GET /contatos/` sem parâmetros retorna os primeiros 20 registros (padrão)
- [ ] `GET /contatos/?skip=0&limit=200` retorna até 200 registros (compatibilidade)
- [ ] A interface exibe botão "Próxima" desabilitado quando estiver na última página
- [ ] A interface exibe botão "Anterior" desabilitado quando estiver na primeira página
- [ ] Alterar o filtro de busca reseta a listagem para a página 1
- [ ] O total de registros é exibido na interface (ex.: "1–20 de 87 contatos")

#### RF-F1-05 / RF-F1-06 — Toast diferenciado
- [ ] Após salvar um contato com sucesso, o toast exibe fundo verde
- [ ] Após falha em salvar (ex.: e-mail duplicado), o toast exibe fundo vermelho/destrutivo
- [ ] As duas variantes têm texto de cor legível (contraste suficiente)
- [ ] Nenhum cenário de erro usa o estilo de toast de sucesso

---

### 13.5 Arquivos Impactados

| Arquivo | Tipo de alteração |
|---|---|
| `frontend/src/app/layout.tsx` | Inclusão do componente `<Navbar />` com renderização condicional |
| `frontend/src/app/contatos/page.tsx` | Adição de estado de tipo de toast + controles de paginação |
| `frontend/src/components/ContatoTable.tsx` | Adição de props de paginação e controles "Anterior / Próxima" |
| `backend/app/routers/contatos.py` | Adição dos parâmetros `skip` e `limit` + campo `total` no response |
| `backend/app/schemas/contato.py` | Adição do schema `ContatoListResponse` com `items` e `total` |

---

### 13.6 Fora de Escopo da Fase 1

- Paginação cursor-based ou infinite scroll
- Alteração de tamanho de página pelo usuário (page size configurável)
- Persistência da página atual entre navegações
- Animações de transição no toast
- Testes E2E de frontend
