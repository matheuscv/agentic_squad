/**
 * Testes unitários para useDebounce — TASK-20 (FASE C / RF-C2)
 *
 * Hook: frontend/src/hooks/useDebounce.ts
 * Cobre:
 *   - Valor inicial é retornado imediatamente
 *   - Atualização do valor é "atrasada" pelo delay informado
 *   - Mudanças rápidas cancelam o timer anterior (debounce real)
 *   - Cleanup limpa o timer ao desmontar
 */

import { renderHook, act } from '@testing-library/react'
import { useDebounce } from '../hooks/useDebounce'

beforeEach(() => {
  jest.useFakeTimers()
})

afterEach(() => {
  jest.useRealTimers()
})


describe('useDebounce', () => {
  test('retorna o valor inicial imediatamente', () => {
    const { result } = renderHook(() => useDebounce('inicial', 300))
    expect(result.current).toBe('inicial')
  })

  test('não propaga novo valor antes do delay', () => {
    const { result, rerender } = renderHook(
      ({ v, d }: { v: string; d: number }) => useDebounce(v, d),
      { initialProps: { v: 'a', d: 500 } }
    )
    rerender({ v: 'b', d: 500 })
    // Antes do timer expirar — valor anterior ainda é exposto
    expect(result.current).toBe('a')
  })

  test('propaga novo valor após o delay expirar', () => {
    const { result, rerender } = renderHook(
      ({ v, d }: { v: string; d: number }) => useDebounce(v, d),
      { initialProps: { v: 'a', d: 500 } }
    )
    rerender({ v: 'b', d: 500 })

    act(() => {
      jest.advanceTimersByTime(500)
    })

    expect(result.current).toBe('b')
  })

  test('mudanças rápidas resetam o timer (debounce real)', () => {
    const { result, rerender } = renderHook(
      ({ v }: { v: string }) => useDebounce(v, 400),
      { initialProps: { v: 'a' } }
    )
    rerender({ v: 'b' })
    act(() => jest.advanceTimersByTime(200)) // ainda dentro do delay
    rerender({ v: 'c' })
    act(() => jest.advanceTimersByTime(200)) // 200ms após a última mudança
    // Não passaram 400ms desde a última mudança — ainda exibe valor original
    expect(result.current).toBe('a')

    act(() => jest.advanceTimersByTime(200)) // total: 400ms após "c"
    expect(result.current).toBe('c')
  })

  test('preserva o tipo genérico (number)', () => {
    const { result, rerender } = renderHook(
      ({ v }: { v: number }) => useDebounce(v, 100),
      { initialProps: { v: 1 } }
    )
    rerender({ v: 42 })
    act(() => jest.advanceTimersByTime(100))
    expect(result.current).toBe(42)
  })

  test('cleanup cancela o timer ao desmontar', () => {
    const { unmount, rerender } = renderHook(
      ({ v }: { v: string }) => useDebounce(v, 500),
      { initialProps: { v: 'a' } }
    )
    rerender({ v: 'b' })
    // Desmonta antes do timer — não deve disparar erros
    expect(() => {
      unmount()
      jest.advanceTimersByTime(500)
    }).not.toThrow()
  })
})
