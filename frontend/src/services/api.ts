'use client'

// Acessa localStorage — deve rodar apenas no cliente (browser).
// 'use client' garante que este módulo não seja executado no servidor.

import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// TASK-10 — Export CSV/XLSX (D.5)
//
// Tipos e helpers usados pelo componente `ContatoExportButton` para acionar
// o download do endpoint `GET /contatos/export` da TASK-06.
//
// O backend aceita o parametro PT-BR `formato` (e nao `format`) com os
// valores `csv` ou `xlsx`. Os mesmos filtros + ordenacao + busca da
// listagem sao aceitos como querystring.
//
// O download e disparado via axios com `responseType: 'blob'` para evitar
// que o axios tente parsear o conteudo como JSON. O JWT e injetado pelo
// interceptor padrao acima.
// ---------------------------------------------------------------------------

export type FormatoExportacao = 'csv' | 'xlsx'

/**
 * Parametros aceitos pelo endpoint de exportacao. Todos opcionais — os que
 * estiverem `undefined` simplesmente nao vao para a querystring (axios omite
 * automaticamente). A combinacao deve espelhar os filtros aplicados na
 * listagem para que o arquivo exportado corresponda ao que o usuario ve.
 */
export interface ExportarContatosParams {
  busca?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  empresa?: string
  criado_desde?: string
  criado_ate?: string
  sem_email?: boolean
  sem_telefone?: boolean
}

/**
 * Tenta extrair o `filename` do header `Content-Disposition`. Cobre as
 * duas formas mais comuns:
 *   - `attachment; filename="contatos.csv"`
 *   - `attachment; filename*=UTF-8''contatos.csv`
 *
 * Retorna `null` quando nao for possivel determinar — o chamador devera
 * gerar um nome padrao nesse caso.
 */
function parseFilenameFromContentDisposition(
  header: string | undefined | null,
): string | null {
  if (!header) return null
  // RFC 5987 (filename*=UTF-8''<urlencoded>) tem prioridade quando presente.
  const matchExt = /filename\*\s*=\s*(?:UTF-8'')?([^;\s]+)/i.exec(header)
  if (matchExt && matchExt[1]) {
    try {
      return decodeURIComponent(matchExt[1].replace(/^"|"$/g, ''))
    } catch {
      // Fallback silencioso para o filename "simples" abaixo.
    }
  }
  // filename="..." (com aspas) ou filename=... (sem aspas).
  const match = /filename\s*=\s*("([^"]+)"|([^;\s]+))/i.exec(header)
  if (match) {
    return (match[2] || match[3] || '').trim() || null
  }
  return null
}

/**
 * Constroi um nome padrao caso o servidor nao envie `Content-Disposition`
 * com filename utilizavel. Usa data ISO curta para evitar colisao no disco.
 */
function defaultExportFilename(formato: FormatoExportacao): string {
  const today = new Date().toISOString().slice(0, 10) // YYYY-MM-DD
  return `contatos_${today}.${formato}`
}

/**
 * Dispara o download de `/contatos/export` no formato indicado, repassando
 * os mesmos filtros / ordenacao / busca da listagem. Cria um Blob a partir
 * da resposta e simula o clique em um anchor temporario para acionar o
 * download no navegador. O JWT vai automaticamente pelo interceptor.
 *
 * @throws Repassa qualquer erro do axios — cabe ao chamador exibir feedback.
 */
export async function exportarContatos(
  formato: FormatoExportacao,
  params: ExportarContatosParams = {},
): Promise<void> {
  // Monta apenas chaves preenchidas para manter a URL limpa.
  // Atencao: o backend espera `formato` (PT-BR), nao `format`.
  const queryParams: Record<string, string | number | boolean> = {
    formato,
  }
  if (params.busca && params.busca.trim() !== '') {
    queryParams.busca = params.busca.trim()
  }
  if (params.sort_by) queryParams.sort_by = params.sort_by
  if (params.sort_order) queryParams.sort_order = params.sort_order
  if (params.empresa && params.empresa.trim() !== '') {
    queryParams.empresa = params.empresa.trim()
  }
  if (params.criado_desde) queryParams.criado_desde = params.criado_desde
  if (params.criado_ate) queryParams.criado_ate = params.criado_ate
  if (params.sem_email) queryParams.sem_email = true
  if (params.sem_telefone) queryParams.sem_telefone = true

  // `responseType: 'blob'` impede o axios de tentar parsear como JSON.
  const response = await api.get('/contatos/export', {
    params: queryParams,
    responseType: 'blob',
  })

  // Determina o nome do arquivo: preferimos o que o servidor sugere via
  // Content-Disposition (alinhado a TASK-06); cai para um nome padrao
  // somente se o header estiver ausente / mal formatado.
  const contentDisposition =
    (response.headers?.['content-disposition'] as string | undefined) ??
    (response.headers?.['Content-Disposition'] as string | undefined)
  const filename =
    parseFilenameFromContentDisposition(contentDisposition) ??
    defaultExportFilename(formato)

  // Cria URL temporaria a partir do blob e simula clique em <a download>.
  // `URL.revokeObjectURL` libera a memoria assim que o download e disparado.
  const blob = response.data as Blob
  const objectUrl = URL.createObjectURL(blob)
  try {
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = filename
    // Necessario em alguns navegadores: anexar ao DOM antes de clicar.
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
  } finally {
    URL.revokeObjectURL(objectUrl)
  }
}

// Interceptor de request: injeta o token JWT no header Authorization
api.interceptors.request.use(
  (config) => {
    // Lê o token armazenado no localStorage após o login
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor de response: ao receber 401, encerra a sessão e redireciona
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Limpa todos os dados de autenticação do localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      // Redireciona para login via window.location (client-side)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
