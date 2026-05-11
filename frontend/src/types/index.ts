export interface Usuario {
  id: number
  nome: string
  email: string
  role: 'default' | 'adm'
}

export interface Contato {
  id: number
  nome: string
  email: string
  telefone?: string
  empresa?: string
  observacoes?: string
  criado_em: string
  atualizado_em: string
}

export interface ContatoForm {
  nome: string
  email: string
  telefone?: string
  empresa?: string
  observacoes?: string
}

export interface LoginForm {
  email: string
  senha: string
}

export interface CadastroForm {
  nome: string
  email: string
  senha: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface AuthContextType {
  usuario: Usuario | null
  token: string | null
  login: (token: string, usuario: Usuario) => void
  logout: () => void
  isAdm: boolean
}
