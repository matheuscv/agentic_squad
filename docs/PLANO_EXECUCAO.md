# Plano de Execução — Fase B.1 + B.2

> **Escopo desta entrega:** somente B.1 (Logging estruturado JSON) e B.2 (Tratamento centralizado de exceções).
> Nenhuma alteração de contrato público, nenhuma feature funcional nova, nenhum trabalho em `frontend/`.

---

## Visão Geral

### Objetivo
Habilitar observabilidade operacional do backend FastAPI: toda requisição rastreável por `request_id`, toda exceção convertida em resposta HTTP semanticamente correta com stack trace registrado em log estruturado, eliminando o `except Exception: pass` existente em `backend/app/main.py`.

### Premissas
- Stack mantida: Python 3.11+, FastAPI, SQLAlchemy, pytest.
- Biblioteca de logging JSON pré-decidida pelo PRD: `python-json-logger` (a ser pinada em `backend/requirements.txt`).
- Variável `ENV` controla o formato (texto em `development`, JSON em `production`) e ainda **não existe** em `backend/app/config.py` — precisa ser adicionada na TASK-01.
- Propagação de contexto via `contextvars` da stdlib.
- Suíte de testes existente (Fases 1, 3.1, 3.2) precisa permanecer 100% verde sem ajustes.
- `python-json-logger` precisa estar instalado antes de o módulo de logging ser importado — adição ao `requirements.txt` é parte da TASK-01.

### Sumário das fases
| Fase | Conteúdo | Tasks |
|------|----------|-------|
| **Fase 1 — Fundações (paralelizável)** | Infra de logging + middleware (B.1) e hierarquia de exceções de domínio (B.2). Tasks independentes em arquivos diferentes. | TASK-01, TASK-02 |
| **Fase 2 — Integração** | Wiring no `main.py`: registrar handlers usando o logger estruturado, plugar o middleware, eliminar `except Exception: pass`. | TASK-03, TASK-04 |
| **Fase 3 — Refactor seletivo e cobertura de testes** | Substituir `HTTPException` ad-hoc por exceções de domínio em pontos claros; testes de middleware, handlers e redaction. | TASK-05, TASK-06, TASK-07 |
| **Fase 4 — Refinamento / DoD** | Garantia de DoD (zero `print`, zero `except Exception: pass`, doc operacional). | TASK-08 |

---

## Stack Confirmada
- **Linguagem:** Python 3.11+
- **Framework:** FastAPI (mantido)
- **Logging JSON:** `python-json-logger` (a ser pinado em `backend/requirements.txt`)
- **Persistência:** SQLAlchemy (sem alterações)
- **Testes:** `pytest`, `pytest-asyncio`, `httpx` (já em uso)
- **Propagação de contexto:** `contextvars` (stdlib)

---

## Estrutura de Diretórios (após as tasks)
```
backend/
  app/
    config.py                 # editado: passa a expor ENV
    logging_config.py         # NOVO (TASK-01) - setup do logger + filtros
    middleware/
      __init__.py             # NOVO (TASK-01)
      request_context.py      # NOVO (TASK-01) - middleware request_id + duration
    exceptions.py             # NOVO (TASK-02) - hierarquia de exceções de domínio
    exception_handlers.py     # NOVO (TASK-03) - handlers globais FastAPI
    main.py                   # editado (TASK-04): wiring + remoção do except pass
    routers/
      contatos.py             # editado (TASK-05): logger nomeado + refactor seletivo
      usuarios.py             # editado (TASK-05): logger nomeado + refactor seletivo
      auth.py                 # editado (TASK-05): logger nomeado
    services/
      contato_service.py      # editado (TASK-05): logger nomeado + raise tipado
      usuario_service.py      # editado (TASK-05): logger nomeado + raise tipado
  tests/
    test_logging_middleware.py     # NOVO (TASK-06)
    test_exception_handlers.py     # NOVO (TASK-06)
    test_log_redaction.py          # NOVO (TASK-07)
  requirements.txt            # editado (TASK-01): + python-json-logger
docs/
  OPERACAO_LOGS.md            # NOVO (TASK-08) - como ler logs em DEV/PROD
```

> Observação: caso o repositório já contenha `backend/app/middleware/__init__.py` (verificado durante a TASK-01), preservar o arquivo e apenas adicionar `request_context.py`.

---

## Fases

### Fase 1 — Fundações (PARALELIZÁVEL)

> TASK-01 e TASK-02 tocam conjuntos disjuntos de arquivos e não dependem uma da outra. **Devem ser executadas em paralelo** por dois DEVs.

---

#### TASK-01 — Infraestrutura de logging estruturado + middleware de request_id
- **ID:** TASK-01
- **Objetivo:** Construir todo o aparato de logging JSON com redaction e o middleware FastAPI que injeta `request_id` em `contextvars` e mede `duration_ms`. Não toca em nada relacionado a exceções de domínio.
- **Dependências:** nenhuma
- **Pode rodar em paralelo com:** TASK-02
- **Requisitos atendidos:** RF-02, RF-03, RF-08, RNF-02, RNF-05; pré-requisito de CA-01, CA-02, CA-03, CA-04, CA-10.

- **Arquivos afetados:**
  - `backend/requirements.txt` (editar — adicionar `python-json-logger` com versão pinada, ex.: `python-json-logger==2.0.7`)
  - `backend/app/config.py` (editar — adicionar campo `env: str = "development"` em `Settings`, lido da variável de ambiente `ENV`)
  - `backend/app/logging_config.py` (criar)
  - `backend/app/middleware/__init__.py` (criar se não existir)
  - `backend/app/middleware/request_context.py` (criar)

- **Detalhamento técnico:**
  1. Em `backend/requirements.txt`, adicionar `python-json-logger==2.0.7` (linha nova, ordem alfabética próxima às demais).
  2. Em `backend/app/config.py`, adicionar `env: str = "development"` ao `Settings`. Garantir que o arquivo `.env` é a fonte (já configurado por `SettingsConfigDict`). Não quebrar nenhum campo existente.
  3. Criar `backend/app/logging_config.py` contendo:
     - Dois `ContextVar` no nível de módulo: `request_id_ctx: ContextVar[str | None]` e `user_id_ctx: ContextVar[str | None]`, ambos com default `None`.
     - Funções `get_request_id()` e `get_user_id()` para leitura segura.
     - Classe `ContextFilter(logging.Filter)` que injeta `request_id` e `user_id` em cada `LogRecord`, lendo dos ContextVars.
     - Classe `RedactionFilter(logging.Filter)` que aplica mascaramento (`"***"`) a valores das chaves: `password`, `senha`, `token`, `access_token`, `refresh_token`, `authorization`, `secret`. Deve mascarar tanto `record.msg` quando dict, quanto `record.args` quando dict/tupla, quanto strings que claramente contenham `key=value`. Implementação conservadora: recursão sobre dicts e listas, com comparação case-insensitive das chaves.
     - Função `setup_logging(env: str) -> None` que:
       - se `env == "production"`: configura handler stdout com `pythonjsonlogger.jsonlogger.JsonFormatter` no formato `"%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(route)s %(duration_ms)s"`;
       - se `env == "development"` (ou qualquer outro): configura handler stdout com `logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")`;
       - aplica `ContextFilter` e `RedactionFilter` no handler;
       - define nível raiz `INFO`;
       - é idempotente (limpa handlers prévios antes de adicionar).
  4. Criar `backend/app/middleware/__init__.py` vazio (apenas garantir o pacote).
  5. Criar `backend/app/middleware/request_context.py` contendo a classe `RequestContextMiddleware(BaseHTTPMiddleware)` que:
     - lê `X-Request-ID` do header da requisição; se ausente, gera `uuid.uuid4().hex` (ou `str(uuid.uuid4())`);
     - executa `request_id_ctx.set(rid)` ANTES de `await call_next(request)`;
     - se `request.state` tiver `user_id`, executa `user_id_ctx.set(...)`;
     - cronometra `start = time.perf_counter()` antes da chamada e calcula `duration_ms = int((time.perf_counter() - start) * 1000)` depois;
     - emite UM log estruturado `INFO` ao final com extras: `request_id`, `route` (preferir `request.scope.get("route").path` ou `request.url.path` como fallback), `method`, `status_code`, `duration_ms`, `user_id`;
     - adiciona `response.headers["X-Request-ID"] = rid` antes de retornar a `response`;
     - se `call_next` levantar exceção, ainda assim faz log de saída com `status_code=500` e re-levanta (sem engolir).
  6. Não importar `main.py` em lugar nenhum destes módulos (evitar ciclos). Não tocar em `backend/app/main.py` nesta task — o wiring é da TASK-04.

- **Critérios de aceite (verificáveis):**
  - [ ] `pip install -r backend/requirements.txt` instala `python-json-logger==2.0.7` sem conflito.
  - [ ] `from app.config import settings; settings.env` retorna `"development"` por padrão e respeita `ENV=production` no ambiente.
  - [ ] `from app.logging_config import setup_logging, request_id_ctx, user_id_ctx, ContextFilter, RedactionFilter` importa sem erro.
  - [ ] Chamar `setup_logging("production")` faz o logger raiz emitir JSON com a chave `request_id` presente (valor pode ser `null`).
  - [ ] Chamar `setup_logging("development")` faz o logger emitir formato texto plano.
  - [ ] `RedactionFilter` aplicado a um `LogRecord` cujo `args` é `{"password": "abc"}` produz `{"password": "***"}` na saída final.
  - [ ] `RequestContextMiddleware` pode ser instanciado isoladamente em um `FastAPI()` mínimo (smoke check local) sem ImportError.
  - [ ] Nenhum arquivo fora da lista acima foi modificado.

---

#### TASK-02 — Hierarquia de exceções de domínio
- **ID:** TASK-02
- **Objetivo:** Criar o módulo `backend/app/exceptions.py` com a hierarquia tipada (`DomainError` e subclasses). Apenas a definição das classes — handlers FastAPI e refactor de chamadas vêm em tasks posteriores.
- **Dependências:** nenhuma
- **Pode rodar em paralelo com:** TASK-01
- **Requisitos atendidos:** RF-04; pré-requisito de RF-05, CA-05, CA-06, CA-07.

- **Arquivos afetados:**
  - `backend/app/exceptions.py` (criar)

- **Detalhamento técnico:**
  1. Criar `backend/app/exceptions.py` com a seguinte hierarquia (em Python puro, sem imports do FastAPI):
     ```
     class DomainError(Exception):
         http_status: int = 400
         def __init__(self, message: str, details: dict | None = None) -> None:
             super().__init__(message)
             self.message = message
             self.details = details or {}

     class NotFoundError(DomainError):        http_status = 404
     class ConflictError(DomainError):        http_status = 409
     class ValidationError(DomainError):      http_status = 422
     class AuthenticationError(DomainError):  http_status = 401
     class AuthorizationError(DomainError):   http_status = 403
     ```
  2. Garantir que cada subclasse herde apenas de `DomainError` e que `http_status` seja atributo de classe sobrescrito.
  3. Adicionar docstrings curtas explicando quando cada classe deve ser lançada (exemplos: `NotFoundError("contato")`, `ConflictError("email já existe")`).
  4. Exportar via `__all__ = ["DomainError", "NotFoundError", "ConflictError", "ValidationError", "AuthenticationError", "AuthorizationError"]`.
  5. NÃO importar FastAPI, NÃO usar `HTTPException` aqui. O módulo deve permanecer agnóstico de framework.
  6. NÃO editar `main.py` nem qualquer router/service nesta task.

- **Critérios de aceite:**
  - [ ] `from app.exceptions import DomainError, NotFoundError, ConflictError, ValidationError, AuthenticationError, AuthorizationError` funciona.
  - [ ] `NotFoundError("contato").http_status == 404`.
  - [ ] `ConflictError("dup", {"campo": "email"}).details == {"campo": "email"}`.
  - [ ] `isinstance(NotFoundError("x"), DomainError) is True`.
  - [ ] `python -c "import app.exceptions"` não importa FastAPI (módulo agnóstico).
  - [ ] Nenhum outro arquivo do repositório foi modificado.

---

### Fase 2 — Integração

> Depende de TASK-01 e TASK-02. TASK-03 cria os handlers; TASK-04 faz o wiring no `main.py` e remove o `except Exception: pass`. **TASK-03 e TASK-04 NÃO são paralelizáveis** entre si — TASK-04 importa o módulo criado em TASK-03.

---

#### TASK-03 — Exception handlers globais (uso conjunto de logger + exceções)
- **ID:** TASK-03
- **Objetivo:** Implementar os handlers globais do FastAPI que convertem cada classe da hierarquia em uma resposta HTTP semanticamente correta, registrando o evento no logger estruturado com `request_id` do contexto.
- **Dependências:** TASK-01, TASK-02
- **Pode rodar em paralelo com:** nenhuma
- **Requisitos atendidos:** RF-05; pré-requisito de CA-05, CA-06, CA-07, CA-08.

- **Arquivos afetados:**
  - `backend/app/exception_handlers.py` (criar)

- **Detalhamento técnico:**
  1. Criar `backend/app/exception_handlers.py` exportando uma função `register_exception_handlers(app: FastAPI) -> None`.
  2. A função registra handlers para:
     - `NotFoundError` -> 404
     - `ConflictError` -> 409
     - `ValidationError` (a de domínio, não a do Pydantic) -> 422
     - `AuthenticationError` -> 401
     - `AuthorizationError` -> 403
     - `DomainError` (fallback) -> 400
     - `Exception` (fallback geral) -> 500 com payload genérico `{"detail": "Erro interno do servidor."}`
  3. Cada handler de exceção de domínio:
     - lê `get_request_id()` do `logging_config`;
     - faz `logger.warning(...)` para 4xx e `logger.error(..., exc_info=True)` para `DomainError` genérico e para `Exception`;
     - retorna `JSONResponse(status_code=exc.http_status, content={"detail": exc.message, **({"details": exc.details} if exc.details else {})})` para subclasses; para `DomainError` genérico, status 400; para `Exception`, payload fixo sem stack trace ao cliente.
  4. Nunca incluir `traceback` no payload retornado ao cliente. O stack trace só vai para o log via `exc_info=True`.
  5. Definir `logger = logging.getLogger(__name__)` no topo do arquivo.
  6. NÃO chamar `app.add_exception_handler` neste módulo direto — apenas dentro da função `register_exception_handlers`.
  7. Não tocar em `main.py` (wiring é TASK-04).

- **Critérios de aceite:**
  - [ ] `from app.exception_handlers import register_exception_handlers` funciona.
  - [ ] Em um `FastAPI()` de teste, após `register_exception_handlers(app)`, uma rota que faça `raise NotFoundError("x")` responde HTTP 404 com `{"detail": "x"}`.
  - [ ] Idem para `ConflictError` -> 409, `AuthenticationError` -> 401, `AuthorizationError` -> 403, `ValidationError` (de domínio) -> 422.
  - [ ] Uma rota que faça `raise RuntimeError("boom")` responde 500 com `{"detail": "Erro interno do servidor."}` e nenhum traceback no body.
  - [ ] O log emitido em caso de `Exception` contém o stack trace (chamada com `exc_info=True`).

---

#### TASK-04 — Wiring no `main.py`, ativação do middleware e remoção do `except Exception: pass`
- **ID:** TASK-04
- **Objetivo:** Plugar `setup_logging`, `RequestContextMiddleware` e `register_exception_handlers` no `app` em `backend/app/main.py`. Substituir o `except Exception: pass` (linha ~36) por tratamento explícito que loga em `WARNING` e não engole silenciosamente.
- **Dependências:** TASK-01, TASK-02, TASK-03
- **Pode rodar em paralelo com:** nenhuma
- **Requisitos atendidos:** RF-02, RF-03, RF-05, RF-06; pré-requisito de CA-01, CA-02, CA-03, CA-04, CA-09.

- **Arquivos afetados:**
  - `backend/app/main.py` (editar)

- **Detalhamento técnico:**
  1. No topo de `backend/app/main.py`, antes de instanciar `FastAPI(...)`:
     - `from app.config import settings`
     - `from app.logging_config import setup_logging`
     - chamar `setup_logging(settings.env)`
     - `logger = logging.getLogger(__name__)`
  2. Após a criação do `app`, antes do `add_middleware(CORSMiddleware, ...)`, adicionar:
     - `from app.middleware.request_context import RequestContextMiddleware`
     - `app.add_middleware(RequestContextMiddleware)`
     - Ordem importa: `RequestContextMiddleware` deve ser o **mais externo** (adicionado por último em ordem de `add_middleware`, pois FastAPI executa LIFO) para envolver TODO o ciclo. Documentar com comentário inline.
  3. Importar e chamar `register_exception_handlers(app)` após os routers serem incluídos.
  4. Tratar o `except Exception: retry_after = 60` (linha ~36 dentro de `rate_limit_handler`): substituir por `except (AttributeError, TypeError) as exc:` + `logger.warning("não foi possível calcular retry_after: %s", exc)`. Manter `retry_after = 60` como fallback. O comportamento HTTP visível permanece idêntico.
     - **Atenção:** o PRD referencia o `except Exception: pass` em `main.py:36`. No código atual existe `except Exception: retry_after = 60` nessa região — não é `pass`, mas ainda assim engole o tipo da exceção. Tratar conforme RF-06: estreitar para exceções esperadas e logar. Se durante a execução for descoberto um `except Exception: pass` literal noutro ponto de `main.py`, eliminar do mesmo modo.
  5. Garantir que NENHUM `print(...)` exista em `main.py` após a edição (substituir por `logger.info/warning/error`).
  6. NÃO mudar contratos: rotas, status codes e payloads continuam idênticos.

- **Critérios de aceite:**
  - [ ] `grep -nR "except Exception: pass" backend/` retorna vazio (CA-09).
  - [ ] `grep -nR "except Exception:" backend/app/main.py` retorna vazio OU mostra apenas exceções estreitadas e logadas — NUNCA engolidas.
  - [ ] Subir o app em DEV (`ENV=development`) e bater em `/` produz log em formato texto com `request_id`, `route=/`, `status_code=200`.
  - [ ] Subir o app com `ENV=production` e bater em `/` produz EXATAMENTE 1 linha JSON em stdout contendo `request_id`, `user_id`, `route`, `duration_ms`, `status_code`.
  - [ ] Requisição com header `X-Request-ID: abc-123` produz log com `request_id="abc-123"` e header de resposta `X-Request-ID: abc-123`.
  - [ ] Requisição sem `X-Request-ID` recebe header de resposta com UUID v4 válido.
  - [ ] Suíte de testes existente passa sem alterações.

---

### Fase 3 — Refactor seletivo e cobertura de testes

> TASK-05 toca código de routers/services. TASK-06 e TASK-07 criam arquivos de teste novos disjuntos. TASK-06 e TASK-07 podem rodar em paralelo entre si; ambas dependem da Fase 2.

---

#### TASK-05 — Refactor seletivo de `HTTPException` para exceções de domínio + logger nomeado nos módulos
- **ID:** TASK-05
- **Objetivo:** (a) Adicionar `logger = logging.getLogger(__name__)` em todos os módulos de `routers/` e `services/` e emitir logs nos pontos relevantes; (b) Substituir `HTTPException(status_code=404, ...)` por `NotFoundError(...)` e `HTTPException(status_code=409, ...)` por `ConflictError(...)` SOMENTE onde a semântica de domínio é clara (ex.: contato/usuário inexistente, email duplicado). Onde o status code resulta de uma regra técnica não-domínio (ex.: validação de query string `sort_by`), manter `HTTPException`.
- **Dependências:** TASK-04
- **Pode rodar em paralelo com:** nenhuma (toca múltiplos arquivos de routers/services em sequência, e testes da TASK-06 dependem deste refactor)
- **Requisitos atendidos:** RF-01, RF-07; pré-requisito de CA-12.

- **Arquivos afetados (editar):**
  - `backend/app/routers/contatos.py`
  - `backend/app/routers/usuarios.py`
  - `backend/app/routers/auth.py`
  - `backend/app/services/contato_service.py`
  - `backend/app/services/usuario_service.py`
  - Demais módulos em `backend/app/services/` que já existam (ex.: `_helpers.py` se aplicável) — adicionar logger nomeado, sem mudar comportamento.

- **Detalhamento técnico:**
  1. Em cada arquivo da lista, adicionar no topo:
     ```
     import logging
     logger = logging.getLogger(__name__)
     ```
  2. Identificar todo `raise HTTPException(status_code=404, detail="...")` cuja mensagem indique "não encontrado" e substituir por `raise NotFoundError(detail_message)`. Importar `from app.exceptions import NotFoundError, ConflictError` no topo.
  3. Identificar `raise HTTPException(status_code=409, ...)` em contexto de unicidade (ex.: email já cadastrado) e substituir por `ConflictError(...)`.
  4. **NÃO** substituir os `HTTPException(status_code=422, ...)` que validam `sort_by`/`sort_order` em `routers/contatos.py` (não é conceito de domínio). Manter.
  5. **NÃO** alterar o `rate_limit_handler` nem o handler de `RateLimitExceeded` (slowapi continua intacto).
  6. Adicionar pelo menos um `logger.info` em operações de criação/atualização/deleção em services (ex.: "contato criado id=%s") e `logger.warning` quando o service decide não-prosseguir por regra (ex.: tentativa de deletar inexistente). Nenhum log com payload bruto que contenha senha/token.
  7. Garantir que o comportamento HTTP visível **não muda**: a suíte regressiva precisa passar.
  8. Nenhum `print(...)` deve permanecer em qualquer arquivo editado.

- **Critérios de aceite:**
  - [ ] `grep -nR "^logger = logging.getLogger" backend/app/routers/ backend/app/services/` lista TODOS os arquivos `.py` desses diretórios.
  - [ ] `grep -nR "print(" backend/app/` retorna vazio (DoD).
  - [ ] Pelo menos UM `HTTPException(status_code=404, ...)` foi convertido para `NotFoundError(...)` em `routers/usuarios.py` (helper `_get_or_404`) ou em `routers/contatos.py`.
  - [ ] Pelo menos UM `HTTPException(status_code=409, ...)` foi convertido para `ConflictError(...)` (cadastro de email duplicado).
  - [ ] Suíte de testes regressivos (Fases 1, 3.1, 3.2) continua 100% verde sem qualquer alteração nos arquivos de teste existentes (CA-11).
  - [ ] Status code observável e payload de erro permanecem idênticos ao anterior (CA-12).

---

#### TASK-06 — Testes do middleware de request_id e dos exception handlers
- **ID:** TASK-06
- **Objetivo:** Cobrir com testes pytest o middleware `RequestContextMiddleware` (geração/propagação do `X-Request-ID`) e cada classe de exception handler.
- **Dependências:** TASK-05
- **Pode rodar em paralelo com:** TASK-07
- **Requisitos atendidos:** RNF-06; verificação direta de CA-03, CA-04, CA-05, CA-06, CA-07, CA-08.

- **Arquivos afetados (criar):**
  - `backend/tests/test_logging_middleware.py`
  - `backend/tests/test_exception_handlers.py`

- **Detalhamento técnico:**
  1. `test_logging_middleware.py`:
     - Usar `httpx.AsyncClient` ou `TestClient` contra o `app` real (ou um `FastAPI()` minimal montado com `RequestContextMiddleware` + uma rota dummy `/ping`).
     - Teste 1: GET sem header -> resposta tem `X-Request-ID` válido como UUID.
     - Teste 2: GET com `X-Request-ID: abc-123` -> resposta devolve o mesmo valor.
     - Teste 3 (async): a rota lê `request_id_ctx.get()` e retorna no body; o valor bate com o header de resposta.
     - Teste 4: o log emitido (capturado com `caplog`) contém `request_id`, `route`, `status_code`, `duration_ms`.
  2. `test_exception_handlers.py`:
     - Montar uma `FastAPI()` de teste, registrar `register_exception_handlers`, expor rotas dummy que façam `raise NotFoundError("x")`, `raise ConflictError("y")`, `raise ValidationError("z")`, `raise AuthenticationError("a")`, `raise AuthorizationError("b")`, `raise DomainError("c")`, `raise RuntimeError("boom")`.
     - Verificar status codes 404/409/422/401/403/400/500 respectivamente.
     - Verificar payload `{"detail": "..."}` consistente.
     - Para o caso `RuntimeError`, verificar que o body **não** contém o texto `"boom"` nem `"Traceback"`.
  3. NÃO modificar testes existentes. NÃO usar PANs ou dados sensíveis reais. Usar fixtures isoladas; se precisar de DB, usar SQLite in-memory de fixture já estabelecida pelo projeto.
  4. Marcar testes async com `@pytest.mark.asyncio` conforme já é prática do projeto.

- **Critérios de aceite:**
  - [ ] `pytest backend/tests/test_logging_middleware.py` passa 100%.
  - [ ] `pytest backend/tests/test_exception_handlers.py` passa 100%.
  - [ ] Cobre no mínimo 1 caso por classe da hierarquia de exceções + 1 caso para `Exception` não tratada.
  - [ ] Verifica explicitamente que header `X-Request-ID` é retornado.
  - [ ] Suíte total continua passando.

---

#### TASK-07 — Teste de redaction de dados sensíveis em logs
- **ID:** TASK-07
- **Objetivo:** Garantir via teste automatizado que o `RedactionFilter` mascara `password`/`senha`/`token`/etc. antes da serialização (atende CA-10).
- **Dependências:** TASK-05
- **Pode rodar em paralelo com:** TASK-06
- **Requisitos atendidos:** RF-08, RNF-04; verificação direta de CA-10.

- **Arquivos afetados (criar):**
  - `backend/tests/test_log_redaction.py`

- **Detalhamento técnico:**
  1. Importar `ContextFilter`, `RedactionFilter`, `setup_logging` de `app.logging_config`.
  2. Teste unitário 1: instanciar `RedactionFilter`, construir um `LogRecord` cujo `args` é `{"password": "minha-senha", "user": "joao"}` e cujo `msg` é `"login=%s"`. Após `filter.filter(record)`, o `record.args["password"]` deve ser `"***"` e `record.args["user"]` permanece `"joao"`.
  3. Teste unitário 2: validar mascaramento em estrutura aninhada (`{"data": {"token": "abc"}}` -> `{"data": {"token": "***"}}`).
  4. Teste de integração: usando `caplog`, fazer uma requisição POST a um endpoint de autenticação com body `{"email": "x@y.com", "password": "segredo123"}`. Validar que NENHUMA linha de log capturada contém a string literal `"segredo123"`.
  5. Não logar valores reais de senha em fixtures. Usar strings curtas claramente sintéticas (`"segredo123"`, nunca senha real de um humano).
  6. NÃO incluir PAN, CVV ou dado de cartão — escopo deste projeto não é CDE.

- **Critérios de aceite:**
  - [ ] `pytest backend/tests/test_log_redaction.py` passa 100%.
  - [ ] Cobre pelo menos as chaves `password`, `senha`, `token`, `authorization`.
  - [ ] Cobre caso de estrutura aninhada.
  - [ ] Em nenhum log capturado durante o teste aparece a string clara da senha.

---

### Fase 4 — Refinamento / DoD

---

#### TASK-08 — Documentação operacional e validação final de DoD
- **ID:** TASK-08
- **Objetivo:** Criar `docs/OPERACAO_LOGS.md` instruindo como ler logs em DEV e em PROD; executar varredura final de `print()`, `except Exception: pass` e medir impacto de latência (RNF-01) com a suíte existente.
- **Dependências:** TASK-04, TASK-05, TASK-06, TASK-07
- **Pode rodar em paralelo com:** nenhuma
- **Requisitos atendidos:** RNF-01, RNF-05; DoD final.

- **Arquivos afetados:**
  - `docs/OPERACAO_LOGS.md` (criar)

- **Detalhamento técnico:**
  1. `docs/OPERACAO_LOGS.md` deve conter:
     - Como rodar o backend em DEV e ver logs em texto plano.
     - Como rodar em PROD (`ENV=production`) e ver JSON em stdout.
     - Tabela de campos do log JSON: `timestamp`, `level`, `logger`, `message`, `request_id`, `user_id`, `route`, `duration_ms`, `status_code`.
     - Exemplo de log de sucesso (200) e de erro (500) anonimizados.
     - Instrução sobre `X-Request-ID`: como o cliente pode enviar para correlacionar e como o servidor sempre devolve no header.
     - Lista de chaves redactadas (`password`, `senha`, `token`, `access_token`, `refresh_token`, `authorization`, `secret`).
     - Nota: Sentry / agregadores externos NÃO fazem parte desta fase.
  2. Executar localmente: `grep -nR "print(" backend/app/` deve retornar vazio.
  3. Executar localmente: `grep -nR "except Exception: pass" backend/` deve retornar vazio.
  4. Rodar a suíte completa de testes do backend e validar que está 100% verde.
  5. Anotar em commit/PR (não em arquivo versionado) a comparação p50/p95 da suíte antes/depois (RNF-01: p50 +5ms e p95 +15ms no máximo). Se exceder, abrir investigação antes de mergear.

- **Critérios de aceite:**
  - [ ] `docs/OPERACAO_LOGS.md` existe e cobre os tópicos acima.
  - [ ] `grep -nR "print(" backend/app/` vazio.
  - [ ] `grep -nR "except Exception: pass" backend/` vazio.
  - [ ] Suíte completa de testes passa.
  - [ ] Linter `bandit` (já no `requirements.txt`) não introduz novas findings de severidade >= MEDIUM.
  - [ ] DoD do PRD (seção 9) inteiramente checado.

---

## Matriz de Paralelização

| Task | Depende de | Paraleliza com | Arquivos exclusivos? |
|------|------------|----------------|----------------------|
| TASK-01 | nenhuma | **TASK-02** | Sim — `requirements.txt`, `config.py`, `logging_config.py`, `middleware/*` |
| TASK-02 | nenhuma | **TASK-01** | Sim — apenas `exceptions.py` |
| TASK-03 | TASK-01, TASK-02 | nenhuma | Sim — apenas `exception_handlers.py` |
| TASK-04 | TASK-01, TASK-02, TASK-03 | nenhuma | Edita `main.py` |
| TASK-05 | TASK-04 | nenhuma | Edita routers + services |
| TASK-06 | TASK-05 | **TASK-07** | Sim — `tests/test_logging_middleware.py`, `tests/test_exception_handlers.py` |
| TASK-07 | TASK-05 | **TASK-06** | Sim — `tests/test_log_redaction.py` |
| TASK-08 | TASK-04..07 | nenhuma | Sim — `docs/OPERACAO_LOGS.md` |

### Pares paralelizáveis (orquestrador deve disparar em 2 DEVs)
- **Fase 1:** TASK-01 e TASK-02 (arranque do trabalho)
- **Fase 3:** TASK-06 e TASK-07 (cobertura de testes)

---

## Resumo executivo
- **Total de tasks:** 8
- **Tasks paralelizáveis no arranque (Fase 1):** TASK-01 (B.1 — infra de logging + middleware) e TASK-02 (B.2 — exceções de domínio)
- **Tasks paralelizáveis adicionais (Fase 3):** TASK-06 e TASK-07
- **Escopo coberto:** somente B.1 + B.2 do roadmap v2, conforme PRD
- **Itens explicitamente fora de escopo:** B.3 (Sentry), B.4 (audit log persistente), B.5 (healthchecks), qualquer alteração no `frontend/`
