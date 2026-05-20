/**
 * Testes unitários para InputField — TASK-20 (FASE C / RF-07)
 *
 * Componente: frontend/src/components/form/InputField.tsx
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import InputField from '../components/form/InputField'


function makeProps(overrides: Partial<Parameters<typeof InputField>[0]> = {}) {
  return {
    label: 'Nome',
    name: 'nome',
    value: '',
    onChange: jest.fn(),
    ...overrides,
  }
}


describe('InputField — renderização', () => {
  test('renderiza label e input associados via htmlFor/id', () => {
    render(<InputField {...makeProps()} />)
    const input = screen.getByLabelText('Nome')
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('id', 'nome')
  })

  test('exibe asterisco quando required=true', () => {
    render(<InputField {...makeProps({ required: true })} />)
    // O asterisco fica dentro de um <span> ao lado do label
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  test('não exibe asterisco quando required=false', () => {
    render(<InputField {...makeProps({ required: false })} />)
    expect(screen.queryByText('*')).not.toBeInTheDocument()
  })

  test('aplica placeholder', () => {
    render(<InputField {...makeProps({ placeholder: 'Ex.: João' })} />)
    expect(screen.getByPlaceholderText('Ex.: João')).toBeInTheDocument()
  })

  test('usa type="text" por padrão', () => {
    render(<InputField {...makeProps()} />)
    expect(screen.getByLabelText('Nome')).toHaveAttribute('type', 'text')
  })

  test('aplica type="email" quando fornecido', () => {
    render(<InputField {...makeProps({ type: 'email' })} />)
    expect(screen.getByLabelText('Nome')).toHaveAttribute('type', 'email')
  })

  test('aplica type="password" quando fornecido', () => {
    render(<InputField {...makeProps({ type: 'password' })} />)
    expect(screen.getByLabelText('Nome')).toHaveAttribute('type', 'password')
  })

  test('marca disabled quando disabled=true', () => {
    render(<InputField {...makeProps({ disabled: true })} />)
    expect(screen.getByLabelText('Nome')).toBeDisabled()
  })
})


describe('InputField — mensagem de erro', () => {
  test('exibe a mensagem quando error está presente', () => {
    render(<InputField {...makeProps({ error: 'Campo inválido' })} />)
    expect(screen.getByText('Campo inválido')).toBeInTheDocument()
  })

  test('não renderiza parágrafo de erro quando error é vazio', () => {
    const { container } = render(<InputField {...makeProps({ error: '' })} />)
    expect(container.querySelector('p')).toBeNull()
  })
})


describe('InputField — eventos', () => {
  test('chama onChange ao digitar', async () => {
    const user = userEvent.setup()
    const onChange = jest.fn()
    render(<InputField {...makeProps({ onChange })} />)
    await user.type(screen.getByLabelText('Nome'), 'A')
    expect(onChange).toHaveBeenCalled()
  })

  test('chama onBlur quando informado', async () => {
    const user = userEvent.setup()
    const onBlur = jest.fn()
    render(<InputField {...makeProps({ onBlur })} />)
    const input = screen.getByLabelText('Nome')
    input.focus()
    await user.tab()
    expect(onBlur).toHaveBeenCalled()
  })
})


describe('InputField — máscara', () => {
  test('renderiza input com máscara para telefone (não quebra)', () => {
    render(
      <InputField
        {...makeProps({
          label: 'Telefone',
          name: 'telefone',
          mask: '(99) 99999-9999',
          value: '',
        })}
      />
    )
    // O componente InputMask delega ao input filho — basta verificar a renderização
    expect(screen.getByLabelText('Telefone')).toBeInTheDocument()
  })
})
