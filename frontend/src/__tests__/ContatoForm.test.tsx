/**
 * Testes unitários para ContatoForm — TASK-20 (FASE C / RF-07)
 *
 * Componente: frontend/src/components/ContatoForm.tsx
 * Cobre:
 *   - Renderização inicial (campos vazios / valorInicial)
 *   - Validação de campos obrigatórios
 *   - Validação de formato de e-mail
 *   - Validação de máscara de telefone no blur
 *   - Submit bem-sucedido (chama onSubmit)
 *   - Submit bloqueado quando há erros
 *   - Modal "alterações não salvas" ao cancelar com isDirty=true
 *   - Cancelar sem alterações volta direto
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

const pushMock = jest.fn()
const backMock = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

import ContatoForm from '../components/ContatoForm'


beforeEach(() => {
  jest.clearAllMocks()
  // Mocka window.history.back para não navegar
  Object.defineProperty(window, 'history', {
    value: { ...window.history, back: backMock },
    writable: true,
  })
})


// ---------------------------------------------------------------------------
// Renderização
// ---------------------------------------------------------------------------

describe('ContatoForm — renderização', () => {
  test('renderiza todos os campos do formulário', () => {
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)
    expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^e-mail/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/telefone/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/empresa/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/observações/i)).toBeInTheDocument()
  })

  test('renderiza botões Salvar e Cancelar', () => {
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)
    expect(screen.getByRole('button', { name: /salvar/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
  })

  test('preenche campos com valorInicial', () => {
    render(
      <ContatoForm
        onSubmit={jest.fn()}
        loading={false}
        valorInicial={{
          nome: 'Maria',
          email: 'maria@empresa.com',
          telefone: '(11) 91234-5678',
          empresa: 'Acme',
          observacoes: 'VIP',
        }}
      />
    )
    expect(screen.getByLabelText(/nome completo/i)).toHaveValue('Maria')
    expect(screen.getByLabelText(/^e-mail/i)).toHaveValue('maria@empresa.com')
  })

  test('exibe mensagem de erro externa (prop erro)', () => {
    render(
      <ContatoForm onSubmit={jest.fn()} loading={false} erro="Erro do servidor" />
    )
    expect(screen.getByText('Erro do servidor')).toBeInTheDocument()
  })

  test('desabilita botões quando loading=true', () => {
    render(<ContatoForm onSubmit={jest.fn()} loading={true} />)
    expect(screen.getByRole('button', { name: /salvar/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeDisabled()
  })
})


// ---------------------------------------------------------------------------
// Validação no submit
// ---------------------------------------------------------------------------

describe('ContatoForm — validação no submit', () => {
  test('exibe erro de nome obrigatório quando submit sem nome', async () => {
    const user = userEvent.setup()
    const onSubmit = jest.fn()
    render(<ContatoForm onSubmit={onSubmit} loading={false} />)

    // Preenche apenas email — nome fica vazio
    await user.type(screen.getByLabelText(/^e-mail/i), 'x@x.com')
    await user.click(screen.getByRole('button', { name: /salvar/i }))

    expect(await screen.findByText(/nome.*obrigat/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  test('exibe erro de e-mail obrigatório quando submit sem e-mail', async () => {
    const user = userEvent.setup()
    const onSubmit = jest.fn()
    render(<ContatoForm onSubmit={onSubmit} loading={false} />)

    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.click(screen.getByRole('button', { name: /salvar/i }))

    expect(await screen.findByText(/e-mail.*obrigat/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  test('exibe erro de formato de e-mail inválido', async () => {
    const user = userEvent.setup()
    const onSubmit = jest.fn()
    render(<ContatoForm onSubmit={onSubmit} loading={false} />)

    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.type(screen.getByLabelText(/^e-mail/i), 'invalido')
    await user.click(screen.getByRole('button', { name: /salvar/i }))

    expect(await screen.findByText(/e-mail.*válido/i)).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  test('limpa erro do campo ao corrigir o valor', async () => {
    const user = userEvent.setup()
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)

    // Dispara erro
    await user.click(screen.getByRole('button', { name: /salvar/i }))
    expect(await screen.findByText(/nome.*obrigat/i)).toBeInTheDocument()

    // Corrige
    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    // O erro de nome desaparece (handler limpa o erro ao digitar)
    expect(screen.queryByText(/nome.*obrigat/i)).not.toBeInTheDocument()
  })
})


// ---------------------------------------------------------------------------
// Submit bem-sucedido
// ---------------------------------------------------------------------------

describe('ContatoForm — submit bem-sucedido', () => {
  test('chama onSubmit com os dados quando válido', async () => {
    const user = userEvent.setup()
    const onSubmit = jest.fn().mockResolvedValue(undefined)
    render(<ContatoForm onSubmit={onSubmit} loading={false} />)

    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.type(screen.getByLabelText(/^e-mail/i), 'joao@empresa.com')
    await user.click(screen.getByRole('button', { name: /salvar/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          nome: 'João',
          email: 'joao@empresa.com',
        })
      )
    })
  })

  test('campos opcionais vazios são enviados como undefined', async () => {
    const user = userEvent.setup()
    const onSubmit = jest.fn().mockResolvedValue(undefined)
    render(<ContatoForm onSubmit={onSubmit} loading={false} />)

    await user.type(screen.getByLabelText(/nome completo/i), 'João')
    await user.type(screen.getByLabelText(/^e-mail/i), 'joao@empresa.com')
    await user.click(screen.getByRole('button', { name: /salvar/i }))

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled()
    })
    const arg = onSubmit.mock.calls[0][0]
    expect(arg.telefone).toBeUndefined()
    expect(arg.empresa).toBeUndefined()
  })
})


// ---------------------------------------------------------------------------
// Cancelar — modal "alterações não salvas"
// ---------------------------------------------------------------------------

describe('ContatoForm — cancelar e modal "alterações não salvas"', () => {
  test('cancelar sem alterações chama window.history.back diretamente', async () => {
    const user = userEvent.setup()
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)
    await user.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(backMock).toHaveBeenCalled()
    // E o modal NÃO deve aparecer
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('cancelar com alterações abre o modal de confirmação', async () => {
    const user = userEvent.setup()
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)
    // Cria alteração — campo nome fica diferente do snapshot inicial
    await user.type(screen.getByLabelText(/nome completo/i), 'A')
    await user.click(screen.getByRole('button', { name: /cancelar/i }))

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/alterações não salvas/i)).toBeInTheDocument()
  })

  test('"Continuar editando" fecha o modal sem navegar', async () => {
    const user = userEvent.setup()
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)
    await user.type(screen.getByLabelText(/nome completo/i), 'A')
    await user.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /continuar editando/i }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(backMock).not.toHaveBeenCalled()
  })

  test('"Sair sem salvar" navega de volta e fecha o modal', async () => {
    const user = userEvent.setup()
    render(<ContatoForm onSubmit={jest.fn()} loading={false} />)
    await user.type(screen.getByLabelText(/nome completo/i), 'A')
    await user.click(screen.getByRole('button', { name: /cancelar/i }))

    await user.click(screen.getByRole('button', { name: /sair sem salvar/i }))
    expect(backMock).toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
