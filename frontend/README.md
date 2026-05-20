# Frontend — Manutenção de Contatos

Interface web construída com Next.js 14 (App Router), TypeScript e Tailwind CSS.

---

## Pré-requisitos

- Node.js 18+
- npm

---

## Instalação e execução

```bash
cd frontend
npm install
npm run dev
```

A aplicação estará disponível em: http://localhost:3000

---

## Variáveis de ambiente

Crie o arquivo `.env.local` na raiz de `frontend/` com o seguinte conteúdo:

| Variável               | Descrição                        | Valor padrão              |
|------------------------|----------------------------------|---------------------------|
| `NEXT_PUBLIC_API_URL`  | URL base da API do backend       | `http://localhost:8000`   |

Exemplo de `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Estrutura de páginas

| Rota                        | Descrição                                      | Acesso         |
|-----------------------------|------------------------------------------------|----------------|
| `/login`                    | Formulário de autenticação                     | Público        |
| `/cadastro`                 | Formulário de criação de conta                 | Público        |
| `/contatos`                 | Listagem de contatos com pesquisa              | Autenticado    |
| `/contatos/[id]`            | Detalhes de um contato                         | Autenticado    |
| `/contatos/novo`            | Formulário de inclusão de contato              | Somente adm    |
| `/contatos/[id]/editar`     | Formulário de edição de contato                | Somente adm    |

---

## Perfis de acesso

- **default** — acesso somente leitura: pode visualizar a listagem e os detalhes dos contatos.
- **adm** — CRUD completo: pode criar, editar e excluir contatos. Promoção para adm é feita diretamente no banco (ver `backend/README.md`).

Páginas restritas redirecionam para `/login` quando o usuário não está autenticado, e exibem erro 403 quando o perfil não tem permissão suficiente.

---

## Análise estática de segurança (eslint-plugin-security)

O frontend usa o [eslint-plugin-security](https://github.com/eslint-community/eslint-plugin-security) para detectar padrões inseguros em código TypeScript/JavaScript (uso de `eval`, regex inseguro, injeção de objeto, etc.).

**Executar localmente:**

```bash
npm run lint:security
```

**Critério de falha:** qualquer warning das regras `security/*` (script roda com `--max-warnings=0`).

A configuração está em `frontend/.eslintrc.json` (extende `plugin:security/recommended-legacy`).
