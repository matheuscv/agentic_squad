# Plano de Execução — Workflow de Aprovação Humana via Jira (Opção B)

> **Escopo desta entrega:** Implementar um mecanismo de checkpoint humano no fluxo agêntico da squad, onde ao final de cada fase o orquestrador move o ticket Jira para um status de "aguardando aprovação", e ao ser aprovado manualmente pelo PO no board, o Jira dispara um webhook que aciona autonomamente a retomada do orquestrador via `claude --print` CLI (MVP) com caminho de evolução para GitHub Actions (produção).
> Nenhuma alteração de contrato público de negócio, nenhuma feature funcional nova no domínio de contatos/usuários.

---

## Visão Geral

### Objetivo
Evoluir a squad agêntica de um fluxo totalmente autônomo (disparo único, sem intervenção humana) para um modelo de **aprovações formais por fase**, onde:
1. O orquestrador conclui uma fase e move o ticket Jira para um status de espera ("Aguardando Aceite PRD", etc.)
2. O PO humano valida o artefato gerado e move o ticket manualmente para o status aprovado ("PRD Validado", etc.)
3. O Jira dispara um webhook para o endpoint do backend FastAPI existente
4. O endpoint retoma o orquestrador executando `claude --print` como subprocess (MVP) ou disparando um GitHub Actions workflow (produção), passando o contexto persistido em arquivo de estado — em ambos os casos o Claude Code roda com acesso completo a todas as ferramentas (Agent, Bash, Write, MCP)

### Premissas
- Backend FastAPI existente (`backend/`) serve como host do endpoint de webhook.
- Infraestrutura de logging e exceções já implementada (Fases B.1 e B.2) é reutilizada integralmente.
- Biblioteca `httpx` já presente no projeto (usada em testes); será reaproveitada para chamadas REST ao Jira.
- Jira Cloud do projeto: `matheuscv.atlassian.net`, projeto `mcv_team` / key `SCRUM`.
- O MCP Atlassian atual (`createJiraIssue`, `getVisibleJiraProjects`, `getAccessibleAtlassianResources`) **não** possui `transitionIssue` — as transições de status serão feitas via REST direta (Jira Cloud REST API v3).
- O arquivo de estado `docs/ESTADO_ORQUESTRADOR.json` é a fonte de verdade entre sessões; reside no repositório e é commitado pelo orquestrador após cada checkpoint.
- A retomada do orquestrador é feita via `claude --print` CLI (subprocess Python) no MVP, garantindo acesso completo às ferramentas do Claude Code (Agent, Bash, Write, MCP). O caminho de evolução para produção é substituir o subprocess por um disparo de GitHub Actions workflow, sem alterar a interface pública do `orquestrador_service.py`.
- O SDK Anthropic **não** é necessário para a retomada — o `claude` CLI já encapsula a comunicação com a API.
- Em desenvolvimento local, o endpoint de webhook é exposto via `ngrok` ou `cloudflared tunnel`.

### Sumário das fases

| Fase | Conteúdo | Tasks |
|------|----------|-------|
| **Fase 1 — Fundações (paralelizável)** | Schema de estado persistido + cliente REST Jira. Tasks independentes em arquivos distintos. | TASK-01, TASK-02 |
| **Fase 2 — Integração Jira** | Serviço de mapeamento fase → transição Jira, consumindo o cliente criado na Fase 1. | TASK-03 |
| **Fase 3 — Webhook + Retomada (paralelizável)** | Endpoint FastAPI `/webhook/jira` com validação HMAC e serviço de retomada em duas camadas: MVP via `claude --print` subprocess e produção via GitHub Actions `workflow_dispatch`. Tasks tocam arquivos disjuntos. | TASK-04, TASK-05 |
| **Fase 4 — Evolução do Orquestrador + Testes (paralelizável)** | Atualização do `PROMPT_ORQUESTRADOR.md` com MODO INÍCIO e checkpoint state write; testes automatizados do webhook e do serviço de retomada. | TASK-06, TASK-07 |
| **Fase 5 — MODO RETOMADA do Orquestrador** | Segunda parte da evolução do `PROMPT_ORQUESTRADOR.md`: instruções para execução autônoma após retomada via CLI. | TASK-08 |
| **Fase 6 — Configuração e Documentação** | Variáveis de ambiente, permissões, Jira Automation Rules e documentação operacional do workflow. | TASK-09, TASK-10 |

---

## Stack Confirmada
- **Linguagem:** Python 3.11+ (backend)
- **Framework:** FastAPI (mantido)
- **HTTP Client REST:** `httpx` (já em `requirements.txt`, via dependência de testes)
- **Retomada do orquestrador (MVP):** `claude --print` CLI como subprocess Python (`subprocess.Popen`)
- **Retomada do orquestrador (produção):** GitHub Actions `workflow_dispatch` via API REST do GitHub (`httpx`)
- **Segurança webhook:** HMAC-SHA256 (stdlib `hmac` + `hashlib`)
- **Persistência de estado:** JSON em `docs/ESTADO_ORQUESTRADOR.json`
- **Testes:** `pytest`, `httpx`, `pytest-mock` (verificar se já presente, caso não, adicionar)
- **Autenticação Jira:** Basic Auth com API Token (padrão Jira Cloud)
- **Autenticação GitHub API:** Personal Access Token com escopo `actions:write` (necessário apenas na camada de produção)

---

## Estrutura de Diretórios (após as tasks)

```
docs/
  ESTADO_ORQUESTRADOR.json        # NOVO (TASK-01) - estado persistido entre sessões
  release_notes/
    OPERACAO_WORKFLOW_JIRA.md     # NOVO (TASK-10) - guia operacional do workflow

backend/
  app/
    config.py                     # editado (TASK-02): + JIRA_BASE_URL, JIRA_API_TOKEN,
                                  #   JIRA_USER_EMAIL, WEBHOOK_SECRET
                                  # editado (TASK-05): + RETOMADA_MODO, CLAUDE_CLI_PATH,
                                  #   GITHUB_TOKEN, GITHUB_REPO, GITHUB_WORKFLOW_FILE
    models/
      estado_orquestrador.py      # NOVO (TASK-01) - Pydantic model do estado
    services/
      estado_orquestrador.py      # NOVO (TASK-01) - ler/salvar/limpar estado em JSON
      jira_client.py              # NOVO (TASK-02) - cliente REST Jira (transitions, status)
      jira_workflow.py            # NOVO (TASK-03) - mapeamento fase → status/transition_id
      orquestrador_service.py     # NOVO (TASK-05) - retomada via claude CLI (subprocess ou GitHub Actions)
    routers/
      webhook.py                  # NOVO (TASK-04) - endpoint POST /webhook/jira
    main.py                       # editado (TASK-04): registrar router webhook
  tests/
    test_webhook.py               # NOVO (TASK-07) - testes do endpoint
    test_orquestrador_service.py  # NOVO (TASK-07) - testes do serviço de retomada

PROMPT_ORQUESTRADOR.md            # editado (TASK-06): MODO INÍCIO + checkpoints + state write
                                  # editado (TASK-08): MODO RETOMADA

.github/
  workflows/
    retomar_orquestrador.yml      # NOVO (TASK-05) - workflow disparado por workflow_dispatch

.env.example                      # editado (TASK-09): novas variáveis documentadas
.claude/settings.local.json       # editado (TASK-09): novas permissões de Bash/MCP
```

---

## Fases

### Fase 1 — Fundações (PARALELIZÁVEL)

> TASK-01 e TASK-02 tocam conjuntos disjuntos de arquivos e não dependem uma da outra. **Devem ser executadas em paralelo** por dois DEVs.

---

#### TASK-01 — Schema de estado persistido + serviço de leitura/escrita
- **ID:** TASK-01
- **Objetivo:** Criar o modelo Pydantic `OrquestradorEstado` e o serviço `EstadoOrquestradorService` que lê e grava `docs/ESTADO_ORQUESTRADOR.json`. Este arquivo é o "cérebro externo" do orquestrador entre sessões — sem ele, a retomada após aprovação humana é impossível.
- **Dependências:** nenhuma
- **Pode rodar em paralelo com:** TASK-02
- **Módulos atendidos:** Módulo 1 (Persistência de Estado)

- **Arquivos afetados:**
  - `backend/app/models/estado_orquestrador.py` (criar — caso o diretório `models/` não exista, criá-lo com `__init__.py` vazio)
  - `backend/app/services/estado_orquestrador.py` (criar)
  - `docs/ESTADO_ORQUESTRADOR.json` (criar — template vazio com estrutura válida)

- **Detalhamento técnico:**
  1. Criar `backend/app/models/estado_orquestrador.py` com a classe `OrquestradorEstado(BaseModel)` contendo:
     ```
     issue_key: str                        # ex: "SCRUM-42"
     fase_atual: str                       # enum string: ver tabela abaixo
     proxima_acao: str                     # descrição da próxima fase a executar
     ideia_original: str                   # texto completo da ideia do usuário
     artifacts: dict[str, str | None]      # {"prd": "docs/PRD.md", "plano": None, ...}
     tasks_concluidas: list[str]           # ["TASK-01", "TASK-02", ...]
     jira_project_key: str                 # ex: "SCRUM"
     criado_em: datetime
     atualizado_em: datetime
     ```
  2. Valores válidos para `fase_atual` (documentar como comentário no arquivo):
     ```
     "INICIO"
     "AGUARDANDO_ACEITE_PRD"
     "PRD_VALIDADO"
     "AGUARDANDO_ACEITE_PLANO"
     "PLANO_VALIDADO"
     "AGUARDANDO_ACEITE_DEV"
     "DEV_VALIDADO"
     "AGUARDANDO_ACEITE_QA"
     "QA_VALIDADO"
     "CONCLUIDO"
     ```
  3. Criar `backend/app/services/estado_orquestrador.py` com a classe `EstadoOrquestradorService` contendo:
     - `ESTADO_PATH: Path` — constante apontando para `docs/ESTADO_ORQUESTRADOR.json` relativo à raiz do projeto (usar `Path(__file__).parents[3] / "docs" / "ESTADO_ORQUESTRADOR.json"`)
     - `ler() -> OrquestradorEstado | None` — lê e parseia o JSON; retorna `None` se arquivo não existe ou está vazio
     - `salvar(estado: OrquestradorEstado) -> None` — serializa e escreve o JSON com `indent=2`; atualiza `atualizado_em` automaticamente antes de salvar
     - `limpar() -> None` — remove o arquivo (fim de ciclo ou reset)
     - `existe() -> bool` — verifica se o arquivo de estado existe e é válido
  4. Criar `docs/ESTADO_ORQUESTRADOR.json` com conteúdo `{}` (arquivo vazio/placeholder); adicionar ao `.gitignore` um comentário explicando que este arquivo é gerado em runtime mas versionado para persistência entre sessões (NÃO adicioná-lo ao `.gitignore` — deve ser versionado).
  5. NÃO criar endpoints FastAPI nesta task. NÃO importar FastAPI aqui.

- **Critérios de aceite:**
  - [ ] `from app.models.estado_orquestrador import OrquestradorEstado` importa sem erro.
  - [ ] `from app.services.estado_orquestrador import EstadoOrquestradorService` importa sem erro.
  - [ ] `EstadoOrquestradorService().ler()` retorna `None` quando o arquivo está vazio (`{}`).
  - [ ] Ciclo completo: `salvar(estado)` seguido de `ler()` retorna objeto equivalente ao salvo.
  - [ ] `salvar()` atualiza automaticamente o campo `atualizado_em`.
  - [ ] `docs/ESTADO_ORQUESTRADOR.json` existe no repositório com conteúdo `{}`.
  - [ ] Nenhum arquivo fora da lista acima foi modificado.

---

#### TASK-02 — Cliente REST Jira para transições de status
- **ID:** TASK-02
- **Objetivo:** Criar `JiraClient` — um cliente HTTP que comunica com a Jira Cloud REST API v3 para consultar transições disponíveis, transitar o status de uma issue e consultar o status atual. Necessário porque o MCP Atlassian atual não expõe `transitionIssue`.
- **Dependências:** nenhuma
- **Pode rodar em paralelo com:** TASK-01
- **Módulos atendidos:** Módulo 2 (Transições Jira)

- **Arquivos afetados:**
  - `backend/app/config.py` (editar — adicionar campos Jira e Webhook)
  - `backend/app/services/jira_client.py` (criar)

- **Detalhamento técnico:**
  1. Em `backend/app/config.py`, adicionar ao `Settings`:
     ```
     jira_base_url: str = ""          # ex: "https://matheuscv.atlassian.net"
     jira_api_token: str = ""         # API Token gerado em id.atlassian.net
     jira_user_email: str = ""        # matheus.castro@cielo.com.br
     webhook_secret: str = ""         # segredo HMAC compartilhado com Jira Automation
     ```
     Todos com `default=""` para não quebrar ambientes sem configuração Jira.
  2. Criar `backend/app/services/jira_client.py` com a classe `JiraClient`:
     - Construtor recebe `base_url`, `user_email`, `api_token` (lidos de `settings`)
     - Método `_auth_header() -> dict` — retorna `Authorization: Basic <base64(email:token)>`
     - Método `get_transitions(issue_key: str) -> list[dict]` — GET `/rest/api/3/issue/{issue_key}/transitions` — retorna lista de `{"id": "21", "name": "Aguardando Aceite PRD"}` disponíveis
     - Método `transition_issue(issue_key: str, transition_id: str) -> bool` — POST `/rest/api/3/issue/{issue_key}/transitions` com body `{"transition": {"id": transition_id}}` — retorna `True` em sucesso (HTTP 204), loga `WARNING` e retorna `False` em falha
     - Método `get_issue_status(issue_key: str) -> str` — GET `/rest/api/3/issue/{issue_key}?fields=status` — retorna `fields.status.name`
     - Usar `httpx.Client` (síncrono) com timeout de 10s
     - Logar via `logger = logging.getLogger(__name__)` — nunca logar o valor do `api_token`
  3. NÃO criar endpoints FastAPI. NÃO hardcodar credenciais.

- **Critérios de aceite:**
  - [ ] `from app.services.jira_client import JiraClient` importa sem erro.
  - [ ] `from app.config import settings; settings.jira_base_url` retorna `""` por padrão e respeita variável de ambiente `JIRA_BASE_URL`.
  - [ ] Instanciar `JiraClient` com credenciais inválidas não lança erro no construtor (falha apenas na chamada de método).
  - [ ] Nenhuma credencial é logada (verificável por inspeção de código).
  - [ ] `JiraClient.get_transitions` usa o endpoint correto `/rest/api/3/issue/{key}/transitions`.
  - [ ] `JiraClient.transition_issue` envia `{"transition": {"id": transition_id}}` no body.
  - [ ] Nenhum arquivo fora da lista acima foi modificado.

---

### Fase 2 — Integração Jira

> Depende de TASK-02. TASK-03 é sequencial e cria a ponte entre os nomes de fase do orquestrador e os IDs de transição do Jira.

---

#### TASK-03 — Serviço de mapeamento de fases → transições Jira
- **ID:** TASK-03
- **Objetivo:** Criar `JiraWorkflowService` que encapsula o mapeamento entre as fases do orquestrador (nomes internos) e os status/transições do Jira. Isola o orquestrador e o webhook da lógica de lookup de transition IDs.
- **Dependências:** TASK-02
- **Pode rodar em paralelo com:** nenhuma
- **Módulos atendidos:** Módulo 2 (Transições Jira)

- **Arquivos afetados:**
  - `backend/app/services/jira_workflow.py` (criar)

- **Detalhamento técnico:**
  1. Criar `backend/app/services/jira_workflow.py` com:
     - Dicionário `FASE_PARA_STATUS_JIRA: dict[str, str]` mapeando:
       ```
       "po_agent_concluido"      → "Aguardando Aceite PRD"
       "lt_agent_concluido"      → "Aguardando Aceite PLANO"
       "dev_agents_concluidos"   → "Aguardando Aceite DEV"
       "qa_agent_concluido"      → "Aguardando Aceite QA"
       ```
     - Dicionário `STATUS_APROVADO_PARA_PROXIMA_FASE: dict[str, str]` mapeando:
       ```
       "PRD Validado"            → "lt_agent"
       "PLANO validado"          → "dev_agents"
       "DEV Validado"            → "qa_agent"
       "QA Validado"             → "concluir"
       ```
     - O valor `"concluir"` em `STATUS_APROVADO_PARA_PROXIMA_FASE` indica ao orquestrador que deve mover o ticket para `"Pronto para deploy"` e encerrar o ciclo (sem disparar novo agente).
     - Classe `JiraWorkflowService` com:
       - `__init__(self, jira_client: JiraClient)`
       - `transitar_para_aprovacao(issue_key: str, fase_concluida: str) -> bool` — usa `FASE_PARA_STATUS_JIRA` para descobrir o nome do status alvo, chama `jira_client.get_transitions(issue_key)` para encontrar o `id` correspondente ao nome, e chama `jira_client.transition_issue(issue_key, id)`. Loga `ERROR` e retorna `False` se o status alvo não estiver nas transições disponíveis.
       - `resolver_proxima_fase(status_aprovado: str) -> str | None` — consulta `STATUS_APROVADO_PARA_PROXIMA_FASE`, retorna `None` se status não reconhecido (evento de transição irrelevante para o workflow).
  2. Nomes de status (ex: "Aguardando Aceite PRD") devem ser tratados como configuração — extraí-los para constantes no topo do arquivo, não hardcodados dentro de métodos.
  3. NÃO criar endpoint nem importar FastAPI.

- **Critérios de aceite:**
  - [ ] `from app.services.jira_workflow import JiraWorkflowService` importa sem erro.
  - [ ] `resolver_proxima_fase("PRD Validado")` retorna `"lt_agent"`.
  - [ ] `resolver_proxima_fase("QA Validado")` retorna `"concluir"`.
  - [ ] `resolver_proxima_fase("status desconhecido")` retorna `None`.
  - [ ] `transitar_para_aprovacao` chama `get_transitions` antes de chamar `transition_issue` (nunca usa transition_id hardcodado).
  - [ ] Se o status alvo não está nas transições disponíveis, loga `ERROR` e retorna `False` sem lançar exceção.
  - [ ] Nenhum arquivo fora da lista acima foi modificado.

---

### Fase 3 — Webhook + Retomada (PARALELIZÁVEL)

> Depende das Fases 1 e 2. TASK-04 e TASK-05 tocam conjuntos disjuntos de arquivos. **Devem ser executadas em paralelo** por dois DEVs.

---

#### TASK-04 — Endpoint FastAPI `/webhook/jira`
- **ID:** TASK-04
- **Objetivo:** Criar o endpoint `POST /webhook/jira` que recebe eventos de transição do Jira Automation, valida a assinatura HMAC-SHA256, extrai `issue_key` e novo status, e dispara a retomada do orquestrador em background (sem bloquear a resposta ao Jira).
- **Dependências:** TASK-01, TASK-03
- **Pode rodar em paralelo com:** TASK-05
- **Módulos atendidos:** Módulo 3 (Endpoint de Webhook)

- **Arquivos afetados:**
  - `backend/app/routers/webhook.py` (criar)
  - `backend/app/main.py` (editar — registrar `webhook_router`)

- **Detalhamento técnico:**
  1. Criar `backend/app/routers/webhook.py` com:
     - `router = APIRouter(prefix="/webhook", tags=["webhook"])`
     - Endpoint `POST /webhook/jira`:
       - Recebe o body como `bytes` (raw body necessário para validação HMAC)
       - Lê o header `X-Hub-Signature-256` enviado pelo Jira
       - Valida HMAC: `hmac.compare_digest(expected, received)` usando `settings.webhook_secret`. Se inválido: retorna `HTTP 401` com `{"detail": "assinatura inválida"}` e loga `WARNING`
       - Parseia o body JSON
       - Extrai `issue_key` de `payload["issue"]["key"]`
       - Extrai o novo status de `payload["changelog"]["items"]` filtrando o item com `"field": "status"` e lendo `"toString"`
       - Verifica se o novo status é reconhecido chamando `jira_workflow.resolver_proxima_fase(novo_status)`. Se retornar `None`: retorna `HTTP 200` com `{"detail": "evento ignorado"}` (transição irrelevante)
       - Verifica se existe estado persistido (`EstadoOrquestradorService().existe()`). Se não existir: loga `WARNING` e retorna `HTTP 200` com `{"detail": "sem estado ativo"}` (webhook chegou sem orquestrador em execução)
       - Dispara retomada via `BackgroundTasks` do FastAPI chamando `orquestrador_service.retomar(estado, proxima_fase)` — **não aguarda conclusão**
       - Retorna imediatamente `HTTP 202 Accepted` com `{"detail": "retomada iniciada", "issue_key": issue_key}`
  2. Em `backend/app/main.py`, adicionar após os demais routers:
     ```python
     from app.routers.webhook import router as webhook_router
     app.include_router(webhook_router)
     ```
  3. Se `settings.webhook_secret` estiver vazio, o endpoint deve logar `ERROR` e retornar `HTTP 503` com mensagem de configuração ausente — nunca aceitar requisições sem validação HMAC em qualquer ambiente.
  4. Usar o logger estruturado já existente (`logging.getLogger(__name__)`). O `request_id` da requisição aparecerá automaticamente via middleware já instalado.

- **Critérios de aceite:**
  - [ ] `POST /webhook/jira` com assinatura HMAC inválida retorna `HTTP 401`.
  - [ ] `POST /webhook/jira` com assinatura válida e status desconhecido retorna `HTTP 200 {"detail": "evento ignorado"}`.
  - [ ] `POST /webhook/jira` com assinatura válida, status reconhecido e sem estado ativo retorna `HTTP 200 {"detail": "sem estado ativo"}`.
  - [ ] `POST /webhook/jira` com assinatura válida, status reconhecido e estado ativo retorna `HTTP 202`.
  - [ ] A resposta `202` é retornada **antes** da conclusão da retomada do orquestrador (background task).
  - [ ] `settings.webhook_secret == ""` faz o endpoint retornar `HTTP 503`.
  - [ ] Suíte de testes existente passa sem alterações.

---

#### TASK-05 — Serviço de retomada via Claude Code CLI (duas camadas: MVP e produção)
- **ID:** TASK-05
- **Objetivo:** Criar `orquestrador_service.py` com a função `retomar()` implementada em duas camadas selecionáveis por configuração: **Camada MVP** executa `claude --print` como subprocess Python (acesso completo a todas as ferramentas do Claude Code — Agent, Bash, Write, MCP, etc.); **Camada Produção** dispara um GitHub Actions `workflow_dispatch` via API REST do GitHub (mais robusto para ambientes de servidor, sem necessidade do `claude` CLI instalado localmente). A interface pública `retomar(estado, proxima_fase)` é idêntica nas duas camadas — a troca é transparente para o endpoint webhook.
- **Dependências:** TASK-01
- **Pode rodar em paralelo com:** TASK-04
- **Módulos atendidos:** Módulo 3 (Retomada via Claude Code CLI)

- **Por que não usar a Anthropic Messages API diretamente:** A API pura devolve apenas texto — o orquestrador não conseguiria spawnar sub-agentes (`Agent` tool), escrever arquivos (`Write`), executar testes (`Bash`) nem acessar MCPs (Jira, Atlassian). Essas ferramentas existem apenas no runtime do Claude Code. O `claude --print` executa Claude Code de forma não-interativa com acesso total a todas as ferramentas.

- **Arquivos afetados:**
  - `backend/app/services/orquestrador_service.py` (criar)
  - `backend/app/config.py` (editar — adicionar `retomada_modo`, `github_token`, `github_repo`, `github_workflow_file`, `claude_cli_path`)
  - `.github/workflows/retomar_orquestrador.yml` (criar — workflow acionado por `workflow_dispatch`)

- **Detalhamento técnico:**

  **Novas configurações (adicionar a `backend/app/config.py`):**
  ```
  retomada_modo: str = "subprocess"          # "subprocess" (MVP) ou "github_actions" (produção)
  github_token: str = ""                     # PAT com escopo actions:write (modo github_actions)
  github_repo: str = ""                      # ex: "matheuscv/agentic_squad"
  github_workflow_file: str = "retomar_orquestrador.yml"
  claude_cli_path: str = "claude"            # caminho do binário — padrão: PATH do sistema
  ```

  **`backend/app/services/orquestrador_service.py`:**
  1. Constante `PROJECT_ROOT: Path` — raiz do projeto (`Path(__file__).parents[3]`); necessária para subprocess rodar no diretório correto e para a Camada Produção construir o contexto de estado.
  2. Função `_montar_mensagem_retomada(estado: OrquestradorEstado, proxima_fase: str) -> str` — produz:
     ```
     MODO: RETOMADA
     issue_key: {estado.issue_key}
     proxima_fase: {proxima_fase}
     ideia_original: {estado.ideia_original}
     artifacts: {json do estado.artifacts}
     tasks_concluidas: {estado.tasks_concluidas}
     fase_anterior: {estado.fase_atual}
     ```
  3. Função `_retomar_subprocess(mensagem: str) -> None` — **Camada MVP**:
     - Executa `subprocess.Popen([settings.claude_cli_path, "--print", "-p", mensagem], cwd=str(PROJECT_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE)`
     - O subprocess herda as variáveis de ambiente do processo pai (incluindo `ANTHROPIC_API_KEY` necessária pelo `claude` CLI)
     - Aguarda conclusão com `proc.wait(timeout=3600)` — orquestrador pode levar até 1h por fase
     - Captura stdout e stderr; loga stdout como `INFO` (resumo da execução) e stderr como `WARNING` se não-vazio
     - `returncode != 0`: loga `ERROR` com o stderr completo
     - `TimeoutExpired`: loga `ERROR` e encerra processo com `proc.kill()`
  4. Função `_retomar_github_actions(estado: OrquestradorEstado, proxima_fase: str) -> None` — **Camada Produção**:
     - Monta payload `workflow_dispatch` com `inputs`:
       ```json
       {
         "issue_key": estado.issue_key,
         "proxima_fase": proxima_fase,
         "estado_json": json.dumps(estado.model_dump(), default=str)
       }
       ```
     - POST via `httpx` para `https://api.github.com/repos/{settings.github_repo}/actions/workflows/{settings.github_workflow_file}/dispatches` com `Authorization: Bearer {settings.github_token}`
     - HTTP 204: sucesso, loga `INFO`. Qualquer outro código: loga `ERROR` com body da resposta.
     - **Fire-and-forget** — não aguarda conclusão do workflow; acompanhamento via GitHub Actions UI.
  5. Função assíncrona pública `retomar(estado: OrquestradorEstado, proxima_fase: str) -> None`:
     - Loga `INFO` com `issue_key`, `proxima_fase` e `settings.retomada_modo`
     - `retomada_modo == "subprocess"` → chama `_retomar_subprocess(_montar_mensagem_retomada(...))`
     - `retomada_modo == "github_actions"` → chama `_retomar_github_actions(estado, proxima_fase)`
     - Qualquer exceção não capturada internamente: loga `ERROR` com `exc_info=True`, **não propaga**
  6. NÃO importar FastAPI. NÃO logar `github_token` nem `ANTHROPIC_API_KEY`.

  **`.github/workflows/retomar_orquestrador.yml`:**
  1. Trigger: `workflow_dispatch` com inputs `issue_key` (string), `proxima_fase` (string), `estado_json` (string)
  2. Job `retomar` em `ubuntu-latest`:
     - Step 1: `actions/checkout@v4`
     - Step 2: `actions/setup-python@v5` com Python 3.11
     - Step 3: `pip install -r backend/requirements.txt`
     - Step 4: Instalar `claude` CLI via método oficial vigente
     - Step 5: Escrever `docs/ESTADO_ORQUESTRADOR.json` com `${{ inputs.estado_json }}`
     - Step 6: Executar `claude --print -p "MODO: RETOMADA\nissue_key: ${{ inputs.issue_key }}\nproxima_fase: ${{ inputs.proxima_fase }}"` com `env: ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}`
     - Step 7: `git add docs/ESTADO_ORQUESTRADOR.json && git commit -m "chore: estado orquestrador pós-retomada" && git push`
  3. Secrets necessários no repositório GitHub: `ANTHROPIC_API_KEY`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL`, `WEBHOOK_SECRET`

- **Critérios de aceite:**
  - [ ] `from app.services.orquestrador_service import retomar` importa sem erro.
  - [ ] `_montar_mensagem_retomada()` inclui `"MODO: RETOMADA"`, `issue_key`, `proxima_fase` e `ideia_original`.
  - [ ] Com `settings.retomada_modo = "subprocess"`, `retomar()` executa `subprocess.Popen` com `cwd` na raiz do projeto.
  - [ ] Com `settings.retomada_modo = "github_actions"`, `retomar()` faz POST para a URL correta da GitHub API com header `Authorization: Bearer`.
  - [ ] `retomar()` não lança exceção quando subprocess falha — apenas loga `ERROR`.
  - [ ] `retomar()` não lança exceção quando GitHub API retorna erro — apenas loga `ERROR`.
  - [ ] Nenhum token ou chave aparece em logs (verificável por inspeção de código).
  - [ ] `.github/workflows/retomar_orquestrador.yml` existe e contém os 7 steps especificados.
  - [ ] Nenhum arquivo fora da lista acima foi modificado.

---

### Fase 4 — Evolução do Orquestrador + Testes (PARALELIZÁVEL)

> TASK-06 edita `PROMPT_ORQUESTRADOR.md`. TASK-07 cria arquivos de teste novos. Arquivos disjuntos — **podem ser executadas em paralelo** por dois DEVs.

---

#### TASK-06 — `PROMPT_ORQUESTRADOR.md` — MODO INÍCIO + checkpoints de estado e Jira
- **ID:** TASK-06
- **Objetivo:** Evoluir o `PROMPT_ORQUESTRADOR.md` para que, ao final de cada fase, o orquestrador: (1) detecte se está em MODO INÍCIO ou MODO RETOMADA; (2) persista o estado em `docs/ESTADO_ORQUESTRADOR.json`; (3) realize a transição de status no Jira via `JiraWorkflowService`; (4) informe o usuário que a squad está aguardando aprovação humana no board.
- **Dependências:** TASK-01, TASK-03
- **Pode rodar em paralelo com:** TASK-07
- **Módulos atendidos:** Módulo 4 (Evolução do Orquestrador — MODO INÍCIO)

- **Arquivos afetados:**
  - `PROMPT_ORQUESTRADOR.md` (editar)

- **Detalhamento técnico:**
  1. Adicionar no início do documento, antes de qualquer outra seção, o bloco `## DETECÇÃO DE MODO`:
     - Instruções para o orquestrador verificar se existe o arquivo `docs/ESTADO_ORQUESTRADOR.json` com conteúdo não-vazio
     - Se existe: entrar em MODO RETOMADA (ver TASK-08)
     - Se não existe: entrar em MODO INÍCIO (fluxo atual)
  2. Adicionar seção `## CHECKPOINTS DE APROVAÇÃO` descrevendo o protocolo após cada fase:
     - **Checkpoint A** (após `po-agent` concluir): salvar estado com `fase_atual = "AGUARDANDO_ACEITE_PRD"`, chamar `JiraWorkflowService.transitar_para_aprovacao(issue_key, "po_agent_concluido")`, informar usuário: _"PRD gerado. Ticket movido para 'Aguardando Aceite PRD' no Jira. Aguardando aceite do PO no board."_
     - **Checkpoint B** (após `lt-agent` concluir): salvar estado com `fase_atual = "AGUARDANDO_ACEITE_PLANO"`, chamar `JiraWorkflowService.transitar_para_aprovacao(issue_key, "lt_agent_concluido")`, informar usuário: _"Plano gerado. Ticket movido para 'Aguardando Aceite PLANO' no Jira. Aguardando aceite do PO no board."_
     - **Checkpoint C** (após todos os `dev-agent` concluírem): salvar estado com `fase_atual = "AGUARDANDO_ACEITE_DEV"`, chamar `JiraWorkflowService.transitar_para_aprovacao(issue_key, "dev_agents_concluidos")`, informar usuário: _"Implementação concluída. Ticket movido para 'Aguardando Aceite DEV' no Jira. Aguardando aceite do PO no board."_
     - **Checkpoint D** (após `qa-agent` concluir): salvar estado com `fase_atual = "AGUARDANDO_ACEITE_QA"`, chamar `JiraWorkflowService.transitar_para_aprovacao(issue_key, "qa_agent_concluido")`, informar usuário: _"Testes concluídos. Ticket movido para 'Aguardando Aceite QA' no Jira. Aguardando aceite do PO no board."_
     - **Checkpoint E** (disparado pelo webhook `"QA Validado"` — sem novo agente): mover Jira para `"Pronto para deploy"`, salvar estado com `fase_atual = "CONCLUIDO"`, informar usuário, **limpar** `docs/ESTADO_ORQUESTRADOR.json` (fim do ciclo)
  3. Especificar o conteúdo mínimo do estado a ser salvo em cada checkpoint: `issue_key`, `fase_atual`, `proxima_acao`, `ideia_original`, `artifacts` atualizados, `tasks_concluidas` acumuladas, `jira_project_key`.
  4. As instruções devem ser claras o suficiente para o orquestrador executar corretamente em MODO RETOMADA (via CLI, sem interação humana) — nenhuma instrução deve depender de memória conversacional prévia.
  5. Manter integralmente toda a lógica de execução sequencial existente (Fase 1 po-agent, Fase 2 lt-agent, Fase 3 dev-agents, Fase 4 qa-agent). Os checkpoints são **adicionados** ao final de cada fase, não substituem o fluxo.

- **Critérios de aceite:**
  - [ ] `PROMPT_ORQUESTRADOR.md` contém a seção `## DETECÇÃO DE MODO` antes de qualquer outra seção de execução.
  - [ ] `PROMPT_ORQUESTRADOR.md` contém a seção `## CHECKPOINTS DE APROVAÇÃO` com os 5 checkpoints (A, B, C, D, E).
  - [ ] Cada checkpoint especifica exatamente: valor de `fase_atual`, nome da fase para `JiraWorkflowService`, mensagem ao usuário.
  - [ ] Checkpoint E (QA Validado → Pronto para deploy) inclui instrução de limpeza do arquivo de estado e não dispara novo agente.
  - [ ] Toda a lógica de execução pré-existente está preservada (verificar por diff que nenhum parágrafo foi removido).

---

#### TASK-07 — Testes do endpoint webhook e do serviço de retomada
- **ID:** TASK-07
- **Objetivo:** Cobrir com testes pytest o endpoint `POST /webhook/jira` (autenticação HMAC, roteamento de eventos, disparo de background task) e a função `retomar()` do `orquestrador_service` (montagem da mensagem, subprocess mockado, GitHub Actions mockado).
- **Dependências:** TASK-04, TASK-05
- **Pode rodar em paralelo com:** TASK-06
- **Módulos atendidos:** Validação dos Módulos 3

- **Arquivos afetados (criar):**
  - `backend/tests/test_webhook.py`
  - `backend/tests/test_orquestrador_service.py`

- **Detalhamento técnico:**
  1. `test_webhook.py`:
     - Usar `TestClient` do FastAPI com o `app` real.
     - Fixture `webhook_payload()` retorna um payload Jira sintético com `issue.key = "SCRUM-42"` e `changelog.items[0] = {"field": "status", "toString": "PRD Validado"}`.
     - Função helper `assinar_payload(body: bytes, secret: str) -> str` — gera o header `X-Hub-Signature-256` correto.
     - Teste 1 — HMAC inválido: POST com assinatura errada → HTTP 401.
     - Teste 2 — Status desconhecido: POST com assinatura válida e `toString = "Status Inexistente"` → HTTP 200 `{"detail": "evento ignorado"}`.
     - Teste 3 — Sem estado ativo: POST com assinatura válida, status reconhecido e `docs/ESTADO_ORQUESTRADOR.json` vazio → HTTP 200 `{"detail": "sem estado ativo"}`.
     - Teste 4 — Fluxo feliz: POST com assinatura válida, status reconhecido, estado válido pré-populado → HTTP 202 `{"detail": "retomada iniciada"}`. Mockar `orquestrador_service.retomar` para não chamar subprocess real.
     - Teste 5 — Secret ausente: com `settings.webhook_secret = ""` → HTTP 503.
  2. `test_orquestrador_service.py`:
     - Teste 1 — Montagem da mensagem: `_montar_mensagem_retomada(estado, "lt_agent")` deve conter `"MODO: RETOMADA"`, `"SCRUM-42"`, `"lt_agent"` e o texto da `ideia_original`.
     - Teste 2 — Camada subprocess: com `settings.retomada_modo = "subprocess"`, mockar `subprocess.Popen`; verificar que foi chamado com `settings.claude_cli_path`, flag `"--print"`, flag `"-p"` e `cwd` apontando para a raiz do projeto.
     - Teste 3 — Camada GitHub Actions: com `settings.retomada_modo = "github_actions"`, mockar `httpx.post`; verificar que foi chamado com a URL correta da GitHub API, header `Authorization: Bearer`, e que o body contém `issue_key` e `proxima_fase` nos `inputs`.
     - Teste 4 — Resiliência subprocess: `_retomar_subprocess` quando subprocess retorna `returncode=1` → não propaga exceção, loga `ERROR`. Verificar via `caplog`.
     - Teste 5 — Resiliência GitHub Actions: `_retomar_github_actions` quando `httpx.post` lança exceção → não propaga, loga `ERROR`. Verificar via `caplog`.
  3. Usar `pytest-mock` (adicionar ao `requirements.txt` se ausente) para mocks.
  4. NÃO fazer chamadas reais ao GitHub API, ao `claude` CLI ou ao Jira nos testes.

- **Critérios de aceite:**
  - [ ] `pytest backend/tests/test_webhook.py` passa 100%.
  - [ ] `pytest backend/tests/test_orquestrador_service.py` passa 100%.
  - [ ] Nenhum teste faz chamada real ao GitHub API, ao `claude` CLI ou ao Jira.
  - [ ] Teste 4 verifica que o código de resposta é 202 **sem** aguardar a conclusão do background task.
  - [ ] Suíte completa de testes passa sem alterações nos testes existentes.

---

### Fase 5 — MODO RETOMADA do Orquestrador

> Depende de TASK-06 (edição de PROMPT_ORQUESTRADOR.md) para manter coerência do documento. Sequencial.

---

#### TASK-08 — `PROMPT_ORQUESTRADOR.md` — MODO RETOMADA
- **ID:** TASK-08
- **Objetivo:** Adicionar ao `PROMPT_ORQUESTRADOR.md` as instruções de MODO RETOMADA: como o orquestrador (executado autonomamente via `claude --print`, sem histórico conversacional) deve ler o estado persistido, identificar a fase a retomar, saltar fases já concluídas e continuar o fluxo agêntico delegando ao próximo agente.
- **Dependências:** TASK-06
- **Pode rodar em paralelo com:** nenhuma
- **Módulos atendidos:** Módulo 4 (Evolução do Orquestrador — MODO RETOMADA)

- **Arquivos afetados:**
  - `PROMPT_ORQUESTRADOR.md` (editar)

- **Detalhamento técnico:**
  1. Adicionar seção `## MODO RETOMADA` no documento, posicionada após a seção `## DETECÇÃO DE MODO` e antes das seções de execução das fases.
  2. O MODO RETOMADA deve especificar as seguintes instruções ao orquestrador:
     - Ler `docs/ESTADO_ORQUESTRADOR.json` e parsear o campo `proxima_acao` e `fase_atual`
     - Confirmar que o `issue_key` no estado corresponde à issue mencionada na mensagem de retomada
     - Pular todas as fases cujos agentes estão em `tasks_concluidas`
     - Restaurar o contexto de `ideia_original` e `artifacts` do estado — estes substituem o histórico conversacional perdido
     - Continuar a execução a partir da fase indicada por `proxima_acao`, seguindo as mesmas regras de validação e qualidade das fases normais
     - Ao concluir a fase retomada, executar o checkpoint correspondente (salvar estado, transitar Jira, informar progresso)
  3. As instruções devem ser explícitas sobre o comportamento esperado em casos de estado corrompido ou inconsistente: logar o problema, **não prosseguir**, retornar mensagem clara sobre a inconsistência detectada.
  4. Incluir um exemplo de mensagem de retomada esperada (o formato gerado por `_montar_mensagem_retomada()`) para que o orquestrador reconheça a estrutura sem ambiguidade.
  5. Preservar integralmente o conteúdo já adicionado na TASK-06.

- **Critérios de aceite:**
  - [ ] `PROMPT_ORQUESTRADOR.md` contém a seção `## MODO RETOMADA` após `## DETECÇÃO DE MODO`.
  - [ ] A seção especifica: leitura do estado, skip de fases concluídas, restauração de contexto, continuação da execução.
  - [ ] A seção especifica comportamento em estado corrompido (não prosseguir, reportar).
  - [ ] A seção inclui exemplo do formato de mensagem de retomada.
  - [ ] Todo o conteúdo da TASK-06 está preservado (verificar por diff).

---

### Fase 6 — Configuração e Documentação

> Depende de todas as fases anteriores. TASK-09 e TASK-10 podem rodar em paralelo pois tocam arquivos distintos.

---

#### TASK-09 — Variáveis de ambiente, permissões e Jira Automation Rules
- **ID:** TASK-09
- **Objetivo:** Atualizar as configurações de ambiente, permissões do Claude Code e documentar os passos de configuração da Jira Automation Rule necessária para que o webhook seja disparado quando o PO move o ticket manualmente.
- **Dependências:** TASK-04, TASK-05
- **Pode rodar em paralelo com:** TASK-10
- **Módulos atendidos:** Módulo 5 (Infraestrutura e Configuração)

- **Arquivos afetados:**
  - `.env.example` (editar — adicionar novas variáveis com valores de exemplo)
  - `.claude/settings.local.json` (editar — novas permissões de Bash)

- **Detalhamento técnico:**
  1. Em `.env.example`, adicionar (com comentários explicativos):
     ```
     # Jira Cloud — necessário para transições de status
     JIRA_BASE_URL=https://matheuscv.atlassian.net
     JIRA_API_TOKEN=<gerar em id.atlassian.net/manage-profile/security/api-tokens>
     JIRA_USER_EMAIL=matheus.castro@cielo.com.br

     # Webhook — segredo compartilhado com Jira Automation
     WEBHOOK_SECRET=<string aleatória segura, ex: openssl rand -hex 32>

     # Retomada do orquestrador
     # "subprocess" = MVP local (claude CLI executado como subprocess)
     # "github_actions" = produção (dispara workflow via GitHub API)
     RETOMADA_MODO=subprocess
     CLAUDE_CLI_PATH=claude

     # Necessário apenas quando RETOMADA_MODO=github_actions
     GITHUB_TOKEN=<PAT com escopo actions:write>
     GITHUB_REPO=matheuscv/agentic_squad
     GITHUB_WORKFLOW_FILE=retomar_orquestrador.yml
     ```
  2. Em `.claude/settings.local.json`, adicionar permissões para:
     - `curl https://matheuscv.atlassian.net/*` (chamadas REST ao Jira quando feitas via Bash pelo orquestrador)
     - Permissão de escrita ao `docs/ESTADO_ORQUESTRADOR.json` (já permitida implicitamente via Write tool, mas documentar)
  3. **Não implementar** a Jira Automation Rule (feita no painel web do Jira pelo operador humano), mas criar no arquivo de documentação da TASK-10 as instruções passo-a-passo para configurá-la.
  4. NÃO commitar valores reais de `ANTHROPIC_API_KEY`, `JIRA_API_TOKEN` ou `WEBHOOK_SECRET`.

- **Critérios de aceite:**
  - [ ] `.env.example` contém todas as novas variáveis com comentários (incluindo `RETOMADA_MODO`, `CLAUDE_CLI_PATH`, `GITHUB_TOKEN`, `GITHUB_REPO`, `GITHUB_WORKFLOW_FILE`).
  - [ ] `.claude/settings.local.json` tem permissão para `curl` no domínio Jira.
  - [ ] Nenhum valor real de credencial está presente em qualquer arquivo versionado.
  - [ ] `.gitignore` inclui `.env` (verificar se já existe — não duplicar).

---

#### TASK-10 — Documentação operacional do workflow de aprovação
- **ID:** TASK-10
- **Objetivo:** Criar `docs/release_notes/OPERACAO_WORKFLOW_JIRA.md` com o guia completo de operação do workflow: como configurar a Jira Automation Rule, como expor o endpoint localmente (ngrok), como monitorar o fluxo via logs, como recuperar de falhas.
- **Dependências:** TASK-04, TASK-05, TASK-08, TASK-09
- **Pode rodar em paralelo com:** TASK-09
- **Módulos atendidos:** Módulo 5 (Documentação operacional)

- **Arquivos afetados:**
  - `docs/release_notes/OPERACAO_WORKFLOW_JIRA.md` (criar)

- **Detalhamento técnico:**
  1. O documento deve cobrir obrigatoriamente:
     - **Visão geral do fluxo** — diagrama textual (ASCII ou Mermaid) mostrando: orquestrador → Jira (status A) → PO aprova → Jira → webhook → endpoint → `claude --print` / GitHub Actions → orquestrador retomado
     - **Pré-requisitos** — variáveis de ambiente necessárias com referência ao `.env.example`
     - **Configuração da Jira Automation Rule** — passo-a-passo: onde criar no Jira Cloud, qual trigger usar (`Issue transitioned`), quais status disparar, como configurar o `Send web request` (URL, método POST, body e header de autenticação HMAC)
     - **Exposição local do endpoint** — comando `ngrok http 8000` e como atualizar a URL no Jira Automation
     - **Escolha do modo de retomada** — quando usar `subprocess` vs `github_actions`, como trocar via `RETOMADA_MODO`
     - **Status do workflow** — tabela com todos os status Jira utilizados, seu significado e qual transição os dispara
     - **Monitoramento** — como ler os logs do endpoint webhook (campos `request_id`, `issue_key`, `novo_status`, `proxima_fase`)
     - **Recuperação de falhas** — o que fazer se: (a) o webhook chegou mas o estado foi perdido; (b) o subprocess/workflow falhou na retomada; (c) a transição Jira falhou
     - **Reset manual** — como limpar `docs/ESTADO_ORQUESTRADOR.json` e mover o ticket Jira manualmente para reiniciar o fluxo

- **Critérios de aceite:**
  - [ ] `docs/release_notes/OPERACAO_WORKFLOW_JIRA.md` existe e cobre todos os tópicos listados.
  - [ ] O documento contém um diagrama do fluxo completo.
  - [ ] A seção de Jira Automation é suficientemente detalhada para ser seguida sem conhecimento prévio do produto.
  - [ ] A seção de recuperação de falhas cobre os 3 cenários especificados.
  - [ ] A seção de escolha de modo documenta claramente as diferenças entre `subprocess` e `github_actions`.

---

## Matriz de Paralelização

| Task | Depende de | Paraleliza com | Arquivos exclusivos? |
|------|------------|----------------|----------------------|
| TASK-01 | nenhuma | **TASK-02** | Sim — `models/estado_orquestrador.py`, `services/estado_orquestrador.py`, `docs/ESTADO_ORQUESTRADOR.json` |
| TASK-02 | nenhuma | **TASK-01** | Sim — `services/jira_client.py`, `config.py` |
| TASK-03 | TASK-02 | nenhuma | Sim — `services/jira_workflow.py` |
| TASK-04 | TASK-01, TASK-03 | **TASK-05** | Sim — `routers/webhook.py`, `main.py` |
| TASK-05 | TASK-01 | **TASK-04** | Sim — `services/orquestrador_service.py`, `config.py` (campos adicionais), `.github/workflows/retomar_orquestrador.yml` |
| TASK-06 | TASK-01, TASK-03 | **TASK-07** | Edita `PROMPT_ORQUESTRADOR.md` |
| TASK-07 | TASK-04, TASK-05 | **TASK-06** | Sim — `tests/test_webhook.py`, `tests/test_orquestrador_service.py` |
| TASK-08 | TASK-06 | nenhuma | Edita `PROMPT_ORQUESTRADOR.md` (sequencial após TASK-06) |
| TASK-09 | TASK-04, TASK-05 | **TASK-10** | Sim — `.env.example`, `settings.local.json` |
| TASK-10 | TASK-04..08 | **TASK-09** | Sim — `docs/release_notes/OPERACAO_WORKFLOW_JIRA.md` |

### Pares paralelizáveis (orquestrador deve disparar em 2 DEVs)
- **Fase 1:** TASK-01 e TASK-02 (fundações independentes)
- **Fase 3:** TASK-04 e TASK-05 (webhook e serviço de retomada — arquivos disjuntos)
- **Fase 4:** TASK-06 e TASK-07 (orquestrador e testes — arquivos disjuntos)
- **Fase 6:** TASK-09 e TASK-10 (configuração e documentação)

---

## Resumo executivo
- **Total de tasks:** 10
- **Tasks paralelizáveis:** 4 pares (Fases 1, 3, 4 e 6)
- **Novos arquivos de código:** 6 (`models/estado_orquestrador.py`, `services/estado_orquestrador.py`, `services/jira_client.py`, `services/jira_workflow.py`, `services/orquestrador_service.py`, `routers/webhook.py`)
- **Novo workflow CI:** 1 (`.github/workflows/retomar_orquestrador.yml`)
- **Arquivos editados:** 4 (`config.py`, `main.py`, `PROMPT_ORQUESTRADOR.md`, `.env.example`)
- **Novos arquivos de teste:** 2 (`test_webhook.py`, `test_orquestrador_service.py`)
- **Novos documentos:** 2 (`docs/ESTADO_ORQUESTRADOR.json`, `docs/release_notes/OPERACAO_WORKFLOW_JIRA.md`)
- **Estratégia de retomada em duas camadas:**
  - **MVP (`subprocess`):** `claude --print` executado como subprocess Python; acesso completo a todas as ferramentas do Claude Code; adequado para desenvolvimento local e validação do conceito.
  - **Produção (`github_actions`):** disparo de `workflow_dispatch` via GitHub API; `claude` CLI roda no ambiente gerenciado do CI; sem dependência do CLI no servidor de produção; troca transparente via variável `RETOMADA_MODO`.
- **Itens explicitamente fora de escopo:** Integração com Sentry, notificações Slack/email, multi-projeto Jira, painel de visualização do estado do workflow, Claude Code SDK (Managed Agents) — aguarda maturidade da API.
