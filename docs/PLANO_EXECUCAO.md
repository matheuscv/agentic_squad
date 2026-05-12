# Plano de Execução — Manutenção de Contatos de Clientes

## Stack Confirmada

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Pytest + httpx
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, lucide-react
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
│       │   └── contatos/
│       │       └── page.tsx
│       ├── components/
│       │   ├── ContatoTable.tsx
│       │   ├── ContatoForm.tsx
│       │   └── UnsavedChangesModal.tsx
│       └── hooks/
│           └── useBeforeUnload.ts
└── backend/
    └── app/
        ├── routers/
        │   ├── contatos.py
        │   └── usuarios.py
        └── schemas/
            ├── contato.py
            └── usuario.py
```

---

## Fases

### Fase 1 — Backend Puro (sem dependências entre si)

> Alterações exclusivas no backend. As duas tasks não compartilham arquivos e podem ser executadas simultaneamente por dois DEVs distintos.

---

- **TASK-01** [paralelo: ✅ com TASK-02] — Backend: Ordenação de colunas em GET /contatos/

  - **Arquivos a modificar**:
    - `backend/app/routers/contatos.py`

  - **Requisitos atendidos**: RF-F2-01

  - **Descrição**:

    O endpoint `GET /contatos/` já aceita `skip`, `limit` e `busca`. Adicionar suporte a ordenação por coluna.

    1. **`backend/app/routers/contatos.py`**:

       a. Adicionar dois parâmetros de query à função do endpoint:
          - `sort_by: str = "nome"` — valores permitidos: `nome`, `email`, `empresa`, `criado_em`
          - `sort_order: str = "asc"` — valores permitidos: `asc`, `desc`

       b. Validar os parâmetros logo no início da função. Se `sort_by` não estiver na lista de valores permitidos ou `sort_order` não for `asc`/`desc`, levantar `HTTPException(status_code=422, detail="<mensagem descritiva>")`.

       c. Construir um dicionário de mapeamento de `sort_by` para a coluna SQLAlchemy correspondente no model `Contato` (ex.: `{"nome": Contato.nome, "email": Contato.email, ...}`).

       d. Aplicar `.order_by(coluna.asc())` ou `.order_by(coluna.desc())` na query do SQLAlchemy, **antes** do `.offset(skip).limit(limit)`. A ordenação deve ocorrer no banco de dados, nunca em memória (RN-F2-01).

       e. Repassar `sort_by` e `sort_order` ao service `listar_contatos` se a lógica de query estiver no service; caso a query esteja no router, aplicar diretamente ali.

  - **Critério de pronto**:
    - `GET /contatos/?sort_by=nome&sort_order=asc` retorna contatos em ordem alfabética crescente por nome
    - `GET /contatos/?sort_by=empresa&sort_order=desc` retorna contatos em ordem decrescente por empresa
    - `GET /contatos/?sort_by=campo_invalido` retorna HTTP 422 com mensagem legível
    - `GET /contatos/` sem parâmetros de ordenação retorna resultados ordenados por `nome ASC` (padrão)
    - Testes Pytest existentes continuam passando; nenhuma quebra de contrato na resposta

---

- **TASK-02** [paralelo: ✅ com TASK-01] — Backend: CRUD completo de usuários

  - **Arquivos a criar/modificar**:
    - `backend/app/routers/usuarios.py` (modificar — adicionar endpoints)
    - `backend/app/schemas/usuario.py` (modificar — adicionar schemas de resposta e atualização)

  - **Requisitos atendidos**: RF-F2-02

  - **Descrição**:

    O router `/usuarios/` pode já ter o endpoint de criação (POST /usuarios/). Esta task adiciona os endpoints restantes de CRUD.

    1. **`backend/app/schemas/usuario.py`** — Adicionar os seguintes schemas Pydantic v2:

       a. `UsuarioResposta` — schema de resposta público (sem senha):
          - Campos: `id: int`, `nome: str`, `email: str`, `role: str`, `criado_em: datetime`
          - Configurar `model_config = ConfigDict(from_attributes=True)`

       b. `UsuarioAtualizacao` — schema de entrada para PUT:
          - Campos opcionais: `nome: str | None = None`, `email: str | None = None`
          - Validar que `email`, quando fornecido, é formato de e-mail válido

       c. `RoleAtualizacao` — schema de entrada para PATCH /role:
          - Campo: `role: str` — deve aceitar apenas `"default"` ou `"adm"` (usar `Literal` ou validador)

    2. **`backend/app/routers/usuarios.py`** — Implementar os endpoints abaixo, todos com `Depends(get_current_user)`:

       a. `GET /usuarios/` — listar todos os usuários:
          - Requer role `adm`; retornar HTTP 403 se role for `default`
          - Retornar lista de `UsuarioResposta` (sem campo senha)

       b. `GET /usuarios/{id}` — detalhar um usuário:
          - Permitido para role `adm` ou para o próprio usuário autenticado (`current_user.id == id`)
          - Retornar HTTP 404 se o ID não existir
          - Retornar HTTP 403 se usuário `default` tentar acessar outro usuário

       c. `PUT /usuarios/{id}` — atualizar nome e/ou email:
          - Permitido para role `adm` ou para o próprio usuário autenticado
          - Validar unicidade do e-mail: se o novo e-mail já pertence a outro usuário, retornar HTTP 400 com mensagem de e-mail duplicado
          - Retornar HTTP 404 se o ID não existir
          - Retornar o registro atualizado como `UsuarioResposta`

       d. `DELETE /usuarios/{id}` — remover um usuário:
          - Requer role `adm`
          - Retornar HTTP 400 se `id == current_user.id` (admin não pode excluir a si mesmo — RN-F2-02)
          - Retornar HTTP 404 se o ID não existir
          - Retornar HTTP 200 com mensagem de confirmação

       e. `PATCH /usuarios/{id}/role` — alterar a role de um usuário:
          - Requer role `adm`
          - Retornar HTTP 400 se `id == current_user.id` (admin não pode rebaixar a si mesmo — RN-F2-02)
          - Retornar HTTP 404 se o ID não existir
          - Aceitar body do tipo `RoleAtualizacao`
          - Retornar o registro atualizado como `UsuarioResposta`

       Regra transversal: **nenhum endpoint deve retornar o campo `senha` (hash ou plain) no payload de resposta.**

  - **Critério de pronto**:
    - `GET /usuarios/` com token de usuário `adm` retorna lista sem campo `senha`
    - `GET /usuarios/` com token de usuário `default` retorna HTTP 403
    - `GET /usuarios/{id}` com ID inexistente retorna HTTP 404
    - `PUT /usuarios/{id}` com e-mail já em uso retorna HTTP 400 ou 422 com mensagem de duplicidade
    - `DELETE /usuarios/{id}` onde `id` é o próprio admin retorna HTTP 400
    - `PATCH /usuarios/{id}/role` executado por usuário `default` retorna HTTP 403
    - `PATCH /usuarios/{id}/role` onde `id` é o próprio admin retorna HTTP 400
    - Todos os endpoints retornam HTTP 401 para requisições sem token válido

---

### Fase 2 — Frontend Independente (sem dependência de backend novo)

> Tasks puramente de frontend que não dependem das alterações de backend da Fase 1. Editam arquivos completamente distintos e podem ser executadas em paralelo.

---

- **TASK-03** [paralelo: ✅ com TASK-04] — Frontend: Ícones nos botões de ação dos contatos

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoTable.tsx`
    - `frontend/src/components/ContatoForm.tsx`

  - **Requisitos atendidos**: RF-F2-04

  - **Descrição**:

    Substituir textos puros dos botões de ação por combinação de ícone + texto usando `lucide-react`. A biblioteca `lucide-react` já é dependência do projeto (shadcn/ui a utiliza); não é necessário instalar.

    1. **`frontend/src/components/ContatoTable.tsx`**:

       a. Importar `Pencil` e `Trash2` de `lucide-react`.

       b. Botão "Editar": substituir o texto puro por:
          ```tsx
          <Pencil size={16} aria-hidden="true" />
          <span>Editar</span>
          ```
          Envolver em `className="flex items-center gap-1"` no botão.

       c. Botão "Excluir": substituir o texto puro por:
          ```tsx
          <Trash2 size={16} aria-hidden="true" />
          <span>Excluir</span>
          ```

       d. Verificar se há botão "Novo Contato" neste componente; se sim, aplicar `UserPlus` + texto.

    2. **`frontend/src/components/ContatoForm.tsx`**:

       a. Importar `Save` e `X` de `lucide-react`. Se houver botão "Novo Contato", importar também `UserPlus`.

       b. Botão "Salvar": substituir por `<Save size={16} aria-hidden="true" /> <span>Salvar</span>`.

       c. Botão "Cancelar": substituir por `<X size={16} aria-hidden="true" /> <span>Cancelar</span>`.

       d. Se a `Navbar` tiver botão de logout neste arquivo, aplicar `LogOut`; caso contrário, ignorar (a Navbar é um arquivo separado).

    Regra: todos os ícones devem ter `aria-hidden="true"`. O texto adjacente deve permanecer sempre visível — nunca usar `sr-only` no texto nem substituir o label por tooltip (RN-F2-04).

  - **Critério de pronto**:
    - Botão "Editar" exibe ícone `Pencil` à esquerda do texto "Editar"
    - Botão "Excluir" exibe ícone `Trash2` à esquerda do texto "Excluir"
    - Botão "Salvar" exibe ícone `Save` à esquerda do texto "Salvar"
    - Botão "Cancelar" exibe ícone `X` à esquerda do texto "Cancelar"
    - Todos os ícones possuem `aria-hidden="true"` no DOM
    - O texto dos botões permanece visível (não está em `sr-only`)
    - `npx tsc --noEmit` sem erros de tipagem

---

- **TASK-04** [paralelo: ✅ com TASK-03] — Frontend: Mensagem de lista vazia contextual em ContatoTable

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoTable.tsx`

  - **Requisitos atendidos**: RF-F2-05

  - **Descrição**:

    O componente `ContatoTable.tsx` atualmente exibe uma mensagem genérica quando a lista está vazia. Esta task a substitui por duas variantes contextuais.

    O componente já recebe (ou deve receber via props) o termo de busca ativo e o total de registros. Verificar as props atuais e adicionar as que faltarem.

    1. **`frontend/src/components/ContatoTable.tsx`**:

       a. Garantir que o componente receba as props:
          - `termoBusca: string` — valor atual do campo de pesquisa
          - `total: number` — total de registros retornados pelo backend
          - `userRole: string` — role do usuário logado (`"adm"` ou `"default"`)

       b. Na seção de renderização da lista vazia (quando `contatos.length === 0`), substituir a mensagem genérica pela lógica:

          ```tsx
          if (termoBusca.trim() !== "") {
            // Estado: busca ativa sem resultados
            return (
              <div className="text-center text-muted-foreground py-8">
                Nenhum resultado para "{termoBusca}".
              </div>
            )
          } else {
            // Estado: banco vazio, sem busca
            return (
              <div className="text-center text-muted-foreground py-8">
                <p>Nenhum contato cadastrado ainda.</p>
                {userRole === "adm" && (
                  <button /* ou <Link href="/contatos/novo"> */>
                    Cadastrar primeiro contato
                  </button>
                )}
              </div>
            )
          }
          ```

       c. Remover completamente qualquer ocorrência da string `"Nenhum contato encontrado"` do componente.

       d. Atualizar a chamada de `<ContatoTable>` em `frontend/src/app/contatos/page.tsx` para passar as novas props `termoBusca`, `total` e `userRole`, se ainda não estiverem sendo passadas.

    Nota: `frontend/src/app/contatos/page.tsx` pode precisar de alteração mínima apenas para passar as novas props. Se isso conflitar com TASK-06 (que também edita `page.tsx`), coordenar a ordem de merge.

  - **Critério de pronto**:
    - Com busca ativa e sem resultados, a mensagem contém o termo pesquisado entre aspas
    - Com banco vazio e sem busca, a mensagem é exatamente "Nenhum contato cadastrado ainda."
    - Com banco vazio e sem busca, usuário `adm` vê link/botão "Cadastrar primeiro contato"
    - Com banco vazio e sem busca, usuário `default` não vê o botão de cadastro
    - A string "Nenhum contato encontrado" não aparece em nenhum estado da interface
    - `npx tsc --noEmit` sem erros de tipagem

---

### Fase 3 — Frontend com Dependência ou Integração

> Tasks de frontend que dependem de backend novo (TASK-01) ou que integram múltiplas partes. Executar após as Fases 1 e 2.

---

- **TASK-05** [paralelo: ✅ com TASK-06] — Frontend: Ordenação de colunas com ícones na tabela de contatos

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoTable.tsx`
    - `frontend/src/app/contatos/page.tsx`

  - **Requisitos atendidos**: RF-F2-01

  - **Dependências**: TASK-01 (backend deve aceitar `sort_by`/`sort_order` antes de ativar no frontend)

  - **Descrição**:

    1. **`frontend/src/app/contatos/page.tsx`**:

       a. Adicionar dois estados de ordenação:
          ```typescript
          const [sortBy, setSortBy] = useState<string>("nome")
          const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc")
          ```

       b. Atualizar a função de chamada ao service `listarContatos` para incluir `sort_by` e `sort_order` na query string.

       c. Implementar a função `handleSort(coluna: string)`:
          - Se `coluna !== sortBy`: setar `sortBy = coluna` e `sortOrder = "asc"`
          - Se `coluna === sortBy && sortOrder === "asc"`: setar `sortOrder = "desc"`
          - Se `coluna === sortBy && sortOrder === "desc"`: resetar para `sortBy = "nome"`, `sortOrder = "asc"` (terceiro clique remove ordenação)
          - Resetar `paginaAtual` para 1 após qualquer mudança de ordenação

       d. Ao alterar o filtro de busca, além de resetar a página, resetar também `sortBy = "nome"` e `sortOrder = "asc"` (RF-F2-01, critério de aceite).

       e. Passar as props `sortBy`, `sortOrder` e `onSort={handleSort}` para `<ContatoTable>`.

    2. **`frontend/src/components/ContatoTable.tsx`**:

       a. Adicionar props:
          ```typescript
          sortBy: string
          sortOrder: "asc" | "desc"
          onSort: (coluna: string) => void
          ```

       b. Importar `ArrowUp`, `ArrowDown`, `ArrowUpDown` de `lucide-react`.

       c. Para as colunas ordenáveis (`Nome`, `Email`, `Empresa`, `Data`), transformar o header em elemento clicável (`<button>` ou `<th onClick>`):
          - Exibir o ícone correspondente ao estado:
            - Coluna inativa (não é a `sortBy` atual): `<ArrowUpDown size={14} />`
            - Coluna ativa com `sortOrder === "asc"`: `<ArrowUp size={14} />`
            - Coluna ativa com `sortOrder === "desc"`: `<ArrowDown size={14} />`
          - O mapeamento entre label de coluna e valor de `sort_by` da API:
            - "Nome" → `"nome"`, "Email" → `"email"`, "Empresa" → `"empresa"`, "Data" → `"criado_em"`

  - **Critério de pronto**:
    - Clicar no header "Nome" uma vez: seta para cima, ordena ASC via API
    - Clicar novamente em "Nome": seta para baixo, ordena DESC via API
    - Clicar uma terceira vez em "Nome": volta ao padrão `nome ASC`, ícone neutro
    - Colunas sem ordenação ativa exibem ícone `ArrowUpDown`
    - Alterar o filtro de busca reseta a ordenação para o padrão
    - `npx tsc --noEmit` sem erros de tipagem

---

- **TASK-06** [paralelo: ✅ com TASK-05] — Frontend: Máscara e validação de telefone no formulário de contato

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoForm.tsx`

  - **Requisitos atendidos**: RF-F2-03

  - **Descrição**:

    O campo `telefone` em `ContatoForm.tsx` atualmente é um `<input type="text">` sem máscara. Esta task adiciona máscara de entrada e validação client-side.

    1. Instalar a dependência de máscara. Usar `react-input-mask` versão compatível com React 18 ou alternativa como `react-phone-input-2`. Verificar compatibilidade antes de escolher. Comando sugerido:
       ```
       npm install react-input-mask @types/react-input-mask
       ```

    2. **`frontend/src/components/ContatoForm.tsx`**:

       a. Importar `InputMask` de `react-input-mask`.

       b. Substituir o `<input>` do campo telefone por `<InputMask>` com máscara dinâmica:
          - Máscara celular: `"(99) 99999-9999"` (11 dígitos)
          - Máscara fixo: `"(99) 9999-9999"` (10 dígitos)
          - Estratégia recomendada: iniciar com máscara de celular `(99) 99999-9999` e ajustar dinamicamente ao 5º dígito do número (se o 9º caractere digitado for `-`, é fixo). Alternativamente, usar máscara `(99) 9{4,5}-9999` se a biblioteca suportar. Consultar a documentação da biblioteca escolhida.

       c. Adicionar validação de formato no `onBlur` ou no `onChange` do campo:
          - Aceitar: `/^\(\d{2}\) \d{5}-\d{4}$/` (celular) ou `/^\(\d{2}\) \d{4}-\d{4}$/` (fixo)
          - Se o valor não corresponder a nenhum dos dois e não estiver vazio, exibir mensagem de erro em PT-BR abaixo do campo: `"Formato inválido. Use (99) 99999-9999 ou (99) 9999-9999."`
          - Se o campo estiver vazio, não exibir erro (campo é opcional — RN-F2-03)

       d. O campo deve ser resetado corretamente quando o formulário for submetido com sucesso ou cancelado.

  - **Critério de pronto**:
    - Digitar `(11) 98765-4321` é aceito sem erro
    - Digitar `(11) 3456-7890` é aceito sem erro
    - Digitar `11987654321` (sem máscara) exibe mensagem de erro antes de submeter
    - Submeter formulário com campo telefone vazio é aceito
    - A máscara formata automaticamente a entrada enquanto o usuário digita
    - `npx tsc --noEmit` sem erros de tipagem

---

### Fase 4 — Frontend Complexo (dependência de estado global e router)

> Task que requer implementação de hook customizado, modal e integração com o Next.js App Router. Executar após as fases anteriores para evitar conflitos em `ContatoForm.tsx`.

---

- **TASK-07** [paralelo: ❌] — Frontend: Alerta ao sair de formulário sem salvar

  - **Arquivos a criar**:
    - `frontend/src/hooks/useBeforeUnload.ts`
    - `frontend/src/components/UnsavedChangesModal.tsx`

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoForm.tsx`

  - **Requisitos atendidos**: RF-F2-06

  - **Descrição**:

    Implementar a detecção de "estado sujo" (formulário modificado mas não salvo) e os dois mecanismos de alerta: evento nativo do navegador (`beforeunload`) e modal customizado para navegação interna via Next.js Router.

    1. **`frontend/src/hooks/useBeforeUnload.ts`** — Criar hook customizado:

       ```typescript
       // Assinatura esperada:
       export function useBeforeUnload(isDirty: boolean): void
       ```

       - Quando `isDirty === true`, adicionar listener para o evento `beforeunload` na `window` que chama `event.preventDefault()` e seta `event.returnValue = ""` (padrão para acionar o diálogo nativo).
       - Quando `isDirty === false`, remover o listener.
       - Limpar o listener no retorno do `useEffect` (cleanup).

    2. **`frontend/src/components/UnsavedChangesModal.tsx`** — Criar modal de confirmação:

       Props esperadas:
       ```typescript
       interface UnsavedChangesModalProps {
         isOpen: boolean
         onContinue: () => void   // "Continuar editando" — fecha o modal
         onLeave: () => void      // "Sair sem salvar" — navega para destino
       }
       ```

       - Usar componente de Dialog do shadcn/ui (`@/components/ui/dialog`) para o modal.
       - Texto do modal em PT-BR:
         - Título: "Sair sem salvar?"
         - Corpo: "Você tem alterações não salvas. Se sair agora, elas serão perdidas."
         - Botão primário: "Continuar editando" → chama `onContinue`
         - Botão secundário: "Sair sem salvar" → chama `onLeave`

    3. **`frontend/src/components/ContatoForm.tsx`** — Integrar os mecanismos:

       a. Calcular `isDirty`: comparar o valor atual de cada campo com os valores originais (do momento em que o formulário foi aberto ou recebeu os dados via props). Se qualquer campo diferir, `isDirty = true`.

       b. Chamar `useBeforeUnload(isDirty)` para interceptar fechamento/reload de aba.

       c. Para navegação interna: o Next.js 14 App Router não expõe `router.events`. Usar a abordagem de interceptar cliques em links internos via:
          - Hook customizado que monitora `window.history.pushState` e `popstate`, ou
          - Envolver os links/botões de navegação no formulário para chamar uma função de guarda antes de navegar.
          - Manter um estado `pendingNavigation: string | null` com a rota destino pretendida.
          - Quando `isDirty === true` e o usuário tenta navegar, setar `pendingNavigation` e abrir o modal.
          - `onContinue`: fechar modal, limpar `pendingNavigation`.
          - `onLeave`: limpar `isDirty`, executar `router.push(pendingNavigation)`.

       d. Após submissão bem-sucedida do formulário: limpar `isDirty` antes de qualquer navegação programática.

       e. Ao clicar no botão "Cancelar" do formulário sem ter alterado nenhum campo (`isDirty === false`): navegar diretamente, sem abrir o modal (RN-F2-06).

       f. Ao clicar no botão "Cancelar" com `isDirty === true`: abrir o modal de confirmação.

  - **Critério de pronto**:
    - Modificar qualquer campo e tentar fechar a aba: navegador exibe diálogo nativo de saída
    - Modificar qualquer campo e clicar em link de navegação interna: modal customizado é exibido
    - "Continuar editando" no modal fecha o modal e mantém os dados preenchidos
    - "Sair sem salvar" navega para a rota destino sem salvar
    - Após salvar com sucesso, navegar para outra rota não exibe nenhum alerta
    - Clicar em "Cancelar" sem ter modificado nenhum campo não exibe modal
    - `npx tsc --noEmit` sem erros de tipagem

---

## Resumo de Paralelismo

| Task    | Fase | Pode rodar em paralelo com | Dependências externas          |
|---------|------|---------------------------|-------------------------------|
| TASK-01 | 1    | TASK-02                   | nenhuma                       |
| TASK-02 | 1    | TASK-01                   | nenhuma                       |
| TASK-03 | 2    | TASK-04                   | nenhuma                       |
| TASK-04 | 2    | TASK-03                   | nenhuma                       |
| TASK-05 | 3    | TASK-06                   | TASK-01 (backend ordenacao)   |
| TASK-06 | 3    | TASK-05                   | nenhuma (backend ja valida)   |
| TASK-07 | 4    | nenhuma                   | TASK-06 (mesmo ContatoForm)   |

> Grupos de paralelismo confirmados:
> - **Grupo A** (Fase 1): TASK-01 e TASK-02 — backend puro, arquivos disjuntos
> - **Grupo B** (Fase 2): TASK-03 e TASK-04 — frontend puro, arquivos disjuntos
> - **Grupo C** (Fase 3): TASK-05 e TASK-06 — frontend, arquivos disjuntos (TASK-05 toca `ContatoTable.tsx` + `page.tsx`; TASK-06 toca somente `ContatoForm.tsx`)

---

## Requisitos Cobertos

| Requisito  | Task    |
|------------|---------|
| RF-F2-01   | TASK-01, TASK-05 |
| RF-F2-02   | TASK-02 |
| RF-F2-03   | TASK-06 |
| RF-F2-04   | TASK-03 |
| RF-F2-05   | TASK-04 |
| RF-F2-06   | TASK-07 |

---

## Fase 3.1 — Qualidade e Segurança

> Tasks exclusivamente de backend. Podem ser executadas em paralelo (TASK-08 e TASK-09 não tocam nos mesmos arquivos; TASK-10 depende de TASK-09 pois altera o modelo e o service antes de escrever os testes que os cobrem).

---

- **TASK-08** [paralelo: ✅ com TASK-09] — Backend: PATCH /contatos/{id} (atualização parcial)

  - **Arquivos a criar/modificar**:
    - `backend/app/schemas/contato.py` (adicionar `ContatoPatch`)
    - `backend/app/routers/contatos.py` (adicionar endpoint `PATCH /{id}`)
    - `backend/app/services/contato_service.py` (adicionar função `patch_contato`)

  - **Requisitos atendidos**: RF-F3-02

  - **Descrição**:

    1. **`backend/app/schemas/contato.py`** — Adicionar schema `ContatoPatch`:
       - Todos os campos de `ContatoCriar` marcados como opcionais (`Optional[tipo] = None`):
         `nome`, `email`, `telefone`, `empresa`, `observacoes`
       - Adicionar validador de nível de model (`@model_validator(mode="after")`) que
         verifica se pelo menos um campo não é `None`; se todos forem `None`, levantar
         `ValueError("Nenhum campo fornecido para atualização.")` — resultará em HTTP 422.
       - Reutilizar o mesmo validador de `telefone` presente em `ContatoCriar`/`ContatoAtualizar`
         (regex `^\(\d{2}\) \d{4,5}-\d{4}$`).

    2. **`backend/app/services/contato_service.py`** — Adicionar função `patch_contato`:
       - Assinatura: `def patch_contato(db: Session, id: int, dados: ContatoPatch) -> Contato`
       - Buscar o contato com `buscar_contato(db, id)` (levanta 404 se ausente).
       - Iterar pelos campos não-`None` do schema e aplicar via `setattr`.
       - Validar unicidade de e-mail se `dados.email is not None` (HTTP 400 se conflito).
       - Atualizar `atualizado_em` com `datetime.now(timezone.utc)`.
       - Commitar e retornar o registro atualizado.

    3. **`backend/app/routers/contatos.py`** — Adicionar endpoint:
       ```python
       @router.patch("/{id}", response_model=ContatoResposta)
       def patch(
           id: int,
           dados: ContatoPatch,
           db: Session = Depends(get_db),
           _usuario=Depends(require_adm),
       ):
           """Atualiza parcialmente um contato (restrito a administradores)."""
           return contato_service.patch_contato(db, id, dados)
       ```

  - **Critério de pronto**:
    - `PATCH /contatos/{id}` com `{"telefone": "(11) 99999-9999"}` retorna 200 e altera só o telefone
    - `PATCH /contatos/{id}` com body `{}` retorna 422 com mensagem de campo ausente
    - `PATCH /contatos/{id}` com e-mail duplicado retorna 400
    - `PATCH /contatos/{id}` com ID inexistente retorna 404
    - `PATCH /contatos/{id}` com role `default` retorna 403
    - `PATCH /contatos/{id}` sem token retorna 401

---

- **TASK-09** [paralelo: ✅ com TASK-08] — Backend: Soft delete + lixeira de contatos

  - **Arquivos a criar/modificar**:
    - `backend/app/models/contato.py` (adicionar campo `deletado_em`)
    - `backend/app/schemas/contato.py` (atualizar `ContatoResposta` com `deletado_em`)
    - `backend/app/services/contato_service.py` (alterar `excluir_contato`; adicionar `listar_lixeira`)
    - `backend/app/routers/contatos.py` (alterar `DELETE /{id}`; adicionar `GET /lixeira`)
    - `backend/alembic/versions/<hash>_add_deletado_em.py` (nova migration)

  - **Requisitos atendidos**: RF-F3-03

  - **Descrição**:

    1. **`backend/app/models/contato.py`** — Adicionar campo:
       ```python
       deletado_em: Mapped[datetime | None] = mapped_column(
           DateTime, nullable=True, default=None
       )
       ```

    2. **`backend/app/schemas/contato.py`** — Adicionar campo em `ContatoResposta`:
       ```python
       deletado_em: datetime | None = None
       ```

    3. **Migration Alembic** — Gerar com:
       ```
       alembic revision --autogenerate -m "add_deletado_em_to_contatos"
       ```
       Revisar o arquivo gerado para garantir que é `ADD COLUMN deletado_em DATETIME NULL DEFAULT NULL`
       sem operações destrutivas. Rodar `alembic upgrade head` para confirmar.

    4. **`backend/app/services/contato_service.py`**:

       a. Alterar `listar_contatos`: adicionar filtro `where(Contato.deletado_em == None)` na
          `stmt_base` antes de qualquer outra cláusula — garante que lixeira não vaza nas consultas normais.

       b. Alterar `buscar_contato`: adicionar `where(Contato.deletado_em == None)` para que
          contatos deletados retornem 404.

       c. Alterar `excluir_contato`: substituir `db.delete(contato)` por:
          ```python
          contato.deletado_em = datetime.now(timezone.utc)
          db.commit()
          ```

       d. Adicionar `listar_lixeira`:
          ```python
          def listar_lixeira(
              db: Session,
              skip: int = 0,
              limit: int = 20,
          ) -> tuple[list[Contato], int]:
          ```
          - Filtrar `Contato.deletado_em != None`
          - Ordenar por `Contato.deletado_em.desc()`
          - Retornar tupla `(items, total)` no mesmo padrão de `listar_contatos`

    5. **`backend/app/routers/contatos.py`**:

       a. Adicionar endpoint `GET /lixeira` **antes** de `GET /{id}` (FastAPI resolve rotas por ordem):
          ```python
          @router.get("/lixeira", response_model=ContatoListResponse)
          def lixeira(
              skip: int = 0,
              limit: int = 20,
              db: Session = Depends(get_db),
              _usuario=Depends(require_adm),
          ):
              items, total = contato_service.listar_lixeira(db, skip=skip, limit=limit)
              return ContatoListResponse(items=items, total=total)
          ```

       b. O endpoint `DELETE /{id}` já chama `contato_service.excluir_contato` — nenhuma
          alteração necessária no router após o service ser atualizado.

  - **Critério de pronto**:
    - `DELETE /contatos/{id}` retorna 204 e contato some de `GET /contatos/`
    - `GET /contatos/{id}` após soft delete retorna 404
    - `GET /contatos/lixeira` com token `adm` lista o contato deletado com `deletado_em` preenchido
    - `GET /contatos/lixeira` com token `default` retorna 403
    - `GET /contatos/lixeira` sem token retorna 401
    - `alembic upgrade head` roda sem erro; `alembic downgrade -1` também

---

- **TASK-10** [paralelo: ❌ — depende de TASK-08 e TASK-09] — Backend: Implementar 22 testes (cobertura ≥ 80%)

  - **Arquivos a criar**:
    - `backend/tests/test_auth.py`
    - `backend/tests/test_contatos.py`
    - `backend/tests/test_services.py`

  - **Arquivos a complementar** (se necessário):
    - `backend/tests/test_usuarios_crud.py` (casos de borda adicionais, se cobertura ainda baixa)

  - **Requisitos atendidos**: RF-F3-01

  - **Fixtures disponíveis (conftest.py)**:
    - `client` — TestClient do FastAPI
    - `db_session` — sessão de banco de dados em memória (SQLite)
    - `usuario_adm_token` — token JWT de usuário com role `adm`
    - `usuario_default_token` — token JWT de usuário com role `default`
    - `usuario_adm_dados` / `usuario_default_dados` — dicts com dados dos usuários das fixtures

  - **Descrição dos grupos de testes**:

    1. **`test_auth.py`** (≥ 5 testes):
       - `test_login_bem_sucedido` — POST /auth/token com credenciais válidas retorna 200 e `access_token`
       - `test_login_senha_incorreta` — POST /auth/token com senha errada retorna 401
       - `test_login_email_inexistente` — POST /auth/token com e-mail não cadastrado retorna 401
       - `test_cadastro_email_duplicado` — POST /usuarios/ com e-mail já existente retorna 400 ou 422
       - `test_cadastro_senha_curta` — POST /usuarios/ com senha < 6 chars retorna 422
       - `test_token_invalido_retorna_401` — GET /contatos/ com token malformado retorna 401

    2. **`test_contatos.py`** (≥ 10 testes — cobrir PATCH e soft delete):
       - CRUD básico: criar, listar, buscar por id, atualizar (PUT), deletar (soft)
       - PATCH parcial: só telefone, só e-mail, body vazio (422), e-mail duplicado (400)
       - Lixeira: contato deletado aparece em `/lixeira`, some de `/contatos/`
       - Controle de acesso: `default` não pode criar/patch/delete (403)

    3. **`test_services.py`** (≥ 5 testes unitários — sem HTTP):
       - `test_criar_contato_service` — chama `criar_contato` direto, verifica retorno
       - `test_criar_contato_email_duplicado_service` — levanta HTTPException 400
       - `test_buscar_contato_inexistente_service` — levanta HTTPException 404
       - `test_patch_contato_service` — atualiza campo parcialmente
       - `test_excluir_contato_soft_delete_service` — verifica que `deletado_em` é preenchido
       - `test_listar_lixeira_service` — verifica que só retorna contatos com `deletado_em != None`

  - **Critério de pronto**:
    - `pytest --cov=app --cov-report=term-missing -q` reporta cobertura ≥ 80% sem falhas
    - `pytest -x` passa todos os testes (zero falhas, zero erros)
    - Nenhum teste usa mock de banco real, sleep ou chamadas externas

---

## Resumo de Paralelismo — Fase 3.1

| Task    | Fase | Pode rodar em paralelo com | Dependências         |
|---------|------|---------------------------|----------------------|
| TASK-08 | 3.1  | TASK-09                   | nenhuma              |
| TASK-09 | 3.1  | TASK-08                   | nenhuma              |
| TASK-10 | 3.1  | nenhuma                   | TASK-08 e TASK-09    |

---

## Requisitos Cobertos — Fase 3.1

| Requisito | Task    |
|-----------|---------|
| RF-F3-01  | TASK-10 |
| RF-F3-02  | TASK-08 |
| RF-F3-03  | TASK-09 |
