# Operação de Logs — Backend

> **Escopo desta entrega:** Fases B.1 (Logging estruturado JSON) e B.2 (Tratamento centralizado de exceções). Este documento descreve como o backend FastAPI emite logs em diferentes ambientes, como correlacionar requisições e quais campos são automaticamente mascarados.

---

## 1. Visão geral

### Objetivo

Padronizar a forma como o backend FastAPI emite registros operacionais para que:

- toda requisição seja rastreável de ponta a ponta por um `request_id`;
- toda exceção produza uma resposta HTTP semanticamente correta, registrando o stack trace **apenas no log** (nunca no corpo da resposta);
- chaves sensíveis (senhas, tokens, headers de autorização) sejam mascaradas antes da serialização do log.

### Modos suportados

O formato de saída é controlado pela variável de ambiente `ENV` (lida em `backend/app/config.py` e propagada a `setup_logging` no startup do `main.py`):

| Valor de `ENV`               | Formato de saída            | Destino | Caso de uso típico                          |
|------------------------------|-----------------------------|---------|---------------------------------------------|
| `development` (default)      | Texto plano legível         | stdout  | Desenvolvimento local, debugging interativo |
| `production`                 | JSON estruturado (uma linha por evento) | stdout  | Ambientes produtivos e coleta por agregadores |

Qualquer valor diferente de `production` é tratado como modo desenvolvimento. O setup é **idempotente**: chamar `setup_logging` mais de uma vez não duplica handlers.

---

## 2. Como rodar em DEV

Configuração mínima (variável de ambiente não setada -> default `development`):

```bash
# .env (raiz do backend) ou export direto
ENV=development

# Subir a API
cd backend
uvicorn app.main:app --reload --port 8000
```

Saída esperada no console (formato texto plano):

```
2026-05-19 14:23:11,402 INFO app.middleware.request_context GET /contatos 200 12ms
2026-05-19 14:23:11,403 INFO app.services.contato_service contato criado id=42
```

Observações:

- O formatter ativo é `logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")`.
- `request_id` e `user_id` continuam sendo injetados via `ContextFilter`, mas em DEV não aparecem na string formatada — eles são acessíveis programaticamente via `get_request_id()` / `get_user_id()` em `app.logging_config`.
- Use este modo apenas localmente. Não exporte logs de DEV para sistemas de produção.

---

## 3. Como rodar em PROD

Configuração mínima:

```bash
ENV=production
# Subir a API (idealmente atrás de um gateway/ingress)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Saída esperada no stdout (uma linha JSON por evento):

```json
{"asctime": "2026-05-19 14:23:11,402", "levelname": "INFO", "name": "app.middleware.request_context", "message": "request completed", "request_id": "8f1c2d3e4b5a6789a1b2c3d4e5f60718", "user_id": "user-001", "route": "/contatos", "duration_ms": 12}
```

Observações:

- O formatter ativo é `pythonjsonlogger.jsonlogger.JsonFormatter` com o template:
  `"%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(route)s %(duration_ms)s"`.
- Cada requisição emite **exatamente uma linha** de log no encerramento (no middleware `RequestContextMiddleware`), além de logs adicionais que os serviços/handlers possam ter emitido durante a execução.
- Os campos `route`, `duration_ms` e `status_code` são adicionados via `extra=` no log call do middleware.
- Stdout é o transporte oficial — qualquer coletor (Docker, Kubernetes, systemd-journald) é responsável por encaminhar para o destino final.

---

## 4. Tabela de campos do log JSON

Em modo `production` cada linha de log é um objeto JSON com os seguintes campos canônicos:

| Campo         | Tipo            | Origem                                         | Descrição                                                                 |
|---------------|-----------------|------------------------------------------------|---------------------------------------------------------------------------|
| `timestamp`   | string (ISO-ish)| `%(asctime)s`                                  | Data/hora local do evento, no formato `YYYY-MM-DD HH:MM:SS,ms`. (No template atual surge como `asctime` — agregadores devem mapeá-lo para `timestamp`.) |
| `level`       | string          | `%(levelname)s`                                | Severidade: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. (Aparece como `levelname` no JSON.) |
| `logger`      | string          | `%(name)s`                                     | Nome do logger emissor (módulo Python), ex.: `app.routers.contatos`. (Aparece como `name`.) |
| `message`     | string          | `%(message)s`                                  | Mensagem livre do evento, já interpolada.                                 |
| `request_id`  | string \| null  | `ContextFilter` (lê `request_id_ctx`)          | Identificador único da requisição. Quando não há contexto ativo (ex.: log de startup), vem `null`. |
| `user_id`     | string \| null  | `ContextFilter` (lê `user_id_ctx`)             | Identificador do usuário autenticado, quando disponível.                  |
| `route`       | string \| null  | `extra=` do middleware                          | Caminho da rota (`request.scope.route.path` ou `request.url.path`).       |
| `duration_ms` | inteiro \| null | `extra=` do middleware                          | Duração total do processamento da requisição em milissegundos.            |
| `status_code` | inteiro \| null | `extra=` do middleware                          | Status HTTP final retornado (ou `500` quando a requisição abortou por exceção não tratada). |

> Notas operacionais: os campos `request_id`, `user_id`, `route` e `duration_ms` estão declarados no template do `JsonFormatter` e por isso aparecem sempre, mesmo quando o valor é `null`. `status_code` é passado via `extra=` no log de saída do middleware.

---

## 5. Exemplo de log de sucesso (HTTP 200)

Linha emitida pelo middleware ao final de um `GET /contatos/42` bem-sucedido:

```json
{
  "asctime": "2026-05-19 14:23:11,402",
  "levelname": "INFO",
  "name": "app.middleware.request_context",
  "message": "request completed",
  "request_id": "8f1c2d3e4b5a6789a1b2c3d4e5f60718",
  "user_id": "user-001",
  "route": "/contatos/{contato_id}",
  "duration_ms": 12,
  "status_code": 200
}
```

Características:

- Valor de `request_id` foi gerado pelo servidor (cliente não enviou header) e é o mesmo retornado em `X-Request-ID`.
- Nenhuma chave sensível (`password`, `token`, etc.) está presente — o `RedactionFilter` garante isso automaticamente caso fossem incluídas em `extra=`.
- Os dados de domínio (id de contato, payload) não aparecem aqui — quem os emite são os loggers nomeados dos services em logs separados (ex.: `app.services.contato_service`).

---

## 6. Exemplo de log de erro (HTTP 500)

Quando uma exceção não tratada (`Exception`/`RuntimeError`) escapa do handler de uma rota, o handler global em `app.exception_handlers` emite o log com `exc_info=True` e o middleware fecha o ciclo com `status_code=500`.

Resposta entregue ao cliente (body — **sem** stack trace):

```json
{ "detail": "Erro interno do servidor." }
```

Log correspondente no servidor (anonimizado):

```json
{
  "asctime": "2026-05-19 14:23:11,510",
  "levelname": "ERROR",
  "name": "app.exception_handlers",
  "message": "unhandled exception during request",
  "request_id": "8f1c2d3e4b5a6789a1b2c3d4e5f60718",
  "user_id": "user-001",
  "route": "/contatos",
  "duration_ms": null,
  "status_code": 500,
  "exc_info": "Traceback (most recent call last):\n  File \"/app/backend/app/routers/contatos.py\", line 88, in listar\n    ...\nRuntimeError: boom"
}
```

Pontos críticos:

- **O stack trace vive apenas no log**, no campo `exc_info` (gerado pelo `logging` ao chamar com `exc_info=True`). O body retornado ao cliente é fixo: `{"detail": "Erro interno do servidor."}`.
- Para os erros de domínio (`NotFoundError`, `ConflictError`, etc.), o handler usa `logger.warning(...)` (4xx) e o body devolve `{"detail": "<message>"}` com o status semântico correto — **sem** stack trace.
- O `request_id` é o mesmo em todos os eventos da mesma requisição: este é o pivot oficial de correlação.

---

## 7. Correlação via `X-Request-ID`

Toda requisição atravessa o `RequestContextMiddleware`, que orquestra o ciclo de vida do `request_id`:

1. **Cliente envia `X-Request-ID`**: o valor recebido é usado como `request_id` para todo o log dessa requisição e devolvido inalterado no header `X-Request-ID` da resposta.
2. **Cliente não envia `X-Request-ID`**: o servidor gera um UUID v4 (`uuid.uuid4().hex`) e o devolve no header `X-Request-ID` da resposta.

Exemplos:

```bash
# Caso 1: cliente envia seu próprio correlation id
curl -i -H "X-Request-ID: pedido-7e9d" http://localhost:8000/contatos
# Resposta inclui: X-Request-ID: pedido-7e9d
# Logs do servidor: request_id="pedido-7e9d"

# Caso 2: cliente não envia
curl -i http://localhost:8000/contatos
# Resposta inclui: X-Request-ID: 8f1c2d3e4b5a6789a1b2c3d4e5f60718  (gerado pelo servidor)
# Logs do servidor: request_id="8f1c2d3e4b5a6789a1b2c3d4e5f60718"
```

Boas práticas para o consumidor:

- Reaproveite o mesmo `X-Request-ID` em toda a cadeia de chamadas associadas a uma operação de negócio para correlacionar logs multi-serviço.
- Trate o `request_id` como **opaco**: não codifique informação sensível dentro dele.
- Em caso de erro, capture o `X-Request-ID` da resposta e envie-o ao suporte — é a chave de busca canônica nos logs.

---

## 8. Lista de chaves redactadas

O `RedactionFilter` (em `backend/app/logging_config.py`) mascara o **valor** de qualquer chave cujo nome bata, **case-insensitive**, com a lista abaixo. O valor mascarado é a string literal `"***"`.

| Chave             | Cobre tipicamente                                              |
|-------------------|----------------------------------------------------------------|
| `password`        | Campos `password` em payloads de login/cadastro                |
| `senha`           | Variante em português                                          |
| `token`           | Tokens genéricos (api, sessão, csrf, etc.)                     |
| `access_token`    | Access tokens OAuth2/JWT                                       |
| `refresh_token`   | Refresh tokens OAuth2/JWT                                      |
| `authorization`   | Conteúdo de header `Authorization` (Bearer, Basic, etc.)       |
| `secret`          | Segredos genéricos (`client_secret`, `app_secret`, etc.)       |

Regras de aplicação:

- **Recursão**: a varredura desce em `dict`, `list` e `tuple`. Estruturas aninhadas como `{"data": {"token": "abc"}}` viram `{"data": {"token": "***"}}`.
- **Comparação case-insensitive**: `PASSWORD`, `Password`, `password` são tratados igualmente.
- **Cobertura no LogRecord**: o filtro atua sobre `record.msg` (quando é dict), sobre `record.args` (dict, list ou tuple) e sobre extras promovidos ao record (ex.: `logger.info("x", extra={"token": "..."})`).
- **Strings cruas não são parseadas**: o filtro **não** tenta detectar `key=value` em strings livres. O contrato é que dados estruturados venham em dict/args. Se o desenvolvedor concatenar o segredo no `message`, ele vai vazar — o controle correto é sempre passar dados via `extra=` ou via `args`.

> Para adicionar novas chaves sensíveis, edite `_SENSITIVE_KEYS` em `backend/app/logging_config.py`. A mudança é declarativa e cobre automaticamente os três pontos (msg, args, extras).

---

## 9. Fora de escopo desta entrega

Os itens abaixo **não** fazem parte das fases B.1 e B.2 e devem ser tratados em fases posteriores do roadmap:

- **Sentry / APM externos**: não há integração com Sentry, Datadog, New Relic ou similares nesta entrega. Os logs continuam apenas em stdout.
- **Agregadores externos** (ELK, Loki, CloudWatch, etc.): a configuração de coleta/forward fica a cargo da plataforma de runtime; o backend não conhece o destino final.
- **Audit log persistente em banco** (fase B.4): trilha de auditoria de domínio gravada em tabela é fora de escopo aqui.
- **Healthchecks operacionais** (fase B.5): liveness/readiness probes formalizados ficam para fase futura.
- **Métricas/Prometheus**: emissão de métricas (counters, histogramas) é assunto separado da observabilidade por log.

Qualquer evolução nestes pontos deve passar por novo PRD e plano de execução próprios.
