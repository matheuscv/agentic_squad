# 🤖 Squad de Agentes — Pipeline PO → LT → DEVs → QA

Projeto didático que demonstra uma squad de desenvolvimento **100%
composta por agentes de IA**, usando os **subagents do Claude Code**.

A partir de uma ideia em linguagem natural, a squad entrega:
PRD → Plano de Execução → Código → Testes Unitários.

---

## 🧩 A squad

| Agente       | Papel              | Entrega                                  |
|--------------|--------------------|------------------------------------------|
| `po-agent`   | Product Owner      | `docs/PRD.md`                            |
| `lt-agent`   | Lead Tech          | `docs/PLANO_EXECUCAO.md` (faseado)       |
| `dev-agent`  | Dev (×2 isolados)  | Código em `src/`                         |
| `qa-agent`   | QA                 | Testes em `tests/`                       |

> Os 2 DEVs rodam **sequencialmente mas isolados**: cada um recebe
> contexto próprio e enxerga **apenas a sua task**.

---

## 📂 Estrutura

```
squad-agentes/
├── PROMPT_ORQUESTRADOR.md      ← O prompt que você cola no Claude Code
├── README.md                   ← Este arquivo
├── .claude/
│   └── agents/
│       ├── po-agent.md         ← Product Owner
│       ├── lt-agent.md         ← Lead Tech
│       ├── dev-agent.md        ← Developer (instanciado 2×)
│       └── qa-agent.md         ← QA Engineer
├── docs/                       ← Gerado pela squad em runtime
│   ├── PRD.md
│   └── PLANO_EXECUCAO.md
├── src/                        ← Gerado pelos DEVs
└── tests/                      ← Gerado pelo QA
```

---

## 🚀 Como usar

### 1. Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado
- Este projeto clonado/baixado localmente

### 2. Rodar

```bash
cd squad-agentes
claude
```

### 3. No chat do Claude Code

Abra `PROMPT_ORQUESTRADOR.md`, copie o prompt de dentro do bloco
` ``` `, troque `<<COLE AQUI A IDEIA...>>` pela sua ideia, e cole no chat.

**Exemplo de ideia:**

> "Uma API REST simples para gerenciar uma lista de tarefas, com
> endpoints para criar, listar, marcar como concluída e remover
> tarefas. Persistência em memória basta."

A partir daí o orquestrador vai delegar, em sequência, para
`po-agent` → `lt-agent` → `dev-agent` (×2) → `qa-agent`,
validando cada entrega.

---

## 🔄 Fluxo visual

```
   Usuário
     │
     ▼  (ideia em texto livre)
 ┌─────────┐
 │ po-agent│ ──► docs/PRD.md
 └─────────┘
     │
     ▼
 ┌─────────┐
 │ lt-agent│ ──► docs/PLANO_EXECUCAO.md
 └─────────┘
     │
     ├──► dev-agent (TASK-01) ──► src/...
     │
     └──► dev-agent (TASK-02) ──► src/...
                   │
                   ▼
              ┌─────────┐
              │ qa-agent│ ──► tests/...
              └─────────┘
                   │
                   ▼
            Relatório Final
```

---

## 🎓 O que este projeto ensina

- Como definir **subagents** no Claude Code com frontmatter YAML
- Como dar a cada agente **um único papel** (princípio da
  responsabilidade única)
- Como **isolar contexto** entre agentes para evitar contaminação
  (cada DEV só conhece a SUA task)
- Como usar um **agente orquestrador** que apenas delega, sem
  executar trabalho
- Como **versionar entregas intermediárias** (PRD, Plano) como
  artefatos auditáveis em disco

---

## 🛠️ Customizações fáceis

- **Mais DEVs?** Basta o `lt-agent` gerar mais tasks paralelizáveis
  e o orquestrador chamar `dev-agent` N vezes
- **Adicionar DevOps?** Crie `.claude/agents/devops-agent.md` no
  mesmo padrão e adicione uma FASE 5 no orquestrador
- **Trocar QA por testes E2E?** Edite `qa-agent.md` mudando o
  framework e a estratégia de testes

---

## ⚠️ Limitações

- Os DEVs rodam **sequencialmente** (não paralelamente de verdade) —
  é a forma mais simples e segura no Claude Code hoje
- Não há ciclo de retrabalho automático se o QA encontrar bugs —
  isso seria uma evolução natural do projeto (rodar PO/LT de novo
  com o relatório de bugs)
