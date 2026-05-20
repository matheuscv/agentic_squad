/**
 * Testes unitários para auth.service.ts — TASK-20 (FASE C / RF-07)
 */

jest.mock('../services/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}))

import { login, cadastrar, getMe } from '../services/auth.service'
import api from '../services/api'

const mockPost = api.post as jest.Mock
const mockGet = api.get as jest.Mock


beforeEach(() => {
  jest.clearAllMocks()
})


describe('auth.service.login', () => {
  test('chama POST /auth/login com email e senha', async () => {
    mockPost.mockResolvedValueOnce({ data: { access_token: 'tok', token_type: 'bearer' } })
    const resultado = await login('a@a.com', 'segredo')
    expect(mockPost).toHaveBeenCalledWith('/auth/login', { email: 'a@a.com', senha: 'segredo' })
    expect(resultado.access_token).toBe('tok')
  })

  test('propaga erros da API', async () => {
    mockPost.mockRejectedValueOnce(new Error('401'))
    await expect(login('a@a.com', 'errada')).rejects.toThrow('401')
  })
})


describe('auth.service.cadastrar', () => {
  test('chama POST /usuarios/ com nome, email e senha', async () => {
    mockPost.mockResolvedValueOnce({
      data: { id: 1, nome: 'A', email: 'a@a.com', role: 'default' },
    })
    const resultado = await cadastrar('A', 'a@a.com', 'segredo')
    expect(mockPost).toHaveBeenCalledWith('/usuarios/', {
      nome: 'A',
      email: 'a@a.com',
      senha: 'segredo',
    })
    expect(resultado.id).toBe(1)
  })

  test('propaga erro 400 (e-mail duplicado)', async () => {
    const err = Object.assign(new Error('Bad Request'), { response: { status: 400 } })
    mockPost.mockRejectedValueOnce(err)
    await expect(cadastrar('A', 'a@a.com', 'p')).rejects.toMatchObject({
      response: { status: 400 },
    })
  })
})


describe('auth.service.getMe', () => {
  test('chama GET /auth/me e retorna o usuário', async () => {
    mockGet.mockResolvedValueOnce({
      data: { id: 1, nome: 'A', email: 'a@a.com', role: 'adm' },
    })
    const resultado = await getMe()
    expect(mockGet).toHaveBeenCalledWith('/auth/me')
    expect(resultado.role).toBe('adm')
  })

  test('propaga erro 401', async () => {
    const err = Object.assign(new Error('Unauthorized'), { response: { status: 401 } })
    mockGet.mockRejectedValueOnce(err)
    await expect(getMe()).rejects.toMatchObject({ response: { status: 401 } })
  })
})
