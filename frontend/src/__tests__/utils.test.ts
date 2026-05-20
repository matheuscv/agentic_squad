/**
 * Testes unitários para lib/utils.ts — TASK-20 (FASE C / RF-07)
 */

import { cn } from '../lib/utils'


describe('cn (className merger)', () => {
  test('concatena classes simples', () => {
    expect(cn('a', 'b')).toBe('a b')
  })

  test('ignora valores falsy', () => {
    expect(cn('a', false, null, undefined, 'b')).toBe('a b')
  })

  test('aplica regras de tailwind-merge (último prevalece)', () => {
    // padding x — o "px-4" deve sobrescrever o "px-2"
    expect(cn('px-2', 'px-4')).toBe('px-4')
  })

  test('aceita arrays e objetos (clsx)', () => {
    expect(cn(['a', 'b'], { c: true, d: false })).toBe('a b c')
  })

  test('sem argumentos retorna string vazia', () => {
    expect(cn()).toBe('')
  })
})
