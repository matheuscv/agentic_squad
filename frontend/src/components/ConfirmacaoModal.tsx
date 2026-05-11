'use client'

import React, { useEffect, useCallback } from 'react'

interface ConfirmacaoModalProps {
  aberto: boolean
  titulo: string
  mensagem: string
  onConfirmar: () => void
  onCancelar: () => void
  loading?: boolean
}

export default function ConfirmacaoModal({
  aberto,
  titulo,
  mensagem,
  onConfirmar,
  onCancelar,
  loading = false,
}: ConfirmacaoModalProps) {
  // Fecha ao pressionar Escape
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) {
        onCancelar()
      }
    },
    [onCancelar, loading]
  )

  useEffect(() => {
    if (aberto) {
      document.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [aberto, handleKeyDown])

  // Não renderiza nada quando fechado
  if (!aberto) return null

  return (
    /* Overlay: clique fora fecha o modal (se não estiver carregando) */
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
      onClick={() => !loading && onCancelar()}
      aria-modal="true"
      role="dialog"
      aria-labelledby="modal-titulo"
    >
      {/* Card do modal — stopPropagation para não fechar ao clicar dentro */}
      <div
        className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4"
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
      >
        <h2
          id="modal-titulo"
          className="text-lg font-semibold text-gray-900 mb-2"
        >
          {titulo}
        </h2>
        <p className="text-gray-600 mb-6">{mensagem}</p>

        <div className="flex justify-end gap-3">
          {/* Botão Cancelar */}
          <button
            onClick={onCancelar}
            disabled={loading}
            className="px-4 py-2 rounded-md text-sm font-medium border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            Cancelar
          </button>

          {/* Botão Confirmar */}
          <button
            onClick={onConfirmar}
            disabled={loading}
            className="px-4 py-2 rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 flex items-center gap-2"
          >
            {loading && (
              /* Spinner simples com border */
              <span
                className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"
                aria-hidden="true"
              />
            )}
            Confirmar
          </button>
        </div>
      </div>
    </div>
  )
}
