/**
 * Testes unitários para LoginPage — TASK-20 (FASE C / RF-07)
 *
 * Página: frontend/src/app/login/page.tsx
 * Cobre:
 *   - Renderização inicial do formulário
 *   - Erros de autenticação (401 / rede)
 *   - Fluxo de sucesso (login + redirecionamento)
 *   - Estado de loading durante submit
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mocks --------------------------------------------------------------

const pushMock = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const loginMock = jest.fn()
jest.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ login: loginMock }),
}))

jest.mock('../services/auth.service', () => ({
  __esModule: true,
  login: jest.fn(),
  getMe: jest.fn(),
}))

// Mock do Link do Next para não exigir contexto de roteamento real
jest.mock('next/link', () => {
  const Link = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  )
  return Link
})

import LoginPage from '../app/login/page'
import * as authService from '../services/auth.service'

const mockedLogin = authService.login as jest.Mock
const mockedGetMe = authService.getMe as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
  localStorage.clear()
})


// ---------------------------------------------------------------------------
// Renderização básica
// ---------------------------------------------------------------------------

describe('LoginPage — renderização', () => {
  test('renderiza título "Entrar"', () => {
    render(<LoginPage />)
    expect(screen.getByRole('heading', { name: /entrar/i })).toBeInTheDocument()
  })

  test('renderiza campos de e-mail e senha', () => {
    render(<LoginPage />)
    expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
  })

  test('renderiza botão "Entrar"', () => {
    render(<LoginPage />)
    expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
  })

  test('renderiza link para cadastro', () => {
    render(<LoginPage />)
    expect(screen.getByText(/criar uma conta/i)).toBeInTheDocument()
  })

  test('input de e-mail é do tipo email', () => {
    render(<LoginPage />)
    const input = screen.getByLabelText(/e-mail/i)
    expect(input).toHaveAttribute('type', 'email')
  })

  test('input de senha é do tipo password', () => {
    render(<LoginPage />)
    const input = screen.getByLabelText(/senha/i)
    expect(input).toHaveAttribute('type', 'password')
  })
})


// ---------------------------------------------------------------------------
// Fluxo de sucesso
// ---------------------------------------------------------------------------

describe('LoginPage — fluxo de sucesso', () => {
  test('chama authService.login com email e senha', async () => {
    const user = userEvent.setup()
    mockedLogin.mockResolvedValueOnce({ access_token: 'tok-123', token_type: 'bearer' })
    mockedGetMe.mockResolvedValueOnce({ id: 1, nome: 'Fulano', email: 'a@a.com', role: 'default' })

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'segredo')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalledWith('a@a.com', 'segredo')
    })
  })

  test('armazena token no localStorage antes de buscar usuário', async () => {
    const user = userEvent.setup()
    mockedLogin.mockResolvedValueOnce({ access_token: 'tok-abc', token_type: 'bearer' })
    mockedGetMe.mockResolvedValueOnce({ id: 1, nome: 'Fulano', email: 'a@a.com', role: 'default' })

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'segredo')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('tok-abc')
    })
  })

  test('chama login() do contexto após buscar usuário', async () => {
    const user = userEvent.setup()
    const usuario = { id: 1, nome: 'Fulano', email: 'a@a.com', role: 'default' as const }
    mockedLogin.mockResolvedValueOnce({ access_token: 'tok-xyz', token_type: 'bearer' })
    mockedGetMe.mockResolvedValueOnce(usuario)

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'pwd')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('tok-xyz', usuario)
    })
  })

  test('redireciona para /contatos após login bem-sucedido', async () => {
    const user = userEvent.setup()
    mockedLogin.mockResolvedValueOnce({ access_token: 'tok', token_type: 'bearer' })
    mockedGetMe.mockResolvedValueOnce({ id: 1, nome: 'F', email: 'a@a.com', role: 'default' })

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'pwd')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/contatos')
    })
  })
})


// ---------------------------------------------------------------------------
// Erros
// ---------------------------------------------------------------------------

describe('LoginPage — fluxo de erro', () => {
  test('exibe mensagem genérica quando authService.login lança erro', async () => {
    const user = userEvent.setup()
    mockedLogin.mockRejectedValueOnce(new Error('401'))

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'errada')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(await screen.findByText(/e-mail ou senha inválidos/i)).toBeInTheDocument()
  })

  test('não redireciona quando login falha', async () => {
    const user = userEvent.setup()
    mockedLogin.mockRejectedValueOnce(new Error('Network'))

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'pwd')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    await screen.findByText(/e-mail ou senha inválidos/i)
    expect(pushMock).not.toHaveBeenCalled()
  })

  test('exibe erro mesmo quando getMe falha após login bem-sucedido', async () => {
    const user = userEvent.setup()
    mockedLogin.mockResolvedValueOnce({ access_token: 'tok', token_type: 'bearer' })
    mockedGetMe.mockRejectedValueOnce(new Error('boom'))

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'pwd')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(await screen.findByText(/e-mail ou senha inválidos/i)).toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// Estado de loading
// ---------------------------------------------------------------------------

describe('LoginPage — loading', () => {
  test('exibe "Entrando..." durante submit', async () => {
    const user = userEvent.setup()
    // Promise que nunca resolve durante este teste — segura o estado em loading
    let resolveLogin: (v: unknown) => void = () => {}
    mockedLogin.mockImplementationOnce(
      () => new Promise((resolve) => { resolveLogin = resolve })
    )

    render(<LoginPage />)
    await user.type(screen.getByLabelText(/e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), 'pwd')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(await screen.findByRole('button', { name: /entrando\.\.\./i })).toBeDisabled()
    // libera para evitar warning do React
    resolveLogin({ access_token: 'tok', token_type: 'bearer' })
  })
})
