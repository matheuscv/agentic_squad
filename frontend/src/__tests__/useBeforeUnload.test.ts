/**
 * Testes unitários para useBeforeUnload — RF-F2-06 (Fase 2)
 *
 * Hook: frontend/src/hooks/useBeforeUnload.ts
 * Critérios de aceite (PRD 14.4 — RF-F2-06):
 *   - Listener beforeunload é adicionado quando isDirty=true
 *   - Listener beforeunload é removido quando isDirty=false
 *   - Listener é removido no cleanup (unmount)
 *   - event.preventDefault() e event.returnValue='' são chamados no handler
 */

import { renderHook } from '@testing-library/react'
import { useBeforeUnload } from '../hooks/useBeforeUnload'

// ---------------------------------------------------------------------------
// Setup: espionar addEventListener/removeEventListener do window
// ---------------------------------------------------------------------------

let addEventSpy: jest.SpyInstance
let removeEventSpy: jest.SpyInstance

beforeEach(() => {
  addEventSpy = jest.spyOn(window, 'addEventListener')
  removeEventSpy = jest.spyOn(window, 'removeEventListener')
})

afterEach(() => {
  addEventSpy.mockRestore()
  removeEventSpy.mockRestore()
})


// ---------------------------------------------------------------------------
// isDirty = true — listener deve ser adicionado
// ---------------------------------------------------------------------------

describe('useBeforeUnload — isDirty=true', () => {
  test('adiciona listener beforeunload quando isDirty é true', () => {
    renderHook(() => useBeforeUnload(true))

    expect(addEventSpy).toHaveBeenCalledWith(
      'beforeunload',
      expect.any(Function)
    )
  })

  test('o listener chama event.preventDefault()', () => {
    renderHook(() => useBeforeUnload(true))

    // Captura a função handler registrada
    const [[, handler]] = addEventSpy.mock.calls.filter(
      ([event]) => event === 'beforeunload'
    )

    const fakeEvent = { preventDefault: jest.fn(), returnValue: '' } as unknown as BeforeUnloadEvent
    handler(fakeEvent)

    expect(fakeEvent.preventDefault).toHaveBeenCalledTimes(1)
  })

  test('o listener define event.returnValue como string vazia', () => {
    renderHook(() => useBeforeUnload(true))

    const [[, handler]] = addEventSpy.mock.calls.filter(
      ([event]) => event === 'beforeunload'
    )

    const fakeEvent = { preventDefault: jest.fn(), returnValue: '' } as unknown as BeforeUnloadEvent
    handler(fakeEvent)

    expect(fakeEvent.returnValue).toBe('')
  })
})


// ---------------------------------------------------------------------------
// isDirty = false — listener NÃO deve ser adicionado
// ---------------------------------------------------------------------------

describe('useBeforeUnload — isDirty=false', () => {
  test('NÃO adiciona listener beforeunload quando isDirty é false', () => {
    renderHook(() => useBeforeUnload(false))

    const beforeunloadCalls = addEventSpy.mock.calls.filter(
      ([event]) => event === 'beforeunload'
    )
    expect(beforeunloadCalls).toHaveLength(0)
  })
})


// ---------------------------------------------------------------------------
// Cleanup — listener deve ser removido ao desmontar
// ---------------------------------------------------------------------------

describe('useBeforeUnload — cleanup no unmount', () => {
  test('remove o listener beforeunload ao desmontar com isDirty=true', () => {
    const { unmount } = renderHook(() => useBeforeUnload(true))

    unmount()

    expect(removeEventSpy).toHaveBeenCalledWith(
      'beforeunload',
      expect.any(Function)
    )
  })

  test('o handler adicionado é o mesmo removido no cleanup', () => {
    const { unmount } = renderHook(() => useBeforeUnload(true))

    const addedHandler = addEventSpy.mock.calls.find(
      ([event]) => event === 'beforeunload'
    )?.[1]

    unmount()

    const removedHandler = removeEventSpy.mock.calls.find(
      ([event]) => event === 'beforeunload'
    )?.[1]

    expect(addedHandler).toBe(removedHandler)
  })
})


// ---------------------------------------------------------------------------
// Transição isDirty: false → true → false
// ---------------------------------------------------------------------------

describe('useBeforeUnload — transição de isDirty', () => {
  test('adiciona listener quando isDirty muda de false para true', () => {
    const { rerender } = renderHook(
      ({ dirty }: { dirty: boolean }) => useBeforeUnload(dirty),
      { initialProps: { dirty: false } }
    )

    expect(addEventSpy).not.toHaveBeenCalledWith('beforeunload', expect.any(Function))

    rerender({ dirty: true })

    expect(addEventSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))
  })

  test('remove o listener quando isDirty muda de true para false', () => {
    const { rerender } = renderHook(
      ({ dirty }: { dirty: boolean }) => useBeforeUnload(dirty),
      { initialProps: { dirty: true } }
    )

    rerender({ dirty: false })

    // O cleanup do effect anterior remove o listener
    expect(removeEventSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))
  })
})
