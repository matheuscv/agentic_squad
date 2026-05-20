import { useEffect, useState } from 'react'

/**
 * Hook genérico de debounce.
 *
 * Retorna o valor `value` somente após `delay` milissegundos sem mudanças.
 * Útil para evitar chamadas excessivas a APIs em campos de busca, filtros
 * dinâmicos e outros inputs reativos.
 *
 * Tipado de forma genérica (<T>) para preservar o tipo do valor original —
 * funciona com string, number, objetos, etc.
 *
 * @template T Tipo do valor a ser debounced.
 * @param value Valor reativo a ser observado.
 * @param delay Atraso em milissegundos antes de propagar a mudança.
 * @returns O valor "estabilizado" após o intervalo de inatividade.
 *
 * @example
 * // Debouncing de campo de busca (uso típico)
 * const [termoInput, setTermoInput] = useState('')
 * const termoDebounced = useDebounce(termoInput, 400)
 *
 * useEffect(() => {
 *   listar(termoDebounced)
 * }, [termoDebounced])
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    // Agenda a atualização do valor debounced.
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    // Cleanup: cancela o timer pendente sempre que `value` ou `delay`
    // mudarem antes do tempo expirar, garantindo o debounce real.
    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}
