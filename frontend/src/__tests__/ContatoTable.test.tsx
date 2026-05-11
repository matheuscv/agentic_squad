/**
 * Testes unitários para ContatoTable — barra de paginação
 *
 * Componente: frontend/src/components/ContatoTable.tsx
 * Critérios de aceite (PRD 13.4 — RF-F1-04):
 *   - Botão "Anterior" desabilitado na primeira página
 *   - Botão "Próxima" desabilitado na última página
 *   - Exibição do contador "X–Y de Z contatos"
 *   - Botões chamam os callbacks corretos
 *
 * DEPENDÊNCIAS NECESSÁRIAS (ver TESTES.md):
 *   jest, @testing-library/react, @testing-library/jest-dom,
 *   @testing-library/user-event, jest-environment-jsdom, ts-jest
 *
 * Mocks: next/navigation (useRouter)
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ContatoTable from '../components/ContatoTable'
import { Contato } from '../types'

// Mock do router para evitar erro em ambiente jsdom
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn() })),
}))


// ---------------------------------------------------------------------------
// Fábrica de props padrão para reutilização
// ---------------------------------------------------------------------------

function makeProps(overrides: Partial<Parameters<typeof ContatoTable>[0]> = {}) {
  const defaults = {
    contatos: [] as Contato[],
    isAdm: false,
    onEditar: jest.fn(),
    onExcluir: jest.fn(),
    loading: false,
    paginaAtual: 1,
    totalRegistros: 0,
    limite: 20,
    onPaginaAnterior: jest.fn(),
    onProximaPagina: jest.fn(),
  }
  return { ...defaults, ...overrides }
}

function makeContato(id: number): Contato {
  return {
    id,
    nome: `Contato ${id}`,
    email: `contato${id}@test.com`,
    telefone: null,
    empresa: null,
    observacoes: null,
    criado_em: '2026-01-01T00:00:00Z',
    atualizado_em: '2026-01-01T00:00:00Z',
  }
}


// ---------------------------------------------------------------------------
// Botão "Anterior" — estado desabilitado
// ---------------------------------------------------------------------------

describe('ContatoTable — botão Anterior', () => {
  test('está desabilitado na primeira página (paginaAtual=1)', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 1, totalRegistros: 40, limite: 20 })} />)
    const btn = screen.getByRole('button', { name: /anterior/i })
    expect(btn).toBeDisabled()
  })

  test('está habilitado quando paginaAtual > 1', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 2, totalRegistros: 40, limite: 20 })} />)
    const btn = screen.getByRole('button', { name: /anterior/i })
    expect(btn).not.toBeDisabled()
  })

  test('chama onPaginaAnterior ao clicar quando habilitado', async () => {
    const user = userEvent.setup()
    const onPaginaAnterior = jest.fn()
    render(
      <ContatoTable
        {...makeProps({ paginaAtual: 2, totalRegistros: 40, limite: 20, onPaginaAnterior })}
      />
    )
    await user.click(screen.getByRole('button', { name: /anterior/i }))
    expect(onPaginaAnterior).toHaveBeenCalledTimes(1)
  })

  test('não chama onPaginaAnterior ao clicar quando desabilitado', async () => {
    const user = userEvent.setup()
    const onPaginaAnterior = jest.fn()
    render(
      <ContatoTable
        {...makeProps({ paginaAtual: 1, totalRegistros: 40, limite: 20, onPaginaAnterior })}
      />
    )
    // Botão desabilitado não dispara click
    await user.click(screen.getByRole('button', { name: /anterior/i }))
    expect(onPaginaAnterior).not.toHaveBeenCalled()
  })
})


// ---------------------------------------------------------------------------
// Botão "Próxima" — estado desabilitado
// ---------------------------------------------------------------------------

describe('ContatoTable — botão Próxima', () => {
  test('está desabilitado na última página', () => {
    // 40 registros, limite 20, página 2 = última página
    render(<ContatoTable {...makeProps({ paginaAtual: 2, totalRegistros: 40, limite: 20 })} />)
    const btn = screen.getByRole('button', { name: /próxima/i })
    expect(btn).toBeDisabled()
  })

  test('está habilitado quando há mais páginas', () => {
    // 40 registros, limite 20, página 1 → totalPaginas=2
    render(<ContatoTable {...makeProps({ paginaAtual: 1, totalRegistros: 40, limite: 20 })} />)
    const btn = screen.getByRole('button', { name: /próxima/i })
    expect(btn).not.toBeDisabled()
  })

  test('está desabilitado quando totalRegistros=0', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 1, totalRegistros: 0, limite: 20 })} />)
    const btn = screen.getByRole('button', { name: /próxima/i })
    // Math.ceil(0/20) = 0, paginaAtual(1) >= totalPaginas(0) → desabilitado
    expect(btn).toBeDisabled()
  })

  test('chama onProximaPagina ao clicar quando habilitado', async () => {
    const user = userEvent.setup()
    const onProximaPagina = jest.fn()
    render(
      <ContatoTable
        {...makeProps({ paginaAtual: 1, totalRegistros: 40, limite: 20, onProximaPagina })}
      />
    )
    await user.click(screen.getByRole('button', { name: /próxima/i }))
    expect(onProximaPagina).toHaveBeenCalledTimes(1)
  })

  test('não chama onProximaPagina na última página', async () => {
    const user = userEvent.setup()
    const onProximaPagina = jest.fn()
    render(
      <ContatoTable
        {...makeProps({ paginaAtual: 2, totalRegistros: 40, limite: 20, onProximaPagina })}
      />
    )
    await user.click(screen.getByRole('button', { name: /próxima/i }))
    expect(onProximaPagina).not.toHaveBeenCalled()
  })
})


// ---------------------------------------------------------------------------
// Contador de registros "X–Y de Z contatos"
// ---------------------------------------------------------------------------

describe('ContatoTable — contador de registros', () => {
  test('exibe "0 contatos" quando não há registros', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 1, totalRegistros: 0, limite: 20 })} />)
    expect(screen.getByText(/0 contatos/i)).toBeInTheDocument()
  })

  test('exibe intervalo correto na primeira página (1–20 de 87 contatos)', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 1, totalRegistros: 87, limite: 20 })} />)
    expect(screen.getByText(/1–20 de 87 contatos/i)).toBeInTheDocument()
  })

  test('exibe intervalo correto na segunda página (21–40 de 87 contatos)', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 2, totalRegistros: 87, limite: 20 })} />)
    expect(screen.getByText(/21–40 de 87 contatos/i)).toBeInTheDocument()
  })

  test('exibe fim correto na última página parcial (81–87 de 87 contatos)', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 5, totalRegistros: 87, limite: 20 })} />)
    expect(screen.getByText(/81–87 de 87 contatos/i)).toBeInTheDocument()
  })

  test('exibe "1–5 de 5 contatos" quando há exatamente uma página', () => {
    render(<ContatoTable {...makeProps({ paginaAtual: 1, totalRegistros: 5, limite: 20 })} />)
    expect(screen.getByText(/1–5 de 5 contatos/i)).toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// Estado vazio e loading
// ---------------------------------------------------------------------------

describe('ContatoTable — estados especiais', () => {
  test('exibe mensagem "Nenhum contato encontrado." quando lista vazia e não carregando', () => {
    render(<ContatoTable {...makeProps({ contatos: [], loading: false, totalRegistros: 0 })} />)
    expect(screen.getByText(/nenhum contato encontrado/i)).toBeInTheDocument()
  })

  test('não exibe dados enquanto loading=true', () => {
    render(
      <ContatoTable
        {...makeProps({
          contatos: [makeContato(1)],
          loading: true,
          paginaAtual: 1,
          totalRegistros: 1,
          limite: 20,
        })}
      />
    )
    // Em loading, as linhas reais não são renderizadas
    expect(screen.queryByText('Contato 1')).not.toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// Controle de acesso — botões de editar/excluir
// ---------------------------------------------------------------------------

describe('ContatoTable — controle de acesso (isAdm)', () => {
  const contatos = [makeContato(1), makeContato(2)]

  test('exibe botões Editar e Excluir para adm', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos, isAdm: true, paginaAtual: 1, totalRegistros: 2, limite: 20 })}
      />
    )
    expect(screen.getAllByRole('button', { name: /editar/i })).toHaveLength(2)
    expect(screen.getAllByRole('button', { name: /excluir/i })).toHaveLength(2)
  })

  test('não exibe botões Editar/Excluir para usuário default (isAdm=false)', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos, isAdm: false, paginaAtual: 1, totalRegistros: 2, limite: 20 })}
      />
    )
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /excluir/i })).not.toBeInTheDocument()
  })
})
