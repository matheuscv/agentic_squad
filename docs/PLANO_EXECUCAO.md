# Plano de Execução — Manutenção de Contatos de Clientes

## Stack Confirmada

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Pytest + httpx
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Banco de dados**: SQLite (arquivo local)
- **Autenticação**: JWT (Bearer token)
- **Portas**: frontend :3000 | backend :8000

---

## Estrutura de Diretórios

```
projeto/
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   └── contatos/
│       │       └── page.tsx
│       └── components/
│           ├── Navbar.tsx
│           └── ContatoTable.tsx
└── backend/
    └── app/
        ├── routers/
        │   └── contatos.py
        └── schemas/
            └── contato.py
```

---

## Fases

### Fase 1 — Correções Imediatas (Fase 1 do PRD)

> Três correções de baixa complexidade que eliminam bloqueadores de usabilidade identificados no MVP entregue.
> Requisitos atendidos: RF-F1-01, RF-F1-02, RF-F1-03, RF-F1-04, RF-F1-05, RF-F1-06

---

- **TASK-01** [paralelo: ❌] — Backend: Paginação no endpoint GET /contatos/

  - **Arquivos a modificar**:
    - `backend/app/routers/contatos.py`
    - `backend/app/schemas/contato.py`

  - **Requisitos atendidos**: RF-F1-03

  - **Descrição**:

    1. **`backend/app/schemas/contato.py`** — Adicionar o schema de resposta paginada:
       - Criar a classe `ContatoListResponse` com dois campos:
         - `items: list[ContatoResposta]` — registros da página atual
         - `total: int` — contagem total de registros que atendem ao filtro de busca

    2. **`backend/app/routers/contatos.py`** — Atualizar o endpoint `GET /contatos/`:
       - Adicionar os parâmetros de query: `skip: int = 0` e `limit: int = 20`
       - Validar que `limit` não ultrapasse 200 (máximo permitido conforme RN-F1-01). Se `limit > 200`, usar 200.
       - Alterar a chamada ao service `listar_contatos` para repassar `skip` e `limit`.
       - Alterar o tipo de retorno do endpoint para `ContatoListResponse`.
       - A resposta deve conter:
         - `total`: resultado de `SELECT COUNT(*)` com o mesmo filtro de `busca`
         - `items`: resultado paginado com `OFFSET skip LIMIT limit`
       - O service `contato_service.listar_contatos` deve ser atualizado para aceitar `skip` e `limit` e retornar a tupla `(items, total)`.

  - **Critério de pronto**:
    - `GET /contatos/?skip=0&limit=20` retorna JSON com a estrutura `{"items": [...], "total": N}`
    - `GET /contatos/` sem parâmetros usa defaults `skip=0`, `limit=20`
    - `GET /contatos/?skip=0&limit=200` retorna até 200 registros
    - `GET /contatos/?skip=0&limit=999` retorna no máximo 200 registros (limite forçado)
    - O campo `total` reflete a contagem total com o filtro de busca aplicado (não apenas o tamanho de `items`)

---

- **TASK-02** [paralelo: ✅ com TASK-03] — Frontend: Navbar no layout com renderização condicional

  - **Arquivos a modificar**:
    - `frontend/src/app/layout.tsx`

  - **Requisitos atendidos**: RF-F1-01, RF-F1-02

  - **Descrição**:

    O componente `Navbar.tsx` já existe em `frontend/src/components/Navbar.tsx` mas não está incluído no layout global. Nesta task, inclua-o com renderização condicional.

    1. **`frontend/src/app/layout.tsx`** — Fazer as seguintes alterações:
       - Importar o componente `<Navbar />` de `@/components/Navbar`
       - Importar o hook `usePathname` do `next/navigation` (ou equivalente para App Router)
       - Criar uma lógica que verifica se a rota atual é `/login` ou `/cadastro`
       - Renderizar `<Navbar />` **somente** quando a rota atual não for `/login` nem `/cadastro`
       - O `<Navbar />` deve ser posicionado acima do `{children}` no JSX
       - Como o `layout.tsx` é um Server Component por padrão no Next.js 14, pode ser necessário extrair a lógica condicional para um Client Component separado (ex.: `NavbarWrapper.tsx` com `'use client'`). Avaliar e implementar a abordagem correta.

    **Observação**: Não alterar o componente `Navbar.tsx` em si — apenas incluí-lo no layout.

  - **Critério de pronto**:
    - Acessar `/contatos` exibe a Navbar com nome do usuário e botão de logout
    - Acessar `/login` não exibe a Navbar
    - Acessar `/cadastro` não exibe a Navbar
    - `npx tsc --noEmit` sem erros de tipagem

---

- **TASK-03** [paralelo: ✅ com TASK-02] — Frontend: Toast tipado com estilos distintos para sucesso e erro

  - **Arquivos a modificar**:
    - `frontend/src/app/contatos/page.tsx`

  - **Requisitos atendidos**: RF-F1-05, RF-F1-06

  - **Descrição**:

    Atualmente o estado de toast em `contatos/page.tsx` não distingue visualmente sucesso de erro. Esta task adiciona o campo `tipo` ao estado e aplica estilos diferentes.

    1. **`frontend/src/app/contatos/page.tsx`** — Fazer as seguintes alterações:

       a. **Atualizar o tipo do estado de toast**: O estado deve passar a ter a forma:
          ```typescript
          { mensagem: string; tipo: 'sucesso' | 'erro' } | null
          ```
          Atualizar a declaração do `useState` e todos os locais que setam o toast.

       b. **Toast de sucesso** (tipo `'sucesso'`): manter o estilo verde atual. Exemplo de classes Tailwind: `bg-green-500 text-white`.

       c. **Toast de erro** (tipo `'erro'`): aplicar estilo vermelho/destrutivo, claramente diferenciado. Exemplo de classes Tailwind: `bg-red-600 text-white`.

       d. **Aplicar o tipo correto em todos os acionamentos**:
          - Operações bem-sucedidas (criação, atualização, exclusão de contato): usar `tipo: 'sucesso'`
          - Qualquer bloco `catch` ou resposta HTTP com status >= 400: usar `tipo: 'erro'`
          - Verificar **todos** os lugares onde o toast é acionado na página e garantir que nenhum cenário de erro use `tipo: 'sucesso'`

       e. **Renderização condicional do toast**: No JSX onde o toast é exibido, aplicar as classes Tailwind dinamicamente com base em `toast.tipo`:
          ```typescript
          toast.tipo === 'sucesso' ? 'bg-green-500 text-white' : 'bg-red-600 text-white'
          ```

  - **Critério de pronto**:
    - Após salvar um contato com sucesso, o toast exibe fundo verde
    - Após falha em salvar (ex.: e-mail duplicado, erro de rede), o toast exibe fundo vermelho
    - As duas variantes têm texto de cor legível (branco sobre verde / branco sobre vermelho)
    - Nenhum cenário de erro usa o estilo de toast de sucesso
    - `npx tsc --noEmit` sem erros de tipagem

---

- **TASK-04** [paralelo: ❌] — Frontend: Controles de paginação em ContatoTable e contatos/page.tsx

  - **Arquivos a modificar**:
    - `frontend/src/app/contatos/page.tsx`
    - `frontend/src/components/ContatoTable.tsx`

  - **Requisitos atendidos**: RF-F1-04

  - **Dependências de tasks**: TASK-01 (backend deve estar pronto para retornar `items` + `total`), TASK-03 (mesmos arquivos de page.tsx — executar após TASK-03)

  - **Descrição**:

    1. **`frontend/src/app/contatos/page.tsx`** — Adicionar estado e lógica de paginação:

       a. Adicionar estados:
          ```typescript
          const [paginaAtual, setPaginaAtual] = useState(1)
          const [totalRegistros, setTotalRegistros] = useState(0)
          const LIMITE = 20
          ```

       b. Atualizar a função que chama o service `listarContatos` para passar `skip` e `limit`:
          ```typescript
          skip: (paginaAtual - 1) * LIMITE,
          limit: LIMITE
          ```

       c. Ao receber a resposta, salvar `total` em `setTotalRegistros` e `items` na lista de contatos.

       d. **Reset de página ao buscar**: quando o usuário alterar o campo de pesquisa (filtro de busca), chamar `setPaginaAtual(1)` antes de disparar a requisição (conforme RN-F1-02).

       e. Passar as props de paginação para `<ContatoTable>`:
          - `paginaAtual`
          - `totalRegistros`
          - `limite={LIMITE}`
          - `onPaginaAnterior={() => setPaginaAtual(p => p - 1)}`
          - `onProximaPagina={() => setPaginaAtual(p => p + 1)}`

       f. Atualizar o service `listarContatos` em `frontend/src/services/contatos.service.ts` para aceitar os parâmetros `skip` e `limit` e incluí-los na query string da requisição.

    2. **`frontend/src/components/ContatoTable.tsx`** — Adicionar props e controles visuais de paginação:

       a. Adicionar ao tipo de props:
          ```typescript
          paginaAtual: number
          totalRegistros: number
          limite: number
          onPaginaAnterior: () => void
          onProximaPagina: () => void
          ```

       b. Calcular `totalPaginas = Math.ceil(totalRegistros / limite)`.

       c. Abaixo da tabela, renderizar a barra de paginação com:
          - Texto informativo: `"{inicio}–{fim} de {totalRegistros} contatos"` onde `inicio = (paginaAtual - 1) * limite + 1` e `fim = Math.min(paginaAtual * limite, totalRegistros)`
          - Botão "Anterior": desabilitado (`disabled`) quando `paginaAtual === 1`
          - Botão "Próxima": desabilitado (`disabled`) quando `paginaAtual >= totalPaginas`
          - Ambos os botões em PT-BR
          - Usar classes Tailwind para estilo; botões desabilitados devem ter aparência visual distinta (ex.: `opacity-50 cursor-not-allowed`)

  - **Critério de pronto**:
    - A interface exibe `"{inicio}–{fim} de {totalRegistros} contatos"` corretamente
    - Botão "Anterior" desabilitado na primeira página
    - Botão "Próxima" desabilitado na última página
    - Clicar "Próxima" carrega o próximo lote de 20 registros do backend
    - Clicar "Anterior" carrega o lote anterior
    - Alterar o filtro de busca reseta para a página 1
    - `npx tsc --noEmit` sem erros de tipagem

---

## Resumo de Paralelismo — Fase 1

| Task    | Pode rodar em paralelo com | Dependências           |
|---------|---------------------------|------------------------|
| TASK-01 | nenhuma (backend puro)    | nenhuma                |
| TASK-02 | TASK-03                   | nenhuma                |
| TASK-03 | TASK-02                   | nenhuma                |
| TASK-04 | nenhuma                   | TASK-01, TASK-03       |

> TASK-02 e TASK-03 são 100% frontend e independentes — editam arquivos distintos e podem ser executadas simultaneamente por dois DEVs diferentes.
> TASK-04 aguarda TASK-01 (contrato de API) e TASK-03 (edita o mesmo `contatos/page.tsx`).

## Requisitos Cobertos

| Requisito      | Task    |
|----------------|---------|
| RF-F1-01       | TASK-02 |
| RF-F1-02       | TASK-02 |
| RF-F1-03       | TASK-01 |
| RF-F1-04       | TASK-04 |
| RF-F1-05       | TASK-03 |
| RF-F1-06       | TASK-03 |
