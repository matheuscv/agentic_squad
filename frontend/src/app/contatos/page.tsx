'use client'

import React, { useState, useEffect, useRef, ChangeEvent } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { Contato } from '../../types/index'
import { useAuth } from '../../hooks/useAuth'
import { useDebounce } from '../../hooks/useDebounce'
import ProtectedRoute from '../../components/ProtectedRoute'
import ContatoTable from '../../components/ContatoTable'
import ConfirmacaoModal from '../../components/ConfirmacaoModal'
import ContatoFiltersPanel, {
  ContatoFiltros,
  FILTROS_VAZIOS,
} from '../../components/ContatoFiltersPanel'
import ContatoExportButton from '../../components/ContatoExportButton'
import {
  listarContatos,
  excluirContato,
} from '../../services/contatos.service'
import { ExportarContatosParams } from '../../services/api'

// Quantidade de registros por página (constante fixa, conservadora e alinhada ao PRD)
const LIMITE = 20

// ------------------------------------------------------------------
// TASK-07 — Ordenação D.1
// Allowlist espelhada do backend (TASK-03). Qualquer valor fora desse
// conjunto vindo via querystring é descartado em favor do default,
// evitando 422 desnecessário e ataques de parameter pollution.
// ------------------------------------------------------------------
const SORT_BY_ALLOWLIST = [
  'nome',
  'email',
  'empresa',
  'telefone',
  'criado_em',
  'atualizado_em',
] as const

type SortByField = (typeof SORT_BY_ALLOWLIST)[number]
type SortOrderDir = 'asc' | 'desc'

// Defaults alinhados ao backend (TASK-03): criado_em desc.
const DEFAULT_SORT_BY: SortByField = 'criado_em'
const DEFAULT_SORT_ORDER: SortOrderDir = 'desc'

function isSortByField(v: string | null): v is SortByField {
  return v !== null && (SORT_BY_ALLOWLIST as readonly string[]).includes(v)
}

function isSortOrder(v: string | null): v is SortOrderDir {
  return v === 'asc' || v === 'desc'
}

// ------------------------------------------------------------------
// TASK-09 — Filtros D.4
//
// Regex simples para validar o formato YYYY-MM-DD vindo da querystring.
// Datas mal formatadas sao silenciosamente descartadas para nao bater
// 422 no backend antes que o usuario interaja com o painel. O backend
// e a fonte da verdade — esta validacao e meramente defensiva contra
// links externos / parameter pollution.
// ------------------------------------------------------------------
const DATE_ISO_RE = /^\d{4}-\d{2}-\d{2}$/

function parseDateParam(v: string | null): string {
  if (!v) return ''
  return DATE_ISO_RE.test(v) ? v : ''
}

function parseBoolParam(v: string | null): boolean {
  // Convencao: aceitamos apenas 'true' como verdadeiro. Qualquer outro
  // valor (incluindo '1', 'on', 'yes') volta a false — mantemos a URL
  // canonica simples.
  return v === 'true'
}

// Le os 5 filtros da querystring respeitando o contrato do backend (TASK-05).
function readFiltrosFromSearch(
  searchParams: URLSearchParams | ReturnType<typeof useSearchParams>,
): ContatoFiltros {
  const empresa = searchParams?.get('empresa') ?? ''
  return {
    empresa: empresa ?? '',
    criado_desde: parseDateParam(searchParams?.get('criado_desde') ?? null),
    criado_ate: parseDateParam(searchParams?.get('criado_ate') ?? null),
    sem_email: parseBoolParam(searchParams?.get('sem_email') ?? null),
    sem_telefone: parseBoolParam(searchParams?.get('sem_telefone') ?? null),
  }
}

// ------------------------------------------------------------------
// Conteúdo interno da página (dentro do ProtectedRoute)
// Separado para que os hooks só rodem após a proteção ser confirmada.
// ------------------------------------------------------------------
function ContatosPageContent() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { isAdm, usuario } = useAuth()
  // userRole: string derivado do objeto usuario para repasse ao ContatoTable
  const userRole = usuario?.role ?? ''

  // Estado principal
  const [contatos, setContatos] = useState<Contato[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  // Campo de busca: o estado bruto reflete o input do usuário em tempo real.
  // O valor "debounced" (400 ms de inatividade) é o que dispara chamadas à API.
  const [busca, setBusca] = useState('')
  const buscaDebounced = useDebounce(busca, 400)

  // Paginação
  const [paginaAtual, setPaginaAtual] = useState(1)
  const [totalRegistros, setTotalRegistros] = useState(0)

  // ------------------------------------------------------------------
  // Ordenação (TASK-07 — D.1)
  //
  // Estado inicial lido da querystring (deep-link): valores fora da
  // allowlist são silenciosamente substituídos pelo default do backend
  // (criado_em desc), evitando 422 ao primeiro request. A sincronia
  // contrária — estado → URL — ocorre em um useEffect dedicado abaixo.
  // ------------------------------------------------------------------
  const initialSortByParam = searchParams?.get('sort_by') ?? null
  const initialSortOrderParam = searchParams?.get('sort_order') ?? null
  const [sortBy, setSortBy] = useState<SortByField>(
    isSortByField(initialSortByParam) ? initialSortByParam : DEFAULT_SORT_BY,
  )
  const [sortOrder, setSortOrder] = useState<SortOrderDir>(
    isSortOrder(initialSortOrderParam)
      ? initialSortOrderParam
      : DEFAULT_SORT_ORDER,
  )

  // ------------------------------------------------------------------
  // TASK-09 — Filtros D.4
  //
  // Estado dos filtros inicializado a partir da querystring (deep-link).
  // O painel `ContatoFiltersPanel` opera em modo controlled — esta
  // pagina e a fonte da verdade. Mudancas no estado disparam:
  //   1. Reload via useEffect de carregamento
  //   2. Sincronia ESTADO -> URL via useEffect dedicado (preservando
  //      sort_by/sort_order/busca ja presentes — TASK-07)
  // ------------------------------------------------------------------
  const [filtros, setFiltros] = useState<ContatoFiltros>(() =>
    readFiltrosFromSearch(searchParams),
  )

  // Modal de exclusão
  const [modalAberto, setModalAberto] = useState(false)
  const [contatoParaExcluir, setContatoParaExcluir] = useState<number | null>(null)
  const [excluindo, setExcluindo] = useState(false)

  // Toast tipado: distingue sucesso (verde) de erro (vermelho)
  const [toastMsg, setToastMsg] = useState<{ mensagem: string; tipo: 'sucesso' | 'erro' } | null>(null)
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ------------------------------------------------------------------
  // Efeito único de carregamento.
  //
  // Sempre que `buscaDebounced`, `paginaAtual`, `sortBy`, `sortOrder`
  // ou `filtros` mudam, recarrega a lista. Se a mudança foi no termo
  // debounced (detectado via ref), também reseta página e ordenação
  // para o padrão — mas usando os valores resetados na PRÓPRIA chamada
  // à API, evitando a request intermediária com estado obsoleto.
  //
  // TASK-09: mudanca nos filtros tambem reseta para pagina 1 (estado
  // ja e refletido aqui via dependencia do useEffect).
  // ------------------------------------------------------------------
  const buscaDebouncedAnteriorRef = useRef<string>(buscaDebounced)
  const filtrosAnterioresRef = useRef<ContatoFiltros>(filtros)
  useEffect(() => {
    const buscaMudou = buscaDebouncedAnteriorRef.current !== buscaDebounced
    buscaDebouncedAnteriorRef.current = buscaDebounced

    // Filtros mudaram desde a ultima execucao? Comparacao shallow campo-a-campo
    // — todos os campos do objeto sao primitivos.
    const filtrosAnteriores = filtrosAnterioresRef.current
    const filtrosMudaram =
      filtrosAnteriores.empresa !== filtros.empresa ||
      filtrosAnteriores.criado_desde !== filtros.criado_desde ||
      filtrosAnteriores.criado_ate !== filtros.criado_ate ||
      filtrosAnteriores.sem_email !== filtros.sem_email ||
      filtrosAnteriores.sem_telefone !== filtros.sem_telefone
    filtrosAnterioresRef.current = filtros

    if (buscaMudou) {
      // Reset declarativo ao trocar de termo: volta para a 1a pagina e
      // restaura a ordenação default (criado_em desc), alinhada ao backend.
      setPaginaAtual(1)
      setSortBy(DEFAULT_SORT_BY)
      setSortOrder(DEFAULT_SORT_ORDER)
      // Carrega imediatamente com os valores resetados, evitando uma chamada
      // intermediária com paginaAtual/sortBy/sortOrder antigos.
      carregarContatos(buscaDebounced, 1, DEFAULT_SORT_BY, DEFAULT_SORT_ORDER, filtros)
    } else if (filtrosMudaram) {
      // TASK-09: ao trocar qualquer filtro, volta para pagina 1
      // (preserva sort_by/sort_order — usuario pode estar refinando
      // resultados num sort especifico).
      setPaginaAtual(1)
      carregarContatos(buscaDebounced, 1, sortBy, sortOrder, filtros)
    } else {
      carregarContatos(buscaDebounced, paginaAtual, sortBy, sortOrder, filtros)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paginaAtual, sortBy, sortOrder, buscaDebounced, filtros])

  // ------------------------------------------------------------------
  // TASK-07 + TASK-09 — Sincronia ESTADO → QUERYSTRING.
  //
  // Sempre que `sortBy`/`sortOrder` ou `filtros` mudam, refletimos na
  // URL via `router.replace` (sem empilhar entradas no histórico).
  // Quando os valores correspondem ao default do backend, os parâmetros
  // são omitidos da URL para manter o link "limpo" — o backend aplica o
  // mesmo default automaticamente.
  //
  // Atenção: preservamos os demais parâmetros já presentes na URL
  // (ex.: futuros filtros de outras features) para não conflitar.
  // Nesta implementacao, gerenciamos:
  //   - sort_by / sort_order (TASK-07)
  //   - empresa / criado_desde / criado_ate / sem_email / sem_telefone
  //     (TASK-09)
  // ------------------------------------------------------------------
  useEffect(() => {
    const current = new URLSearchParams(
      searchParams ? searchParams.toString() : '',
    )

    // ----- Sort (TASK-07) -----
    const isSortDefault =
      sortBy === DEFAULT_SORT_BY && sortOrder === DEFAULT_SORT_ORDER
    if (isSortDefault) {
      current.delete('sort_by')
      current.delete('sort_order')
    } else {
      current.set('sort_by', sortBy)
      current.set('sort_order', sortOrder)
    }

    // ----- Filtros (TASK-09) -----
    // Cada campo so vai para a URL quando preenchido / ativo. Limpar um
    // filtro = remover seu key da querystring.
    if (filtros.empresa && filtros.empresa.trim() !== '') {
      current.set('empresa', filtros.empresa.trim())
    } else {
      current.delete('empresa')
    }
    if (filtros.criado_desde) {
      current.set('criado_desde', filtros.criado_desde)
    } else {
      current.delete('criado_desde')
    }
    if (filtros.criado_ate) {
      current.set('criado_ate', filtros.criado_ate)
    } else {
      current.delete('criado_ate')
    }
    if (filtros.sem_email) {
      current.set('sem_email', 'true')
    } else {
      current.delete('sem_email')
    }
    if (filtros.sem_telefone) {
      current.set('sem_telefone', 'true')
    } else {
      current.delete('sem_telefone')
    }

    const qs = current.toString()
    const targetUrl = qs ? `${pathname}?${qs}` : pathname
    // Só dispara replace quando a URL mudou de fato, evitando loops.
    const currentQs = searchParams ? searchParams.toString() : ''
    if (qs !== currentQs) {
      router.replace(targetUrl, { scroll: false })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy, sortOrder, filtros])

  // Limpa timer do toast ao desmontar para evitar memory leaks.
  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
    }
  }, [])

  async function carregarContatos(
    termo?: string,
    pagina: number = 1,
    ordenarPor: SortByField = DEFAULT_SORT_BY,
    ordemDirecao: SortOrderDir = DEFAULT_SORT_ORDER,
    filtrosAtivos: ContatoFiltros = FILTROS_VAZIOS,
  ) {
    setLoading(true)
    setErro(null)
    try {
      const skip = (pagina - 1) * LIMITE
      // Defesa em profundidade: se o range estiver invertido, nao chama o
      // backend (que retornaria 422). O painel ja exibe o aviso inline.
      if (
        filtrosAtivos.criado_desde &&
        filtrosAtivos.criado_ate &&
        filtrosAtivos.criado_desde > filtrosAtivos.criado_ate
      ) {
        setContatos([])
        setTotalRegistros(0)
        setErro('A data inicial deve ser anterior ou igual a data final.')
        return
      }
      const resposta = await listarContatos(
        termo,
        skip,
        LIMITE,
        ordenarPor,
        ordemDirecao,
        {
          empresa: filtrosAtivos.empresa || undefined,
          criado_desde: filtrosAtivos.criado_desde || undefined,
          criado_ate: filtrosAtivos.criado_ate || undefined,
          sem_email: filtrosAtivos.sem_email || undefined,
          sem_telefone: filtrosAtivos.sem_telefone || undefined,
        },
      )
      // O backend retorna { items, total } após TASK-01
      setContatos(resposta.items)
      setTotalRegistros(resposta.total)
    } catch {
      setErro('Não foi possível carregar os contatos. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  // ------------------------------------------------------------------
  // Campo de busca: apenas reflete o input do usuário no estado.
  // O debounce (400 ms) é aplicado pelo hook useDebounce; o reset de
  // página/ordenação e a chamada à API acontecem nos useEffects acima.
  // ------------------------------------------------------------------
  function handleBuscaChange(e: ChangeEvent<HTMLInputElement>) {
    setBusca(e.target.value)
  }

  // ------------------------------------------------------------------
  // TASK-09 — Handler do painel de filtros.
  // Recebe o objeto completo de filtros do componente e atualiza o
  // estado. O useEffect de carregamento reage; o useEffect de sincronia
  // atualiza a querystring.
  // ------------------------------------------------------------------
  function handleFiltrosChange(novosFiltros: ContatoFiltros) {
    setFiltros(novosFiltros)
  }

  // ------------------------------------------------------------------
  // Handlers de paginação
  // ------------------------------------------------------------------
  function handlePaginaAnterior() {
    setPaginaAtual((p) => Math.max(1, p - 1))
  }

  function handleProximaPagina() {
    const totalPaginas = Math.ceil(totalRegistros / LIMITE)
    setPaginaAtual((p) => Math.min(totalPaginas, p + 1))
  }

  // ------------------------------------------------------------------
  // TASK-07 — Ordenação de colunas (D.1)
  //
  // Comportamento (especificado pelo gerenciador da squad):
  //   - Clicar em coluna inativa: ativa em ASC.
  //   - Clicar novamente na coluna ativa: alterna entre ASC e DESC.
  //
  // O efeito de sincronia ESTADO → URL acima propaga `sort_by` /
  // `sort_order` na querystring. Sempre voltamos para a primeira página
  // ao trocar a ordenação para que o usuário veja o topo do novo
  // resultado.
  // ------------------------------------------------------------------
  function handleSort(coluna: string) {
    if (!isSortByField(coluna)) {
      // Defesa em profundidade: ignora cliques em colunas fora da allowlist.
      return
    }
    const novaSortOrder: SortOrderDir =
      coluna === sortBy ? (sortOrder === 'asc' ? 'desc' : 'asc') : 'asc'

    setPaginaAtual(1)
    setSortBy(coluna)
    setSortOrder(novaSortOrder)
    // O useEffect de carregamento reage à mudança de sortBy/sortOrder;
    // o useEffect de sincronia atualiza a querystring.
  }

  // ------------------------------------------------------------------
  // Navegação
  // ------------------------------------------------------------------
  function handleEditar(id: number) {
    router.push(`/contatos/${id}/editar`)
  }

  function handleExcluir(id: number) {
    setContatoParaExcluir(id)
    setModalAberto(true)
  }

  // ------------------------------------------------------------------
  // Confirmação de exclusão
  // ------------------------------------------------------------------
  async function handleConfirmarExclusao() {
    if (contatoParaExcluir === null) return

    setExcluindo(true)
    try {
      await excluirContato(contatoParaExcluir)
      // Remove da lista local sem precisar recarregar da API
      setContatos((prev: Contato[]) => prev.filter((c: Contato) => c.id !== contatoParaExcluir))
      setModalAberto(false)
      setContatoParaExcluir(null)
      exibirToast('Contato excluído com sucesso!', 'sucesso')
    } catch {
      // Fecha o modal e informa o erro via toast vermelho
      setModalAberto(false)
      exibirToast('Erro ao excluir o contato. Tente novamente.', 'erro')
    } finally {
      setExcluindo(false)
    }
  }

  // ------------------------------------------------------------------
  // Toast: exibe por 3 segundos e some.
  // O parâmetro `tipo` determina a cor de fundo no JSX.
  // ------------------------------------------------------------------
  function exibirToast(msg: string, tipo: 'sucesso' | 'erro') {
    // Cancela toast anterior se existir
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
    setToastMsg({ mensagem: msg, tipo })
    toastTimerRef.current = setTimeout(() => {
      setToastMsg(null)
    }, 3000)
  }

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  return (
    <div className="container max-w-6xl mx-auto px-4 py-8">
      {/* Cabeçalho: título + botão "Novo Contato" */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Contatos</h1>

        {/* Botão "Novo Contato" visível apenas para administradores */}
        {isAdm && (
          <button
            onClick={() => router.push('/contatos/novo')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            {/* Ícone "+" */}
            <span className="text-lg leading-none" aria-hidden="true">+</span>
            Novo Contato
          </button>
        )}
      </div>

      {/* Campo de busca + botao Exportar (TASK-10).
          Layout flex: busca a esquerda, botao Exportar a direita. */}
      <div className="mb-4 flex items-start justify-between gap-3 flex-wrap">
        <input
          type="text"
          value={busca}
          onChange={handleBuscaChange}
          placeholder="Pesquisar por nome, e-mail ou empresa..."
          className="flex-1 max-w-md px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />

        {/* TASK-10 — Botao Exportar com dropdown CSV/XLSX.
            Recebe o estado consolidado (busca + sort + filtros) para que o
            arquivo exportado reflita exatamente o que esta visivel. */}
        <ContatoExportButton
          params={
            {
              busca: buscaDebounced || undefined,
              sort_by: sortBy,
              sort_order: sortOrder,
              empresa: filtros.empresa || undefined,
              criado_desde: filtros.criado_desde || undefined,
              criado_ate: filtros.criado_ate || undefined,
              sem_email: filtros.sem_email || undefined,
              sem_telefone: filtros.sem_telefone || undefined,
            } satisfies ExportarContatosParams
          }
          onSucesso={() => exibirToast('Download iniciado.', 'sucesso')}
          onErro={(msg) => exibirToast(msg, 'erro')}
        />
      </div>

      {/* TASK-09 — Painel de filtros colapsavel acima da tabela */}
      <ContatoFiltersPanel value={filtros} onChange={handleFiltrosChange} />

      {/* Mensagem de erro da API */}
      {erro && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {erro}
        </div>
      )}

      {/* Tabela de contatos com paginação */}
      <ContatoTable
        contatos={contatos}
        isAdm={isAdm}
        onEditar={handleEditar}
        onExcluir={handleExcluir}
        loading={loading}
        paginaAtual={paginaAtual}
        totalRegistros={totalRegistros}
        limite={LIMITE}
        onPaginaAnterior={handlePaginaAnterior}
        onProximaPagina={handleProximaPagina}
        termoBusca={busca}
        userRole={userRole}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
      />

      {/* Modal de confirmação de exclusão */}
      <ConfirmacaoModal
        aberto={modalAberto}
        titulo="Excluir Contato"
        mensagem="Tem certeza que deseja excluir este contato? Esta ação não pode ser desfeita."
        onConfirmar={handleConfirmarExclusao}
        onCancelar={() => setModalAberto(false)}
        loading={excluindo}
      />

      {/* Toast tipado (fixo no canto superior direito, desaparece após 3s).
          Sucesso: fundo verde. Erro: fundo vermelho. */}
      {toastMsg && (
        <div
          role="status"
          aria-live="polite"
          className={`fixed top-4 right-4 z-50 px-5 py-3 text-white text-sm font-medium rounded-lg shadow-lg transition-opacity ${
            toastMsg.tipo === 'sucesso' ? 'bg-green-500' : 'bg-red-600'
          }`}
        >
          {toastMsg.mensagem}
        </div>
      )}
    </div>
  )
}

// ------------------------------------------------------------------
// Página exportada — envolve o conteúdo com ProtectedRoute
// ------------------------------------------------------------------
export default function ContatosPage() {
  return (
    <ProtectedRoute>
      <ContatosPageContent />
    </ProtectedRoute>
  )
}
