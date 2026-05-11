'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * ProtectedRoute — envolve páginas que exigem autenticação.
 * - Antes da verificação (mounted=false): exibe spinner centralizado.
 * - Sem token: redireciona para /login.
 * - Com token: renderiza os filhos normalmente.
 *
 * Decisão conservadora: a verificação é feita via localStorage para
 * evitar depender do AuthContext, o que permite usar este componente
 * mesmo em layouts sem AuthProvider (ex: testes isolados).
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [hasToken, setHasToken] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
    } else {
      setHasToken(true)
    }
    setMounted(true)
  }, [router])

  // Enquanto verifica, exibe spinner para evitar flash de conteúdo protegido
  if (!mounted || !hasToken) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  return <>{children}</>
}
