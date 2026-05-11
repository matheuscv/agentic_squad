'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
  ReactNode,
} from 'react'
import { useRouter } from 'next/navigation'
import { AuthContextType, Usuario } from '../types/index'

// Contexto de autenticação — null indica que o Provider ainda não foi montado
export const AuthContext = createContext<AuthContextType | null>(null)

// ------------------------------------------------------------------
// AuthProvider — Client Component que mantém o estado de autenticação
// ------------------------------------------------------------------
export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter()
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [token, setToken] = useState<string | null>(null)

  // Restaura sessão persistida no localStorage ao montar o provider
  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUsuario = localStorage.getItem('usuario')
    if (storedToken) setToken(storedToken)
    if (storedUsuario) {
      try {
        setUsuario(JSON.parse(storedUsuario))
      } catch {
        // JSON inválido — descarta dado corrompido
        localStorage.removeItem('usuario')
      }
    }
  }, [])

  // Persiste token e usuário no localStorage e atualiza o estado local
  const login = useCallback((newToken: string, newUsuario: Usuario) => {
    localStorage.setItem('token', newToken)
    localStorage.setItem('usuario', JSON.stringify(newUsuario))
    setToken(newToken)
    setUsuario(newUsuario)
  }, [])

  // Limpa sessão e redireciona para /login
  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('usuario')
    setToken(null)
    setUsuario(null)
    router.push('/login')
  }, [router])

  // isAdm: memoizado para evitar re-renders desnecessários
  const isAdm = useMemo(() => usuario?.role === 'adm', [usuario])

  const value: AuthContextType = { usuario, token, login, logout, isAdm }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ------------------------------------------------------------------
// useAuth — hook de consumo do contexto
// Lança erro descritivo se usado fora de AuthProvider
// ------------------------------------------------------------------
export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth deve ser usado dentro de um <AuthProvider>')
  }
  return ctx
}
