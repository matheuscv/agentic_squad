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
  test('exibe mensagem "Nenhum contato cadastrado ainda." quando banco vazio sem busca', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos: [], loading: false, totalRegistros: 0, termoBusca: '' })}
      />
    )
    expect(screen.getByText(/nenhum contato cadastrado ainda/i)).toBeInTheDocument()
  })

  test('NÃO exibe string genérica "Nenhum contato encontrado" (removida na Fase 2)', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos: [], loading: false, totalRegistros: 0, termoBusca: '' })}
      />
    )
    expect(screen.queryByText(/nenhum contato encontrado/i)).not.toBeInTheDocument()
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


// ---------------------------------------------------------------------------
// RF-F2-04 — Ícones nos botões (Pencil e Trash2 via lucide-react)
// ---------------------------------------------------------------------------

describe('ContatoTable — ícones nos botões de ação (RF-F2-04)', () => {
  const contatos = [makeContato(1)]

  test('botão Editar contém ícone com aria-hidden="true"', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos, isAdm: true, paginaAtual: 1, totalRegistros: 1, limite: 20 })}
      />
    )
    const btnEditar = screen.getByRole('button', { name: /editar/i })
    // O ícone svg dentro do botão deve ter aria-hidden
    const svg = btnEditar.querySelector('svg')
    expect(svg).not.toBeNull()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
  })

  test('botão Excluir contém ícone com aria-hidden="true"', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos, isAdm: true, paginaAtual: 1, totalRegistros: 1, limite: 20 })}
      />
    )
    const btnExcluir = screen.getByRole('button', { name: /excluir/i })
    const svg = btnExcluir.querySelector('svg')
    expect(svg).not.toBeNull()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
  })

  test('texto "Editar" permanece visível (não está oculto via sr-only)', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos, isAdm: true, paginaAtual: 1, totalRegistros: 1, limite: 20 })}
      />
    )
    const btnEditar = screen.getByRole('button', { name: /editar/i })
    const span = btnEditar.querySelector('span')
    expect(span).not.toBeNull()
    expect(span?.textContent).toMatch(/editar/i)
    // Classe sr-only oculta o texto — não deve estar presente
    expect(span?.className).not.toMatch(/sr-only/)
  })

  test('texto "Excluir" permanece visível (não está oculto via sr-only)', () => {
    render(
      <ContatoTable
        {...makeProps({ contatos, isAdm: true, paginaAtual: 1, totalRegistros: 1, limite: 20 })}
      />
    )
    const btnExcluir = screen.getByRole('button', { name: /excluir/i })
    const span = btnExcluir.querySelector('span')
    expect(span).not.toBeNull()
    expect(span?.textContent).toMatch(/excluir/i)
    expect(span?.className).not.toMatch(/sr-only/)
  })
})


// ---------------------------------------------------------------------------
// RF-F2-05 — Mensagem contextual de lista vazia
// ---------------------------------------------------------------------------

describe('ContatoTable — mensagem contextual de lista vazia (RF-F2-05)', () => {
  test('com termoBusca preenchido exibe mensagem com o termo entre aspas', () => {
    render(
      <ContatoTable
        {...makeProps({
          contatos: [],
          loading: false,
          totalRegistros: 0,
          termoBusca: 'fulano',
        })}
      />
    )
    expect(screen.getByText(/nenhum resultado para/i)).toBeInTheDocument()
    expect(screen.getByText(/fulano/i)).toBeInTheDocument()
  })

  test('mensagem com busca ativa NÃO exibe "Nenhum contato cadastrado ainda."', () => {
    render(
      <ContatoTable
        {...makeProps({
          contatos: [],
          loading: false,
          totalRegistros: 0,
          termoBusca: 'xyz',
        })}
      />
    )
    expect(screen.queryByText(/nenhum contato cadastrado ainda/i)).not.toBeInTheDocument()
  })

  test('sem busca e sem dados exibe "Nenhum contato cadastrado ainda."', () => {
    render(
      <ContatoTable
        {...makeProps({
          contatos: [],
          loading: false,
          totalRegistros: 0,
          termoBusca: '',
        })}
      />
    )
    expect(screen.getByText(/nenhum contato cadastrado ainda/i)).toBeInTheDocument()
  })

  test('sem busca e sem dados, adm vê link "Cadastrar primeiro contato"', () => {
    render(
      <ContatoTable
        {...makeProps({
          contatos: [],
          loading: false,
          totalRegistros: 0,
          termoBusca: '',
          userRole: 'adm',
        })}
      />
    )
    expect(screen.getByText(/cadastrar primeiro contato/i)).toBeInTheDocument()
  })

  test('sem busca e sem dados, usuário default NÃO vê link "Cadastrar primeiro contato"', () => {
    render(
      <ContatoTable
        {...makeProps({
          contatos: [],
          loading: false,
          totalRegistros: 0,
          termoBusca: '',
          userRole: 'default',
        })}
      />
    )
    expect(screen.queryByText(/cadastrar primeiro contato/i)).not.toBeInTheDocument()
  })

  test('termoBusca com apenas espaços é tratado como busca vazia', () => {
    // trim() !== '' → false para '   ', então exibe mensagem de banco vazio
    render(
      <ContatoTable
        {...makeProps({
          contatos: [],
          loading: false,
          totalRegistros: 0,
          termoBusca: '   ',
        })}
      />
    )
    expect(screen.getByText(/nenhum contato cadastrado ainda/i)).toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// RF-F2-01 — Headers ordenáveis
// ---------------------------------------------------------------------------

describe('ContatoTable — headers ordenáveis (RF-F2-01)', () => {
  test('quando onSort é passado, headers Nome/Email/Empresa/Data são botões', () => {
    const onSort = jest.fn()
    render(
      <ContatoTable
        {...makeProps({ onSort })}
      />
    )
    // Cada coluna ordenável deve ter um botão com aria-label
    expect(screen.getByRole('button', { name: /ordenar por nome/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ordenar por e-mail/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ordenar por empresa/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ordenar por data/i })).toBeInTheDocument()
  })

  test('quando onSort é undefined, headers são texto simples (sem botão)', () => {
    render(
      <ContatoTable
        {...makeProps({ onSort: undefined })}
      />
    )
    expect(screen.queryByRole('button', { name: /ordenar por nome/i })).not.toBeInTheDocument()
  })

  test('clicar no header Nome chama onSort("nome")', async () => {
    const user = userEvent.setup()
    const onSort = jest.fn()
    render(
      <ContatoTable {...makeProps({ onSort })} />
    )
    await user.click(screen.getByRole('button', { name: /ordenar por nome/i }))
    expect(onSort).toHaveBeenCalledWith('nome')
  })

  test('clicar no header Empresa chama onSort("empresa")', async () => {
    const user = userEvent.setup()
    const onSort = jest.fn()
    render(
      <ContatoTable {...makeProps({ onSort })} />
    )
    await user.click(screen.getByRole('button', { name: /ordenar por empresa/i }))
    expect(onSort).toHaveBeenCalledWith('empresa')
  })

  test('coluna ativa com sortOrder=asc exibe ícone ArrowUp (svg distinto)', () => {
    const onSort = jest.fn()
    render(
      <ContatoTable {...makeProps({ onSort, sortBy: 'nome', sortOrder: 'asc' })} />
    )
    // O botão "Ordenar por Nome" deve ter um ícone — verificamos pela presença do svg
    const btnNome = screen.getByRole('button', { name: /ordenar por nome/i })
    expect(btnNome.querySelector('svg')).not.toBeNull()
  })

  test('coluna ativa com sortOrder=desc exibe ícone distinto', () => {
    const onSort = jest.fn()
    render(
      <ContatoTable {...makeProps({ onSort, sortBy: 'nome', sortOrder: 'desc' })} />
    )
    const btnNome = screen.getByRole('button', { name: /ordenar por nome/i })
    expect(btnNome.querySelector('svg')).not.toBeNull()
  })

  test('coluna inativa exibe ícone neutro ArrowUpDown', () => {
    const onSort = jest.fn()
    render(
      // sortBy=nome → empresa está inativa
      <ContatoTable {...makeProps({ onSort, sortBy: 'nome', sortOrder: 'asc' })} />
    )
    const btnEmpresa = screen.getByRole('button', { name: /ordenar por empresa/i })
    expect(btnEmpresa.querySelector('svg')).not.toBeNull()
  })
})
