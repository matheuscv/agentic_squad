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

// ---------------------------------------------------------------------------
// TASK-09 — Filtros avancados (D.4).
// Container opcional para os 5 filtros do RF-05. Todos os campos sao
// opcionais e ignorados quando ausentes / vazios.
// ---------------------------------------------------------------------------
export interface ContatosFilterParams {
  /** Busca parcial case-insensitive sobre o campo empresa. */
  empresa?: string
  /** Data inicial inclusiva no formato YYYY-MM-DD. */
  criado_desde?: string
  /** Data final inclusiva no formato YYYY-MM-DD. */
  criado_ate?: string
  /** Quando true, retorna apenas contatos com email vazio. */
  sem_email?: boolean
  /** Quando true, retorna apenas contatos com telefone vazio. */
  sem_telefone?: boolean
}

/**
 * Lista contatos com suporte a paginação, busca, ordenação e filtros avancados.
 * - `busca`: filtra por nome, e-mail ou empresa (LIKE case-insensitive no backend)
 * - `skip`: quantos registros pular (offset)
 * - `limit`: quantos registros retornar
 * - `sort_by`: campo de ordenação (nome, email, empresa, criado_em)
 * - `sort_order`: direção de ordenação (asc | desc)
 * - `filtros`: filtros avancados — empresa, criado_desde, criado_ate,
 *   sem_email, sem_telefone (TASK-05 / TASK-09, RF-06)
 * O backend retorna `{ items: [...], total: N }`.
 */
export async function listarContatos(
  busca?: string,
  skip?: number,
  limit?: number,
  sort_by?: string,
  sort_order?: 'asc' | 'desc',
  filtros?: ContatosFilterParams,
): Promise<ContatosPageResponse> {
  // Aceita tipos primitivos heterogeneos: o axios serializa cada valor
  // corretamente em sua representacao textual de query string.
  const params: Record<string, string | number | boolean> = {}
  if (busca && busca.trim() !== '') {
    params.busca = busca.trim()
  }
  // Inclui skip/limit apenas quando explicitamente fornecidos
  if (skip !== undefined) params.skip = skip
  if (limit !== undefined) params.limit = limit
  // Inclui ordenação apenas quando fornecida
  if (sort_by) params.sort_by = sort_by
  if (sort_order) params.sort_order = sort_order

  // -------------------------------------------------------------------------
  // TASK-09 — Filtros avancados.
  // Cada filtro so e adicionado a query quando preenchido. Strings vazias
  // sao tratadas como "nao informado" — o backend ja faz a mesma
  // normalizacao (ContatoFilterParams), mas evitamos enviar lixo na URL.
  // Booleans sao adicionados apenas quando `true` (filtro ativo).
  // -------------------------------------------------------------------------
  if (filtros) {
    if (filtros.empresa && filtros.empresa.trim() !== '') {
      params.empresa = filtros.empresa.trim()
    }
    if (filtros.criado_desde && filtros.criado_desde.trim() !== '') {
      params.criado_desde = filtros.criado_desde
    }
    if (filtros.criado_ate && filtros.criado_ate.trim() !== '') {
      params.criado_ate = filtros.criado_ate
    }
    if (filtros.sem_email) {
      params.sem_email = true
    }
    if (filtros.sem_telefone) {
      params.sem_telefone = true
    }
  }

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
