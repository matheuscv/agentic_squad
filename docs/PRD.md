# PRD — Melhorias v2 Fase D (D.1, D.3, D.4, D.5)

## 1. Visao Geral e Contexto

Este PRD consolida o escopo da Fase D parcial do roadmap de melhorias v2 do Contact
Management App (FastAPI + Next.js 14), cobrindo quatro entregas de UX e novas
funcionalidades para a gestao de contatos:

- D.1 — Ordenacao de colunas na tabela de contatos
- D.3 — Mascara e validacao de telefone
- D.4 — Filtros avancados de contatos
- D.5 — Exportar contatos (CSV / Excel)

O produto ja conta com: paginacao, busca textual com debounce, soft delete (lixeira),
auditoria de criacao/atualizacao (`criado_por_id` / `atualizado_por_id`), autenticacao
JWT, rate limiting, logging estruturado em JSON (B.1) e tratamento centralizado de
excecoes (B.2). As fases A (seguranca), B.3 a B.5 (Sentry, audit log persistente,
healthcheck) e a Fase E (infraestrutura) permanecem fora deste ciclo.

Stack ja em uso:

- Backend: FastAPI + SQLAlchemy 2.x + SQLite, em `backend/`
- Frontend: Next.js 14 + React + Tailwind + react-hook-form + Zod, em `frontend/`
- Autenticacao JWT (em `localStorage` hoje — migracao para httpOnly cookie e Fase A.1, fora deste PRD)

## 2. Objetivos de Negocio

- **Reduzir tempo de localizacao de contato**: ordenacao por colunas + filtros avancados
  permitem ao usuario operacional encontrar registros sem depender de busca textual
  livre, especialmente em bases com centenas ou milhares de contatos.
- **Aumentar qualidade dos dados**: mascara e validacao de telefone padronizam o
  formato `(99) 99999-9999` na origem (frontend) e reforcam a regra no backend,
  reduzindo retrabalho e falhas em integracoes futuras (importacao, dashboards).
- **Habilitar consumo externo dos dados**: exportacao em CSV/Excel respeitando o
  filtro/busca atual permite uso em planilhas, relatorios e BIs sem necessidade de
  acesso direto ao banco.
- **Preparar base para evolucoes**: os filtros e a ordenacao reusam o hook
  `useDebounce` (C.2) e dependem de indices em colunas frequentes (C.6), o que
  reduz custo das proximas fases D.6 (import) e D.7 (dashboard).

## 3. Publico-Alvo

- **Usuarios operacionais** da aplicacao (atendimento/cadastro), que listam, buscam
  e ordenam contatos no dia a dia.
- **Gestores** que precisam exportar bases filtradas para acompanhamento offline
  ou compartilhamento com areas parceiras.
- **Desenvolvedores da squad**, que herdarao o hook `useDebounce` e os indices
  como base para D.6 e D.7.

## 4. Premissas e Decisoes

- **D.2 (CRUD de usuarios) NAO esta no escopo** desta entrega; sera tratada em ciclo
  separado.
- A migracao do JWT para httpOnly cookie (Fase A.1) **nao depende** deste PRD; as
  novas rotas continuam usando o mesmo esquema de autenticacao atual.
- O banco continua sendo **SQLite** durante esta fase. Volume de exportacao sera
  limitado por configuracao (premissa: ate 50.000 linhas por exportacao em SQLite
  sem degradacao critica). Migracao para PostgreSQL (E.2) e fora de escopo.
- O hook `useDebounce` (C.2) sera criado ou consumido como parte deste pacote caso
  ainda nao exista isolado; a referencia ad-hoc em `contatos/page.tsx` sera
  substituida.
- Indices das colunas frequentes (`nome`, `email`, `criado_em`, `empresa`) serao
  criados via migration Alembic dentro deste pacote — adianta C.6 do roadmap, na
  parte estritamente necessaria para D.1 e D.4.
- Exportacao **Excel** sera implementada com biblioteca `openpyxl` (formato `.xlsx`).
  CSV usara a stdlib (`csv` + StreamingResponse).
- O botao de exportar respeita **busca textual + filtros + ordenacao atuais**, mas
  **ignora paginacao** (exporta o conjunto completo que casa com os filtros).
- A mascara de telefone aceita apenas o formato BR `(99) 99999-9999` (celular com
  9 digitos). Validacao backend usara regex equivalente. Telefone permanece
  **opcional** no modelo (premissa mantida do estado atual).
- Logs estruturados (B.1) e handlers globais (B.2) serao reaproveitados — qualquer
  nova rota deve emitir log com `request_id`, `route`, `duration_ms`.

## 5. Requisitos Funcionais

### D.1 — Ordenacao de colunas

- **RF-01**: O endpoint `GET /contatos/` deve aceitar os parametros opcionais
  `sort_by` (enum: `nome`, `email`, `empresa`, `telefone`, `criado_em`,
  `atualizado_em`) e `sort_order` (enum: `asc`, `desc`, default `asc`).
- **RF-02**: O frontend, na pagina `/contatos`, deve renderizar icones de seta nos
  headers ordenaveis (`nome`, `email`, `empresa`, `criado_em`), alternando entre
  estados **sem ordenacao**, **ASC** e **DESC** ao clicar. A ordenacao atual deve
  ser refletida na URL (querystring) para permitir compartilhamento e refresh.

### D.3 — Mascara e validacao de telefone

- **RF-03**: O componente `ContatoForm` (frontend) deve aplicar a mascara
  `(99) 99999-9999` ao campo telefone usando `react-input-mask` (ja presente em
  `package.json`). O valor enviado ao backend pode ser o texto formatado ou
  digits-only, conforme padrao definido pelo time, **mas o contrato deve ser unico
  e documentado** no schema Zod.
- **RF-04**: O schema Zod do frontend (`frontend/src/lib/schemas.ts`) deve validar
  telefone como opcional e, quando preenchido, exigir o formato `(99) 99999-9999`
  (ou 11 digitos numericos, conforme decisao do contrato). O schema Pydantic do
  backend (`backend/app/schemas/contato.py`) deve aplicar regra equivalente
  (regex) e devolver erro 422 com mensagem clara em caso de violacao.

### D.4 — Filtros avancados

- **RF-05**: A pagina `/contatos` deve exibir um **painel "Filtros" colapsavel**
  acima da tabela, com os seguintes campos:
  - empresa (input texto, debounced)
  - data de criacao inicial e final (date pickers)
  - checkbox "sem email"
  - checkbox "sem telefone"
- **RF-06**: O endpoint `GET /contatos/` deve aceitar os parametros opcionais
  `empresa`, `criado_de` (date), `criado_ate` (date), `sem_email` (bool),
  `sem_telefone` (bool), combinaveis entre si e com `search`, `sort_by`,
  `sort_order` e paginacao. O estado de filtros deve ser refletido na URL.

### D.5 — Exportar contatos

- **RF-07**: A pagina `/contatos` deve exibir um botao **"Exportar"** com menu de
  formato (CSV / Excel). Ao acionar, o frontend chama o endpoint de exportacao
  passando **busca, filtros e ordenacao atuais** (paginacao ignorada).
- **RF-08**: O backend deve expor `GET /contatos/export?format=csv|xlsx` (ou rota
  equivalente) que aceita os mesmos parametros de filtro/busca/ordenacao do
  `GET /contatos/` e devolve um **StreamingResponse** com:
  - `Content-Type` apropriado (`text/csv; charset=utf-8` ou
    `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
  - `Content-Disposition: attachment; filename="contatos_YYYYMMDD_HHMMSS.<ext>"`
  - Colunas: `id`, `nome`, `email`, `telefone`, `empresa`, `criado_em`,
    `atualizado_em` (ordem fixa, headers em PT-BR).
- **RF-09**: A exportacao **NAO** deve incluir contatos em lixeira (soft-deleted),
  alinhada ao comportamento atual da listagem.
- **RF-10**: A exportacao deve ser registrada nos logs estruturados (B.1) com
  campos: `route`, `user_id`, `format`, `rows_exported`, `duration_ms`.

## 6. Requisitos Nao-Funcionais

- **RNF-01 (Performance — ordenacao/filtros)**: As consultas com `sort_by` e os
  filtros de D.4 devem responder em < 300 ms (p95) para bases ate 50.000 contatos
  em SQLite. Indices em `nome`, `email`, `empresa` e `criado_em` devem ser criados
  via migration Alembic.
- **RNF-02 (Performance — exportacao)**: A exportacao deve usar streaming
  (`StreamingResponse`) para nao carregar todo o conjunto em memoria. Tempo total
  de exportacao de 10.000 linhas em CSV deve ser < 5 segundos.
- **RNF-03 (Seguranca)**: Todas as novas rotas devem exigir autenticacao JWT (mesma
  dependencia das rotas existentes). Parametros de filtro/ordenacao devem ser
  validados como **enums fechados** no backend para evitar SQL injection via
  `sort_by` (sem concatenacao de string em queries — uso obrigatorio de
  `getattr(Model, col)` apos validacao em allowlist).
- **RNF-04 (Observabilidade)**: Toda nova rota deve emitir log estruturado JSON
  herdando o `request_id` do middleware existente, incluindo `duration_ms` e
  parametros relevantes (sem PII alem do `user_id`). Erros devem passar pelo
  handler global de excecoes (B.2).
- **RNF-05 (Validacao)**: Schemas Pydantic devem rejeitar combinacoes invalidas
  (ex: `criado_de` > `criado_ate`) com erro 422 e mensagem clara.
- **RNF-06 (UX)**: O painel de filtros deve manter o estado ao paginar e ao trocar
  ordenacao. Filtros e ordenacao devem refletir na URL (deep link).
- **RNF-07 (Acessibilidade)**: Headers ordenaveis devem expor `aria-sort`. Botao
  "Exportar" e dropdown de formato devem expor `aria-label`. Alinhado com D.10
  (a11y) embora D.10 esteja fora de escopo geral.
- **RNF-08 (Compatibilidade)**: A exportacao XLSX deve abrir corretamente em
  Microsoft Excel 2016+, LibreOffice Calc 7+ e Google Sheets.
- **RNF-09 (Cobertura de testes)**: Backend — novos endpoints e parametros devem
  manter regressivo verde e cobertura >= 95% no modulo de contatos. Frontend —
  ao menos um teste por feature (D.1, D.3, D.4, D.5) cobrindo o caminho feliz.
- **RNF-10 (Internacionalizacao de numeros/datas)**: Datas exibidas no painel de
  filtros e na exportacao devem seguir o locale `pt-BR` (DD/MM/AAAA), exceto no
  nome do arquivo (que usa timestamp ISO compacto).

## 7. Stack Tecnica Sugerida

- **Linguagem (backend)**: Python 3.11+
- **Framework (backend)**: FastAPI (existente) + SQLAlchemy 2.x
- **Persistencia**: SQLite (existente) + Alembic para nova migration de indices
- **Exportacao**: stdlib `csv` (CSV) + `openpyxl` (XLSX) com StreamingResponse
- **Linguagem (frontend)**: TypeScript
- **Framework (frontend)**: Next.js 14 + React + Tailwind
- **Formularios**: react-hook-form + Zod (existente) + `react-input-mask`
  (ja em `package.json`)
- **Testes**: pytest + httpx (backend); Jest + Testing Library (frontend)

## 8. Criterios de Aceite (por item)

### D.1 — Ordenacao de colunas

- [ ] `GET /contatos/?sort_by=nome&sort_order=desc` retorna lista ordenada
      decrescente por `nome`; valores invalidos retornam 422.
- [ ] `sort_by` aceita apenas colunas da allowlist (`nome`, `email`, `empresa`,
      `telefone`, `criado_em`, `atualizado_em`); qualquer outro valor retorna 422.
- [ ] Headers ordenaveis em `/contatos` exibem icone de seta indicando estado
      atual (none / asc / desc) e alternam ao clique.
- [ ] Ordenacao escolhida persiste em refresh da pagina (via querystring).
- [ ] Indice criado via migration Alembic em `contatos.nome`, `contatos.email`,
      `contatos.criado_em`, `contatos.empresa`.
- [ ] Tempo de resposta p95 < 300 ms com 50k contatos em base local.

### D.3 — Mascara e validacao de telefone

- [ ] Campo telefone em `ContatoForm` aplica mascara `(99) 99999-9999` ao digitar.
- [ ] Schema Zod rejeita telefones em formato invalido com mensagem clara em PT-BR.
- [ ] Schema Pydantic do backend rejeita o mesmo conjunto (regex equivalente) com
      422.
- [ ] Telefone permanece opcional — submeter formulario sem telefone continua
      funcionando.
- [ ] Teste de unidade no frontend valida pelo menos: vazio (ok), formato correto
      (ok), formato invalido (rejeita).
- [ ] Teste de integracao no backend valida POST e PATCH de contato com telefone
      valido (201/200) e invalido (422).

### D.4 — Filtros avancados

- [ ] Painel "Filtros" e colapsavel (estado lembrado durante a sessao).
- [ ] Filtros `empresa`, `criado_de`, `criado_ate`, `sem_email`, `sem_telefone`
      sao aplicaveis isoladamente e combinaveis entre si.
- [ ] `criado_de > criado_ate` retorna 422 com mensagem clara.
- [ ] Filtros combinam com `search`, `sort_by`, `sort_order` e paginacao sem
      perda de estado.
- [ ] Filtro `empresa` usa o hook `useDebounce` (300 ms) para evitar chamadas
      excessivas ao backend.
- [ ] Filtros refletem na URL (deep link funcional).
- [ ] Cobertura de teste cobre pelo menos: filtro por empresa, filtro por range
      de data, filtros booleanos isolados, combinacao de dois filtros.

### D.5 — Exportar contatos

- [ ] Botao "Exportar" visivel na pagina `/contatos` com opcao de formato
      (CSV / Excel).
- [ ] `GET /contatos/export?format=csv` devolve `Content-Type: text/csv;
      charset=utf-8` e `Content-Disposition: attachment;
      filename="contatos_YYYYMMDD_HHMMSS.csv"`.
- [ ] `GET /contatos/export?format=xlsx` devolve `Content-Type:
      application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` e
      `filename="contatos_YYYYMMDD_HHMMSS.xlsx"`.
- [ ] A exportacao aplica os mesmos filtros, busca e ordenacao da listagem atual;
      paginacao e ignorada.
- [ ] Contatos em lixeira nao aparecem na exportacao.
- [ ] Resposta usa streaming — exportar 10k linhas nao deve estourar memoria
      acima de 50 MB no processo backend.
- [ ] Log estruturado de cada exportacao registra `format`, `rows_exported`,
      `user_id`, `duration_ms`.
- [ ] Arquivo XLSX gerado abre sem aviso em Excel 2016+, LibreOffice Calc 7+ e
      Google Sheets.

## 9. Fora de Escopo

- **D.2 — CRUD completo de usuarios** (lista, detalhe, PUT, DELETE, PATCH role,
  tela `/usuarios`). Sera tratado em ciclo separado.
- **D.6 — Importacao de contatos via CSV** (upload, mapping, dry-run).
- **D.7 — Dashboard de metricas** (`/dashboard`, `GET /stats`).
- **D.8 — Recuperacao de senha por e-mail**.
- **D.9 — Tags / categorias em contatos**.
- **D.10 — Acessibilidade global e axe-core no CI** (apenas o minimo necessario
  para os componentes desta entrega).
- **D.11 — Internacionalizacao (i18n) com next-intl**.
- **Fase A** completa (httpOnly cookie, SECRET_KEY forte, CORS via env,
  rate limit composto, TrustedHost, politica de senha).
- **Fase B.3 a B.5** (Sentry, audit log persistente, healthcheck).
- **Fase C completa**, exceto o estritamente necessario para esta entrega: hook
  `useDebounce` reusavel (C.2) e indices em colunas frequentes (C.6) — apenas as
  colunas exigidas por D.1 e D.4.
- **Fase E** inteira (Docker, PostgreSQL, CI/CD, dark mode, pre-commit, retry
  HTTP).
- Exportacao em outros formatos (PDF, JSON).
- Agendamento de exportacao recorrente.
- Limites de quota/throttle especificos para exportacao alem do rate limit global
  ja existente.

## 10. Riscos e Premissas

| # | Risco | Mitigacao |
|---|---|---|
| R1 | SQLite pode degradar em exportacao de bases > 50k linhas | Limitar exportacao por configuracao; promover migracao para PostgreSQL (E.2) em fase posterior |
| R2 | Mudanca de contrato no campo telefone (formatado vs digits-only) pode quebrar integradores | Documentar contrato no PRD / OpenAPI; aplicar apenas validacao (sem mudar tipo da coluna) |
| R3 | Validacao por `sort_by` exposto a injection caso seja concatenado em SQL | Allowlist enum + `getattr(Model, col)` apos validacao; vetada concatenacao de string |
| R4 | Streaming XLSX e mais complexo que CSV (openpyxl tende a carregar em memoria) | Avaliar `xlsxwriter` ou geracao em chunks; em ultimo caso, limitar XLSX a N linhas e oferecer CSV para volumes maiores |
| R5 | Indices novos podem aumentar tempo de write em INSERT/UPDATE | Aceitavel para volume atual; revisar quando migrar para PostgreSQL |
| R6 | Filtros + ordenacao + busca podem produzir querystrings muito longas | Aceitavel — limite de URL no Next/FastAPI cobre o caso de uso |
| R7 | Mascara de telefone pode atrapalhar colagem de telefones ja formatados em outros padroes | Aceitar input formatado e digits-only no parser do `react-input-mask`; rejeitar apenas no submit |

Premissas chave (resumo):

- Telefone permanece **opcional**.
- Exportacao **ignora paginacao** e respeita filtro/busca/ordem.
- Lixeira **nao** entra na exportacao.
- `useDebounce` sera consolidado em `frontend/src/hooks/useDebounce.ts`.
- Indices serao criados via Alembic dentro deste pacote.

---

**PRONTO PARA O ORQUESTRADOR CRIAR ISSUE NO JIRA**
