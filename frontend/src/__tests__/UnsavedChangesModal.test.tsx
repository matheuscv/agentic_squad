/**
 * Testes unitários para UnsavedChangesModal — RF-F2-06 (Fase 2)
 *
 * Componente: frontend/src/components/UnsavedChangesModal.tsx
 * Critérios de aceite (PRD 14.4 — RF-F2-06):
 *   - Modal não renderiza nada quando isOpen=false
 *   - Modal renderiza conteúdo quando isOpen=true
 *   - Clicar "Continuar editando" chama onContinue
 *   - Clicar "Sair sem salvar" chama onLeave
 *   - Atributos de acessibilidade role="dialog" e aria-modal="true" presentes
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import UnsavedChangesModal from '../components/UnsavedChangesModal'


// ---------------------------------------------------------------------------
// Fábrica de props
// ---------------------------------------------------------------------------

function makeProps(overrides: Partial<{ isOpen: boolean; onContinue: () => void; onLeave: () => void }> = {}) {
  return {
    isOpen: true,
    onContinue: jest.fn(),
    onLeave: jest.fn(),
    ...overrides,
  }
}


// ---------------------------------------------------------------------------
// isOpen = false — nada deve ser renderizado
// ---------------------------------------------------------------------------

describe('UnsavedChangesModal — fechado (isOpen=false)', () => {
  test('não renderiza nenhum elemento quando isOpen é false', () => {
    const { container } = render(<UnsavedChangesModal {...makeProps({ isOpen: false })} />)
    expect(container).toBeEmptyDOMElement()
  })

  test('não exibe texto do modal quando fechado', () => {
    render(<UnsavedChangesModal {...makeProps({ isOpen: false })} />)
    expect(screen.queryByText(/sair sem salvar/i)).not.toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// isOpen = true — conteúdo deve ser renderizado
// ---------------------------------------------------------------------------

describe('UnsavedChangesModal — aberto (isOpen=true)', () => {
  test('exibe o título "Sair sem salvar?"', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    expect(screen.getByRole('heading', { name: /sair sem salvar/i })).toBeInTheDocument()
  })

  test('exibe a mensagem sobre alterações não salvas', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    expect(screen.getByText(/alterações não salvas/i)).toBeInTheDocument()
  })

  test('exibe botão "Continuar editando"', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    expect(screen.getByRole('button', { name: /continuar editando/i })).toBeInTheDocument()
  })

  test('exibe botão "Sair sem salvar"', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    expect(screen.getByRole('button', { name: /sair sem salvar/i })).toBeInTheDocument()
  })

  test('possui role="dialog" para acessibilidade', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  test('possui aria-modal="true"', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
  })

  test('possui aria-labelledby apontando para o título', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    const dialog = screen.getByRole('dialog')
    const labelledBy = dialog.getAttribute('aria-labelledby')
    expect(labelledBy).toBeTruthy()
    // O elemento com esse ID deve existir e ter o texto do título
    const titleEl = document.getElementById(labelledBy!)
    expect(titleEl).not.toBeNull()
    expect(titleEl?.textContent).toMatch(/sair sem salvar/i)
  })
})


// ---------------------------------------------------------------------------
// Callbacks — interações do usuário
// ---------------------------------------------------------------------------

describe('UnsavedChangesModal — callbacks', () => {
  test('chama onContinue ao clicar "Continuar editando"', async () => {
    const user = userEvent.setup()
    const onContinue = jest.fn()
    render(<UnsavedChangesModal {...makeProps({ onContinue })} />)

    await user.click(screen.getByRole('button', { name: /continuar editando/i }))
    expect(onContinue).toHaveBeenCalledTimes(1)
  })

  test('não chama onLeave ao clicar "Continuar editando"', async () => {
    const user = userEvent.setup()
    const onLeave = jest.fn()
    render(<UnsavedChangesModal {...makeProps({ onLeave })} />)

    await user.click(screen.getByRole('button', { name: /continuar editando/i }))
    expect(onLeave).not.toHaveBeenCalled()
  })

  test('chama onLeave ao clicar "Sair sem salvar"', async () => {
    const user = userEvent.setup()
    const onLeave = jest.fn()
    render(<UnsavedChangesModal {...makeProps({ onLeave })} />)

    await user.click(screen.getByRole('button', { name: /sair sem salvar/i }))
    expect(onLeave).toHaveBeenCalledTimes(1)
  })

  test('não chama onContinue ao clicar "Sair sem salvar"', async () => {
    const user = userEvent.setup()
    const onContinue = jest.fn()
    render(<UnsavedChangesModal {...makeProps({ onContinue })} />)

    await user.click(screen.getByRole('button', { name: /sair sem salvar/i }))
    expect(onContinue).not.toHaveBeenCalled()
  })

  test('cada botão tem type="button" (não dispara submit)', () => {
    render(<UnsavedChangesModal {...makeProps()} />)
    const buttons = screen.getAllByRole('button')
    buttons.forEach((btn) => {
      expect(btn).toHaveAttribute('type', 'button')
    })
  })
})


// ---------------------------------------------------------------------------
// Transição de estado: fechado → aberto → fechado
// ---------------------------------------------------------------------------

describe('UnsavedChangesModal — transição de estado', () => {
  test('exibe conteúdo ao mudar isOpen de false para true', () => {
    const { rerender } = render(<UnsavedChangesModal {...makeProps({ isOpen: false })} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    rerender(<UnsavedChangesModal {...makeProps({ isOpen: true })} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  test('remove conteúdo ao mudar isOpen de true para false', () => {
    const { rerender } = render(<UnsavedChangesModal {...makeProps({ isOpen: true })} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    rerender(<UnsavedChangesModal {...makeProps({ isOpen: false })} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
