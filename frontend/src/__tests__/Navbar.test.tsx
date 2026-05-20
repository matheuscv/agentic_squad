/**
 * Testes unitários para Navbar — TASK-20 (FASE C / RF-07)
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const mockUseAuth = jest.fn()
jest.mock('../hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
}))

import Navbar from '../components/Navbar'


beforeEach(() => {
  jest.clearAllMocks()
})


describe('Navbar', () => {
  test('exibe o título da aplicação', () => {
    mockUseAuth.mockReturnValue({ usuario: null, logout: jest.fn() })
    render(<Navbar />)
    expect(screen.getByText(/contatos de clientes/i)).toBeInTheDocument()
  })

  test('NÃO exibe área do usuário quando usuario=null', () => {
    mockUseAuth.mockReturnValue({ usuario: null, logout: jest.fn() })
    render(<Navbar />)
    expect(screen.queryByText(/olá/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sair/i })).not.toBeInTheDocument()
  })

  test('exibe nome do usuário quando autenticado', () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: 1, nome: 'Maria', email: 'm@m.com', role: 'default' },
      logout: jest.fn(),
    })
    render(<Navbar />)
    expect(screen.getByText('Maria')).toBeInTheDocument()
  })

  test('exibe botão "Sair" quando autenticado', () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: 1, nome: 'Maria', email: 'm@m.com', role: 'default' },
      logout: jest.fn(),
    })
    render(<Navbar />)
    expect(screen.getByRole('button', { name: /sair/i })).toBeInTheDocument()
  })

  test('clicar em "Sair" chama logout', async () => {
    const logout = jest.fn()
    mockUseAuth.mockReturnValue({
      usuario: { id: 1, nome: 'Maria', email: 'm@m.com', role: 'default' },
      logout,
    })
    const user = userEvent.setup()
    render(<Navbar />)
    await user.click(screen.getByRole('button', { name: /sair/i }))
    expect(logout).toHaveBeenCalledTimes(1)
  })
})
