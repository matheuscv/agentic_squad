import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '../hooks/useAuth'
import NavbarWrapper from '../components/NavbarWrapper'

export const metadata: Metadata = {
  title: 'Manutenção de Contatos',
  description: 'Sistema de manutenção de contatos de clientes',
}

// RootLayout permanece Server Component — AuthProvider é Client Component
// e pode ser importado aqui sem problemas (Next.js trata o boundary automaticamente).
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>
        <AuthProvider>
          <NavbarWrapper />
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
