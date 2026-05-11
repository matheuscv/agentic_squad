# Testes Unitários — Frontend

## Status do Setup

O projeto **não possui** configuração de testes Jest. As dependências abaixo
precisam ser instaladas antes de executar os testes criados em
`src/__tests__/`.

## Instalação

```bash
cd frontend
npm install --save-dev \
  jest \
  jest-environment-jsdom \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  @types/jest \
  ts-jest \
  babel-jest \
  @babel/core \
  @babel/preset-env \
  @babel/preset-react \
  @babel/preset-typescript \
  identity-obj-proxy
```

## Arquivos de configuração necessários

### `jest.config.js`

```js
const nextJest = require('next/jest')

const createJestConfig = nextJest({ dir: './' })

const customJestConfig = {
  setupFilesAfterFramework: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '\\.(css|scss)$': 'identity-obj-proxy',
  },
}

module.exports = createJestConfig(customJestConfig)
```

### `jest.setup.js`

```js
import '@testing-library/jest-dom'
```

### `tsconfig.jest.json` (opcional, se ts-jest for usado diretamente)

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": { "jsx": "react-jsx" }
}
```

### Script no `package.json`

```json
"scripts": {
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage"
}
```

## Executar os testes

```bash
cd frontend
npm test
```

## Arquivos de teste criados

| Arquivo | Componente coberto |
|---|---|
| `src/__tests__/NavbarWrapper.test.tsx` | `NavbarWrapper.tsx` — renderização condicional |
| `src/__tests__/ContatoTable.test.tsx` | `ContatoTable.tsx` — barra de paginação |
| `src/__tests__/contatos.service.test.ts` | `contatos.service.ts` — query string skip/limit |

## Bugs identificados (não corrigidos — responsabilidade do DEV)

Nenhum bug encontrado nos arquivos de frontend avaliados.

## Notas sobre test_services.py (backend)

O arquivo `backend/tests/test_services.py` existente possui testes de
`listar_contatos` que estão **incompatíveis** com a nova assinatura da função,
que agora retorna `tuple[list, int]` em vez de `list`:

- `test_listar_contatos_retorna_lista_vazia_quando_banco_vazio` compara
  `resultado == []` — falhará porque `resultado` é agora uma tupla.
- `test_listar_contatos_retorna_todos_sem_filtro` verifica `len(resultado) == 2`
  — falhará pela mesma razão.
- Os demais testes de busca também indexam o resultado como lista direta.

Esses testes devem ser atualizados para desempacotar a tupla:
`items, total = contato_service.listar_contatos(db_session, ...)`.
