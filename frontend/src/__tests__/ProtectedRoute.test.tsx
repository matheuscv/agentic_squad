/**
 * Testes unitários para ProtectedRoute — TASK-20 (FASE C / RF-07)
 *
 * Componente: frontend/src/components/ProtectedRoute.tsx
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'

const pushMock = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

import ProtectedRoute from '../components/ProtectedRoute'


beforeEach(() => {
  localStorage.clear()
  jest.clearAllMocks()
})


describe('ProtectedRoute', () => {
  test('redireciona para /login quando não há token', async () => {
    render(
      <ProtectedRoute>
        <div data-testid="content">protegido</div>
      </ProtectedRoute>
    )
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith('/login')
    })
    expect(screen.queryByTestId('content')).not.toBeInTheDocument()
  })

  test('renderiza children quando há token', async () => {
    localStorage.setItem('token', 'abc')
    render(
      <ProtectedRoute>
        <div data-testid="content">protegido</div>
      </ProtectedRoute>
    )
    expect(await screen.findByTestId('content')).toBeInTheDocument()
  })

  test('não redireciona quando há token', async () => {
    localStorage.setItem('token', 'abc')
    render(
      <ProtectedRoute>
        <div data-testid="content">protegido</div>
      </ProtectedRoute>
    )
    await screen.findByTestId('content')
    expect(pushMock).not.toHaveBeenCalled()
  })
})
