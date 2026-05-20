/**
 * Testes unitários para useAuth / AuthProvider — TASK-20 (FASE C / RF-07)
 *
 * Arquivo: frontend/src/hooks/useAuth.tsx
 */

import React from 'react'
import { renderHook, act } from '@testing-library/react'

const pushMock = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

import { AuthProvider, useAuth } from '../hooks/useAuth'

const USUARIO_DEFAULT = { id: 1, nome: 'A', email: 'a@a.com', role: 'default' as const }
const USUARIO_ADM = { id: 2, nome: 'Adm', email: 'b@b.com', role: 'adm' as const }


function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}


beforeEach(() => {
  localStorage.clear()
  jest.clearAllMocks()
})


describe('useAuth', () => {
  test('lança erro quando usado fora do AuthProvider', () => {
    // Suprime o console.error padrão do React para teste de erro
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => renderHook(() => useAuth())).toThrow(/useAuth.*AuthProvider/)
    spy.mockRestore()
  })

  test('retorna estado inicial sem usuário/token', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.usuario).toBeNull()
    expect(result.current.token).toBeNull()
    expect(result.current.isAdm).toBe(false)
  })

  test('login persiste token e usuário no localStorage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login('tok-1', USUARIO_DEFAULT)
    })

    expect(localStorage.getItem('token')).toBe('tok-1')
    expect(JSON.parse(localStorage.getItem('usuario')!)).toEqual(USUARIO_DEFAULT)
    expect(result.current.usuario).toEqual(USUARIO_DEFAULT)
    expect(result.current.token).toBe('tok-1')
  })

  test('isAdm=true quando usuário tem role adm', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login('tok-2', USUARIO_ADM)
    })

    expect(result.current.isAdm).toBe(true)
  })

  test('isAdm=false quando usuário tem role default', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login('tok-3', USUARIO_DEFAULT)
    })

    expect(result.current.isAdm).toBe(false)
  })

  test('logout limpa estado e localStorage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.login('tok-4', USUARIO_DEFAULT)
    })

    act(() => {
      result.current.logout()
    })

    expect(result.current.usuario).toBeNull()
    expect(result.current.token).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('usuario')).toBeNull()
    expect(pushMock).toHaveBeenCalledWith('/login')
  })

  test('restaura sessão do localStorage ao montar', () => {
    localStorage.setItem('token', 'persisted-token')
    localStorage.setItem('usuario', JSON.stringify(USUARIO_DEFAULT))

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.token).toBe('persisted-token')
    expect(result.current.usuario).toEqual(USUARIO_DEFAULT)
  })

  test('descarta usuario corrompido (JSON inválido) do localStorage', () => {
    localStorage.setItem('token', 't')
    localStorage.setItem('usuario', '{json-quebrado}')

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.usuario).toBeNull()
    // Item corrompido foi removido
    expect(localStorage.getItem('usuario')).toBeNull()
  })
})
