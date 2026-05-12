// Serviço de CRUD para a entidade Contato.
// Todas as chamadas usam a instância Axios centralizada (api.ts),
// que injeta o JWT automaticamente via interceptor de request.

import api from './api'
import { Contato, ContatoForm } from '../types/index'

// Formato da resposta paginada retornada pelo backend (TASK-01)
export interface ContatosPageResponse {
  items: Contato[]
  total: number
}

/**
 * Lista contatos com suporte a paginação, busca e ordenação.
 * - `busca`: filtra por nome, e-mail ou empresa (LIKE case-insensitive no backend)
 * - `skip`: quantos registros pular (offset)
 * - `limit`: quantos registros retornar
 * - `sort_by`: campo de ordenação (nome, email, empresa, criado_em)
 * - `sort_order`: direção de ordenação (asc | desc)
 * O backend retorna `{ items: [...], total: N }`.
 */
export async function listarContatos(
  busca?: string,
  skip?: number,
  limit?: number,
  sort_by?: string,
  sort_order?: 'asc' | 'desc'
): Promise<ContatosPageResponse> {
  const params: Record<string, string | number> = {}
  if (busca && busca.trim() !== '') {
    params.busca = busca.trim()
  }
  // Inclui skip/limit apenas quando explicitamente fornecidos
  if (skip !== undefined) params.skip = skip
  if (limit !== undefined) params.limit = limit
  // Inclui ordenação apenas quando fornecida
  if (sort_by) params.sort_by = sort_by
  if (sort_order) params.sort_order = sort_order

  const response = await api.get<ContatosPageResponse>('/contatos/', { params })
  return response.data
}

/**
 * Busca um único contato pelo ID.
 * Lança AxiosError com status 404 se não encontrado.
 */
export async function buscarContato(id: number): Promise<Contato> {
  const response = await api.get<Contato>(`/contatos/${id}`)
  return response.data
}

/**
 * Cria um novo contato (requer perfil adm no backend).
 */
export async function criarContato(dados: ContatoForm): Promise<Contato> {
  const response = await api.post<Contato>('/contatos/', dados)
  return response.data
}

/**
 * Atualiza todos os campos de um contato existente (PUT — substitui o recurso).
 * Requer perfil adm no backend.
 */
export async function atualizarContato(
  id: number,
  dados: ContatoForm
): Promise<Contato> {
  const response = await api.put<Contato>(`/contatos/${id}`, dados)
  return response.data
}

/**
 * Remove um contato pelo ID.
 * Requer perfil adm no backend. Retorna void (204 No Content).
 */
export async function excluirContato(id: number): Promise<void> {
  await api.delete(`/contatos/${id}`)
}
