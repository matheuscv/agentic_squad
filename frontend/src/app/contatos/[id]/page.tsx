'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '../../../components/ProtectedRoute'
import ContatoDetalhe from '../../../components/ContatoDetalhe'
import ConfirmacaoModal from '../../../components/ConfirmacaoModal'
import { useAuth } from '../../../hooks/useAuth'
import { Contato } from '../../../types/index'
import {
  buscarContato,
  excluirContato,
} from '../../../services/contatos.service'

interface PageProps {
  params: { id: string }
}

// Spinner reutilizado localmente
function Spinner() {
  return (
    <div className="flex min-h-[200px] items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
    </div>
  )
}

function DetalheContato({ params }: PageProps) {
  const router = useRouter()
  const { isAdm } = useAuth()

  const [contato, setContato] = useState<Contato | null>(null)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [modalAberto, setModalAberto] = useState(false)
  const [excluindo, setExcluindo] = useState(false)

  const id = Number(params.id)

  useEffect(() => {
    let cancelado = false

    async function carregar() {
      try {
        const dados = await buscarContato(id)
        if (!cancelado) setContato(dados)
      } catch (err: unknown) {
        if (cancelado) return
        // Trata 404 explicitamente; demais erros exibem mensagem genérica
        const status = (err as { status?: number })?.status
        if (status === 404) {
          setErro('Contato não encontrado.')
        } else {
          setErro('Erro ao carregar contato. Tente novamente.')
        }
      } finally {
        if (!cancelado) setLoading(false)
      }
    }

    carregar()
    return () => {
      cancelado = true
    }
  }, [id])

  function handleEditar() {
    router.push(`/contatos/${id}/editar`)
  }

  async function handleExcluir() {
    setExcluindo(true)
    try {
      await excluirContato(id)
      router.push('/contatos')
    } catch {
      setErro('Erro ao excluir contato. Tente novamente.')
      setModalAberto(false)
    } finally {
      setExcluindo(false)
    }
  }

  return (
    <div className="container max-w-2xl mx-auto px-4 py-8">
      {/* Botão Voltar */}
      <button
        onClick={() => router.push('/contatos')}
        className="mb-6 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
      >
        ← Voltar
      </button>

      {loading && <Spinner />}

      {!loading && erro && (
        <div className="flex flex-col items-start gap-4">
          <p className="text-red-600">{erro}</p>
          <button
            onClick={() => router.push('/contatos')}
            className="px-4 py-2 rounded-md bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Voltar para lista
          </button>
        </div>
      )}

      {!loading && !erro && contato && (
        <>
          <ContatoDetalhe
            contato={contato}
            isAdm={isAdm}
            onEditar={handleEditar}
            onExcluir={() => setModalAberto(true)}
          />

          <ConfirmacaoModal
            aberto={modalAberto}
            titulo="Excluir contato"
            mensagem={`Tem certeza que deseja excluir "${contato.nome}"? Esta ação não pode ser desfeita.`}
            onConfirmar={handleExcluir}
            onCancelar={() => setModalAberto(false)}
            loading={excluindo}
          />
        </>
      )}
    </div>
  )
}

export default function Page(props: PageProps) {
  return (
    <ProtectedRoute>
      <DetalheContato {...props} />
    </ProtectedRoute>
  )
}
