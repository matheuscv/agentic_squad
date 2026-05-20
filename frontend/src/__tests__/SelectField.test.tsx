/**
 * Testes unitários para SelectField — TASK-20 (FASE C / RF-07)
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SelectField from '../components/form/SelectField'


const OPTIONS = [
  { value: 'a', label: 'Opção A' },
  { value: 'b', label: 'Opção B' },
]

function makeProps(overrides: Partial<Parameters<typeof SelectField>[0]> = {}) {
  return {
    label: 'Categoria',
    name: 'categoria',
    value: '',
    onChange: jest.fn(),
    options: OPTIONS,
    ...overrides,
  }
}


describe('SelectField — renderização', () => {
  test('renderiza label associado ao select', () => {
    render(<SelectField {...makeProps()} />)
    expect(screen.getByLabelText('Categoria')).toBeInTheDocument()
  })

  test('renderiza todas as opções', () => {
    render(<SelectField {...makeProps()} />)
    expect(screen.getByRole('option', { name: 'Opção A' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Opção B' })).toBeInTheDocument()
  })

  test('renderiza placeholder como option vazia quando informado', () => {
    render(<SelectField {...makeProps({ placeholder: 'Selecione...' })} />)
    expect(screen.getByRole('option', { name: 'Selecione...' })).toBeInTheDocument()
  })

  test('NÃO renderiza placeholder quando não informado', () => {
    render(<SelectField {...makeProps()} />)
    expect(screen.queryByRole('option', { name: 'Selecione...' })).not.toBeInTheDocument()
  })

  test('exibe asterisco quando required=true', () => {
    render(<SelectField {...makeProps({ required: true })} />)
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  test('marca disabled quando disabled=true', () => {
    render(<SelectField {...makeProps({ disabled: true })} />)
    expect(screen.getByLabelText('Categoria')).toBeDisabled()
  })

  test('exibe mensagem de erro quando error está presente', () => {
    render(<SelectField {...makeProps({ error: 'Obrigatório' })} />)
    expect(screen.getByText('Obrigatório')).toBeInTheDocument()
  })
})


describe('SelectField — eventos', () => {
  test('chama onChange ao selecionar', async () => {
    const user = userEvent.setup()
    const onChange = jest.fn()
    render(<SelectField {...makeProps({ onChange })} />)
    await user.selectOptions(screen.getByLabelText('Categoria'), 'b')
    expect(onChange).toHaveBeenCalled()
  })
})
