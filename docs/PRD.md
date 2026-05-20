# PRD — Fase B.1 + B.2 — Observabilidade backend (Logging estruturado e Tratamento centralizado de exceções)

## 1. Visão Geral

O Contact Management App (backend FastAPI + frontend Next.js 14) já concluiu as Fases 1, 3.1 e 3.2, entregando correções imediatas, soft delete, lixeira, auditoria de criação/atualização, rate limiting e validação Zod. Apesar dessas evoluções, o backend ainda não tem **logging estruturado** nem **tratamento centralizado de exceções**, o que dificulta a investigação de incidentes, esconde erros silenciosamente (existe um `except Exception: pass` em `backend/app/main.py:36`) e impede correlação de eventos por requisição.

Esta entrega corresponde **exclusivamente** aos itens **B.1 (Logging estruturado em JSON)** e **B.2 (Tratamento centralizado de exceções)** da Fase B do roadmap v2. Trata-se de uma fase preparatória obrigatória para qualquer operação real do sistema, sem alterações de contratos públicos da API nem novas features funcionais para o usuário final.

## 2. Objetivo

Habilitar observabilidade operacional do backend de forma que qualquer requisição possa ser rastreada ponta-a-ponta por um `request_id`, e que toda exceção lançada pelas camadas de serviço seja convertida automaticamente em uma resposta HTTP semanticamente correta, com stack trace registrado em log estruturado, eliminando a captura silenciosa de exceções existente hoje.

## 3. Público-Alvo

- **Squad de engenharia** (devs e SRE) que precisa investigar incidentes em ambiente produtivo.
- **Tech Lead / Code reviewer** que precisa garantir que o backend siga padrões de logging e de propagação de erros.
- **Operações futuras** (Sentry, agregadores de log, K8s) que dependem de logs estruturados para alertas e dashboards.

## 4. Premissas e Decisões

- **Sem alterações em contratos públicos da API** — todos os endpoints continuam respondendo com o mesmo schema atual; apenas a forma de produzir esses status codes muda internamente.
- **Biblioteca escolhida para JSON logging:** `python-json-logger` (sugerida no item B.1 da release v2). Decisão registrada para evitar avaliação adicional no momento do desenvolvimento.
- **Ambiente DEV mantém logs em texto legível** (formato `%(asctime)s %(levelname)s %(name)s %(message)s`); ambiente PROD usa JSON. A escolha é dirigida pela variável de ambiente `ENV` já existente em `backend/app/config.py`.
- **`request_id` é gerado por middleware**; se o header `X-Request-ID` chegar na requisição, ele é reutilizado (idempotência com proxies/edge); caso contrário, gera-se um UUID v4.
- **`user_id` é obtido do contexto JWT** quando disponível (usuário autenticado); para rotas públicas ou anônimas, o campo fica como `null` no log.
- **Dados sensíveis NUNCA são logados** — payloads de senha, tokens, headers `Authorization`, e qualquer PII além do `user_id` estão proibidos. Implementação deve incluir filtro de redaction explícito.
- **Refatoração de `HTTPException` ad-hoc** é feita somente onde a substituição por exceção tipada faz sentido de domínio (ex: contato não encontrado vira `NotFoundError`). Onde já há controle local de status code que não corresponde a um conceito de domínio, mantém-se como está para não inflar o escopo.
- **Compatibilidade com testes existentes**: a suíte atual de testes regressivos (Fases 3.1 e 3.2) deve continuar verde sem modificações.
- **Sem dependência de serviços externos** — Sentry (B.3) está fora do escopo desta entrega.

## 5. Requisitos Funcionais

- **RF-01 — Logger nomeado em services e routers**: Todo módulo dentro de `backend/app/services/` e `backend/app/routers/` deve declarar `logger = logging.getLogger(__name__)` no topo do arquivo e emitir logs nos pontos de entrada/saida relevantes (sucesso, erro tratado, decisão de negócio).

- **RF-02 — Configuração de logging JSON em produção**: Em `ENV=production`, o backend deve configurar um handler raiz com formato JSON usando `python-json-logger`, contendo no mínimo os campos: `timestamp`, `level`, `logger`, `message`, `request_id`, `user_id`, `route`, `duration_ms`. Em `ENV=development` o formato deve ser texto legível em uma linha.

- **RF-03 — Middleware de `request_id` e medição de duração**: Um middleware FastAPI deve, para cada requisição, (a) ler `X-Request-ID` do header ou gerar um UUID v4, (b) armazenar o valor em `contextvars` acessível por todo o ciclo da requisição, (c) marcar o tempo de início, (d) ao final da requisição emitir um log estruturado com `request_id`, `route` (path template), `method`, `status_code`, `duration_ms`, `user_id` (se autenticado) e (e) devolver `X-Request-ID` no header de resposta.

- **RF-04 — Hierarquia de exceções de domínio**: Criar `backend/app/exceptions.py` contendo, no mínimo, as classes: `DomainError` (base, derivada de `Exception`), `NotFoundError`, `ConflictError`, `ValidationError`, `AuthenticationError`, `AuthorizationError`. Cada classe aceita `message: str` e `details: dict | None` no construtor.

- **RF-05 — Exception handlers globais no FastAPI**: Registrar handlers globais que convertam:
  - `NotFoundError` -> HTTP 404
  - `ConflictError` -> HTTP 409
  - `ValidationError` -> HTTP 422
  - `AuthenticationError` -> HTTP 401
  - `AuthorizationError` -> HTTP 403
  - `DomainError` (genérica não mapeada acima) -> HTTP 400
  - `Exception` (qualquer não tratada) -> HTTP 500 com payload genérico (sem vazar stack trace ao cliente)

  Todos os handlers devem registrar o evento no logger estruturado, com `exc_info=True` para `Exception` e `DomainError`, incluindo `request_id` no contexto.

- **RF-06 — Remoção do `except Exception: pass`**: O bloco em `backend/app/main.py:36` deve ser eliminado e substituído pelo uso correto da infraestrutura de exceções, sem omitir falhas. Caso a finalidade original do bloco fosse tolerar a ausência de um recurso (ex: criação opcional de tabelas), o tratamento explícito deve logar o erro em nível `WARNING` e continuar; caso fosse erro acidental, deve propagar.

- **RF-07 — Refactor seletivo de `HTTPException` para exceções de domínio**: Onde já existem `raise HTTPException(status_code=404, ...)` claramente vinculados a "recurso não encontrado" (ex: contato/usuário inexistente) e `HTTPException(status_code=409, ...)` para "email duplicado", substituir por `NotFoundError` / `ConflictError`. O comportamento HTTP visível ao cliente deve permanecer idêntico.

- **RF-08 — Redaction de dados sensíveis em logs**: Implementar um filtro de logging que remova/mascare valores das chaves: `password`, `senha`, `token`, `access_token`, `refresh_token`, `authorization`, `secret`. O filtro é aplicado antes da serialização JSON.

## 6. Requisitos Não-Funcionais

- **RNF-01 — Performance**: A introdução de logging e middleware não pode aumentar a latência média (p50) de endpoints em mais de **5 ms**, e a p95 em mais de **15 ms**, medidos com a suíte de testes atual. Logging em `INFO` deve ser usado com parcimônia em hot paths.

- **RNF-02 — Compatibilidade de ambiente**: Ambiente `development` mantém logs legíveis (texto, uma linha por evento) para não atrapalhar o debug local. Comportamento controlado por `ENV` em `backend/app/config.py`.

- **RNF-03 — Compatibilidade de contrato**: Nenhum endpoint pode mudar request schema, response schema ou status code observável após este PR. A suíte de testes existente deve passar sem alterações.

- **RNF-04 — Segurança de logs (LGPD / hardening)**: Logs NÃO podem conter senhas, tokens JWT, headers `Authorization`, ou qualquer credencial. A redaction (RF-08) é mandatória. Stack traces no log podem conter request_id e nome de função, mas nunca payloads brutos com PII.

- **RNF-05 — Manutenibilidade**: O setup de logging deve estar centralizado em um módulo único (`backend/app/logging_config.py` ou similar) carregado uma única vez no startup. Nenhum `print()` deve permanecer no código de produção.

- **RNF-06 — Testabilidade**: Os exception handlers e o middleware de `request_id` devem ser cobertos por testes unitários/integrados (pytest), com pelo menos um caso por classe de exceção e um caso para a propagação do header `X-Request-ID`.

## 7. Stack Técnica Sugerida

- **Linguagem**: Python 3.11+ (mesma do backend atual)
- **Framework**: FastAPI (mantido)
- **Logging JSON**: `python-json-logger`
- **Persistência**: SQLAlchemy (sem alterações)
- **Testes**: `pytest` + `pytest-asyncio` + `httpx` (já em uso)
- **Suporte ao `request_id`**: `contextvars` (stdlib) para propagação segura entre middleware, services e logger filters.

## 8. Critérios de Aceite (alto nível)

- [ ] **CA-01**: Em `ENV=production`, ao chamar qualquer endpoint, o stdout produz exatamente 1 linha JSON por requisição contendo `request_id`, `user_id`, `route`, `duration_ms`, `status_code`.
- [ ] **CA-02**: Em `ENV=development`, ao chamar qualquer endpoint, o stdout produz logs em texto legível, sem JSON.
- [ ] **CA-03**: Enviar `X-Request-ID: abc-123` na requisição faz o mesmo valor aparecer no log estruturado e no header `X-Request-ID` da resposta.
- [ ] **CA-04**: Ausência do header `X-Request-ID` na requisição faz o backend gerar um UUID v4 válido e devolvê-lo no header de resposta.
- [ ] **CA-05**: Levantar `NotFoundError("contato")` em qualquer service produz HTTP 404 com payload `{"detail": "..."}` consistente.
- [ ] **CA-06**: Levantar `ConflictError("email já existe")` produz HTTP 409.
- [ ] **CA-07**: Levantar `AuthenticationError` produz HTTP 401; `AuthorizationError` produz HTTP 403.
- [ ] **CA-08**: Levantar uma exceção não tratada (`Exception`) produz HTTP 500 com payload genérico (sem stack trace exposto), e o stack trace completo é registrado em log.
- [ ] **CA-09**: O bloco `except Exception: pass` original em `backend/app/main.py:36` não existe mais no código (`grep -nR "except Exception: pass" backend/` retorna vazio).
- [ ] **CA-10**: Um teste automatizado envia uma requisição com `password` no corpo e verifica que o log emitido contém o valor mascarado (ex: `"***"`) e não o texto original.
- [ ] **CA-11**: A suíte de testes existente (Fases 1, 3.1, 3.2) passa 100% sem modificações nos testes.
- [ ] **CA-12**: Pelo menos um endpoint que hoje usa `HTTPException(status_code=404, ...)` é refatorado para usar `NotFoundError`, mantendo o comportamento observável idêntico, com teste regressivo confirmando.

## 9. Definição de Pronto (DoD)

- [ ] Código implementado e merged na `master` (ou branch principal acordada).
- [ ] Todos os critérios de aceite (CA-01 a CA-12) verificados.
- [ ] Testes novos cobrindo: middleware de `request_id`, cada classe de exception handler, redaction de senhas.
- [ ] Suíte completa de testes (backend) passando em local e CI.
- [ ] Linter de segurança (bandit, se ativo) sem novas findings de severidade >= MEDIUM.
- [ ] Nenhum `print()` remanescente em `backend/app/`.
- [ ] Nenhum `except Exception: pass` em `backend/app/`.
- [ ] README ou doc operacional atualizado com instrução de como ler logs em DEV e em PROD.
- [ ] Aprovação de code review por pelo menos 1 par.

## 10. Dependências e Premissas Técnicas

- **Dependência interna**: `backend/app/config.py` já expõe `ENV`; nenhum trabalho adicional é necessário para detectar ambiente.
- **Dependência de pacote**: adicionar `python-json-logger` ao `requirements.txt` (versão pinned).
- **Premissa**: Sentry (B.3) NÃO é integrado nesta fase — porém o desenho de logging deve permitir que B.3 seja plugado depois sem refatorações.
- **Premissa**: O usuário autenticado é resolvido pela dependência `Depends(get_current_user)` já existente; o middleware NÃO duplica essa lógica — apenas lê `request.state.user_id` se a dependência tiver preenchido.
- **Premissa**: Não há requisito de centralizar logs em agregador externo (Datadog/CloudWatch) nesta entrega — stdout é o destino.

## 11. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Logging síncrono em hot path degrada latência | Médio | Manter nível `INFO` em rotas, `DEBUG` apenas dentro de services; medir p50/p95 antes e depois e validar contra RNF-01. |
| Vazamento acidental de senha/token em log | Alto (PCI/LGPD) | Filtro de redaction obrigatório (RF-08) + teste automatizado (CA-10). Revisão manual dos pontos onde se loga `request.body`. |
| Refactor de `HTTPException` quebra teste regressivo | Médio | Substituições feitas uma a uma, com a suíte rodando após cada mudança. Comportamento HTTP visível precisa permanecer idêntico (CA-12). |
| `contextvars` mal propagado em handlers async | Médio | Cobrir com teste async dedicado; usar `ContextVar.set()` no middleware ANTES de `await call_next(request)`. |
| Remoção do `except Exception: pass` quebra startup | Baixo | Investigar a intenção original do bloco (provavelmente criação tolerante de tabelas) antes de remover; substituir por log + propagação controlada. |
| Volume excessivo de logs em PROD aumenta custo | Baixo | Padronizar níveis: rotas em `INFO`, services em `DEBUG`, erros em `ERROR`/`WARNING`. Sem `INFO` dentro de loops. |

## 12. Fora de Escopo

- **B.3 — Integração com Sentry** (backend e frontend) — fica para fase posterior.
- **B.4 — Audit log persistente em tabela `audit_log`** — fica para fase posterior.
- **B.5 — Healthcheck `/health/live` e `/health/ready`** — fica para fase posterior (será necessário para Docker/K8s em Fase E).
- Qualquer item das Fases A, C, D, E do roadmap v2.
- Mudanças em contratos públicos da API.
- Frontend: nenhuma alteração em `frontend/` faz parte desta entrega.
- Integração com agregadores externos de log (Datadog, CloudWatch, ELK).
- Métricas / tracing distribuído (OpenTelemetry) — não solicitado.
- Configuração de níveis de log dinâmica em runtime — fora do escopo.
