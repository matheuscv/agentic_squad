// Serviço de CRUD para a entidade Contato.
// Todas as chamadas usam a instância Axios centralizada (api.ts),
// que injeta o JWT automaticamente via interceptor de request.

import api from './api'
import { Contato, ContatoForm } from '../types/index'

/**
 * Lista contatos. Passa o parâmetro `busca` como query string quando fornecido.
 * O backend faz LIKE case-insensitive em nome, e-mail e empresa.
 */
export async function listarContatos(busca?: string): Promise<Contato[]> {
  const params: Record<string, string> = {}
  if (busca && busca.trim() !== '') {
    params.busca = busca.trim()
  }
  const response = await api.get<Contato[]>('/contatos/', { params })
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
