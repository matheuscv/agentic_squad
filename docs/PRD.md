# PRD — FASE C: Qualidade de Código e Arquitetura

## 1. Visão Geral
A FASE C do roadmap v2 do Contact Management App é uma fase de **redução de dívida técnica e refatoração arquitetural**, focada em melhorar a qualidade interna do código antes do início da Fase D (novas funcionalidades). Engloba refatoração de componentes React de alta complexidade, criação de hooks reutilizáveis, modernização da API SQLAlchemy (1.x -> 2.0), criação de helpers compartilhados no backend, otimização de consultas via índices, elevação da cobertura de testes do frontend e introdução de linters de segurança no pipeline. O objetivo geral é entregar uma base de código mais manutenível, mais testada e mais segura, sem alterar o comportamento funcional já entregue nas Fases 1, 3.1 e 3.2.

## 2. Objetivo
Reduzir a dívida técnica acumulada nas Fases 1 a 3.2 e preparar terreno arquitetural para a Fase D, padronizando o código (SQLAlchemy 2.0, hooks reutilizáveis, componentes pequenos), elevando a cobertura de testes do frontend para >= 60% e introduzindo varredura automatizada de segurança no pipeline.

## 3. Público-Alvo
- **Equipe de desenvolvimento (frontend e backend)** — principais beneficiários da melhoria de manutenibilidade.
- **Squad de QA** — recebe testes automatizados ampliados e pipeline com gates de segurança.
- **Tech Lead / Arquiteto** — valida padronização SQLAlchemy 2.0 e estrutura de hooks/helpers.
- **Time de segurança (AppSec)** — passa a contar com bandit + eslint-plugin-security no CI.
- **Stakeholders de produto** — beneficiados indiretamente pela maior velocidade de entrega das próximas fases.

## 4. Premissas e Decisões
- A Fase C é puramente **interna/refatoração**: não altera contratos públicos (REST API, UI visível) nem o modelo de dados (exceto adição de índices).
- O backend (`backend/app/`) já está em FastAPI + SQLAlchemy + Alembic e suporta migrar para a API 2.0 (`select()`) sem upgrade de versão maior.
- O frontend (`frontend/src/`) usa Next.js 14 + Jest + Testing Library, com cobertura aparente < 20% — assume-se que a infraestrutura de testes já está pronta e basta escrever os casos.
- **Fase E.5 (pre-commit hook)** ainda não existe; nesta fase, basta deixar `bandit` e `eslint-plugin-security` instalados e configurados para uso futuro.
- A migração `db.query(Model)` -> `select(Model)` será aplicada apenas em routers e services existentes, sem alterar comportamento observável.
- Todos os índices criados em `contato.py` serão refletidos em uma migration Alembic dedicada, sem `down_revision` quebrando o histórico.
- A meta de cobertura de 60% no frontend é medida pelo `coverage` global agregado do Jest (statements).
- Componentes extraídos (`InputField`, `SelectField`, `TextAreaField`) ficarão em `frontend/src/components/form/` (estrutura sugerida) e seguirão o padrão de props do `ContatoForm` atual.

## 5. Requisitos Funcionais

### Frontend — Refatoração e Reuso

- **RF-01 (C.1) — Quebra do ContatoForm.tsx**
  Refatorar `frontend/src/components/ContatoForm.tsx` (atualmente 377 linhas) extraindo:
  - Lógica de validação para um hook `useContatoFormValidation()` em `frontend/src/hooks/`.
  - Campos do formulário em componentes reutilizáveis `InputField`, `SelectField`, `TextAreaField` (em `frontend/src/components/form/`).
  - O componente final `ContatoForm.tsx` deve ficar entre **150 e 180 linhas**.

- **RF-02 (C.2) — Hook useDebounce reutilizável**
  Criar `frontend/src/hooks/useDebounce.ts` com assinatura `useDebounce<T>(value: T, delay: number): T`.
  Substituir o debounce ad-hoc com `useRef` em `frontend/src/app/contatos/page.tsx` pelo novo hook, mantendo o mesmo comportamento de busca.

- **RF-03 (C.3) — Memoização estratégica em ContatoTable**
  Em `frontend/src/components/ContatoTable.tsx`:
  - Envolver o componente `SkeletonRow` em `React.memo`.
  - Envolver a função/array de ordenação dos contatos em `useMemo`, com dependências corretas.
  - Não alterar comportamento visual ou ordenação atual.

### Backend — Modernização e Padronização

- **RF-04 (C.4) — Migração SQLAlchemy 1.x -> 2.0**
  Substituir, em **todos** os arquivos de `backend/app/routers/` e `backend/app/services/`, o padrão `db.query(Model)...` pelo padrão SQLAlchemy 2.0 baseado em `select(Model)` + `db.execute(...)` (ou `db.scalars(...)`).
  Manter o comportamento observável idêntico.

- **RF-05 (C.5) — Helper de validação de unicidade**
  Criar `backend/app/services/_helpers.py` com função utilitária para o padrão "buscar registro por campo único (ex.: email) e levantar `HTTPException(409)` se já existir".
  Substituir o padrão duplicado em `backend/app/routers/usuarios.py` e `backend/app/services/contato_service.py` pelo helper.

- **RF-06 (C.6) — Índices em colunas de busca e ordenação**
  Em `backend/app/models/contato.py`, adicionar `index=True` nas colunas: `nome`, `email`, `criado_em`.
  Gerar uma **migration Alembic** correspondente (autogenerate revisada) que crie esses índices no banco.

### Qualidade — Testes e Segurança

- **RF-07 (C.7) — Elevar cobertura de testes do frontend para >= 60%**
  Escrever testes Jest + Testing Library cobrindo, no mínimo:
  - Fluxo de **login** (formulário, erros, sucesso).
  - **Validação do ContatoForm** (campos obrigatórios, formato de email, máscaras).
  - **Paginação e busca** da listagem em `app/contatos/page.tsx`.
  - **Modal de "alterações não salvas"** ao tentar sair de um formulário sujo.
  Meta: cobertura global de **statements >= 60%** reportada pelo Jest.

- **RF-08 (C.8) — Linter de segurança no pipeline**
  - Backend: instalar e configurar **bandit** (Python) com arquivo de configuração na raiz do `backend/`.
  - Frontend: instalar **eslint-plugin-security** e ativá-lo na configuração ESLint do `frontend/`.
  - O build (CI) deve **falhar** quando houver findings de severidade `MEDIUM` ou superior.
  - As ferramentas devem ficar prontas para futuro uso em pre-commit (Fase E.5), mas **não** é necessário criar o hook agora.

## 6. Requisitos Não-Funcionais

- **RNF-01 — Manutenibilidade**: nenhum arquivo `.tsx` de componente deve exceder 200 linhas após a refatoração da FASE C.
- **RNF-02 — Compatibilidade**: nenhum contrato público (REST API, payloads, status codes, UI visível) pode ser alterado. Todos os testes existentes devem continuar passando.
- **RNF-03 — Performance de leitura**: consultas em `contatos` por `nome`, `email` ou ordenadas por `criado_em` devem se beneficiar dos novos índices (validação por `EXPLAIN` recomendada em base de teste com >= 10k linhas).
- **RNF-04 — Cobertura de testes**: cobertura global do frontend (statements) **>= 60%** medida via `jest --coverage`.
- **RNF-05 — Segurança estática**: pipeline deve quebrar build com findings `MEDIUM` ou `HIGH` do bandit e do eslint-plugin-security.
- **RNF-06 — Padronização SQLAlchemy**: zero ocorrências de `db.query(` em `backend/app/routers/` e `backend/app/services/` após a fase.
- **RNF-07 — Reusabilidade**: hooks (`useDebounce`, `useContatoFormValidation`) e componentes (`InputField`, `SelectField`, `TextAreaField`) devem ser genéricos o suficiente para uso por outras telas no futuro.
- **RNF-08 — Documentação mínima**: cada hook/helper criado deve ter docstring/JSDoc com exemplo de uso.

## 7. Stack Técnica Sugerida

- **Linguagem (backend)**: Python 3.11+
- **Framework (backend)**: FastAPI + SQLAlchemy 2.0 (API `select()`) + Alembic
- **Linguagem (frontend)**: TypeScript
- **Framework (frontend)**: Next.js 14 (App Router) + React 18 + Tailwind CSS
- **Validação**: Zod (frontend) + Pydantic (backend)
- **Testes**: Jest + React Testing Library (frontend); pytest (backend, já existente)
- **Linters de segurança**: bandit (Python) + eslint-plugin-security (JS/TS)
- **Persistência**: o banco já configurado (SQLite/Postgres conforme ambiente); somente adição de índices via Alembic.

## 8. Critérios de Aceite (alto nível)

- [ ] **C.1**: `ContatoForm.tsx` reduzido para 150–180 linhas; hook `useContatoFormValidation` e componentes `InputField`/`SelectField`/`TextAreaField` criados e usados.
- [ ] **C.2**: `frontend/src/hooks/useDebounce.ts` criado; `app/contatos/page.tsx` usa o hook em lugar do debounce com `useRef`; comportamento de busca idêntico.
- [ ] **C.3**: `SkeletonRow` envolvido em `React.memo`; função de ordenação em `useMemo` com deps corretas; sem regressões visuais.
- [ ] **C.4**: Nenhuma ocorrência de `db.query(` em `backend/app/routers/` ou `backend/app/services/`; todos os testes pytest continuam passando.
- [ ] **C.5**: `backend/app/services/_helpers.py` criado; `routers/usuarios.py` e `services/contato_service.py` consomem o helper; sem duplicação do padrão de 409.
- [ ] **C.6**: `nome`, `email`, `criado_em` com `index=True` em `models/contato.py`; migration Alembic gerada, revisada e aplicável.
- [ ] **C.7**: Cobertura global do frontend (statements) **>= 60%** no relatório do Jest; suítes de login, validação, paginação/busca e modal "alterações não salvas" presentes e passando.
- [ ] **C.8**: `bandit` e `eslint-plugin-security` instalados e configurados; pipeline falha em findings `MEDIUM`/`HIGH`; documentação de uso registrada no README do backend e do frontend.
- [ ] Nenhuma quebra nos endpoints/contratos públicos; documentação OpenAPI inalterada.
- [ ] PR único ou conjunto de PRs revisados e aprovados pelo Tech Lead.

## 9. Riscos e Dependências

- **Risco R-01 — Migração SQLAlchemy 2.0 silenciosa**: trocas mecânicas de `query()` por `select()` podem alterar lazy loading ou eager loading. **Mitigação**: rodar suite de testes completa após cada arquivo migrado.
- **Risco R-02 — Migration Alembic em ambientes existentes**: criação de índices em tabela grande pode ser lenta. **Mitigação**: usar `CREATE INDEX CONCURRENTLY` caso o banco-alvo seja Postgres; documentar tempo estimado.
- **Risco R-03 — Quebra de testes existentes ao refatorar ContatoForm**: extração de componentes pode invalidar snapshots/seletores. **Mitigação**: atualizar testes em conjunto com a refatoração e priorizar `getByRole`/`getByLabelText`.
- **Risco R-04 — Findings de bandit/eslint-plugin-security em código legado**: ativar gate `MEDIUM` pode travar build no dia 1. **Mitigação**: rodar varredura prévia, corrigir ou suprimir falsos positivos justificados antes de ligar o gate.
- **Dependência D-01**: C.6 (índices) **prepara** D.1 e D.4 (listagem de contatos com filtros avançados / ordenação).
- **Dependência D-02**: C.2 (`useDebounce`) **prepara** D.4 (busca global com debounce padronizado).
- **Dependência D-03**: C.4 (SQLAlchemy 2.0) é pré-requisito implícito para qualquer feature futura que use `async` sessions.

## 10. Definition of Done (DoD)

Esta fase é considerada **pronta** quando:

1. Todos os 8 critérios de aceite (RF-01 a RF-08) estão marcados como concluídos.
2. CI verde em todos os jobs (lint, type-check, testes backend, testes frontend, bandit, eslint-plugin-security).
3. Cobertura global do frontend (statements) **>= 60%** reportada no log do CI.
4. Migration Alembic da RF-06 testada em ambiente de homologação (up + down).
5. Code review aprovado por pelo menos um Tech Lead.
6. CHANGELOG ou release note atualizado mencionando a entrega da FASE C.
7. Nenhum endpoint REST teve seu contrato (path, payload, status code) alterado.
8. Nenhuma feature funcional nova foi introduzida.

## 11. Fora de Escopo

- **Fase A** (correções urgentes futuras) — fora de escopo.
- **Fase B** (correções imediatas adicionais) — fora de escopo.
- **Fase D** (novas funcionalidades, ex.: filtros avançados, busca global, importação) — fora de escopo; será habilitada por esta fase, mas não executada agora.
- **Fase E** (DevEx, pre-commit hooks, CI avançado) — apenas as ferramentas `bandit` e `eslint-plugin-security` são introduzidas; a integração via `pre-commit` (E.5) **não** faz parte desta fase.
- Alterações de UX/UI visíveis ao usuário final.
- Alterações em contratos REST públicos, payloads ou OpenAPI.
- Migração para outra versão do FastAPI, Next.js, React, Node ou Python.
- Refatoração de componentes fora do escopo listado (apenas `ContatoForm`, `ContatoTable`, `app/contatos/page.tsx`).
- Otimização de queries via reescrita SQL — apenas índices e migração para API 2.0.
- Implementação de testes E2E (Playwright/Cypress) — apenas testes unitários/integração via Jest.
