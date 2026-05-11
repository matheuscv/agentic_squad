'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import * as authService from '../../services/auth.service'

export default function CadastroPage() {
  const router = useRouter()

  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState(false)

  // Validação client-side antes de enviar ao servidor
  function validar(): boolean {
    if (!nome.trim()) {
      setErro('O nome completo é obrigatório.')
      return false
    }
    if (!email.trim()) {
      setErro('O e-mail é obrigatório.')
      return false
    }
    if (senha.length < 6) {
      setErro('A senha deve ter no mínimo 6 caracteres.')
      return false
    }
    return true
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setErro(null)

    if (!validar()) return

    setLoading(true)

    try {
      await authService.cadastrar(nome.trim(), email.trim(), senha)
      setSucesso(true)
      // Redireciona para /login após 2 segundos para o usuário ler o aviso
      setTimeout(() => router.push('/login'), 2000)
    } catch (err: unknown) {
      // Status 400 normalmente indica e-mail duplicado no backend
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 400) {
        setErro('Este e-mail já está cadastrado.')
      } else {
        setErro('Erro ao criar a conta. Tente novamente.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-md">
        {/* Cabeçalho */}
        <h1 className="text-2xl font-bold text-gray-900">Criar Conta</h1>
        <p className="mt-1 text-sm text-gray-500">
          Preencha os dados abaixo para se cadastrar.
        </p>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          {/* Nome Completo */}
          <div>
            <label
              htmlFor="nome"
              className="block text-sm font-medium text-gray-700"
            >
              Nome Completo <span className="text-red-500">*</span>
            </label>
            <input
              id="nome"
              type="text"
              autoComplete="name"
              required
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="João da Silva"
            />
          </div>

          {/* E-mail */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              E-mail <span className="text-red-500">*</span>
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="seu@email.com"
            />
          </div>

          {/* Senha */}
          <div>
            <label
              htmlFor="senha"
              className="block text-sm font-medium text-gray-700"
            >
              Senha <span className="text-red-500">*</span>
            </label>
            <input
              id="senha"
              type="password"
              autoComplete="new-password"
              required
              minLength={6}
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Mínimo 6 caracteres"
            />
          </div>

          {/* Mensagem de erro */}
          {erro && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {erro}
            </p>
          )}

          {/* Mensagem de sucesso */}
          {sucesso && (
            <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">
              Conta criada com sucesso! Faça login.
            </p>
          )}

          {/* Botão de submit */}
          <button
            type="submit"
            disabled={loading || sucesso}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            )}
            {loading ? 'Criando conta...' : 'Criar Conta'}
          </button>
        </form>

        {/* Link para login */}
        <p className="mt-4 text-center text-sm text-gray-500">
          Já tem uma conta?{' '}
          <Link href="/login" className="font-medium text-blue-600 hover:underline">
            Já tenho uma conta
          </Link>
        </p>
      </div>
    </main>
  )
}
