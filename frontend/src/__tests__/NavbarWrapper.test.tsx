/**
 * Testes unitários para NavbarWrapper
 *
 * Componente: frontend/src/components/NavbarWrapper.tsx
 * Critério de aceite (PRD 13.4 — RF-F1-01/RF-F1-02):
 *   - Acessar /contatos exibe a Navbar
 *   - Acessar /login não exibe a Navbar
 *   - Acessar /cadastro não exibe a Navbar
 *
 * DEPENDÊNCIAS NECESSÁRIAS (ver TESTES.md):
 *   jest, @testing-library/react, @testing-library/jest-dom,
 *   jest-environment-jsdom, ts-jest
 *
 * Mock: next/navigation (usePathname) e ./Navbar (componente filho)
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import NavbarWrapper from '../components/NavbarWrapper'

// Mock de next/navigation — usePathname é controlado por cada teste
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}))

// Mock do componente Navbar para isolar o teste do wrapper
jest.mock('../components/Navbar', () => {
  return function MockNavbar() {
    return <nav data-testid="navbar">Navbar</nav>
  }
})

import { usePathname } from 'next/navigation'
const mockUsePathname = usePathname as jest.Mock


// ---------------------------------------------------------------------------
// Caminho feliz — rotas onde a Navbar DEVE aparecer
// ---------------------------------------------------------------------------

describe('NavbarWrapper — rotas com Navbar', () => {
  test('exibe Navbar em /contatos', () => {
    mockUsePathname.mockReturnValue('/contatos')
    render(<NavbarWrapper />)
    expect(screen.getByTestId('navbar')).toBeInTheDocument()
  })

  test('exibe Navbar em / (raiz)', () => {
    mockUsePathname.mockReturnValue('/')
    render(<NavbarWrapper />)
    expect(screen.getByTestId('navbar')).toBeInTheDocument()
  })

  test('exibe Navbar em /contatos/1 (rota de detalhe)', () => {
    mockUsePathname.mockReturnValue('/contatos/1')
    render(<NavbarWrapper />)
    expect(screen.getByTestId('navbar')).toBeInTheDocument()
  })

  test('exibe Navbar em /contatos/novo', () => {
    mockUsePathname.mockReturnValue('/contatos/novo')
    render(<NavbarWrapper />)
    expect(screen.getByTestId('navbar')).toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// Rotas públicas — Navbar NÃO deve aparecer
// ---------------------------------------------------------------------------

describe('NavbarWrapper — rotas públicas sem Navbar', () => {
  test('oculta Navbar em /login', () => {
    mockUsePathname.mockReturnValue('/login')
    const { container } = render(<NavbarWrapper />)
    // Componente retorna null — nada deve ser renderizado
    expect(screen.queryByTestId('navbar')).not.toBeInTheDocument()
    expect(container).toBeEmptyDOMElement()
  })

  test('oculta Navbar em /cadastro', () => {
    mockUsePathname.mockReturnValue('/cadastro')
    const { container } = render(<NavbarWrapper />)
    expect(screen.queryByTestId('navbar')).not.toBeInTheDocument()
    expect(container).toBeEmptyDOMElement()
  })
})


// ---------------------------------------------------------------------------
// Casos de borda
// ---------------------------------------------------------------------------

describe('NavbarWrapper — casos de borda', () => {
  test('/loginxyz (não é /login exato) exibe Navbar', () => {
    // A lógica usa includes() — verifica correspondência exata com ROTAS_SEM_NAVBAR
    mockUsePathname.mockReturnValue('/loginxyz')
    render(<NavbarWrapper />)
    expect(screen.getByTestId('navbar')).toBeInTheDocument()
  })

  test('/cadastro/confirmar (sub-rota de /cadastro) exibe Navbar', () => {
    // ROTAS_SEM_NAVBAR contém '/cadastro' (exato) — sub-rotas não são bloqueadas
    mockUsePathname.mockReturnValue('/cadastro/confirmar')
    render(<NavbarWrapper />)
    expect(screen.getByTestId('navbar')).toBeInTheDocument()
  })
})
