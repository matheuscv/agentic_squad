'use client'

import React, { useEffect, useRef, useState } from 'react'
import { ChevronDown, Download } from 'lucide-react'
import {
  exportarContatos,
  ExportarContatosParams,
  FormatoExportacao,
} from '../services/api'

// ---------------------------------------------------------------------------
// TASK-10 — Botao "Exportar" com dropdown CSV / XLSX (D.5)
//
// Componente puramente apresentacional:
//   - Le os parametros consolidados (busca + sort + filtros) via prop
//     `params`. NAO tem estado proprio sobre filtros — a unica fonte da
//     verdade e a pagina pai (`/contatos`), garantindo que o arquivo
//     exportado corresponda exatamente ao que esta na tela.
//   - Expoe dois itens no menu: "Exportar CSV" e "Exportar Excel" (xlsx).
//   - Aciona o helper `exportarContatos` de `services/api.ts`, que faz o
//     GET com `responseType: 'blob'`, le `Content-Disposition` para o nome
//     do arquivo e dispara o download.
//   - Estado de loading "trava" o botao durante o request; toast de erro
//     amigavel e propagado via callback opcional `onErro`.
//
// Acessibilidade (RNF-07):
//   - `aria-label` no botao principal e em cada item do menu.
//   - `aria-haspopup` / `aria-expanded` no trigger.
//   - `role="menu"` no contedor; `role="menuitem"` nos itens.
//   - Fecha com `Escape`, com clique fora e ao selecionar um item.
// ---------------------------------------------------------------------------

export interface ContatoExportButtonProps {
  /** Params consolidados (busca + ordenacao + filtros) a serem repassados. */
  params: ExportarContatosParams
  /**
   * Callback invocado quando o download falha. Mantemos a UX desacoplada:
   * o pai decide se mostra toast, alert ou banner inline.
   */
  onErro?: (mensagem: string) => void
  /**
   * Callback opcional para sucesso — util quando o pai quer exibir um
   * toast verde como "Download iniciado".
   */
  onSucesso?: (formato: FormatoExportacao) => void
}

export default function ContatoExportButton({
  params,
  onErro,
  onSucesso,
}: ContatoExportButtonProps) {
  const [aberto, setAberto] = useState(false)
  const [loading, setLoading] = useState<FormatoExportacao | null>(null)
  // Refs para fechar o menu ao clicar fora do conjunto botao+menu.
  const containerRef = useRef<HTMLDivElement | null>(null)

  // Fecha o menu ao clicar fora ou pressionar Escape.
  useEffect(() => {
    if (!aberto) return

    function handleClickFora(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setAberto(false)
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setAberto(false)
      }
    }

    document.addEventListener('mousedown', handleClickFora)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickFora)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [aberto])

  async function handleExportar(formato: FormatoExportacao) {
    // Evita disparos concorrentes — se ja ha um download em andamento,
    // ignora cliques adicionais ate concluir.
    if (loading !== null) return
    setLoading(formato)
    setAberto(false)
    try {
      await exportarContatos(formato, params)
      onSucesso?.(formato)
    } catch {
      // Mensagem generica — nao vazamos detalhes do backend (PCI/LGPD).
      // O interceptor de api.ts ja redireciona 401 para /login.
      onErro?.('Nao foi possivel exportar os contatos. Tente novamente.')
    } finally {
      setLoading(null)
    }
  }

  const carregando = loading !== null
  // Rotulo dinamico no botao: durante o download, indica o formato em uso.
  const rotuloBotao = carregando
    ? `Exportando ${loading === 'csv' ? 'CSV' : 'Excel'}...`
    : 'Exportar'

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      <button
        type="button"
        onClick={() => setAberto((v) => !v)}
        disabled={carregando}
        aria-label="Exportar contatos"
        aria-haspopup="menu"
        aria-expanded={aberto}
        className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
      >
        <Download className="w-4 h-4" aria-hidden="true" />
        {rotuloBotao}
        <ChevronDown
          className={`w-4 h-4 transition-transform ${aberto ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>

      {aberto && (
        <div
          role="menu"
          aria-label="Formatos de exportacao"
          className="absolute right-0 z-20 mt-2 w-48 origin-top-right bg-white border border-gray-200 rounded-md shadow-lg focus:outline-none"
        >
          <button
            type="button"
            role="menuitem"
            onClick={() => handleExportar('csv')}
            aria-label="Exportar contatos em CSV"
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none rounded-t-md"
          >
            Exportar CSV
          </button>
          <button
            type="button"
            role="menuitem"
            onClick={() => handleExportar('xlsx')}
            aria-label="Exportar contatos em Excel"
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 focus:bg-gray-50 focus:outline-none rounded-b-md border-t border-gray-100"
          >
            Exportar Excel
          </button>
        </div>
      )}
    </div>
  )
}
