/**
 * Testes unitários para ContatoDetalhe — TASK-20 (FASE C / RF-07)
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ContatoDetalhe from '../components/ContatoDetalhe'

const CONTATO = {
  id: 1,
  nome: 'João',
  email: 'joao@x.com',
  telefone: '(11) 99999-9999',
  empresa: 'Acme',
  observacoes: 'VIP',
  criado_em: '2026-01-01T10:00:00Z',
  atualizado_em: '2026-01-02T11:00:00Z',
}


describe('ContatoDetalhe — renderização', () => {
  test('exibe todos os campos do contato', () => {
    render(
      <ContatoDetalhe
        contato={CONTATO}
        isAdm={false}
        onEditar={jest.fn()}
        onExcluir={jest.fn()}
      />
    )
    expect(screen.getByText('João')).toBeInTheDocument()
    expect(screen.getByText('joao@x.com')).toBeInTheDocument()
    expect(screen.getByText('(11) 99999-9999')).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
    expect(screen.getByText('VIP')).toBeInTheDocument()
  })

  test('exibe "Não informado" para campos opcionais ausentes', () => {
    render(
      <ContatoDetalhe
        contato={{ ...CONTATO, telefone: undefined, empresa: undefined, observacoes: undefined }}
        isAdm={false}
        onEditar={jest.fn()}
        onExcluir={jest.fn()}
      />
    )
    const naoInformados = screen.getAllByText(/não informado/i)
    expect(naoInformados.length).toBeGreaterThanOrEqual(3)
  })

  test('NÃO exibe botões Editar/Excluir quando isAdm=false', () => {
    render(
      <ContatoDetalhe
        contato={CONTATO}
        isAdm={false}
        onEditar={jest.fn()}
        onExcluir={jest.fn()}
      />
    )
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /excluir/i })).not.toBeInTheDocument()
  })

  test('exibe botões Editar/Excluir quando isAdm=true', () => {
    render(
      <ContatoDetalhe
        contato={CONTATO}
        isAdm={true}
        onEditar={jest.fn()}
        onExcluir={jest.fn()}
      />
    )
    expect(screen.getByRole('button', { name: /editar/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /excluir/i })).toBeInTheDocument()
  })
})


describe('ContatoDetalhe — interações', () => {
  test('clicar em Editar chama onEditar', async () => {
    const user = userEvent.setup()
    const onEditar = jest.fn()
    render(
      <ContatoDetalhe
        contato={CONTATO}
        isAdm={true}
        onEditar={onEditar}
        onExcluir={jest.fn()}
      />
    )
    await user.click(screen.getByRole('button', { name: /editar/i }))
    expect(onEditar).toHaveBeenCalledTimes(1)
  })

  test('clicar em Excluir chama onExcluir', async () => {
    const user = userEvent.setup()
    const onExcluir = jest.fn()
    render(
      <ContatoDetalhe
        contato={CONTATO}
        isAdm={true}
        onEditar={jest.fn()}
        onExcluir={onExcluir}
      />
    )
    await user.click(screen.getByRole('button', { name: /excluir/i }))
    expect(onExcluir).toHaveBeenCalledTimes(1)
  })
})


describe('ContatoDetalhe — formatação de data', () => {
  test('formata data ISO para pt-BR', () => {
    render(
      <ContatoDetalhe
        contato={CONTATO}
        isAdm={false}
        onEditar={jest.fn()}
        onExcluir={jest.fn()}
      />
    )
    // Formato pt-BR contém / na separação dia/mês/ano
    expect(screen.getAllByText(/\d{2}\/\d{2}\/\d{4}/).length).toBeGreaterThan(0)
  })

  test('exibe "Não informado" quando data é inválida', () => {
    render(
      <ContatoDetalhe
        contato={{ ...CONTATO, criado_em: 'data-invalida', atualizado_em: 'data-invalida' }}
        isAdm={false}
        onEditar={jest.fn()}
        onExcluir={jest.fn()}
      />
    )
    // As datas viraram "Não informado"
    const naoInformados = screen.getAllByText(/não informado/i)
    expect(naoInformados.length).toBeGreaterThanOrEqual(2)
  })
})
