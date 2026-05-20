/**
 * Testes unitários para o CRUD de contatos — TASK-20 (FASE C / RF-07)
 *
 * Complementa contatos.service.test.ts cobrindo buscarContato, criarContato,
 * atualizarContato, excluirContato e os parâmetros sort_by/sort_order.
 */

jest.mock('../services/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

import {
  buscarContato,
  criarContato,
  atualizarContato,
  excluirContato,
  listarContatos,
} from '../services/contatos.service'
import api from '../services/api'

const mockGet = api.get as jest.Mock
const mockPost = api.post as jest.Mock
const mockPut = api.put as jest.Mock
const mockDelete = api.delete as jest.Mock


beforeEach(() => {
  jest.clearAllMocks()
})

const CONTATO_FAKE = {
  id: 1,
  nome: 'A',
  email: 'a@a.com',
  telefone: null,
  empresa: null,
  observacoes: null,
  criado_em: '2026-01-01T00:00:00Z',
  atualizado_em: '2026-01-01T00:00:00Z',
}


describe('buscarContato', () => {
  test('chama GET /contatos/:id', async () => {
    mockGet.mockResolvedValueOnce({ data: CONTATO_FAKE })
    const r = await buscarContato(1)
    expect(mockGet).toHaveBeenCalledWith('/contatos/1')
    expect(r.id).toBe(1)
  })

  test('propaga 404', async () => {
    mockGet.mockRejectedValueOnce(
      Object.assign(new Error('Not Found'), { response: { status: 404 } })
    )
    await expect(buscarContato(99)).rejects.toMatchObject({
      response: { status: 404 },
    })
  })
})


describe('criarContato', () => {
  test('chama POST /contatos/ com os dados', async () => {
    mockPost.mockResolvedValueOnce({ data: CONTATO_FAKE })
    const dados = { nome: 'A', email: 'a@a.com' }
    const r = await criarContato(dados)
    expect(mockPost).toHaveBeenCalledWith('/contatos/', dados)
    expect(r.id).toBe(1)
  })

  test('propaga erro do backend', async () => {
    mockPost.mockRejectedValueOnce(new Error('boom'))
    await expect(criarContato({ nome: 'A', email: 'a@a.com' })).rejects.toThrow('boom')
  })
})


describe('atualizarContato', () => {
  test('chama PUT /contatos/:id com os dados', async () => {
    mockPut.mockResolvedValueOnce({ data: CONTATO_FAKE })
    const dados = { nome: 'A', email: 'a@a.com' }
    await atualizarContato(1, dados)
    expect(mockPut).toHaveBeenCalledWith('/contatos/1', dados)
  })

  test('propaga 404', async () => {
    mockPut.mockRejectedValueOnce(
      Object.assign(new Error('Not Found'), { response: { status: 404 } })
    )
    await expect(
      atualizarContato(9, { nome: 'A', email: 'a@a.com' })
    ).rejects.toMatchObject({ response: { status: 404 } })
  })
})


describe('excluirContato', () => {
  test('chama DELETE /contatos/:id', async () => {
    mockDelete.mockResolvedValueOnce({})
    await excluirContato(5)
    expect(mockDelete).toHaveBeenCalledWith('/contatos/5')
  })

  test('propaga erro 403', async () => {
    mockDelete.mockRejectedValueOnce(
      Object.assign(new Error('Forbidden'), { response: { status: 403 } })
    )
    await expect(excluirContato(5)).rejects.toMatchObject({
      response: { status: 403 },
    })
  })
})


describe('listarContatos — sort_by / sort_order', () => {
  test('inclui sort_by quando fornecido', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await listarContatos(undefined, 0, 20, 'email')
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params.sort_by).toBe('email')
  })

  test('inclui sort_order quando fornecido', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await listarContatos(undefined, 0, 20, 'nome', 'desc')
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params.sort_order).toBe('desc')
  })

  test('omite sort_by/sort_order quando undefined', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [], total: 0 } })
    await listarContatos(undefined, 0, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).not.toHaveProperty('sort_by')
    expect(chamada.params).not.toHaveProperty('sort_order')
  })
})
