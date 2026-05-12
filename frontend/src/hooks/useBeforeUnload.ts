import { useEffect } from 'react'

/**
 * Intercepta fechamento/reload de aba quando há alterações não salvas.
 * Adiciona o listener `beforeunload` apenas quando isDirty === true,
 * removendo-o automaticamente no cleanup ou quando isDirty voltar a false.
 */
export function useBeforeUnload(isDirty: boolean): void {
  useEffect(() => {
    if (!isDirty) return

    function handleBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault()
      // Necessário para navegadores mais antigos exibirem o diálogo nativo
      event.returnValue = ''
    }

    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [isDirty])
}
