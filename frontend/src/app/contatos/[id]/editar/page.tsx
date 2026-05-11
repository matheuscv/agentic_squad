'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '../../../../components/ProtectedRoute'
import ContatoForm from '../../../../components/ContatoForm'
import { useAuth } from '../../../../hooks/useAuth'
import { Contato, ContatoForm as ContatoFormType } from '../../../../types/index'
import { buscarContato, atualizarContato } from '../../../../services/contatos.service'

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

// Toast simples com auto-dismiss
interface ToastProps {
  mensagem: string
  visivel: boolean
}

function Toast({ mensagem, visivel }: ToastProps) {
  if (!visivel) return null
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed top-4 right-4 z-50 rounded-md bg-green-600 px-4 py-3 text-white text-sm font-medium shadow-lg"
    >
      {mensagem}
    </div>
  )
}

/**
 * Transforma um Contato (com campos de auditoria) em ContatoForm
 * mantendo apenas os campos editáveis pelo usuário.
 */
function contatoParaForm(contato: Contato): ContatoFormType {
  return {
    nome: contato.nome,
    email: contato.email,
    telefone: contato.telefone,
    empresa: contato.empresa,
    observacoes: contato.observacoes,
  }
}

function EditarContatoInner({ params }: PageProps) {
  const router = useRouter()
  const { isAdm, usuario } = useAuth()

  const [contato, setContato] = useState<Contato | null>(null)
  const [loading, setLoading] = useState(true)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [toast, setToast] = useState<ToastProps>({ mensagem: '', visivel: false })

  const id = Number(params.id)

  // Aguarda hidratação: redireciona para detalhe se não for administrador
  useEffect(() => {
    if (usuario !== null && !isAdm) {
      router.replace(`/contatos/${id}`)
    }
  }, [usuario, isAdm, id, router])

  // Carrega dados do contato para pré-preencher o formulário
  useEffect(() => {
    let cancelado = false

    async function carregar() {
      try {
        const dados = await buscarContato(id)
        if (!cancelado) setContato(dados)
      } catch (err: unknown) {
        if (cancelado) return
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

  // Auto-dismiss do toast após 2s
  useEffect(() => {
    if (!toast.visivel) return
    const timer = setTimeout(() => {
      setToast((prev) => ({ ...prev, visivel: false }))
    }, 2000)
    return () => clearTimeout(timer)
  }, [toast.visivel])

  async function handleSubmit(dados: ContatoFormType) {
    setSalvando(true)
    setErro(null)
    try {
      await atualizarContato(id, dados)
      setToast({ mensagem: 'Contato atualizado com sucesso!', visivel: true })
      // Redireciona para a página de detalhe após 1.5s
      setTimeout(() => router.push(`/contatos/${id}`), 1500)
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status
      if (status === 400) {
        setErro('Dados inválidos. Verifique os campos e tente novamente.')
      } else if (status === 404) {
        setErro('Contato não encontrado.')
      } else {
        setErro('Erro ao atualizar contato. Tente novamente.')
      }
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div className="container max-w-2xl mx-auto px-4 py-8">
      <Toast mensagem={toast.mensagem} visivel={toast.visivel} />

      {/* Botão Voltar */}
      <button
        onClick={() => router.push(`/contatos/${id}`)}
        className="mb-6 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
      >
        ← Voltar
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Editar Contato</h1>

      {loading && <Spinner />}

      {!loading && erro && !contato && (
        <div className="flex flex-col items-start gap-4">
          <p className="text-red-600">{erro}</p>
          <button
            onClick={() => router.push(`/contatos/${id}`)}
            className="px-4 py-2 rounded-md bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Voltar para detalhe
          </button>
        </div>
      )}

      {!loading && contato && (
        <ContatoForm
          valorInicial={contatoParaForm(contato)}
          onSubmit={handleSubmit}
          loading={salvando}
          erro={erro ?? undefined}
        />
      )}
    </div>
  )
}

export default function Page(props: PageProps) {
  return (
    <ProtectedRoute>
      <EditarContatoInner {...props} />
    </ProtectedRoute>
  )
}
