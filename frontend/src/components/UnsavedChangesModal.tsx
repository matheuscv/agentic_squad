'use client'

// Modal de confirmação para saída sem salvar.
// Implementado com overlay Tailwind puro pois @/components/ui/dialog
// ainda não está scaffolded no projeto (shadcn/ui não inicializado).
// Substituir por <Dialog> do shadcn/ui quando disponível.

interface UnsavedChangesModalProps {
  isOpen: boolean
  onContinue: () => void // "Continuar editando"
  onLeave: () => void    // "Sair sem salvar"
}

export default function UnsavedChangesModal({
  isOpen,
  onContinue,
  onLeave,
}: UnsavedChangesModalProps) {
  if (!isOpen) return null

  return (
    // Overlay que bloqueia interação com o fundo
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="unsaved-modal-title"
    >
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4">
        <h2
          id="unsaved-modal-title"
          className="text-base font-semibold text-gray-900 mb-2"
        >
          Sair sem salvar?
        </h2>
        <p className="text-sm text-gray-600 mb-6">
          Você tem alterações não salvas. Se sair agora, elas serão perdidas.
        </p>
        <div className="flex gap-3 justify-end">
          {/* Botão primário: mantém o usuário na página */}
          <button
            type="button"
            onClick={onContinue}
            className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Continuar editando
          </button>
          {/* Botão secundário: confirma saída */}
          <button
            type="button"
            onClick={onLeave}
            className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            Sair sem salvar
          </button>
        </div>
      </div>
    </div>
  )
}
