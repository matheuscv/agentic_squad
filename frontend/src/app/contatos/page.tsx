'use client'

import React, { useState, useEffect, useRef, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Contato } from '../../types/index'
import { useAuth } from '../../hooks/useAuth'
import { useDebounce } from '../../hooks/useDebounce'
import ProtectedRoute from '../../components/ProtectedRoute'
import ContatoTable from '../../components/ContatoTable'
import ConfirmacaoModal from '../../components/ConfirmacaoModal'
import {
  listarContatos,
  excluirContato,
} from '../../services/contatos.service'

// Quantidade de registros por página (constante fixa, conservadora e alinhada ao PRD)
const LIMITE = 20

// ------------------------------------------------------------------
// Conteúdo interno da página (dentro do ProtectedRoute)
// Separado para que os hooks só rodem após a proteção ser confirmada.
// ------------------------------------------------------------------
function ContatosPageContent() {
  const router = useRouter()
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

  // Ordenação (TASK-05)
  const [sortBy, setSortBy] = useState<string>('nome')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

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
  // Sempre que `buscaDebounced`, `paginaAtual`, `sortBy` ou `sortOrder`
  // mudam, recarrega a lista. Se a mudança foi no termo debounced
  // (detectado via ref), também reseta página e ordenação para o padrão
  // — mas usando os valores resetados na PRÓPRIA chamada à API, evitando
  // a request intermediária com estado obsoleto.
  // ------------------------------------------------------------------
  const buscaDebouncedAnteriorRef = useRef<string>(buscaDebounced)
  useEffect(() => {
    const buscaMudou = buscaDebouncedAnteriorRef.current !== buscaDebounced
    buscaDebouncedAnteriorRef.current = buscaDebounced

    if (buscaMudou) {
      // Reset declarativo: garante que os próximos renders enxerguem o padrão.
      setPaginaAtual(1)
      setSortBy('nome')
      setSortOrder('asc')
      // Carrega imediatamente com os valores resetados, evitando uma chamada
      // intermediária com paginaAtual/sortBy/sortOrder antigos.
      carregarContatos(buscaDebounced, 1, 'nome', 'asc')
    } else {
      carregarContatos(buscaDebounced, paginaAtual, sortBy, sortOrder)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paginaAtual, sortBy, sortOrder, buscaDebounced])

  // Limpa timer do toast ao desmontar para evitar memory leaks.
  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
    }
  }, [])

  async function carregarContatos(
    termo?: string,
    pagina: number = 1,
    ordenarPor: string = 'nome',
    ordemDirecao: 'asc' | 'desc' = 'asc'
  ) {
    setLoading(true)
    setErro(null)
    try {
      const skip = (pagina - 1) * LIMITE
      const resposta = await listarContatos(termo, skip, LIMITE, ordenarPor, ordemDirecao)
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
  // Ordenação de colunas (TASK-05)
  // Ciclo: inativa → ASC → DESC → volta ao padrão nome ASC
  // ------------------------------------------------------------------
  function handleSort(coluna: string) {
    let novaSortBy = coluna
    let novaSortOrder: 'asc' | 'desc' = 'asc'

    if (coluna === sortBy) {
      if (sortOrder === 'asc') {
        // Segunda vez na mesma coluna: vai para DESC
        novaSortOrder = 'desc'
      } else {
        // Terceira vez: reseta para o padrão
        novaSortBy = 'nome'
        novaSortOrder = 'asc'
      }
    }
    // Sempre volta para a primeira página ao mudar ordenação
    setPaginaAtual(1)
    setSortBy(novaSortBy)
    setSortOrder(novaSortOrder)
    // Disparo direto: o useEffect reagirá às mudanças de estado
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

      {/* Campo de busca */}
      <div className="mb-4">
        <input
          type="text"
          value={busca}
          onChange={handleBuscaChange}
          placeholder="Pesquisar por nome, e-mail ou empresa..."
          className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

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
