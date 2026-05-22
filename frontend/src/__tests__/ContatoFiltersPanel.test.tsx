/**
 * Testes do componente ContatoFiltersPanel — TASK-09 (Fase D / D.4 / RF-05).
 *
 * Componente: frontend/src/components/ContatoFiltersPanel.tsx
 *
 * Cobertura:
 *  - Render inicial: painel expandido com os 5 controles (empresa, criado_desde,
 *    criado_ate, sem_email, sem_telefone) e botao "Limpar filtros"
 *  - Toggle: clique no cabecalho colapsa / expande
 *  - Filtros booleanos: clique nos checkboxes dispara onChange imediatamente
 *  - Range invertido: exibe aviso (role="alert")
 *  - "Limpar filtros": reseta para FILTROS_VAZIOS
 *  - Debounce do campo empresa (300 ms) — usa fake timers
 *
 * Mocks:
 *  - sessionStorage e usado pelo componente; jsdom ja fornece a API por
 *    padrao, entao nao precisamos mockar.
 */

import React from 'react'
import { render, screen, act, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import ContatoFiltersPanel, {
  ContatoFiltros,
  FILTROS_VAZIOS,
} from '../components/ContatoFiltersPanel'


function renderPanel(initial: ContatoFiltros = FILTROS_VAZIOS) {
  const onChange = jest.fn()
  const utils = render(
    <ContatoFiltersPanel value={initial} onChange={onChange} />
  )
  return { ...utils, onChange }
}


// O componente usa sessionStorage para lembrar o estado colapsado durante a
// sessao. No ambiente jsdom isso persiste entre os testes do mesmo arquivo —
// limpamos antes de cada teste para garantir isolamento.
beforeEach(() => {
  window.sessionStorage.clear()
})


describe('ContatoFiltersPanel — render inicial', () => {
  test('renderiza os 5 controles de filtro', () => {
    renderPanel()
    expect(screen.getByLabelText(/^empresa$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^criado desde$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^criado ate$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/somente sem e-mail/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/somente sem telefone/i)).toBeInTheDocument()
  })

  test('exibe botao "Limpar filtros" desabilitado quando nao ha filtros ativos', () => {
    renderPanel()
    const btn = screen.getByRole('button', { name: /limpar filtros/i })
    expect(btn).toBeDisabled()
  })

  test('cabecalho do painel exibe "Filtros"', () => {
    renderPanel()
    expect(screen.getByRole('button', { name: /^filtros/i })).toBeInTheDocument()
  })
})


describe('ContatoFiltersPanel — collapse/expand', () => {
  test('clicar no cabecalho colapsa o conteudo', async () => {
    const user = userEvent.setup()
    renderPanel()

    // Inicialmente expandido — campo empresa visivel.
    expect(screen.getByLabelText(/^empresa$/i)).toBeInTheDocument()

    const toggle = screen.getByRole('button', { name: /^filtros/i })
    await user.click(toggle)

    // Apos colapsar, o conteudo nao deve estar no DOM.
    expect(screen.queryByLabelText(/^empresa$/i)).not.toBeInTheDocument()
  })

  test('aria-expanded reflete estado collapsed/expanded', async () => {
    const user = userEvent.setup()
    renderPanel()
    const toggle = screen.getByRole('button', { name: /^filtros/i })

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })
})


describe('ContatoFiltersPanel — filtros booleanos', () => {
  test('clicar em "Somente sem e-mail" dispara onChange com sem_email=true', async () => {
    const user = userEvent.setup()
    const { onChange } = renderPanel()

    await user.click(screen.getByLabelText(/somente sem e-mail/i))

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ sem_email: true })
    )
  })

  test('clicar em "Somente sem telefone" dispara onChange com sem_telefone=true', async () => {
    const user = userEvent.setup()
    const { onChange } = renderPanel()

    await user.click(screen.getByLabelText(/somente sem telefone/i))

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ sem_telefone: true })
    )
  })
})


describe('ContatoFiltersPanel — date inputs', () => {
  test('alterar criado_desde dispara onChange com a nova data', () => {
    const { onChange } = renderPanel()

    const inputDesde = screen.getByLabelText(/^criado desde$/i)
    fireEvent.change(inputDesde, { target: { value: '2026-01-01' } })

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ criado_desde: '2026-01-01' })
    )
  })

  test('alterar criado_ate dispara onChange com a nova data', () => {
    const { onChange } = renderPanel()

    const inputAte = screen.getByLabelText(/^criado ate$/i)
    fireEvent.change(inputAte, { target: { value: '2026-12-31' } })

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ criado_ate: '2026-12-31' })
    )
  })
})


describe('ContatoFiltersPanel — range invertido', () => {
  test('quando criado_desde > criado_ate exibe aviso role="alert"', () => {
    renderPanel({
      ...FILTROS_VAZIOS,
      criado_desde: '2026-12-31',
      criado_ate: '2026-01-01',
    })

    const aviso = screen.getByRole('alert')
    expect(aviso).toBeInTheDocument()
    expect(aviso.textContent).toMatch(/anterior ou igual/i)
  })

  test('range valido NAO exibe aviso', () => {
    renderPanel({
      ...FILTROS_VAZIOS,
      criado_desde: '2026-01-01',
      criado_ate: '2026-12-31',
    })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})


describe('ContatoFiltersPanel — Limpar filtros', () => {
  test('quando ha filtros ativos, "Limpar filtros" fica habilitado', () => {
    renderPanel({ ...FILTROS_VAZIOS, sem_email: true })
    const btn = screen.getByRole('button', { name: /limpar filtros/i })
    expect(btn).not.toBeDisabled()
  })

  test('clicar em "Limpar filtros" reseta os filtros via onChange', async () => {
    const user = userEvent.setup()
    const { onChange } = renderPanel({
      ...FILTROS_VAZIOS,
      empresa: 'Acme',
      sem_email: true,
    })

    await user.click(screen.getByRole('button', { name: /limpar filtros/i }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTROS_VAZIOS })
  })

  test('quantidade de filtros ativos exibida no badge', () => {
    renderPanel({
      ...FILTROS_VAZIOS,
      empresa: 'Acme',
      sem_email: true,
      sem_telefone: true,
    })
    // O badge tem aria-label "3 filtros ativos"
    expect(screen.getByLabelText(/3 filtros ativos/i)).toBeInTheDocument()
  })
})


describe('ContatoFiltersPanel — debounce empresa (300 ms)', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('digitar no input empresa NAO dispara onChange imediatamente', () => {
    const onChange = jest.fn()
    render(<ContatoFiltersPanel value={FILTROS_VAZIOS} onChange={onChange} />)

    const input = screen.getByLabelText(/^empresa$/i) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'A' } })

    // Antes do debounce expirar, onChange nao foi chamado para empresa.
    const chamadasComEmpresa = onChange.mock.calls.filter(
      (args) => (args[0] as ContatoFiltros).empresa === 'A'
    )
    expect(chamadasComEmpresa.length).toBe(0)
  })

  test('apos 300ms do ultimo input, onChange e disparado com o valor debounced', () => {
    const onChange = jest.fn()
    render(<ContatoFiltersPanel value={FILTROS_VAZIOS} onChange={onChange} />)

    const input = screen.getByLabelText(/^empresa$/i) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'Acme' } })

    act(() => {
      jest.advanceTimersByTime(300)
    })

    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ empresa: 'Acme' })
    )
  })
})
