/**
 * Testes unitários para contatos.service.ts
 *
 * Arquivo: frontend/src/services/contatos.service.ts
 * Foco: listarContatos passa skip/limit corretamente na query string
 *
 * DEPENDÊNCIAS NECESSÁRIAS (ver TESTES.md):
 *   jest, ts-jest
 *
 * Mock: ./api (instância Axios centralizada)
 */

import { listarContatos, ContatosPageResponse } from '../services/contatos.service'

// Mock completo do módulo api (axios instance)
jest.mock('../services/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}))

import api from '../services/api'
const mockGet = api.get as jest.Mock


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockResponse(data: ContatosPageResponse) {
  mockGet.mockResolvedValueOnce({ data })
}

const EMPTY_RESPONSE: ContatosPageResponse = { items: [], total: 0 }


// ---------------------------------------------------------------------------
// Caminho feliz — retorno de dados
// ---------------------------------------------------------------------------

describe('listarContatos — resposta e estrutura', () => {
  beforeEach(() => jest.clearAllMocks())

  test('retorna objeto com items e total da resposta da API', async () => {
    const resposta: ContatosPageResponse = {
      items: [
        {
          id: 1,
          nome: 'Fulano',
          email: 'fulano@test.com',
          telefone: null,
          empresa: null,
          observacoes: null,
          criado_em: '2026-01-01T00:00:00Z',
          atualizado_em: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    }
    mockResponse(resposta)
    const resultado = await listarContatos()
    expect(resultado.items).toHaveLength(1)
    expect(resultado.total).toBe(1)
  })

  test('retorna objeto com items=[] e total=0 para banco vazio', async () => {
    mockResponse(EMPTY_RESPONSE)
    const resultado = await listarContatos()
    expect(resultado.items).toEqual([])
    expect(resultado.total).toBe(0)
  })
})


// ---------------------------------------------------------------------------
// Parâmetros de query — skip/limit
// ---------------------------------------------------------------------------

describe('listarContatos — query string skip/limit', () => {
  beforeEach(() => jest.clearAllMocks())

  test('inclui skip e limit nos params quando fornecidos', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos(undefined, 20, 20)
    expect(mockGet).toHaveBeenCalledWith(
      '/contatos/',
      expect.objectContaining({
        params: expect.objectContaining({ skip: 20, limit: 20 }),
      })
    )
  })

  test('NÃO inclui skip quando undefined', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos(undefined, undefined, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).not.toHaveProperty('skip')
  })

  test('NÃO inclui limit quando undefined', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos(undefined, 0, undefined)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).not.toHaveProperty('limit')
  })

  test('skip=0 é incluído (zero explícito não é ignorado)', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos(undefined, 0, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).toHaveProperty('skip', 0)
  })

  test('sem nenhum argumento não envia skip nem limit', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos()
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).not.toHaveProperty('skip')
    expect(chamada.params).not.toHaveProperty('limit')
  })

  test('segunda página: skip=20&limit=20 passados corretamente', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos(undefined, 20, 20)
    expect(mockGet).toHaveBeenCalledWith('/contatos/', {
      params: { skip: 20, limit: 20 },
    })
  })
})


// ---------------------------------------------------------------------------
// Parâmetro busca
// ---------------------------------------------------------------------------

describe('listarContatos — parâmetro busca', () => {
  beforeEach(() => jest.clearAllMocks())

  test('inclui busca nos params quando fornecida', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos('João', 0, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).toHaveProperty('busca', 'João')
  })

  test('NÃO inclui busca quando string vazia', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos('', 0, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).not.toHaveProperty('busca')
  })

  test('NÃO inclui busca quando apenas espaços', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos('   ', 0, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params).not.toHaveProperty('busca')
  })

  test('trimeia a busca antes de enviar', async () => {
    mockResponse(EMPTY_RESPONSE)
    await listarContatos('  João  ', 0, 20)
    const chamada = mockGet.mock.calls[0][1]
    expect(chamada.params.busca).toBe('João')
  })
})


// ---------------------------------------------------------------------------
// Tratamento de erros
// ---------------------------------------------------------------------------

describe('listarContatos — erros de rede', () => {
  beforeEach(() => jest.clearAllMocks())

  test('propaga erro quando API falha', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network Error'))
    await expect(listarContatos()).rejects.toThrow('Network Error')
  })

  test('propaga erro 401 da API', async () => {
    const err = Object.assign(new Error('Unauthorized'), { response: { status: 401 } })
    mockGet.mockRejectedValueOnce(err)
    await expect(listarContatos()).rejects.toMatchObject({
      response: { status: 401 },
    })
  })
})
