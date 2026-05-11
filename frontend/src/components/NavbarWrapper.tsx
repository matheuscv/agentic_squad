'use client'

import { usePathname } from 'next/navigation'
import Navbar from './Navbar'

// Rotas onde a Navbar NÃO deve ser exibida
const ROTAS_SEM_NAVBAR = ['/login', '/cadastro']

export default function NavbarWrapper() {
  const pathname = usePathname()

  // Oculta a Navbar nas rotas de autenticação
  if (ROTAS_SEM_NAVBAR.includes(pathname)) {
    return null
  }

  return <Navbar />
}
