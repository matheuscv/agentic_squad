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

---

## 14. Fase 2 — Funcionalidades de UX

> **Data de referência:** 2026-05-11
> Conjunto de melhorias de experiência do usuário que elevam a usabilidade e completude da aplicação após a estabilização do MVP (Fase 1).

---

### 14.1 Visão Geral da Fase 2

Esta fase endereça seis pontos de atrito identificados após a entrega do MVP: ausência de ordenação na tabela de contatos, CRUD incompleto de usuários, validação fraca do campo telefone, ausência de iconografia nos botões de ação, mensagem de "sem resultados" genérica e perda silenciosa de dados ao navegar com formulário preenchido.

---

### 14.2 Requisitos Funcionais — Fase 2

#### RF-F2-01 — Ordenação de colunas na tabela de contatos

- O endpoint `GET /contatos/` deve aceitar os parâmetros de query `sort_by` (valores permitidos: `nome`, `email`, `empresa`, `criado_em`) e `sort_order` (valores permitidos: `asc`, `desc`).
- O valor padrão deve ser `sort_by=nome&sort_order=asc`.
- Parâmetros inválidos devem retornar HTTP 422 com mensagem descritiva.
- O backend deve aplicar a ordenação diretamente na query SQL (não em memória).
- No frontend, cada cabeçalho de coluna ordenável (`Nome`, `Email`, `Empresa`, `Data`) deve ser clicável.
- O primeiro clique em uma coluna inativa ordena ASC; o segundo clique na mesma coluna inverte para DESC; o terceiro clique remove a ordenação explícita (retorna ao padrão `nome ASC`).
- Um ícone de seta (via `lucide-react`: `ArrowUp`, `ArrowDown`, `ArrowUpDown`) deve indicar o estado de ordenação ativo de cada coluna.
- A ordenação deve ser resetada para o padrão ao alterar o filtro de busca.

#### RF-F2-02 — CRUD completo de usuários

- O backend deve expor os seguintes endpoints no router `/usuarios/`, todos protegidos por token JWT:
  - `GET /usuarios/` — lista todos os usuários (apenas role `adm`); retorna array com `id`, `nome`, `email`, `role`, `criado_em` (sem senha).
  - `GET /usuarios/{id}` — retorna os dados de um usuário específico (role `adm` ou o próprio usuário); HTTP 404 se não encontrado.
  - `PUT /usuarios/{id}` — atualiza `nome` e/ou `email` de um usuário (role `adm` ou o próprio usuário); e-mail deve continuar único; retorna o registro atualizado.
  - `DELETE /usuarios/{id}` — remove um usuário (apenas role `adm`); HTTP 400 se o usuário tentar excluir a si mesmo; HTTP 404 se não encontrado.
  - `PATCH /usuarios/{id}/role` — altera a role de um usuário para `default` ou `adm` (apenas role `adm`); HTTP 400 se tentar rebaixar a si mesmo.
- Senhas nunca devem ser expostas em nenhum endpoint de listagem ou detalhe.
- Todos os endpoints devem retornar HTTP 401 para requisições sem token válido e HTTP 403 para usuários sem permissão.

#### RF-F2-03 — Máscara e validação de telefone

- O campo `telefone` no formulário frontend deve aplicar máscara de entrada no formato `(99) 99999-9999` (celular) ou `(99) 9999-9999` (fixo), aceitando ambos.
- A máscara deve ser implementada via biblioteca `react-input-mask` ou equivalente mantida e compatível com React 18+.
- O frontend deve exibir mensagem de erro em PT-BR abaixo do campo se o número digitado não completar nenhum dos dois formatos válidos.
- O backend deve validar o campo `telefone` no schema Pydantic usando expressão regular; valores que não correspondam aos padrões `^\(\d{2}\) \d{4,5}-\d{4}$` devem retornar HTTP 422 com mensagem descritiva.
- O campo telefone permanece opcional; a validação de formato é aplicada apenas quando um valor for fornecido.

#### RF-F2-04 — Ícones nos botões e ações

- Os botões de ação primária da interface devem exibir ícone + texto (nunca ícone isolado, para preservar acessibilidade).
- Mapeamento mínimo obrigatório de ícones (biblioteca `lucide-react`):
  - "Novo Contato" → ícone `UserPlus`
  - "Editar" → ícone `Pencil`
  - "Excluir" → ícone `Trash2`
  - "Salvar" → ícone `Save`
  - "Cancelar" → ícone `X`
  - "Sair" (logout) → ícone `LogOut`
- Os ícones devem ter `aria-hidden="true"` e o texto adjacente deve permanecer visível (não apenas em tooltip), garantindo conformidade básica de acessibilidade.
- O tamanho padrão dos ícones deve ser 16px (`size={16}`) para botões compactos e 20px para botões de destaque.

#### RF-F2-05 — Mensagem de "sem resultados" contextual

- O componente que exibe a tabela de contatos deve distinguir dois estados de lista vazia:
  - **Com filtro ativo** (campo de busca preenchido): exibir a mensagem `Nenhum resultado para "[termo buscado]".`
  - **Sem filtro, banco vazio** (campo de busca vazio e `total === 0`): exibir a mensagem `Nenhum contato cadastrado ainda.` acompanhada de um link/botão "Cadastrar primeiro contato" visível apenas para usuários `adm`.
- Ambas as mensagens devem ser centralizadas na área da tabela, com tipografia diferenciada (ex.: texto secundário/muted).
- A mensagem `Nenhum contato encontrado` genérica deve ser removida e substituída pelas duas variantes acima.

#### RF-F2-06 — Alerta ao sair de formulário sem salvar

- Os formulários de criação e edição de contato devem monitorar se houve alguma alteração nos campos após a renderização inicial (estado "sujo").
- Enquanto o formulário estiver no estado sujo e o usuário tentar fechar ou recarregar a aba do navegador, o evento `beforeunload` deve ser interceptado, acionando o diálogo nativo do navegador com aviso de saída.
- Enquanto o formulário estiver no estado sujo e o usuário tentar navegar para outra rota via link interno (Next.js Router), um modal de confirmação customizado deve ser exibido com as opções:
  - "Continuar editando" — fecha o modal e mantém o formulário.
  - "Sair sem salvar" — descarta as alterações e navega para a rota destino.
- Após salvar ou cancelar explicitamente (botão "Cancelar" do formulário), o estado sujo deve ser limpo antes da navegação, para que nenhum alerta seja exibido.
- A interceptação de rota deve usar o hook `useBeforeUnload` (implementação própria ou biblioteca) e o router events do Next.js App Router.

---

### 14.3 Regras de Negócio — Fase 2

- **RN-F2-01**: A ordenação de contatos deve ser processada no banco de dados; nunca ordenar arrays em memória no backend.
- **RN-F2-02**: Um administrador não pode excluir sua própria conta nem rebaixar sua própria role via API; essas operações devem retornar HTTP 400 com mensagem explicativa.
- **RN-F2-03**: O telefone é sempre opcional, mas quando fornecido deve obrigatoriamente satisfazer a validação de formato tanto no frontend quanto no backend.
- **RN-F2-04**: Ícones são decorativos (`aria-hidden="true"`); o texto dos botões deve permanecer sempre visível — não usar tooltip como substituto de label.
- **RN-F2-05**: O estado "sujo" do formulário é determinado comparando os valores atuais dos campos com os valores originais (do momento em que o formulário foi aberto); campos não alterados não contam como modificação.
- **RN-F2-06**: O alerta de saída de formulário não deve ser exibido se o usuário clicar em "Cancelar" ou se o formulário tiver sido submetido com sucesso.

---

### 14.4 Critérios de Aceite — Fase 2

#### RF-F2-01 — Ordenação de colunas

- [ ] `GET /contatos/?sort_by=nome&sort_order=asc` retorna contatos em ordem alfabética crescente por nome
- [ ] `GET /contatos/?sort_by=empresa&sort_order=desc` retorna contatos em ordem decrescente por empresa
- [ ] `GET /contatos/?sort_by=campo_invalido` retorna HTTP 422
- [ ] `GET /contatos/` sem parâmetros de ordenação retorna resultados ordenados por nome ASC (padrão)
- [ ] Clicar no header "Nome" uma vez exibe seta para cima e ordena ASC; clicar novamente exibe seta para baixo e ordena DESC
- [ ] Colunas sem ordenação ativa exibem ícone neutro (`ArrowUpDown`)
- [ ] Alterar o filtro de busca reseta a ordenação para o padrão

#### RF-F2-02 — CRUD de usuários

- [ ] `GET /usuarios/` retornado para usuário `adm` lista todos os usuários sem campo `senha`
- [ ] `GET /usuarios/` retornado para usuário `default` retorna HTTP 403
- [ ] `GET /usuarios/{id}` retorna HTTP 404 para ID inexistente
- [ ] `PUT /usuarios/{id}` com e-mail já usado por outro usuário retorna HTTP 400 ou 422 com mensagem de e-mail duplicado
- [ ] `DELETE /usuarios/{id}` onde `{id}` é o próprio usuário autenticado retorna HTTP 400
- [ ] `PATCH /usuarios/{id}/role` executado por usuário `default` retorna HTTP 403
- [ ] `PATCH /usuarios/{id}/role` onde `{id}` é o próprio admin retorna HTTP 400
- [ ] Nenhum endpoint retorna o campo `senha` (hash ou plain) no payload de resposta

#### RF-F2-03 — Validação de telefone

- [ ] Digitar `(11) 98765-4321` no campo telefone é aceito (formato celular)
- [ ] Digitar `(11) 3456-7890` no campo telefone é aceito (formato fixo)
- [ ] Digitar `11987654321` (sem máscara) exibe erro de validação no frontend antes de submeter
- [ ] `POST /contatos/` com `telefone: "11987654321"` retorna HTTP 422 com mensagem de formato inválido
- [ ] Submeter o formulário com campo telefone vazio é aceito (campo opcional)
- [ ] A máscara formata automaticamente a entrada enquanto o usuário digita

#### RF-F2-04 — Ícones nos botões

- [ ] Botão "Novo Contato" exibe ícone `UserPlus` à esquerda do texto
- [ ] Botão "Editar" exibe ícone `Pencil` à esquerda do texto
- [ ] Botão "Excluir" exibe ícone `Trash2` à esquerda do texto
- [ ] Todos os ícones possuem `aria-hidden="true"` no DOM
- [ ] O texto dos botões permanece visível (não está oculto via classe `sr-only`)

#### RF-F2-05 — Mensagem contextual de lista vazia

- [ ] Com busca ativa e sem resultados, a mensagem exibida contém o termo pesquisado entre aspas
- [ ] Com banco vazio e sem busca ativa, a mensagem exibida é "Nenhum contato cadastrado ainda."
- [ ] Com banco vazio e sem busca, usuário `adm` vê link/botão "Cadastrar primeiro contato"
- [ ] Com banco vazio e sem busca, usuário `default` não vê o botão de cadastro
- [ ] A string "Nenhum contato encontrado" não aparece mais em nenhum estado da interface

#### RF-F2-06 — Alerta ao sair sem salvar

- [ ] Ao modificar qualquer campo do formulário e tentar fechar a aba, o navegador exibe o diálogo nativo de saída
- [ ] Ao modificar qualquer campo e clicar em um link de navegação interna, um modal de confirmação é exibido
- [ ] Clicar em "Continuar editando" no modal fecha o modal e mantém o formulário com os dados preenchidos
- [ ] Clicar em "Sair sem salvar" navega para a rota destino sem salvar os dados
- [ ] Após salvar o formulário com sucesso, navegar para outra rota não exibe nenhum alerta
- [ ] Clicar no botão "Cancelar" do formulário sem ter alterado nenhum campo não exibe modal de confirmação

---

### 14.5 Arquivos Impactados — Fase 2

| Arquivo | Tipo de alteração |
|---|---|
| `backend/app/routers/contatos.py` | Adição dos parâmetros `sort_by` e `sort_order` na query |
| `backend/app/routers/usuarios.py` | Adição dos endpoints `GET /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `PATCH /{id}/role` |
| `backend/app/schemas/usuario.py` | Novos schemas de resposta e atualização de usuário |
| `backend/app/schemas/contato.py` | Atualização da validação do campo `telefone` (regex Pydantic) |
| `frontend/src/components/ContatoTable.tsx` | Cabeçalhos clicáveis com ícones de ordenação |
| `frontend/src/components/ContatoTable.tsx` | Mensagens de lista vazia contextuais |
| `frontend/src/app/contatos/page.tsx` | Estado de `sort_by`/`sort_order` + passagem de parâmetros para a API |
| `frontend/src/components/ContatoForm.tsx` | Máscara de telefone + detecção de estado sujo + alerta de saída |
| `frontend/src/hooks/useBeforeUnload.ts` | Novo hook para interceptação de fechamento de aba |
| `frontend/src/components/UnsavedChangesModal.tsx` | Novo componente de modal de confirmação de saída |
| `frontend/src/components/ui/` (geral) | Substituição de textos por ícone + texto via `lucide-react` |

---

### 14.6 Fora de Escopo da Fase 2

- Interface administrativa completa de gerenciamento de usuários (tela dedicada de listagem e edição de usuários no frontend — apenas os endpoints backend são entregues nesta fase)
- Internacionalização de formatos de telefone (apenas o padrão brasileiro é suportado)
- Persistência da ordenação escolhida pelo usuário entre sessões (localStorage)
- Detecção de estado sujo em formulários que não sejam de contato (ex.: formulário de perfil de usuário)
- Testes E2E de frontend para os novos comportamentos

---

## 15. Fase 3.1 — Qualidade e Segurança

> **Data de referência:** 2026-05-12
> Fase focada em cobertura de testes, atualização parcial de contatos via PATCH e soft delete com lixeira para administradores.

---

### 15.1 Visão Geral da Fase 3.1

Com o MVP e as melhorias de UX entregues, esta fase eleva a qualidade técnica da aplicação em três frentes: (1) implementação dos 22 testes planejados para atingir cobertura ≥ 80% no backend, (2) adição de endpoint PATCH para atualização parcial de contatos sem exigir todos os campos, e (3) substituição do delete físico de contatos por soft delete com campo `deletado_em` e endpoint de lixeira exclusivo para administradores.

---

### 15.2 Requisitos Funcionais — Fase 3.1

#### RF-F3-01 — Cobertura de testes ≥ 80%

- O backend deve atingir cobertura mínima de 80% medida com `pytest-cov`.
- As fixtures em `backend/tests/conftest.py` já estão prontas e devem ser reutilizadas sem modificação.
- Os 22 testes devem ser distribuídos nos seguintes arquivos:
  - `test_auth.py` — fluxos de autenticação: login bem-sucedido, credenciais inválidas, token expirado/inválido, cadastro com e-mail duplicado, cadastro com senha curta.
  - `test_usuarios.py` — endpoints de usuário já cobertos pelo arquivo `test_usuarios_crud.py` existente; complementar com casos de borda identificados.
  - `test_contatos.py` — CRUD completo de contatos: criar, listar, buscar, atualizar (PUT e PATCH), excluir (soft delete), lixeira, acesso sem token, acesso com role errada.
  - `test_services.py` — testes unitários diretos nas funções de serviço (`contato_service`, `usuario_service`), sem dependência de HTTP.
- Cada teste deve ter docstring descritiva e seguir o padrão AAA (Arrange / Act / Assert).
- A execução de `pytest --cov=app --cov-report=term-missing` não deve falhar por erros de importação ou fixture ausente.

#### RF-F3-02 — PATCH /contatos/{id} (atualização parcial)

- O endpoint `PUT /contatos/{id}` atual exige todos os campos obrigatórios no body. Adicionar um endpoint `PATCH /contatos/{id}` com os mesmos campos, todos opcionais via `Optional` (Pydantic).
- O schema de entrada para o PATCH deve ser `ContatoPatch`, com todos os campos de `Contato` marcados como `Optional[tipo] = None`.
- Campos não enviados no body não devem ser alterados no banco.
- O endpoint deve retornar o registro atualizado como `ContatoResposta` (HTTP 200).
- Regras de negócio preservadas: unicidade de e-mail, validação de formato de telefone, restrição de acesso a role `adm`.
- Retornar HTTP 404 se o contato não existir; HTTP 403 se o usuário não for `adm`; HTTP 400 se o e-mail fornecido já estiver em uso por outro contato.

#### RF-F3-03 — Soft delete de contatos

- Adicionar coluna `deletado_em: datetime | None` (nullable) no modelo `Contato` (`app/models/contato.py`).
- Criar migration Alembic para adicionar a coluna sem perda de dados existentes.
- O endpoint `DELETE /contatos/{id}` deve parar de excluir fisicamente o registro; em vez disso, deve setar `deletado_em = datetime.now(timezone.utc)` e retornar HTTP 204.
- Todos os endpoints de listagem e busca (`GET /contatos/`, `GET /contatos/{id}`) devem filtrar automaticamente registros com `deletado_em IS NOT NULL` (contatos na lixeira ficam invisíveis para consultas normais).
- Adicionar endpoint `GET /contatos/lixeira` exclusivo para role `adm`:
  - Retorna todos os contatos com `deletado_em IS NOT NULL`, ordenados por `deletado_em DESC`.
  - Suporta os mesmos parâmetros de paginação (`skip`, `limit`) que o endpoint principal.
  - Resposta no formato `ContatoListResponse` (`items`, `total`).
  - Usuários `default` recebem HTTP 403; sem token recebe HTTP 401.

---

### 15.3 Regras de Negócio — Fase 3.1

- **RN-F3-01**: A cobertura de testes é medida exclusivamente no diretório `app/`; arquivos de teste e migrations não entram no cálculo.
- **RN-F3-02**: O endpoint PATCH não deve aceitar body vazio como operação válida se nenhum campo for enviado — retornar HTTP 422 com mensagem "Nenhum campo fornecido para atualização." Exceção: body com todos os campos explicitamente `null` também é rejeitado pela mesma razão.
- **RN-F3-03**: Um contato com `deletado_em` preenchido não pode ser recuperado via `GET /contatos/{id}` (retorna 404); apenas via `GET /contatos/lixeira`.
- **RN-F3-04**: Não é necessário implementar "restaurar da lixeira" nesta fase (fora de escopo).
- **RN-F3-05**: A migration Alembic deve ser `non-destructive` — adicionar coluna com `DEFAULT NULL`, sem alterar ou remover dados existentes.
- **RN-F3-06**: O campo `deletado_em` deve ser incluído no schema `ContatoResposta` como `deletado_em: datetime | None = None` para que o endpoint de lixeira o exponha corretamente.

---

### 15.4 Critérios de Aceite — Fase 3.1

#### RF-F3-01 — Cobertura de testes

- [ ] `pytest --cov=app --cov-report=term-missing` executa sem erro e reporta cobertura ≥ 80%
- [ ] Os arquivos `test_auth.py`, `test_contatos.py` e `test_services.py` existem e contêm testes executáveis
- [ ] Nenhum teste usa `sleep`, dados hardcoded de banco real ou chama serviços externos
- [ ] Todos os testes passam com `pytest -x` (fail-fast)

#### RF-F3-02 — PATCH de contatos

- [ ] `PATCH /contatos/{id}` com `{"telefone": "(11) 99999-9999"}` atualiza apenas o telefone, preservando os demais campos
- [ ] `PATCH /contatos/{id}` com `{"email": "novo@email.com"}` atualiza apenas o e-mail
- [ ] `PATCH /contatos/{id}` com body vazio ou sem campos válidos retorna HTTP 422
- [ ] `PATCH /contatos/{id}` com e-mail já em uso por outro contato retorna HTTP 400
- [ ] `PATCH /contatos/{id}` com ID inexistente retorna HTTP 404
- [ ] `PATCH /contatos/{id}` executado por usuário `default` retorna HTTP 403
- [ ] `PATCH /contatos/{id}` sem token retorna HTTP 401

#### RF-F3-03 — Soft delete e lixeira

- [ ] `DELETE /contatos/{id}` retorna HTTP 204 e o contato deixa de aparecer em `GET /contatos/`
- [ ] `GET /contatos/{id}` após soft delete retorna HTTP 404
- [ ] `GET /contatos/lixeira` com token `adm` retorna o contato deletado com campo `deletado_em` preenchido
- [ ] `GET /contatos/lixeira` com token `default` retorna HTTP 403
- [ ] `GET /contatos/lixeira` sem token retorna HTTP 401
- [ ] A migration Alembic executa com `alembic upgrade head` sem erro em banco existente
- [ ] Contatos criados antes da migration continuam visíveis normalmente (`deletado_em = NULL`)

---

### 15.5 Arquivos Impactados — Fase 3.1

| Arquivo | Tipo de alteração |
|---|---|
| `backend/tests/test_auth.py` | Novo arquivo — testes de autenticação |
| `backend/tests/test_contatos.py` | Novo arquivo — testes CRUD contatos (inclui PATCH e soft delete) |
| `backend/tests/test_services.py` | Novo arquivo — testes unitários de serviço |
| `backend/tests/test_usuarios.py` | Novo arquivo ou complemento de `test_usuarios_crud.py` |
| `backend/app/models/contato.py` | Adição do campo `deletado_em: datetime | None` |
| `backend/app/schemas/contato.py` | Adição do schema `ContatoPatch`; atualização de `ContatoResposta` com `deletado_em` |
| `backend/app/routers/contatos.py` | Adição do endpoint `PATCH /{id}` e `GET /lixeira` |
| `backend/app/services/contato_service.py` | Adaptação de `excluir_contato` para soft delete; nova função `listar_lixeira`; nova função `patch_contato` |
| `backend/alembic/versions/<hash>_add_deletado_em.py` | Nova migration: adiciona coluna `deletado_em` |

---

### 15.6 Fora de Escopo da Fase 3.1

- Restauração de contatos da lixeira (undelete)
- Exclusão definitiva (hard delete) de contatos via API
- Testes de frontend (E2E ou unitários)
- Cobertura de testes do frontend
- Purga automática da lixeira por tempo (ex.: 30 dias)
- Interface visual de lixeira no frontend
