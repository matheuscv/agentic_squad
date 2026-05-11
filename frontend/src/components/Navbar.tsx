'use client'

import { useAuth } from '../hooks/useAuth'

export default function Navbar() {
  // useAuth estará disponível quando AuthProvider for adicionado ao layout (TASK-06)
  const { usuario, logout } = useAuth()

  return (
    <nav className="w-full h-16 bg-white border-b border-gray-200 shadow-sm flex items-center px-6">
      {/* Logo / título da aplicação */}
      <div className="flex items-center gap-2 flex-1">
        {/* Ícone de usuários (SVG simples) */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 text-blue-600"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <span className="text-gray-900 font-bold text-lg tracking-tight">
          Contatos de Clientes
        </span>
      </div>

      {/* Área do usuário (lado direito) */}
      {usuario && (
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600 hidden sm:inline">
            Olá,{' '}
            <span className="font-medium text-gray-800">{usuario.nome}</span>
          </span>
          <button
            onClick={logout}
            className="text-sm px-4 py-1.5 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Sair
          </button>
        </div>
      )}
    </nav>
  )
}
