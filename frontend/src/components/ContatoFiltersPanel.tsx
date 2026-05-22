'use client'

import React, { useEffect, useRef, useState, ChangeEvent } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import { useDebounce } from '../hooks/useDebounce'

// ---------------------------------------------------------------------------
// TASK-09 — Painel de filtros avancados (D.4)
//
// Componente colapsavel com 5 filtros alinhados ao contrato do backend
// (TASK-05): `empresa`, `criado_desde`, `criado_ate`, `sem_email`,
// `sem_telefone`.
//
// Decisoes de design:
//
//  1. `empresa` e o unico campo de texto livre. Aplicamos `useDebounce(300ms)`
//     internamente para nao bombardear a API a cada tecla (RF-05 do PRD).
//     Os outros filtros (datas e booleanos) sao discretos por natureza e
//     propagam imediatamente.
//
//  2. O estado COLAPSADO/EXPANDIDO e persistido em `sessionStorage`
//     ("lembrado durante a sessao" — criterio da TASK-09). Em SSR /
//     primeira render, defaultamos a EXPANDIDO para que filtros vindos via
//     deep-link fiquem visiveis sem clique extra.
//
//  3. Os VALORES dos filtros sao "controlled" pelo pai (page.tsx), que e
//     a fonte da verdade (sincronia com URL). Mantemos apenas o input bruto
//     de `empresa` em estado local para debounce — o pai recebe somente o
//     valor debounced via `onChange`.
//
//  4. Validacao cliente leve: se `criado_desde > criado_ate`, exibimos um
//     aviso amigavel inline (o backend tambem retorna 422 — defesa em
//     profundidade).
// ---------------------------------------------------------------------------

export interface ContatoFiltros {
  /** Busca parcial case-insensitive sobre a coluna empresa. */
  empresa: string
  /** Data inicial inclusiva no formato YYYY-MM-DD (contrato do <input type="date">). */
  criado_desde: string
  /** Data final inclusiva no formato YYYY-MM-DD. */
  criado_ate: string
  /** Quando true, retorna apenas contatos com email vazio. */
  sem_email: boolean
  /** Quando true, retorna apenas contatos com telefone vazio. */
  sem_telefone: boolean
}

export const FILTROS_VAZIOS: ContatoFiltros = {
  empresa: '',
  criado_desde: '',
  criado_ate: '',
  sem_email: false,
  sem_telefone: false,
}

interface ContatoFiltersPanelProps {
  /** Valores atuais dos filtros (controlled pelo pai). */
  value: ContatoFiltros
  /** Callback disparado a cada mudanca debounced/imediata. */
  onChange: (filtros: ContatoFiltros) => void
}

// Chave dedicada ao estado colapsado/expandido — escopo curto e nao-sensivel,
// portanto `sessionStorage` e suficiente (e nao persiste entre sessoes).
const STORAGE_KEY = 'contatos_filtros_collapsed'

export default function ContatoFiltersPanel({
  value,
  onChange,
}: ContatoFiltersPanelProps) {
  // -------------------------------------------------------------------------
  // Estado: collapsed/expanded.
  // Inicializa com `false` (expandido) tanto em SSR quanto em CSR para evitar
  // mismatch de hidratacao. Logo apos a hidratacao, lemos sessionStorage no
  // useEffect e ajustamos se necessario.
  // -------------------------------------------------------------------------
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    // Roda apenas no cliente (sessionStorage indisponivel em SSR).
    try {
      const stored = window.sessionStorage.getItem(STORAGE_KEY)
      if (stored === 'true') {
        setCollapsed(true)
      }
    } catch {
      // Ignora — privacy mode / iframes sandboxed podem bloquear storage.
    }
  }, [])

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev
      try {
        window.sessionStorage.setItem(STORAGE_KEY, String(next))
      } catch {
        // Ignora falha silenciosa de storage (modo privado, etc.).
      }
      return next
    })
  }

  // -------------------------------------------------------------------------
  // Campo `empresa`: estado local bruto + debounce 300 ms.
  //
  // Quando o pai muda o valor externamente (ex.: refresh com deep-link ou
  // botao "Limpar filtros"), sincronizamos o input bruto via useEffect.
  // -------------------------------------------------------------------------
  const [empresaInput, setEmpresaInput] = useState(value.empresa)
  const empresaDebounced = useDebounce(empresaInput, 300)

  // Sincroniza input bruto quando o valor controlado externo muda
  // (ex.: limpar filtros). Comparamos para evitar loops de update.
  useEffect(() => {
    if (value.empresa !== empresaInput) {
      setEmpresaInput(value.empresa)
    }
    // Apenas reagir ao valor controlado externo — nao ao empresaInput.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.empresa])

  // Propaga o valor debounced ao pai SOMENTE quando ele diverge do valor
  // controlado atual — evita disparar onChange em cada render.
  const lastEmpresaEmitidoRef = useRef<string>(value.empresa)
  useEffect(() => {
    if (empresaDebounced !== value.empresa && empresaDebounced !== lastEmpresaEmitidoRef.current) {
      lastEmpresaEmitidoRef.current = empresaDebounced
      onChange({ ...value, empresa: empresaDebounced })
    }
    // Dependencias intencionalmente restritas: o efeito reage ao debounced.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [empresaDebounced])

  // -------------------------------------------------------------------------
  // Handlers dos outros campos — propagam imediatamente ao pai.
  // -------------------------------------------------------------------------
  function handleEmpresaChange(e: ChangeEvent<HTMLInputElement>) {
    setEmpresaInput(e.target.value)
  }

  function handleCriadoDesdeChange(e: ChangeEvent<HTMLInputElement>) {
    onChange({ ...value, criado_desde: e.target.value })
  }

  function handleCriadoAteChange(e: ChangeEvent<HTMLInputElement>) {
    onChange({ ...value, criado_ate: e.target.value })
  }

  function handleSemEmailChange(e: ChangeEvent<HTMLInputElement>) {
    onChange({ ...value, sem_email: e.target.checked })
  }

  function handleSemTelefoneChange(e: ChangeEvent<HTMLInputElement>) {
    onChange({ ...value, sem_telefone: e.target.checked })
  }

  function handleLimpar() {
    // Reset completo. Atualiza tambem o input bruto para refletir no UI.
    setEmpresaInput('')
    lastEmpresaEmitidoRef.current = ''
    onChange({ ...FILTROS_VAZIOS })
  }

  // -------------------------------------------------------------------------
  // Validacao client-side leve: range invertido.
  // Comparacao via string YYYY-MM-DD funciona lexicograficamente.
  // -------------------------------------------------------------------------
  const rangeInvertido =
    value.criado_desde !== '' &&
    value.criado_ate !== '' &&
    value.criado_desde > value.criado_ate

  // Quantidade de filtros ativos — exibida no toggle quando colapsado para
  // dar feedback de que ha filtros aplicados mesmo com painel fechado.
  const filtrosAtivos =
    (value.empresa ? 1 : 0) +
    (value.criado_desde ? 1 : 0) +
    (value.criado_ate ? 1 : 0) +
    (value.sem_email ? 1 : 0) +
    (value.sem_telefone ? 1 : 0)

  return (
    <div className="mb-4 border border-gray-200 rounded-md bg-white shadow-sm">
      {/* Cabecalho clicavel: toggle de collapsed/expanded */}
      <button
        type="button"
        onClick={toggleCollapsed}
        aria-expanded={!collapsed}
        aria-controls="contato-filtros-panel"
        className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-400 rounded-t-md"
      >
        <span className="flex items-center gap-2">
          Filtros
          {filtrosAtivos > 0 && (
            <span
              className="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-xs font-semibold text-white bg-blue-600 rounded-full"
              aria-label={`${filtrosAtivos} filtro${filtrosAtivos > 1 ? 's' : ''} ativo${filtrosAtivos > 1 ? 's' : ''}`}
            >
              {filtrosAtivos}
            </span>
          )}
        </span>
        {collapsed ? (
          <ChevronDown size={18} className="text-gray-500" aria-hidden="true" />
        ) : (
          <ChevronUp size={18} className="text-gray-500" aria-hidden="true" />
        )}
      </button>

      {/* Conteudo colapsavel */}
      {!collapsed && (
        <div
          id="contato-filtros-panel"
          className="px-4 py-4 border-t border-gray-200"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Empresa — texto livre com debounce 300 ms */}
            <div>
              <label
                htmlFor="filtro-empresa"
                className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1"
              >
                Empresa
              </label>
              <input
                id="filtro-empresa"
                type="text"
                value={empresaInput}
                onChange={handleEmpresaChange}
                placeholder="Ex: Acme Corp"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Criado desde — date picker */}
            <div>
              <label
                htmlFor="filtro-criado-desde"
                className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1"
              >
                Criado desde
              </label>
              <input
                id="filtro-criado-desde"
                type="date"
                value={value.criado_desde}
                onChange={handleCriadoDesdeChange}
                aria-invalid={rangeInvertido}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Criado ate — date picker */}
            <div>
              <label
                htmlFor="filtro-criado-ate"
                className="block text-xs font-semibold text-gray-600 uppercase tracking-wider mb-1"
              >
                Criado ate
              </label>
              <input
                id="filtro-criado-ate"
                type="date"
                value={value.criado_ate}
                onChange={handleCriadoAteChange}
                aria-invalid={rangeInvertido}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Checkboxes — agrupados num bloco com layout simples */}
            <div className="flex items-center gap-2">
              <input
                id="filtro-sem-email"
                type="checkbox"
                checked={value.sem_email}
                onChange={handleSemEmailChange}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <label
                htmlFor="filtro-sem-email"
                className="text-sm text-gray-700 select-none cursor-pointer"
              >
                Somente sem e-mail
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                id="filtro-sem-telefone"
                type="checkbox"
                checked={value.sem_telefone}
                onChange={handleSemTelefoneChange}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <label
                htmlFor="filtro-sem-telefone"
                className="text-sm text-gray-700 select-none cursor-pointer"
              >
                Somente sem telefone
              </label>
            </div>
          </div>

          {/* Aviso de range invertido (defesa em profundidade — backend tambem valida) */}
          {rangeInvertido && (
            <div
              role="alert"
              className="mt-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-800"
            >
              A data inicial deve ser anterior ou igual a data final.
            </div>
          )}

          {/* Botao Limpar filtros */}
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleLimpar}
              disabled={filtrosAtivos === 0}
              className={`px-3 py-1.5 text-sm font-medium rounded border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 ${
                filtrosAtivos === 0 ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              Limpar filtros
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
