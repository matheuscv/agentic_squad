'use client'

import { Contato } from '../types'

interface ContatoDetalheProps {
  contato: Contato
  isAdm: boolean
  onEditar: () => void
  onExcluir: () => void
}

// Helper: formata data ISO para pt-BR ou retorna null
function formatarData(valor: string | undefined | null): string | null {
  if (!valor) return null
  const data = new Date(valor)
  if (isNaN(data.getTime())) return null
  return data.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Linha individual de campo
function Campo({
  label,
  valor,
}: {
  label: string
  valor: string | undefined | null
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:gap-4 py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm font-medium text-gray-500 sm:w-36 shrink-0">
        {label}
      </span>
      {valor ? (
        <span className="text-sm text-gray-900">{valor}</span>
      ) : (
        <span className="text-sm text-gray-400 italic">Não informado</span>
      )}
    </div>
  )
}

export default function ContatoDetalhe({
  contato,
  isAdm,
  onEditar,
  onExcluir,
}: ContatoDetalheProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6 max-w-xl">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Detalhes do Contato
      </h2>

      <div className="space-y-0">
        <Campo label="Nome" valor={contato.nome} />
        <Campo label="E-mail" valor={contato.email} />
        <Campo label="Telefone" valor={contato.telefone} />
        <Campo label="Empresa" valor={contato.empresa} />
        <Campo label="Observações" valor={contato.observacoes} />
        <Campo label="Criado em" valor={formatarData(contato.criado_em)} />
        <Campo
          label="Atualizado em"
          valor={formatarData(contato.atualizado_em)}
        />
      </div>

      {/* Botões visíveis apenas para administradores */}
      {isAdm && (
        <div className="flex gap-3 mt-6 pt-4 border-t border-gray-100">
          <button
            onClick={onEditar}
            className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Editar
          </button>
          <button
            onClick={onExcluir}
            className="px-4 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Excluir
          </button>
        </div>
      )}
    </div>
  )
}
