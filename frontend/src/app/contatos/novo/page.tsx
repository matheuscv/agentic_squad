'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '../../../components/ProtectedRoute'
import ContatoForm from '../../../components/ContatoForm'
import { useAuth } from '../../../hooks/useAuth'
import { ContatoForm as ContatoFormType } from '../../../types/index'
import { criarContato } from '../../../services/contatos.service'

// Toast simples: estado local com auto-dismiss via useEffect
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
      className="fixed top-4 right-4 z-50 rounded-md bg-green-600 px-4 py-3 text-white text-sm font-medium shadow-lg transition-opacity"
    >
      {mensagem}
    </div>
  )
}

function NovoContatoInner() {
  const router = useRouter()
  const { isAdm, usuario } = useAuth()

  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [toast, setToast] = useState<ToastProps>({ mensagem: '', visivel: false })

  // Aguarda hidratação: redireciona caso não seja administrador
  useEffect(() => {
    // usuario !== null indica que o AuthProvider já hidratou o estado
    if (usuario !== null && !isAdm) {
      router.replace('/contatos')
    }
  }, [usuario, isAdm, router])

  // Auto-dismiss do toast após 2s
  useEffect(() => {
    if (!toast.visivel) return
    const timer = setTimeout(() => {
      setToast((prev) => ({ ...prev, visivel: false }))
    }, 2000)
    return () => clearTimeout(timer)
  }, [toast.visivel])

  async function handleSubmit(dados: ContatoFormType) {
    setLoading(true)
    setErro(null)
    try {
      await criarContato(dados)
      setToast({ mensagem: 'Contato criado com sucesso!', visivel: true })
      // Redireciona após 1.5s para permitir leitura do toast
      setTimeout(() => router.push('/contatos'), 1500)
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status
      if (status === 400) {
        setErro('Este e-mail já está cadastrado.')
      } else {
        setErro('Erro ao criar contato. Tente novamente.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container max-w-2xl mx-auto px-4 py-8">
      <Toast mensagem={toast.mensagem} visivel={toast.visivel} />

      {/* Botão Voltar para lista */}
      <button
        onClick={() => router.push('/contatos')}
        className="mb-6 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
      >
        ← Voltar para lista
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Novo Contato</h1>

      <ContatoForm onSubmit={handleSubmit} loading={loading} erro={erro ?? undefined} />
    </div>
  )
}

export default function Page() {
  return (
    <ProtectedRoute>
      <NovoContatoInner />
    </ProtectedRoute>
  )
}
