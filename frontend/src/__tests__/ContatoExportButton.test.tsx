/**
 * Testes do componente ContatoExportButton — TASK-10 (Fase D / D.5 / RF-07).
 *
 * Componente: frontend/src/components/ContatoExportButton.tsx
 *
 * Cobertura:
 *  - Render: botao "Exportar" com aria-label e dropdown fechado
 *  - Clique no botao abre o menu com itens CSV / Excel (XLSX)
 *  - Cada item chama exportarContatos com o formato correto + params
 *  - Estado loading: durante a chamada o botao mostra "Exportando ..." e
 *    fica desabilitado
 *  - Tecla Escape fecha o menu
 *  - Erro do helper aciona o callback onErro com mensagem amigavel
 *  - aria-label em itens (acessibilidade RNF-07)
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mocka o helper antes de importar o componente.
jest.mock('../services/api', () => ({
  __esModule: true,
  exportarContatos: jest.fn(),
}))

import ContatoExportButton from '../components/ContatoExportButton'
import * as apiModule from '../services/api'

const mockedExportar = apiModule.exportarContatos as jest.Mock


beforeEach(() => {
  jest.clearAllMocks()
  mockedExportar.mockResolvedValue(undefined)
})


describe('ContatoExportButton — render', () => {
  test('renderiza botao "Exportar" com aria-label', () => {
    render(<ContatoExportButton params={{}} />)
    const btn = screen.getByRole('button', { name: /exportar contatos/i })
    expect(btn).toBeInTheDocument()
    expect(btn).toHaveAttribute('aria-haspopup', 'menu')
    expect(btn).toHaveAttribute('aria-expanded', 'false')
  })

  test('menu (role="menu") nao esta no DOM no estado inicial', () => {
    render(<ContatoExportButton params={{}} />)
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })
})


describe('ContatoExportButton — abrir menu', () => {
  test('clicar no botao abre o menu com itens CSV e XLSX', async () => {
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))

    expect(screen.getByRole('menu')).toBeInTheDocument()
    // Cada item tem aria-label especifico
    expect(
      screen.getByRole('menuitem', { name: /exportar contatos em csv/i })
    ).toBeInTheDocument()
    expect(
      screen.getByRole('menuitem', { name: /exportar contatos em excel/i })
    ).toBeInTheDocument()
  })

  test('aria-expanded vira true quando menu abre', async () => {
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} />)
    const btn = screen.getByRole('button', { name: /exportar contatos/i })

    await user.click(btn)
    expect(btn).toHaveAttribute('aria-expanded', 'true')
  })
})


describe('ContatoExportButton — disparar export', () => {
  test('clique em "Exportar CSV" chama exportarContatos com formato=csv + params', async () => {
    const user = userEvent.setup()
    const params = { busca: 'teste', sort_by: 'nome', sort_order: 'asc' as const }
    render(<ContatoExportButton params={params} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    await user.click(screen.getByRole('menuitem', { name: /exportar contatos em csv/i }))

    expect(mockedExportar).toHaveBeenCalledTimes(1)
    expect(mockedExportar).toHaveBeenCalledWith('csv', params)
  })

  test('clique em "Exportar Excel" chama exportarContatos com formato=xlsx', async () => {
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    await user.click(screen.getByRole('menuitem', { name: /exportar contatos em excel/i }))

    expect(mockedExportar).toHaveBeenCalledTimes(1)
    expect(mockedExportar).toHaveBeenCalledWith('xlsx', {})
  })

  test('chamada bem-sucedida dispara onSucesso com o formato', async () => {
    const user = userEvent.setup()
    const onSucesso = jest.fn()
    render(<ContatoExportButton params={{}} onSucesso={onSucesso} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    await user.click(screen.getByRole('menuitem', { name: /csv/i }))

    await waitFor(() => {
      expect(onSucesso).toHaveBeenCalledWith('csv')
    })
  })
})


describe('ContatoExportButton — estado loading', () => {
  test('durante o download o botao fica desabilitado e mostra "Exportando CSV..."', async () => {
    // Faz a promise nao resolver imediatamente para conseguirmos observar o
    // estado intermediario de loading.
    let resolveFn: (v: unknown) => void = () => undefined
    mockedExportar.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFn = resolve
        })
    )
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    await user.click(screen.getByRole('menuitem', { name: /csv/i }))

    // Em loading: rotulo dinamico e disabled.
    const btn = screen.getByRole('button', { name: /exportar contatos/i })
    expect(btn).toBeDisabled()
    expect(btn.textContent).toMatch(/exportando csv/i)

    // Resolve para nao deixar timer pendente.
    resolveFn(undefined)
    await waitFor(() => {
      expect(btn).not.toBeDisabled()
    })
  })
})


describe('ContatoExportButton — erro', () => {
  test('erro no helper aciona onErro com mensagem amigavel', async () => {
    mockedExportar.mockRejectedValueOnce(new Error('boom'))
    const onErro = jest.fn()
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} onErro={onErro} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    await user.click(screen.getByRole('menuitem', { name: /csv/i }))

    await waitFor(() => {
      expect(onErro).toHaveBeenCalled()
    })
    // Mensagem generica — nao vaza detalhes do backend
    expect(onErro.mock.calls[0][0]).toMatch(/n[aã]o foi poss[ií]vel/i)
  })
})


describe('ContatoExportButton — fechar menu', () => {
  test('tecla Escape fecha o menu', async () => {
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    expect(screen.getByRole('menu')).toBeInTheDocument()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  })

  test('apos selecionar um item, o menu fecha', async () => {
    const user = userEvent.setup()
    render(<ContatoExportButton params={{}} />)

    await user.click(screen.getByRole('button', { name: /exportar contatos/i }))
    await user.click(screen.getByRole('menuitem', { name: /csv/i }))

    // Apos a acao, o menu deve sair do DOM.
    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })
})
