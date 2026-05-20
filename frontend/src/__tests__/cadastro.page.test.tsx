/**
 * Testes unitários para CadastroPage — TASK-20 (FASE C / RF-07)
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const pushMock = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

jest.mock('../services/auth.service', () => ({
  __esModule: true,
  cadastrar: jest.fn(),
}))

jest.mock('next/link', () => {
  const Link = ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  )
  return Link
})

import CadastroPage from '../app/cadastro/page'
import * as authService from '../services/auth.service'

const mockedCadastrar = authService.cadastrar as jest.Mock


beforeEach(() => {
  jest.clearAllMocks()
})


describe('CadastroPage — renderização', () => {
  test('exibe título "Criar Conta"', () => {
    render(<CadastroPage />)
    expect(screen.getByRole('heading', { name: /criar conta/i })).toBeInTheDocument()
  })

  test('exibe campos nome, email e senha', () => {
    render(<CadastroPage />)
    expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^e-mail/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
  })

  test('exibe link "Já tenho uma conta"', () => {
    render(<CadastroPage />)
    expect(screen.getByText(/já tenho uma conta/i)).toBeInTheDocument()
  })
})


describe('CadastroPage — validação client-side', () => {
  test('exibe erro quando nome está vazio', async () => {
    const user = userEvent.setup()
    render(<CadastroPage />)
    await user.click(screen.getByRole('button', { name: /criar conta/i }))
    expect(await screen.findByText(/nome.*obrigat/i)).toBeInTheDocument()
    expect(mockedCadastrar).not.toHaveBeenCalled()
  })

  test('exibe erro quando e-mail está vazio', async () => {
    const user = userEvent.setup()
    render(<CadastroPage />)
    await user.type(screen.getByLabelText(/nome completo/i), 'A')
    await user.click(screen.getByRole('button', { name: /criar conta/i }))
    expect(await screen.findByText(/e-mail.*obrigat/i)).toBeInTheDocument()
  })

  test('exibe erro quando senha < 6 caracteres', async () => {
    const user = userEvent.setup()
    render(<CadastroPage />)
    await user.type(screen.getByLabelText(/nome completo/i), 'A')
    await user.type(screen.getByLabelText(/^e-mail/i), 'a@a.com')
    await user.type(screen.getByLabelText(/senha/i), '123')
    await user.click(screen.getByRole('button', { name: /criar conta/i }))
    expect(await screen.findByText(/mínimo 6 caracteres/i)).toBeInTheDocument()
  })
})


describe('CadastroPage — submit', () => {
  test('chama authService.cadastrar com dados válidos', async () => {
    const user = userEvent.setup()
    mockedCadastrar.mockResolvedValueOnce({
      id: 1, nome: 'João', email: 'j@j.com', role: 'default',
    })
    render(<CadastroPage />)
    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.type(screen.getByLabelText(/^e-mail/i), 'j@j.com')
    await user.type(screen.getByLabelText(/senha/i), '123456')
    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    await waitFor(() => {
      expect(mockedCadastrar).toHaveBeenCalledWith('João', 'j@j.com', '123456')
    })
  })

  test('exibe erro "e-mail já cadastrado" em caso de 400', async () => {
    const user = userEvent.setup()
    mockedCadastrar.mockRejectedValueOnce(
      Object.assign(new Error('Bad Request'), { response: { status: 400 } })
    )
    render(<CadastroPage />)
    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.type(screen.getByLabelText(/^e-mail/i), 'j@j.com')
    await user.type(screen.getByLabelText(/senha/i), '123456')
    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    expect(await screen.findByText(/e-mail.*já está cadastrado/i)).toBeInTheDocument()
  })

  test('exibe mensagem genérica em outros erros', async () => {
    const user = userEvent.setup()
    mockedCadastrar.mockRejectedValueOnce(new Error('Network Error'))
    render(<CadastroPage />)
    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.type(screen.getByLabelText(/^e-mail/i), 'j@j.com')
    await user.type(screen.getByLabelText(/senha/i), '123456')
    await user.click(screen.getByRole('button', { name: /criar conta/i }))

    expect(await screen.findByText(/erro ao criar a conta/i)).toBeInTheDocument()
  })

  test('exibe mensagem de sucesso e redireciona para /login após delay', async () => {
    jest.useFakeTimers({ advanceTimers: true })
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
    try {
      mockedCadastrar.mockResolvedValueOnce({
        id: 1, nome: 'João', email: 'j@j.com', role: 'default',
      })
      render(<CadastroPage />)
      await user.type(screen.getByLabelText(/nome completo/i), 'João')
      await user.type(screen.getByLabelText(/^e-mail/i), 'j@j.com')
      await user.type(screen.getByLabelText(/senha/i), '123456')
      await user.click(screen.getByRole('button', { name: /criar conta/i }))

      expect(await screen.findByText(/conta criada com sucesso/i)).toBeInTheDocument()

      jest.advanceTimersByTime(2100)
      await waitFor(() => {
        expect(pushMock).toHaveBeenCalledWith('/login')
      })
    } finally {
      jest.useRealTimers()
    }
  })
})
