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

---

## Fase 3.2 — Qualidade e Segurança (continuação)

> Tasks de backend (TASK-11 e TASK-12) são independentes entre si e podem rodar em paralelo. TASK-13 (frontend Zod) é independente de ambas e pode rodar em paralelo também.

---

- **TASK-11** [paralelo: ✅ com TASK-12, TASK-13] — Backend: Auditoria de criação/modificação em Contato

  - **Arquivos a criar/modificar**:
    - `backend/app/models/contato.py` (adicionar `criado_por_id`, `atualizado_por_id`)
    - `backend/app/schemas/contato.py` (expor campos em `ContatoResposta`)
    - `backend/app/services/contato_service.py` (popular campos de auditoria)
    - `backend/app/routers/contatos.py` (passar `current_user.id` ao service)
    - `backend/alembic/versions/<hash>_add_auditoria_contatos.py` (nova migration)

  - **Requisitos atendidos**: RF-F3.2-01

  - **Descrição**:

    1. **`backend/app/models/contato.py`** — Adicionar dois campos FK nullable:
       ```python
       criado_por_id: Mapped[int | None] = mapped_column(
           Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, default=None
       )
       atualizado_por_id: Mapped[int | None] = mapped_column(
           Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, default=None
       )
       ```
       Nota: SQLite aceita FK com `ON DELETE SET NULL` mas não as executa por padrão. Garantir que `PRAGMA foreign_keys = ON` está configurado na engine se a integridade for necessária. Para esta fase, nullable sem `ondelete` também é aceitável dado que soft delete já protege o dado.

    2. **`backend/app/schemas/contato.py`** — Adicionar em `ContatoResposta`:
       ```python
       criado_por_id: int | None = None
       atualizado_por_id: int | None = None
       ```

    3. **`backend/app/services/contato_service.py`**:

       a. Alterar a assinatura de `criar_contato` para receber `usuario_id: int`:
          - Setar `contato.criado_por_id = usuario_id` e `contato.atualizado_por_id = usuario_id` antes do commit.

       b. Alterar a assinatura de `atualizar_contato` (PUT) para receber `usuario_id: int`:
          - Setar `contato.atualizado_por_id = usuario_id` antes do commit.
          - Não tocar em `criado_por_id` (RN-F3.2-01).

       c. Alterar a assinatura de `patch_contato` (PATCH) para receber `usuario_id: int`:
          - Setar `contato.atualizado_por_id = usuario_id` antes do commit.
          - Não tocar em `criado_por_id`.

    4. **`backend/app/routers/contatos.py`** — Nos endpoints POST, PUT e PATCH:
       - Passar `usuario_id=current_user.id` nas chamadas ao service correspondente.
       - O parâmetro `current_user` já vem de `Depends(require_adm)`.

    5. **Migration Alembic** — Gerar com:
       ```
       alembic revision --autogenerate -m "add_auditoria_contatos"
       ```
       Revisar o arquivo gerado: deve conter apenas `ADD COLUMN criado_por_id INTEGER NULL` e `ADD COLUMN atualizado_por_id INTEGER NULL`, sem operações destrutivas. Rodar `alembic upgrade head` para confirmar.

  - **Critério de pronto**:
    - `POST /contatos/` retorna payload com `criado_por_id` igual ao `id` do usuário autenticado
    - `PUT /contatos/{id}` atualiza `atualizado_por_id`; `criado_por_id` permanece inalterado
    - `PATCH /contatos/{id}` atualiza `atualizado_por_id`; `criado_por_id` permanece inalterado
    - `alembic upgrade head` e `alembic downgrade -1` executam sem erro em banco existente
    - Contatos anteriores à migration ficam com `NULL` nos dois campos (sem erro)

---

- **TASK-12** [paralelo: ✅ com TASK-11, TASK-13] — Backend: Rate limiting no endpoint de login

  - **Arquivos a modificar**:
    - `backend/app/main.py` (configurar `slowapi`: Limiter, exception handler, middleware)
    - `backend/app/routers/auth.py` (aplicar decorator `@limiter.limit` no endpoint de login)
    - `backend/requirements.txt` (adicionar `slowapi`)

  - **Requisitos atendidos**: RF-F3.2-02

  - **Descrição**:

    1. **`backend/requirements.txt`** — Adicionar:
       ```
       slowapi>=0.1.9
       ```

    2. **`backend/app/main.py`** — Configurar o `slowapi`:

       a. Importar e instanciar o Limiter:
          ```python
          from slowapi import Limiter, _rate_limit_exceeded_handler
          from slowapi.util import get_remote_address
          from slowapi.errors import RateLimitExceeded

          limiter = Limiter(key_func=get_remote_address)
          ```

       b. Registrar no app FastAPI:
          ```python
          app.state.limiter = limiter
          app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
          ```
          Nota: o handler padrão do slowapi retorna 429 com mensagem em inglês. Substituir por handler customizado que retorna `{"detail": "Muitas tentativas. Tente novamente em 1 minuto."}` e inclui o header `Retry-After`.

       c. Handler customizado de 429:
          ```python
          from fastapi import Request
          from fastapi.responses import JSONResponse

          async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
              retry_after = exc.limit.reset_time - int(time.time()) if hasattr(exc, "limit") else 60
              return JSONResponse(
                  status_code=429,
                  content={"detail": "Muitas tentativas. Tente novamente em 1 minuto."},
                  headers={"Retry-After": str(max(retry_after, 1))},
              )

          app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
          ```

    3. **`backend/app/routers/auth.py`** — Aplicar o limite no endpoint de login:

       a. Importar o `limiter` do `main.py` (ou de um módulo compartilhado `app/limiter.py` para evitar import circular):
          ```python
          from app.limiter import limiter  # módulo dedicado, se necessário
          ```

       b. Adicionar o decorator antes do endpoint:
          ```python
          @router.post("/login")  # ou "/token" — conforme path atual
          @limiter.limit("5/minute")
          async def login(request: Request, ...):
              ...
          ```
          Nota: o `slowapi` exige que `request: Request` seja o primeiro parâmetro da função do endpoint para extrair o IP.

       c. Se o path atual não for `/auth/login` mas `/auth/token`, aplicar no path correto. Verificar o router existente antes de editar.

    4. **Isolamento em testes** — Para evitar que os testes de autenticação sejam bloqueados pelo rate limiter:
       - Criar fixture no `conftest.py` que reseta o storage do limiter antes de cada teste, ou
       - Usar variável de ambiente `RATELIMIT_ENABLED=false` verificada na inicialização do Limiter (ex.: `Limiter(key_func=get_remote_address, enabled=os.getenv("RATELIMIT_ENABLED", "true") == "true")`).

  - **Critério de pronto**:
    - 5 requisições consecutivas ao endpoint de login são processadas (retornam 200 ou 401, nunca 429)
    - A 6ª requisição dentro de 1 minuto retorna HTTP 429
    - Body da resposta 429: `{"detail": "Muitas tentativas. Tente novamente em 1 minuto."}`
    - Header `Retry-After` presente na resposta 429
    - `GET /contatos/` não é afetado pelo rate limiter (nenhum 429 em uso normal)
    - Testes de autenticação existentes passam sem acionar 429

---

- **TASK-13** [paralelo: ✅ com TASK-11, TASK-12] — Frontend: Validação com Zod em todos os formulários

  - **Arquivos a criar**:
    - `frontend/src/lib/schemas.ts`

  - **Arquivos a modificar**:
    - `frontend/src/app/login/page.tsx` (ou equivalente — formulário de login)
    - `frontend/src/app/cadastro/page.tsx` (ou equivalente — formulário de cadastro)
    - `frontend/src/components/ContatoForm.tsx`
    - `frontend/package.json` (novas dependências)

  - **Requisitos atendidos**: RF-F3.2-03

  - **Descrição**:

    1. **Instalar dependências**:
       ```bash
       npm install zod react-hook-form @hookform/resolvers
       ```
       Se `react-hook-form` já estiver instalado, apenas garantir que `zod` e `@hookform/resolvers` são adicionados.

    2. **`frontend/src/lib/schemas.ts`** — Criar os três schemas Zod:

       ```typescript
       import { z } from "zod"

       export const loginSchema = z.object({
         email: z.string().email("E-mail inválido."),
         senha: z.string().min(6, "A senha deve ter pelo menos 6 caracteres."),
       })

       export const cadastroSchema = z.object({
         nome: z
           .string()
           .min(2, "O nome deve ter pelo menos 2 caracteres.")
           .max(100, "O nome deve ter no máximo 100 caracteres."),
         email: z.string().email("E-mail inválido."),
         senha: z.string().min(6, "A senha deve ter pelo menos 6 caracteres."),
       })

       export const contatoSchema = z.object({
         nome: z.string().min(2, "O nome deve ter pelo menos 2 caracteres."),
         email: z.string().email("E-mail inválido."),
         telefone: z
           .string()
           .optional()
           .refine(
             (val) =>
               !val ||
               /^\(\d{2}\) \d{5}-\d{4}$/.test(val) ||
               /^\(\d{2}\) \d{4}-\d{4}$/.test(val),
             { message: "Formato inválido. Use (99) 99999-9999 ou (99) 9999-9999." }
           ),
         empresa: z.string().optional(),
         observacoes: z.string().optional(),
       })

       // Tipos inferidos — usar no lugar de interfaces manuais
       export type LoginFormData = z.infer<typeof loginSchema>
       export type CadastroFormData = z.infer<typeof cadastroSchema>
       export type ContatoFormData = z.infer<typeof contatoSchema>
       ```

    3. **Formulário de login** (`login/page.tsx` ou equivalente):

       a. Substituir o gerenciamento de estado atual (`useState` por campo) por `useForm` do `react-hook-form` com `zodResolver`:
          ```typescript
          import { useForm } from "react-hook-form"
          import { zodResolver } from "@hookform/resolvers/zod"
          import { loginSchema, LoginFormData } from "@/lib/schemas"

          const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
            resolver: zodResolver(loginSchema),
          })
          ```

       b. Substituir a validação inline por exibição dos erros do `react-hook-form`:
          ```tsx
          {errors.email && <p className="text-sm text-red-500">{errors.email.message}</p>}
          {errors.senha && <p className="text-sm text-red-500">{errors.senha.message}</p>}
          ```

       c. Remover toda lógica de validação manual (`if (!email.includes("@"))`, etc.).

    4. **Formulário de cadastro** (`cadastro/page.tsx` ou equivalente):
       - Mesma abordagem do login, usando `cadastroSchema` e `CadastroFormData`.

    5. **`frontend/src/components/ContatoForm.tsx`**:

       a. Substituir a validação manual de telefone (regex inline) pela regra do `contatoSchema`.

       b. Integrar `useForm` com `zodResolver(contatoSchema)`:
          - Se o formulário já usa `react-hook-form`, apenas adicionar o resolver.
          - Se ainda usa `useState` por campo, migrar para `useForm` (preservando a lógica de `isDirty` do hook `useBeforeUnload` — adaptar para usar `formState.isDirty` do `react-hook-form` em vez de comparação manual).

       c. Garantir que nenhuma regex de validação de telefone permaneça fora do `contatoSchema`.

    6. **Verificação de tipagem**:
       ```bash
       npx tsc --noEmit
       ```
       Deve passar sem erros após todas as alterações.

  - **Critério de pronto**:
    - `frontend/src/lib/schemas.ts` existe e exporta os três schemas e tipos
    - Formulário de login rejeita e-mail inválido com mensagem do Zod em PT-BR antes de submeter
    - Formulário de login rejeita senha < 6 caracteres com mensagem do Zod em PT-BR
    - Formulário de cadastro rejeita nome < 2 caracteres com mensagem do Zod em PT-BR
    - `ContatoForm` rejeita telefone em formato inválido com mensagem do `contatoSchema`
    - `ContatoForm` aceita telefone vazio sem erro
    - Nenhuma regex de validação de telefone existe fora de `schemas.ts`
    - `npx tsc --noEmit` sem erros de tipagem

---

## Resumo de Paralelismo — Fase 3.2

| Task    | Fase | Pode rodar em paralelo com | Dependências |
|---------|------|---------------------------|--------------|
| TASK-11 | 3.2  | TASK-12, TASK-13          | nenhuma      |
| TASK-12 | 3.2  | TASK-11, TASK-13          | nenhuma      |
| TASK-13 | 3.2  | TASK-11, TASK-12          | nenhuma      |

> As três tasks da Fase 3.2 são totalmente independentes entre si — editam arquivos disjuntos e não há dependência de runtime entre elas. Podem ser distribuídas para três DEVs distintos e integradas em qualquer ordem.

---

## Requisitos Cobertos — Fase 3.2

| Requisito    | Task    |
|--------------|---------|
| RF-F3.2-01   | TASK-11 |
| RF-F3.2-02   | TASK-12 |
| RF-F3.2-03   | TASK-13 |

---

## Fase 4 — FASE C — Qualidade de Código e Arquitetura

> Fase de **redução de dívida técnica**: refatoração de componentes, modernização da API SQLAlchemy (1.x → 2.0), criação de hooks/helpers reutilizáveis, otimização de queries via índices, elevação da cobertura de testes do frontend (≥ 60%) e introdução de linters de segurança no pipeline.
>
> A FASE C **não altera contratos públicos** (REST API, payloads, UI visível) e **não introduz novas funcionalidades**. Todos os testes existentes devem continuar passando.
>
> Organização em três sub-fases para isolar conflitos de arquivo:
> - **Sub-fase C.1 — Frontend Refactor + Linters**: TASK-14, TASK-15, TASK-16, TASK-21 (paralelas entre si).
> - **Sub-fase C.2 — SQLAlchemy 2.0 (exclusiva)**: TASK-17 (sozinha — toca todos routers/services).
> - **Sub-fase C.3 — Backend Helpers + Índices**: TASK-18, TASK-19 (paralelas entre si).
> - **Sub-fase C.4 — Testes Frontend (final)**: TASK-20 (depende de TASK-14, TASK-15, TASK-16).

---

### Sub-fase C.1 — Frontend Refactor + Linters de Segurança

> Tasks de frontend que tocam arquivos disjuntos + introdução de linters (sem conflito com nenhum outro arquivo). As quatro tasks abaixo podem ser executadas **em paralelo** por DEVs distintos.

---

- **TASK-14** [paralelo: ✅ com TASK-15, TASK-16, TASK-21] — Frontend: Quebra do ContatoForm.tsx (hook + 3 componentes de campo)

  - **Arquivos a criar**:
    - `frontend/src/hooks/useContatoFormValidation.ts`
    - `frontend/src/components/form/InputField.tsx`
    - `frontend/src/components/form/SelectField.tsx`
    - `frontend/src/components/form/TextAreaField.tsx`

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoForm.tsx`

  - **Requisitos atendidos**: RF-01 (C.1)

  - **Descrição**:

    O componente `ContatoForm.tsx` está com 377 linhas e mistura validação, máscara, renderização e estado de campos. Esta task extrai responsabilidades em um hook e três componentes reutilizáveis.

    1. **`frontend/src/hooks/useContatoFormValidation.ts`** — Criar hook de validação:
       - Extrair toda a lógica de validação de campos (regex de telefone, e-mail, obrigatórios) que hoje vive dentro de `ContatoForm.tsx`.
       - Assinatura sugerida:
         ```typescript
         export function useContatoFormValidation(values: ContatoFormData): {
           errors: Partial<Record<keyof ContatoFormData, string>>
           isValid: boolean
         }
         ```
       - Se o componente atual já usa `react-hook-form` + `zodResolver` (da TASK-13), o hook deve apenas **encapsular** o `useForm` + `zodResolver(contatoSchema)` e expor `register`, `handleSubmit`, `formState`, `reset` — mantendo `isDirty` acessível para integração com `useBeforeUnload`.
       - Incluir JSDoc com exemplo de uso (RNF-08).

    2. **`frontend/src/components/form/InputField.tsx`** — Componente de input genérico:
       - Props:
         ```typescript
         interface InputFieldProps {
           label: string
           name: string
           type?: "text" | "email" | "tel" | "password"
           placeholder?: string
           error?: string
           mask?: string  // opcional, para integração com react-input-mask quando aplicável
           register?: any  // saída de react-hook-form .register()
         }
         ```
       - Renderiza `<label>` + `<input>` + mensagem de erro condicional.
       - Estilo Tailwind alinhado ao padrão atual do `ContatoForm` (mesmas classes).

    3. **`frontend/src/components/form/SelectField.tsx`** — Componente de select genérico:
       - Props similares ao `InputField`, com `options: Array<{ value: string; label: string }>`.

    4. **`frontend/src/components/form/TextAreaField.tsx`** — Componente de textarea:
       - Props similares ao `InputField`, com `rows?: number` (default 4).

    5. **`frontend/src/components/ContatoForm.tsx`** — Refatorar:
       - Importar e usar `useContatoFormValidation`, `InputField`, `SelectField`, `TextAreaField`.
       - Remover toda a lógica de validação inline (já foi para o hook).
       - Substituir os `<input>` / `<select>` / `<textarea>` puros pelos novos componentes.
       - **Meta de linhas**: arquivo final entre **150 e 180 linhas** (RF-01).
       - **Não alterar** o comportamento observável: validações, máscaras, submit, integração com `useBeforeUnload`/`UnsavedChangesModal`.

  - **Critério de pronto**:
    - Existem os 4 arquivos novos: hook + 3 componentes em `frontend/src/components/form/`.
    - `ContatoForm.tsx` tem entre 150 e 180 linhas (`wc -l` confirma).
    - Nenhum `<input>` / `<select>` / `<textarea>` cru permanece em `ContatoForm.tsx` — todos passam pelos novos componentes.
    - Todos os testes Jest existentes que cobrem `ContatoForm` continuam passando (ou atualizados para usar `getByRole`/`getByLabelText`).
    - `npx tsc --noEmit` sem erros.
    - Hook e componentes contêm JSDoc com exemplo de uso.

---

- **TASK-15** [paralelo: ✅ com TASK-14, TASK-16, TASK-21] — Frontend: Hook useDebounce reutilizável

  - **Arquivos a criar**:
    - `frontend/src/hooks/useDebounce.ts`

  - **Arquivos a modificar**:
    - `frontend/src/app/contatos/page.tsx`

  - **Requisitos atendidos**: RF-02 (C.2)

  - **Descrição**:

    1. **`frontend/src/hooks/useDebounce.ts`** — Criar hook genérico:
       ```typescript
       /**
        * Retorna o valor `value` após `delay` ms sem mudanças.
        * Útil para debouncing de campos de busca.
        *
        * @example
        * const termoDebounced = useDebounce(termoBusca, 400)
        * useEffect(() => { listar(termoDebounced) }, [termoDebounced])
        */
       export function useDebounce<T>(value: T, delay: number): T
       ```
       Implementação típica com `useState` + `useEffect` + `setTimeout`/`clearTimeout` na cleanup do effect.

    2. **`frontend/src/app/contatos/page.tsx`**:
       - Localizar o debounce ad-hoc atual (provavelmente usando `useRef` + `setTimeout` para a busca).
       - Substituir pela chamada `const termoBusca = useDebounce(termoBuscaInput, 400)` (ajustar nome conforme variáveis existentes).
       - Remover o código antigo de debounce (refs, timers manuais).
       - **Não alterar** o comportamento observável: latência da busca, paginação, ordenação, reset de filtros.
       - Se a TASK-15 e a TASK-20 forem ambas executadas, atenção: TASK-20 escreve testes para a paginação/busca desta página — sequenciar para que os testes sejam escritos após esta refatoração estar mergeada.

  - **Critério de pronto**:
    - `frontend/src/hooks/useDebounce.ts` existe, tipado genericamente, com JSDoc + exemplo.
    - `app/contatos/page.tsx` usa `useDebounce` em vez de `useRef` + `setTimeout`.
    - Comportamento de busca idêntico ao anterior (mesmo delay efetivo).
    - `npx tsc --noEmit` sem erros.
    - Testes existentes de `app/contatos/page.tsx` continuam passando.

---

- **TASK-16** [paralelo: ✅ com TASK-14, TASK-15, TASK-21] — Frontend: Memoização estratégica em ContatoTable

  - **Arquivos a modificar**:
    - `frontend/src/components/ContatoTable.tsx`

  - **Requisitos atendidos**: RF-03 (C.3)

  - **Descrição**:

    1. **`frontend/src/components/ContatoTable.tsx`**:

       a. Localizar o subcomponente `SkeletonRow` (renderizado durante loading). Envolvê-lo em `React.memo`:
          ```typescript
          const SkeletonRow = React.memo(function SkeletonRow() {
            return <tr>...</tr>
          })
          ```

       b. Localizar a lógica de ordenação dos contatos (array `.sort()` ou função de comparação aplicada na renderização). Envolver em `useMemo`:
          ```typescript
          const contatosOrdenados = useMemo(
            () => [...contatos].sort(...),
            [contatos, sortBy, sortOrder]
          )
          ```
          Garantir que as **dependências sejam exatamente** as que afetam a ordem (não incluir variáveis externas que não impactam).

       c. **Não alterar**:
          - Ordem visual atual.
          - Props recebidas pelo componente.
          - Comportamento de ordenação por header (TASK-05).
          - Ícones de ação (TASK-03).
          - Mensagem de lista vazia (TASK-04).

  - **Critério de pronto**:
    - `SkeletonRow` está envolvido em `React.memo` (visível no diff).
    - O array de contatos ordenados é produzido por um `useMemo` com array de dependências correto.
    - React DevTools (manual) mostra `SkeletonRow` como memoizado.
    - Nenhuma regressão visual: tabela renderiza identicamente.
    - `npx tsc --noEmit` sem erros.
    - Testes existentes de `ContatoTable` continuam passando.

---

- **TASK-21** [paralelo: ✅ com TASK-14, TASK-15, TASK-16] — Qualidade: Linters de segurança (bandit + eslint-plugin-security)

  - **Arquivos a criar**:
    - `backend/.bandit` (configuração do bandit — formato INI ou YAML)
    - `frontend/.eslintrc.security.js` (ou apenas estender o `.eslintrc` existente com o plugin — escolher conforme estrutura atual)
    - `.github/workflows/security.yml` (job de CI dedicado — opcional se já houver workflow consolidado; nesse caso, apenas adicionar steps)

  - **Arquivos a modificar**:
    - `backend/requirements.txt` (adicionar `bandit`)
    - `frontend/package.json` (adicionar `eslint-plugin-security` em devDependencies)
    - `frontend/.eslintrc.json` ou `frontend/.eslintrc.js` (adicionar `"plugin:security/recommended"` em `extends`)
    - `backend/README.md` (mini-seção com comando `bandit -c .bandit -r app/`)
    - `frontend/README.md` (mini-seção com comando `npm run lint:security`)

  - **Requisitos atendidos**: RF-08 (C.8)

  - **Descrição**:

    Esta task **não toca código de produção** — apenas configuração de ferramentas. Por isso é segura para rodar em paralelo com qualquer outra task.

    1. **Backend (bandit)**:

       a. Adicionar em `backend/requirements.txt`:
          ```
          bandit>=1.7.5
          ```

       b. Criar `backend/.bandit` (formato INI):
          ```ini
          [bandit]
          exclude_dirs = ["tests", "alembic/versions"]
          skips = []
          ```
          (Excluir testes e migrations geradas; manter todos os checks ativados.)

       c. Documentar no `backend/README.md` a seção "Análise estática de segurança":
          - Comando local: `bandit -c .bandit -r app/`
          - Critério de falha: severidade `MEDIUM` ou `HIGH`.

       d. Rodar **uma varredura prévia** em base limpa e listar findings encontrados. Se houver findings `MEDIUM`/`HIGH` em código legado, criar arquivo `backend/.bandit.baseline.json` (output do `bandit --baseline`) e referenciá-lo no `.bandit` para não travar build no dia 1 (mitigação do risco R-04 do PRD). Cada item do baseline deve ter comentário com justificativa.

    2. **Frontend (eslint-plugin-security)**:

       a. Instalar:
          ```bash
          npm install --save-dev eslint-plugin-security
          ```

       b. No `.eslintrc.*` do frontend, adicionar:
          ```json
          {
            "plugins": ["security"],
            "extends": ["...existing", "plugin:security/recommended"]
          }
          ```

       c. Adicionar script em `frontend/package.json`:
          ```json
          "scripts": {
            "lint:security": "eslint . --ext .ts,.tsx --max-warnings=0"
          }
          ```

       d. Documentar no `frontend/README.md`: comando `npm run lint:security`, critério de falha (qualquer warning `security/*` de severidade ≥ médio).

       e. Rodar prévia e silenciar/corrigir findings legados antes de ligar o gate (R-04).

    3. **CI Gate**:
       - Adicionar steps no workflow de CI existente (ou criar `.github/workflows/security.yml`) para:
         - Backend: `bandit -c backend/.bandit -r backend/app/ --severity-level medium --confidence-level medium` (exit ≠ 0 falha o job).
         - Frontend: `npm --prefix frontend run lint:security` (exit ≠ 0 falha o job).
       - Garantir que o job é obrigatório no branch protection do `master`.

    4. **Não criar** pre-commit hook nesta task — fica para Fase E.5 (fora de escopo, ver PRD seção 11).

  - **Critério de pronto**:
    - `bandit -c backend/.bandit -r backend/app/` roda localmente sem findings novos de `MEDIUM`/`HIGH` (ou todos suprimidos via baseline justificado).
    - `npm --prefix frontend run lint:security` roda sem erros.
    - Pipeline de CI tem jobs `backend-security` e `frontend-security` configurados.
    - Ambos os READMEs (`backend/README.md` e `frontend/README.md`) documentam os comandos.
    - PR de teste com `eval()` adicionado ao código falha o CI (sanity check manual).
    - Nenhuma alteração em código de produção (somente config + dependências + docs).

---

### Sub-fase C.2 — Migração SQLAlchemy 2.0 (exclusiva — sem paralelismo)

> Esta sub-fase contém **apenas TASK-17**. A migração `db.query()` → `select()` toca **todos** os routers e services do backend, criando conflito potencial com qualquer outra task de backend. Portanto, esta task **roda sozinha**, entre a Sub-fase C.1 e a Sub-fase C.3.

---

- **TASK-17** [paralelo: ❌ — exclusiva] — Backend: Migração SQLAlchemy 1.x → 2.0 (todos os routers e services)

  - **Arquivos a modificar** (lista exaustiva esperada):
    - `backend/app/routers/contatos.py`
    - `backend/app/routers/usuarios.py`
    - `backend/app/routers/auth.py`
    - `backend/app/services/contato_service.py`
    - `backend/app/services/usuario_service.py` (se existir)
    - Quaisquer outros arquivos em `backend/app/routers/` e `backend/app/services/` que contenham `db.query(`.

  - **Requisitos atendidos**: RF-04 (C.4)

  - **Descrição**:

    Padronizar **toda** a camada de acesso a dados para a API SQLAlchemy 2.0 baseada em `select()` + `db.execute()` / `db.scalars()`. **Não alterar comportamento observável** — esta é uma migração mecânica de padrão.

    1. **Padrão antigo (1.x) a ser substituído**:
       ```python
       contatos = db.query(Contato).filter(Contato.email == email).all()
       contato = db.query(Contato).filter(Contato.id == id).first()
       total = db.query(Contato).count()
       ```

    2. **Padrão novo (2.0) a ser adotado**:
       ```python
       from sqlalchemy import select, func

       stmt = select(Contato).where(Contato.email == email)
       contatos = db.scalars(stmt).all()

       stmt = select(Contato).where(Contato.id == id)
       contato = db.scalars(stmt).first()  # ou .one_or_none()

       stmt = select(func.count()).select_from(Contato)
       total = db.scalar(stmt)
       ```

    3. **Procedimento recomendado** (mitigação do risco R-01):

       a. Buscar todas as ocorrências: `grep -rn "db.query(" backend/app/`. Listar todas em um checklist antes de começar.

       b. Migrar **um arquivo por vez**, na ordem:
          1. `services/contato_service.py`
          2. `services/usuario_service.py` (se existir)
          3. `routers/contatos.py`
          4. `routers/usuarios.py`
          5. `routers/auth.py`
          6. Qualquer outro arquivo restante.

       c. Após cada arquivo migrado, rodar:
          ```bash
          pytest -x backend/tests/
          ```
          Se algum teste quebrar, investigar (provável diferença em lazy loading ou retorno de tupla vs. escalar) **antes** de prosseguir.

       d. Atenção especial a:
          - `.all()` em `db.query` retorna `list[Model]`; em `db.execute(select(Model))` retorna `list[Row]` — usar `db.scalars()` em vez de `db.execute()` quando o retorno esperado for o modelo direto.
          - Joins e `options(joinedload(...))` mantêm a mesma sintaxe.
          - Subqueries: usar `select().subquery()` em vez de `db.query().subquery()`.

    4. **Validação final**:
       - `grep -rn "db.query(" backend/app/routers/ backend/app/services/` deve retornar **zero ocorrências**.
       - `pytest --cov=app` continua com cobertura ≥ 80% (mantida da Fase 3.1).
       - Nenhum endpoint mudou de contrato (path, payload, status code).

  - **Critério de pronto**:
    - Zero ocorrências de `db.query(` em `backend/app/routers/` e `backend/app/services/`.
    - Todos os testes pytest passam (`pytest -x`).
    - Cobertura backend mantida ≥ 80%.
    - `EXPLAIN` (manual, opcional) confirma que os planos de query são equivalentes.
    - Documentação OpenAPI inalterada (diff vazio em `/docs/openapi.json`).

---

### Sub-fase C.3 — Backend: Helpers + Índices

> Duas tasks de backend com **arquivos disjuntos**. TASK-18 toca `services/_helpers.py`, `routers/usuarios.py`, `services/contato_service.py`. TASK-19 toca `models/contato.py` + nova migration. Não há sobreposição. Podem rodar **em paralelo**.

---

- **TASK-18** [paralelo: ✅ com TASK-19] — Backend: Helper de validação de unicidade (DRY do padrão 409)

  - **Arquivos a criar**:
    - `backend/app/services/_helpers.py`

  - **Arquivos a modificar**:
    - `backend/app/routers/usuarios.py`
    - `backend/app/services/contato_service.py`

  - **Requisitos atendidos**: RF-05 (C.5)

  - **Descrição**:

    Eliminar duplicação do padrão "buscar registro por campo único; se existir, levantar HTTP 409 (ou 400, conforme padrão atual)".

    1. **`backend/app/services/_helpers.py`** — Criar helper:
       ```python
       from typing import Type, TypeVar
       from fastapi import HTTPException, status
       from sqlalchemy import select
       from sqlalchemy.orm import Session

       T = TypeVar("T")

       def garantir_unicidade(
           db: Session,
           model: Type[T],
           campo: str,
           valor: str,
           mensagem: str,
           status_code: int = status.HTTP_409_CONFLICT,
           excluir_id: int | None = None,
       ) -> None:
           """
           Verifica se já existe um registro de `model` com `model.<campo> == valor`.
           Se sim, levanta HTTPException com `status_code` e `mensagem`.

           `excluir_id` permite ignorar um ID específico (útil em updates/PATCH onde o próprio
           registro já tem o valor que está sendo "revalidado").

           Exemplo:
               garantir_unicidade(db, Usuario, "email", dados.email,
                                  "E-mail já cadastrado.", excluir_id=usuario.id)
           """
           stmt = select(model).where(getattr(model, campo) == valor)
           if excluir_id is not None:
               stmt = stmt.where(getattr(model, "id") != excluir_id)
           existente = db.scalars(stmt).first()
           if existente is not None:
               raise HTTPException(status_code=status_code, detail=mensagem)
       ```
       - Incluir docstring com exemplo de uso (RNF-08).
       - Decidir entre 409 (RESTful clássico) e 400 (padrão atual do projeto) consultando uso existente; manter consistência com o que já é retornado em `usuarios.py`/`contato_service.py` para **não alterar contratos** (RNF-02).

    2. **`backend/app/routers/usuarios.py`**:
       - Localizar os blocos `if db.query(Usuario).filter(...).first(): raise HTTPException(...)` (no POST de criação e no PUT de atualização).
       - Substituir por chamadas a `garantir_unicidade(db, Usuario, "email", dados.email, "E-mail já cadastrado.")`.
       - No PUT, passar `excluir_id=id` para permitir manter o próprio email.

    3. **`backend/app/services/contato_service.py`**:
       - Localizar o bloco de validação de e-mail único em `criar_contato`, `atualizar_contato` e `patch_contato` (criados nas Fases 3.1/3.2).
       - Substituir cada um por chamada ao helper.
       - No PATCH/PUT, passar `excluir_id=contato.id`.

    4. **Atenção**: Se a TASK-17 (SQLAlchemy 2.0) já foi mergeada antes desta, o helper já nasce com `select()` (como acima). Se algum arquivo ainda tem `db.query()`, a TASK-18 **não regride**, mantém o `select()`.

  - **Critério de pronto**:
    - `backend/app/services/_helpers.py` existe com função `garantir_unicidade` documentada.
    - `routers/usuarios.py` e `services/contato_service.py` usam o helper — não há mais blocos duplicados de "if existente then raise".
    - Todos os testes pytest existentes passam (`pytest -x`).
    - Status codes retornados em respostas (409 ou 400) **idênticos** aos retornados antes da refatoração — testes de contrato confirmam.
    - `grep -rn "E-mail já" backend/app/routers backend/app/services` mostra a string apenas dentro do helper ou em chamadas a ele.

---

- **TASK-19** [paralelo: ✅ com TASK-18] — Backend: Índices em colunas de busca/ordenação + migration Alembic

  - **Arquivos a criar**:
    - `backend/alembic/versions/<hash>_add_indices_contatos.py` (nova migration — nome do hash gerado pelo Alembic)

  - **Arquivos a modificar**:
    - `backend/app/models/contato.py`

  - **Requisitos atendidos**: RF-06 (C.6)

  - **Descrição**:

    Otimização de leitura: adicionar índices nas colunas `nome`, `email`, `criado_em` da tabela `contatos`. Estas colunas são usadas em busca (LIKE/=), ordenação (`ORDER BY`) e filtros.

    1. **`backend/app/models/contato.py`** — Adicionar `index=True`:
       ```python
       nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
       email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
       criado_em: Mapped[datetime] = mapped_column(
           DateTime, default=lambda: datetime.now(timezone.utc), index=True
       )
       ```
       - **Não tocar** em outras colunas (`telefone`, `empresa`, `observacoes`, `deletado_em`, `criado_por_id`, `atualizado_por_id`).
       - Se `email` já tem `unique=True`, ele **já tem índice implícito** — neste caso, **omitir** `index=True` (evita índice duplicado). Confirmar antes de adicionar.

    2. **Migration Alembic** — Gerar:
       ```bash
       cd backend
       alembic revision --autogenerate -m "add_indices_contatos"
       ```
       Revisar o arquivo gerado em `backend/alembic/versions/<hash>_add_indices_contatos.py`. Deve conter apenas:
       ```python
       def upgrade():
           op.create_index("ix_contatos_nome", "contatos", ["nome"])
           op.create_index("ix_contatos_email", "contatos", ["email"])  # se não duplicado
           op.create_index("ix_contatos_criado_em", "contatos", ["criado_em"])

       def downgrade():
           op.drop_index("ix_contatos_criado_em", table_name="contatos")
           op.drop_index("ix_contatos_email", table_name="contatos")
           op.drop_index("ix_contatos_nome", table_name="contatos")
       ```
       Remover qualquer operação destrutiva ou não relacionada que o autogenerate possa incluir.

    3. **Postgres (produção)** — Se o ambiente alvo for Postgres com tabela grande, considerar editar a migration para usar `op.create_index(..., postgresql_concurrently=True)` e `with op.get_context().autocommit_block():` (R-02). Documentar no comentário da migration.

    4. **Validação**:
       - `alembic upgrade head` aplica sem erro.
       - `alembic downgrade -1` reverte sem erro.
       - Em base de teste com ≥ 10k linhas (opcional), executar `EXPLAIN SELECT * FROM contatos WHERE nome LIKE 'Jo%'` e confirmar uso do índice.

  - **Critério de pronto**:
    - `nome`, `email` (se não-único) e `criado_em` têm `index=True` em `models/contato.py`.
    - Migration Alembic existe em `backend/alembic/versions/`, autogenerate revisado, sem operações destrutivas.
    - `alembic upgrade head` + `alembic downgrade -1` rodam sem erro.
    - Todos os testes pytest passam (índices não quebram queries).
    - Nenhuma outra coluna do modelo foi alterada (diff cirúrgico em `contato.py`).

---

### Sub-fase C.4 — Testes Frontend (depende de C.1)

> TASK-20 depende de **TASK-14, TASK-15, TASK-16** estarem mergeadas — escreve testes para os componentes refatorados. Não pode rodar em paralelo com C.1.

---

- **TASK-20** [paralelo: ❌ — depende de TASK-14, TASK-15, TASK-16] — Frontend: Elevar cobertura Jest para ≥ 60% (login, ContatoForm, paginação/busca, modal unsaved)

  - **Arquivos a criar** (estrutura sugerida; ajustar conforme convenção do projeto):
    - `frontend/src/__tests__/login.test.tsx` (ou `frontend/src/app/login/__tests__/page.test.tsx`)
    - `frontend/src/__tests__/contatoForm.test.tsx` (ou `frontend/src/components/__tests__/ContatoForm.test.tsx`)
    - `frontend/src/__tests__/contatosPage.test.tsx` (paginação e busca)
    - `frontend/src/__tests__/unsavedChangesModal.test.tsx`

  - **Arquivos a modificar** (se necessário):
    - `frontend/jest.config.js` (garantir threshold de cobertura ≥ 60% em statements)
    - `frontend/package.json` (script `test:coverage` se ainda não existir)

  - **Requisitos atendidos**: RF-07 (C.7)

  - **Dependências**: TASK-14 (ContatoForm refatorado), TASK-15 (useDebounce em uso na page de contatos), TASK-16 (ContatoTable memoizado).

  - **Descrição**:

    Escrever testes Jest + React Testing Library cobrindo quatro fluxos críticos. Meta: **cobertura global de statements ≥ 60%** no relatório do Jest.

    1. **`login.test.tsx`** (mínimo 4 testes):
       - Renderiza campos email/senha e botão.
       - Submit com email vazio: exibe mensagem do Zod "E-mail inválido." (TASK-13).
       - Submit com senha < 6 chars: exibe mensagem "A senha deve ter pelo menos 6 caracteres.".
       - Submit com credenciais válidas: chama `fetch`/service mockado e navega para `/contatos` (usar `jest.fn()` para o router).

    2. **`contatoForm.test.tsx`** (mínimo 6 testes — usa componentes refatorados de TASK-14):
       - Renderiza todos os campos via `InputField`/`SelectField`/`TextAreaField` (verificar por `getByLabelText`).
       - Campo obrigatório vazio bloqueia submit.
       - Telefone com formato inválido exibe mensagem do `contatoSchema`.
       - Telefone vazio é aceito (campo opcional).
       - Modificar campo seta `isDirty=true` (validar via efeito observável).
       - Submit bem-sucedido chama `onSubmit` mock e reseta `isDirty`.

    3. **`contatosPage.test.tsx`** (mínimo 5 testes — depende de TASK-15):
       - Renderiza lista de contatos mockada e paginação.
       - Digitar no campo busca aciona debounce (avançar timers com `jest.useFakeTimers()` + `jest.advanceTimersByTime(400)`) e refaz fetch.
       - Clicar em "próxima página" incrementa o offset enviado à API.
       - Lista vazia com busca ativa exibe `Nenhum resultado para "<termo>"`.
       - Lista vazia sem busca exibe "Nenhum contato cadastrado ainda.".

    4. **`unsavedChangesModal.test.tsx`** (mínimo 4 testes):
       - Modal não renderiza quando `isOpen=false`.
       - Modal renderiza título e corpo em PT-BR quando `isOpen=true`.
       - Clicar em "Continuar editando" dispara `onContinue`.
       - Clicar em "Sair sem salvar" dispara `onLeave`.

    5. **`frontend/jest.config.js`** — Configurar threshold:
       ```javascript
       coverageThreshold: {
         global: {
           statements: 60,
           branches: 50,
           functions: 55,
           lines: 60,
         },
       },
       ```
       Build falha automaticamente se a meta não for atingida.

    6. **Scripts**:
       - Garantir que `npm --prefix frontend run test:coverage` (ou equivalente) gera `coverage/` e log com `Statements: XX%`.
       - Adicionar ao CI um step que falha se cobertura < 60%.

  - **Critério de pronto**:
    - Os 4 arquivos de teste existem com no mínimo o número de testes indicado por arquivo.
    - `npm --prefix frontend run test:coverage` reporta `Statements ≥ 60%`.
    - Todos os testes passam (zero falhas, zero `.skip` injustificados).
    - `jest.config.js` tem `coverageThreshold.global.statements >= 60`.
    - CI verde no job de testes frontend.
    - Nenhum teste depende de servidor real, banco real, ou faz network real (todos mockam fetch/services).

---

## Resumo de Paralelismo — Fase 4 (FASE C)

| Task    | Sub-fase | Pode rodar em paralelo com           | Dependências                          |
|---------|----------|--------------------------------------|---------------------------------------|
| TASK-14 | C.1      | TASK-15, TASK-16, TASK-21            | nenhuma                               |
| TASK-15 | C.1      | TASK-14, TASK-16, TASK-21            | nenhuma                               |
| TASK-16 | C.1      | TASK-14, TASK-15, TASK-21            | nenhuma                               |
| TASK-21 | C.1      | TASK-14, TASK-15, TASK-16            | nenhuma (só config)                   |
| TASK-17 | C.2      | nenhuma (toca todos routers/services)| recomendado após C.1                  |
| TASK-18 | C.3      | TASK-19                              | TASK-17 (preferencial)                |
| TASK-19 | C.3      | TASK-18                              | nenhuma                               |
| TASK-20 | C.4      | nenhuma                              | TASK-14, TASK-15, TASK-16             |

> **Grupos de paralelismo confirmados na FASE C**:
> - **Grupo D (Sub-fase C.1)**: TASK-14, TASK-15, TASK-16, TASK-21 — 4 tasks em paralelo, arquivos totalmente disjuntos. Esta é a sub-fase com **maior paralelismo** da FASE C.
> - **Grupo E (Sub-fase C.3)**: TASK-18 e TASK-19 — 2 tasks em paralelo, arquivos disjuntos.

---

## Requisitos Cobertos — Fase 4 (FASE C)

| Requisito | Task     |
|-----------|----------|
| RF-01     | TASK-14  |
| RF-02     | TASK-15  |
| RF-03     | TASK-16  |
| RF-04     | TASK-17  |
| RF-05     | TASK-18  |
| RF-06     | TASK-19  |
| RF-07     | TASK-20  |
| RF-08     | TASK-21  |
