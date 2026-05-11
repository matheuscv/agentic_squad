// auth.service.ts — funções de autenticação que consomem a API backend.
// Este módulo é client-side: depende da instância axios que usa localStorage.

import api from './api'
import { TokenResponse, Usuario } from '../types/index'

/**
 * Realiza login e retorna o token JWT.
 * Endpoint: POST /auth/login
 */
export async function login(email: string, senha: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/login', { email, senha })
  return response.data
}

/**
 * Cadastra um novo usuário.
 * Endpoint: POST /usuarios/
 * Retorna o usuário criado (sem token — o fluxo exige login separado).
 */
export async function cadastrar(
  nome: string,
  email: string,
  senha: string
): Promise<Usuario> {
  // O backend retorna o objeto do usuário criado (sem token)
  const response = await api.post<Usuario>('/usuarios/', { nome, email, senha })
  return response.data
}

/**
 * Busca os dados do usuário autenticado a partir do token já configurado
 * no interceptor da instância axios.
 * Endpoint: GET /auth/me
 */
export async function getMe(): Promise<Usuario> {
  const response = await api.get<Usuario>('/auth/me')
  return response.data
}
