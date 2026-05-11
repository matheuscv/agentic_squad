'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '../../hooks/useAuth'
import * as authService from '../../services/auth.service'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setErro(null)
    setLoading(true)

    try {
      // 1. Autentica e obtém o token JWT
      const tokenResponse = await authService.login(email, senha)
      // 2. Armazena o token no localStorage antes de chamar getMe (interceptor lê dali)
      localStorage.setItem('token', tokenResponse.access_token)
      // 3. Busca os dados do usuário autenticado
      const usuario = await authService.getMe()
      // 4. Registra a sessão no contexto (também persiste no localStorage)
      login(tokenResponse.access_token, usuario)
      // 5. Redireciona para a área autenticada
      router.push('/contatos')
    } catch {
      // Qualquer erro (401, 422, rede) exibe mensagem genérica em PT-BR
      setErro('E-mail ou senha inválidos.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-md">
        {/* Cabeçalho */}
        <h1 className="text-2xl font-bold text-gray-900">Entrar</h1>
        <p className="mt-1 text-sm text-gray-500">
          Acesse sua conta para gerenciar seus contatos.
        </p>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          {/* E-mail */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              E-mail
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
              Senha
            </label>
            <input
              id="senha"
              type="password"
              autoComplete="current-password"
              required
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="••••••••"
            />
          </div>

          {/* Mensagem de erro */}
          {erro && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
              {erro}
            </p>
          )}

          {/* Botão de submit */}
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading && (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            )}
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        {/* Link de cadastro */}
        <p className="mt-4 text-center text-sm text-gray-500">
          Não tem uma conta?{' '}
          <Link href="/cadastro" className="font-medium text-blue-600 hover:underline">
            Criar uma conta
          </Link>
        </p>
      </div>
    </main>
  )
}
