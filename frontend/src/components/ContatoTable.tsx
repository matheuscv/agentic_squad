'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Contato } from '../types'

interface ContatoTableProps {
  contatos: Contato[]
  isAdm: boolean
  onEditar: (id: number) => void
  onExcluir: (id: number) => void
  loading: boolean
}

// Skeleton de linha para estado de carregamento
function SkeletonRow() {
  return (
    <tr>
      {[...Array(5)].map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  )
}

export default function ContatoTable({
  contatos,
  isAdm,
  onEditar,
  onExcluir,
  loading,
}: ContatoTableProps) {
  const router = useRouter()

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            {['Nome', 'E-mail', 'Telefone', 'Empresa', 'Ações'].map((col) => (
              <th
                key={col}
                className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>

        <tbody className="divide-y divide-gray-100">
          {/* Estado de carregamento: 5 linhas skeleton */}
          {loading &&
            [...Array(5)].map((_, i) => <SkeletonRow key={i} />)}

          {/* Lista vazia */}
          {!loading && contatos.length === 0 && (
            <tr>
              <td
                colSpan={5}
                className="px-4 py-8 text-center text-gray-400 italic"
              >
                Nenhum contato encontrado.
              </td>
            </tr>
          )}

          {/* Linhas de dados */}
          {!loading &&
            contatos.map((contato) => (
              <tr
                key={contato.id}
                className="cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => router.push(`/contatos/${contato.id}`)}
              >
                <td className="px-4 py-3 font-medium text-gray-900">
                  {contato.nome}
                </td>
                <td className="px-4 py-3 text-gray-700">{contato.email}</td>
                <td className="px-4 py-3 text-gray-600">
                  {contato.telefone ?? '—'}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {contato.empresa ?? '—'}
                </td>
                <td
                  className="px-4 py-3"
                  // Impede que o clique nos botões propague para o row
                  onClick={(e: React.MouseEvent) => e.stopPropagation()}
                >
                  {isAdm && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => onEditar(contato.id)}
                        className="px-3 py-1 text-xs font-medium rounded border border-blue-500 text-blue-600 hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => onExcluir(contato.id)}
                        className="px-3 py-1 text-xs font-medium rounded border border-red-500 text-red-600 hover:bg-red-50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
                      >
                        Excluir
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}
