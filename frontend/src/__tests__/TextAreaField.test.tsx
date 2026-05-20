/**
 * Testes unitários para TextAreaField — TASK-20 (FASE C / RF-07)
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TextAreaField from '../components/form/TextAreaField'


function makeProps(overrides: Partial<Parameters<typeof TextAreaField>[0]> = {}) {
  return {
    label: 'Observações',
    name: 'observacoes',
    value: '',
    onChange: jest.fn(),
    ...overrides,
  }
}


describe('TextAreaField — renderização', () => {
  test('renderiza label associado ao textarea', () => {
    render(<TextAreaField {...makeProps()} />)
    expect(screen.getByLabelText('Observações')).toBeInTheDocument()
  })

  test('usa rows padrão = 4 quando não informado', () => {
    render(<TextAreaField {...makeProps()} />)
    expect(screen.getByLabelText('Observações')).toHaveAttribute('rows', '4')
  })

  test('aplica rows customizado', () => {
    render(<TextAreaField {...makeProps({ rows: 7 })} />)
    expect(screen.getByLabelText('Observações')).toHaveAttribute('rows', '7')
  })

  test('exibe asterisco quando required=true', () => {
    render(<TextAreaField {...makeProps({ required: true })} />)
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  test('marca disabled quando disabled=true', () => {
    render(<TextAreaField {...makeProps({ disabled: true })} />)
    expect(screen.getByLabelText('Observações')).toBeDisabled()
  })

  test('aplica placeholder', () => {
    render(<TextAreaField {...makeProps({ placeholder: 'Detalhes...' })} />)
    expect(screen.getByPlaceholderText('Detalhes...')).toBeInTheDocument()
  })

  test('exibe mensagem de erro quando error está presente', () => {
    render(<TextAreaField {...makeProps({ error: 'Muito longo' })} />)
    expect(screen.getByText('Muito longo')).toBeInTheDocument()
  })
})


describe('TextAreaField — eventos', () => {
  test('chama onChange ao digitar', async () => {
    const user = userEvent.setup()
    const onChange = jest.fn()
    render(<TextAreaField {...makeProps({ onChange })} />)
    await user.type(screen.getByLabelText('Observações'), 'A')
    expect(onChange).toHaveBeenCalled()
  })
})
