'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Pencil, Trash2, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'
import { Contato } from '../types'

interface ContatoTableProps {
  contatos: Contato[]
  isAdm: boolean
  onEditar: (id: number) => void
  onExcluir: (id: number) => void
  loading: boolean
  // Props de paginação
  paginaAtual: number
  totalRegistros: number
  limite: number
  onPaginaAnterior: () => void
  onProximaPagina: () => void
  // Props de estado contextual da lista vazia (TASK-04); opcionais com fallback ''
  termoBusca?: string
  userRole?: string
  // Props de ordenação (TASK-05)
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (coluna: string) => void
}

// Skeleton de linha para estado de carregamento (6 colunas: Nome, E-mail, Empresa, Data, Telefone, Ações)
// TASK-16: envolvido em React.memo — o componente não recebe props e seu output é estático,
// portanto pode ser reutilizado entre renders sem reconciliação adicional.
const SkeletonRow = React.memo(function SkeletonRow() {
  return (
    <tr>
      {[...Array(6)].map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse" />
        </td>
      ))}
    </tr>
  )
})

export default function ContatoTable({
  contatos,
  isAdm,
  onEditar,
  onExcluir,
  loading,
  paginaAtual,
  totalRegistros,
  limite,
  onPaginaAnterior,
  onProximaPagina,
  termoBusca = '',
  userRole = '',
  sortBy = 'nome',
  sortOrder = 'asc',
  onSort,
}: ContatoTableProps) {
  const router = useRouter()

  // Mapeamento label → campo sort_by aceito pelo backend
  const sortableColumns: { label: string; field: string }[] = [
    { label: 'Nome', field: 'nome' },
    { label: 'E-mail', field: 'email' },
    { label: 'Empresa', field: 'empresa' },
    { label: 'Data', field: 'criado_em' },
  ]

  // Retorna o ícone correto para o header de uma coluna ordenável
  function SortIcon({ field }: { field: string }) {
    if (field !== sortBy) return <ArrowUpDown size={14} className="inline ml-1 text-gray-400" />
    if (sortOrder === 'asc') return <ArrowUp size={14} className="inline ml-1 text-blue-500" />
    return <ArrowDown size={14} className="inline ml-1 text-blue-500" />
  }

  // TASK-16: memoizar a lista de contatos exibida.
  // A ordenação efetiva acontece no backend (sort_by/sort_order — TASK-01/TASK-05),
  // por isso este useMemo apenas estabiliza a referência do array entre renders quando
  // `contatos`, `sortBy` e `sortOrder` não mudam. Mantém-se a ordem visual atual sem
  // reordenar em memória (RN-F2-01). As dependências são exatamente as que afetam a
  // ordem dos itens; nada externo é incluído.
  const contatosOrdenados = React.useMemo(
    () => [...contatos],
    [contatos, sortBy, sortOrder],
  )

  // Cálculos de paginação
  const totalPaginas = Math.ceil(totalRegistros / limite)
  // Índice do primeiro e último item exibido na página atual (1-based)
  const inicio = totalRegistros === 0 ? 0 : (paginaAtual - 1) * limite + 1
  const fim = Math.min(paginaAtual * limite, totalRegistros)

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            {/* Colunas ordenáveis: Nome, E-mail, Empresa, Data */}
            {sortableColumns.map(({ label, field }) => (
              <th
                key={field}
                className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
              >
                {onSort ? (
                  <button
                    type="button"
                    onClick={() => onSort(field)}
                    className="flex items-center gap-0.5 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-400 rounded transition-colors"
                    aria-label={`Ordenar por ${label}`}
                  >
                    {label}
                    <SortIcon field={field} />
                  </button>
                ) : (
                  label
                )}
              </th>
            ))}
            {/* Coluna Telefone — não ordenável */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Telefone
            </th>
            {/* Coluna Ações — não ordenável */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Ações
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-gray-100">
          {/* Estado de carregamento: 5 linhas skeleton */}
          {loading &&
            [...Array(5)].map((_, i) => <SkeletonRow key={i} />)}

          {/* Lista vazia — mensagem contextual dependendo do estado de busca */}
          {!loading && contatos.length === 0 && (
            <tr>
              <td
                colSpan={6}
                className="px-4 py-8 text-center text-gray-400"
              >
                {termoBusca.trim() !== '' ? (
                  // Busca ativa sem resultados: exibe o termo pesquisado
                  <span className="italic">
                    Nenhum resultado para &ldquo;{termoBusca}&rdquo;.
                  </span>
                ) : (
                  // Banco vazio sem filtro: mensagem genérica + atalho para adm
                  <div className="flex flex-col items-center gap-3">
                    <span className="italic">Nenhum contato cadastrado ainda.</span>
                    {userRole === 'adm' && (
                      // Botão visível apenas para administradores
                      <a
                        href="/contatos/novo"
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                      >
                        Cadastrar primeiro contato
                      </a>
                    )}
                  </div>
                )}
              </td>
            </tr>
          )}

          {/* Linhas de dados — usa o array memoizado (TASK-16) */}
          {!loading &&
            contatosOrdenados.map((contato) => (
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
                  {contato.empresa ?? '—'}
                </td>
                {/* Coluna Data: exibe criado_em formatado (pt-BR) */}
                <td className="px-4 py-3 text-gray-600">
                  {new Date(contato.criado_em).toLocaleDateString('pt-BR')}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {contato.telefone ?? '—'}
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
                        className="flex items-center gap-1 px-3 py-1 text-xs font-medium rounded border border-blue-500 text-blue-600 hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
                      >
                        <Pencil size={16} aria-hidden="true" /><span>Editar</span>
                      </button>
                      <button
                        onClick={() => onExcluir(contato.id)}
                        className="flex items-center gap-1 px-3 py-1 text-xs font-medium rounded border border-red-500 text-red-600 hover:bg-red-50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
                      >
                        <Trash2 size={16} aria-hidden="true" /><span>Excluir</span>
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
      {/* Barra de paginação — exibida abaixo da tabela */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-white">
        {/* Texto informativo: "1–20 de 87 contatos" */}
        <span className="text-sm text-gray-600">
          {totalRegistros === 0
            ? '0 contatos'
            : `${inicio}–${fim} de ${totalRegistros} contatos`}
        </span>

        <div className="flex gap-2">
          {/* Botão Anterior */}
          <button
            onClick={onPaginaAnterior}
            disabled={paginaAtual === 1}
            className={`px-3 py-1.5 text-sm font-medium rounded border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 ${
              paginaAtual === 1 ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            Anterior
          </button>

          {/* Botão Próxima */}
          <button
            onClick={onProximaPagina}
            disabled={paginaAtual >= totalPaginas}
            className={`px-3 py-1.5 text-sm font-medium rounded border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 ${
              paginaAtual >= totalPaginas ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            Próxima
          </button>
        </div>
      </div>
    </div>
  )
}
