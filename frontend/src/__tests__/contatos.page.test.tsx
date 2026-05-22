/**
 * Testes unitários para a página de Contatos — TASK-20 (FASE C / RF-07)
 *
 * Página: frontend/src/app/contatos/page.tsx
 * Cobre:
 *   - Busca com debounce (chamadas à API)
 *   - Paginação (skip/limit)
 *   - Botão "Novo Contato" só visível para adm
 *   - Renderização da listagem
 */

import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mocks --------------------------------------------------------------

const pushMock = jest.fn()
const replaceMock = jest.fn()
// Fase D / TASK-07 e TASK-09: a pagina agora usa usePathname e
// useSearchParams para sincronizar sort + filtros com a URL. Adicionamos
// mocks consistentes para que o componente renderize sem TypeError.
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock, replace: replaceMock }),
  usePathname: () => '/contatos',
  useSearchParams: () => new URLSearchParams(),
}))

jest.mock('../components/ProtectedRoute', () => {
  return {
    __esModule: true,
    default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  }
})

// Mock do hook useAuth — começamos como adm (Botão "Novo Contato" visível)
const mockUseAuth = jest.fn()
jest.mock('../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}))

// Mock do service de contatos
jest.mock('../services/contatos.service', () => ({
  __esModule: true,
  listarContatos: jest.fn(),
  excluirContato: jest.fn(),
}))

import ContatosPage from '../app/contatos/page'
import * as contatosService from '../services/contatos.service'

const mockedListar = contatosService.listarContatos as jest.Mock
const mockedExcluir = contatosService.excluirContato as jest.Mock


beforeEach(() => {
  jest.clearAllMocks()
  mockUseAuth.mockReturnValue({
    isAdm: true,
    usuario: { id: 1, nome: 'Admin', email: 'a@a.com', role: 'adm' },
  })
  mockedListar.mockResolvedValue({ items: [], total: 0 })
})


// ---------------------------------------------------------------------------
// Renderização inicial
// ---------------------------------------------------------------------------

describe('ContatosPage — renderização inicial', () => {
  test('exibe título "Contatos"', async () => {
    render(<ContatosPage />)
    expect(await screen.findByRole('heading', { name: /^contatos$/i })).toBeInTheDocument()
  })

  test('exibe botão "Novo Contato" quando usuário é adm', async () => {
    render(<ContatosPage />)
    expect(await screen.findByRole('button', { name: /novo contato/i })).toBeInTheDocument()
  })

  test('NÃO exibe botão "Novo Contato" quando usuário não é adm', async () => {
    mockUseAuth.mockReturnValue({
      isAdm: false,
      usuario: { id: 1, nome: 'User', email: 'u@u.com', role: 'default' },
    })
    render(<ContatosPage />)
    // Aguarda renderização
    await screen.findByRole('heading', { name: /^contatos$/i })
    expect(screen.queryByRole('button', { name: /novo contato/i })).not.toBeInTheDocument()
  })

  test('exibe campo de busca', async () => {
    render(<ContatosPage />)
    expect(
      await screen.findByPlaceholderText(/pesquisar por nome/i)
    ).toBeInTheDocument()
  })

  test('chama listarContatos no mount', async () => {
    render(<ContatosPage />)
    await waitFor(() => {
      expect(mockedListar).toHaveBeenCalled()
    })
  })
})


// ---------------------------------------------------------------------------
// Busca com debounce
// ---------------------------------------------------------------------------

describe('ContatosPage — busca com debounce', () => {
  test('chama listarContatos com termo após debounce', async () => {
    jest.useFakeTimers({ advanceTimers: true })
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
    try {
      render(<ContatosPage />)
      await screen.findByPlaceholderText(/pesquisar por nome/i)
      mockedListar.mockClear()

      const input = screen.getByPlaceholderText(/pesquisar por nome/i)
      await user.type(input, 'joao')

      // Avança o tempo para passar do debounce (400ms)
      await act(async () => {
        jest.advanceTimersByTime(500)
      })

      await waitFor(() => {
        const chamadas = mockedListar.mock.calls
        // A última chamada deve incluir o termo digitado
        const ultimaChamada = chamadas[chamadas.length - 1]
        expect(ultimaChamada[0]).toBe('joao')
      })
    } finally {
      jest.useRealTimers()
    }
  })

  test('reseta paginação para página 1 ao alterar o termo de busca', async () => {
    jest.useFakeTimers({ advanceTimers: true })
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
    try {
      render(<ContatosPage />)
      await screen.findByPlaceholderText(/pesquisar por nome/i)
      mockedListar.mockClear()

      const input = screen.getByPlaceholderText(/pesquisar por nome/i)
      await user.type(input, 'X')

      await act(async () => {
        jest.advanceTimersByTime(500)
      })

      await waitFor(() => {
        const ultima = mockedListar.mock.calls[mockedListar.mock.calls.length - 1]
        // listarContatos(busca, skip=0, limit=20, sortBy, sortOrder)
        expect(ultima[1]).toBe(0)
        expect(ultima[2]).toBe(20)
      })
    } finally {
      jest.useRealTimers()
    }
  })
})


// ---------------------------------------------------------------------------
// Listagem
// ---------------------------------------------------------------------------

describe('ContatosPage — listagem', () => {
  test('exibe contatos retornados pela API', async () => {
    mockedListar.mockResolvedValueOnce({
      items: [
        {
          id: 1,
          nome: 'Fulano',
          email: 'fulano@x.com',
          telefone: null,
          empresa: null,
          observacoes: null,
          criado_em: '2026-01-01T00:00:00Z',
          atualizado_em: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    render(<ContatosPage />)
    expect(await screen.findByText('Fulano')).toBeInTheDocument()
  })

  test('exibe mensagem de erro quando API falha', async () => {
    mockedListar.mockRejectedValueOnce(new Error('boom'))
    render(<ContatosPage />)
    expect(
      await screen.findByText(/não foi possível carregar/i)
    ).toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// Navegação
// ---------------------------------------------------------------------------

describe('ContatosPage — navegação', () => {
  test('clicar em "Novo Contato" navega para /contatos/novo', async () => {
    const user = userEvent.setup()
    render(<ContatosPage />)
    const btn = await screen.findByRole('button', { name: /novo contato/i })
    await user.click(btn)
    expect(pushMock).toHaveBeenCalledWith('/contatos/novo')
  })
})


// ---------------------------------------------------------------------------
// Exclusão
// ---------------------------------------------------------------------------

describe('ContatosPage — exclusão', () => {
  test('exibe modal de confirmação ao clicar em Excluir', async () => {
    const user = userEvent.setup()
    mockedListar.mockResolvedValueOnce({
      items: [
        {
          id: 7,
          nome: 'Beltrano',
          email: 'beltrano@x.com',
          telefone: null,
          empresa: null,
          observacoes: null,
          criado_em: '2026-01-01T00:00:00Z',
          atualizado_em: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })
    render(<ContatosPage />)
    await screen.findByText('Beltrano')

    await user.click(screen.getByRole('button', { name: /excluir/i }))
    expect(await screen.findByText(/tem certeza/i)).toBeInTheDocument()
  })

  test('confirmar exclusão chama excluirContato com o id correto', async () => {
    const user = userEvent.setup()
    mockedListar.mockResolvedValueOnce({
      items: [
        {
          id: 9,
          nome: 'Sicrano',
          email: 'sicrano@x.com',
          telefone: null,
          empresa: null,
          observacoes: null,
          criado_em: '2026-01-01T00:00:00Z',
          atualizado_em: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })
    mockedExcluir.mockResolvedValueOnce(undefined)
    render(<ContatosPage />)
    await screen.findByText('Sicrano')

    await user.click(screen.getByRole('button', { name: /excluir/i }))
    // Clica no botão Confirmar do modal
    const confirmar = await screen.findByRole('button', { name: /^confirmar$/i })
    await user.click(confirmar)

    await waitFor(() => {
      expect(mockedExcluir).toHaveBeenCalledWith(9)
    })
  })
})
