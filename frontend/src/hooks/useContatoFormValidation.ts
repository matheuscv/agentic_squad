import { useMemo } from 'react'
import { ContatoForm as ContatoFormType } from '../types'

/**
 * Estrutura plana usada pelo formulário — todos os campos são strings
 * (mesmo os opcionais), evitando `undefined` nos inputs controlados.
 */
export interface CamposContatoForm {
  nome: string
  email: string
  telefone: string
  empresa: string
  observacoes: string
}

export type ErrosContatoForm = Partial<Record<keyof CamposContatoForm, string>>

export interface UseContatoFormValidationResult {
  /** Erros por campo — só presentes para campos inválidos. */
  errors: ErrosContatoForm
  /** `true` quando nenhum campo apresenta erro. */
  isValid: boolean
  /** Função pura de validação reutilizável (ex.: chamar no submit). */
  validate: (valores: CamposContatoForm) => ErrosContatoForm
}

// Regex de e-mail simples (mesma adotada anteriormente em ContatoForm).
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Regex de telefone — aceita celular (11 dígitos) ou fixo (10 dígitos).
const TELEFONE_CELULAR_REGEX = /^\(\d{2}\) \d{5}-\d{4}$/
const TELEFONE_FIXO_REGEX = /^\(\d{2}\) \d{4}-\d{4}$/

/**
 * Valida um campo de telefone segundo as regras do PRD (RN-F2-03):
 *  - Campo opcional: se vazio, válido.
 *  - Se preenchido, deve casar com celular ou fixo.
 *
 * @example
 *   validarTelefone('') // => ''
 *   validarTelefone('(11) 99999-9999') // => ''
 *   validarTelefone('11999999999') // => 'Formato inválido...'
 */
export function validarTelefone(valor: string): string {
  const soDigitos = valor.replace(/\D/g, '')
  if (soDigitos.length === 0) return ''
  if (!TELEFONE_CELULAR_REGEX.test(valor) && !TELEFONE_FIXO_REGEX.test(valor)) {
    return 'Formato inválido. Use (99) 99999-9999 ou (99) 9999-9999.'
  }
  return ''
}

/**
 * Função pura que valida todos os campos e devolve um mapa de erros.
 * Exportada para permitir validação imperativa no `handleSubmit`.
 */
export function validarCampos(valores: CamposContatoForm): ErrosContatoForm {
  const erros: ErrosContatoForm = {}

  if (!valores.nome.trim()) {
    erros.nome = 'Nome Completo é obrigatório.'
  }

  if (!valores.email.trim()) {
    erros.email = 'E-mail é obrigatório.'
  } else if (!EMAIL_REGEX.test(valores.email)) {
    erros.email = 'Informe um e-mail válido.'
  }

  const erroTel = validarTelefone(valores.telefone)
  if (erroTel) {
    erros.telefone = erroTel
  }

  return erros
}

/**
 * Hook de validação reativa para o formulário de contato.
 *
 * Encapsula toda a lógica de validação (e-mail, telefone, obrigatórios)
 * antes vivia inline em `ContatoForm.tsx`. O hook **não** gerencia estado
 * dos campos — o componente continua dono do estado, o que permite manter
 * a integração existente com `useBeforeUnload` (que precisa de `isDirty`
 * derivado do snapshot original vs. atual).
 *
 * @example
 *   const { errors, isValid, validate } = useContatoFormValidation(campos)
 *   // No submit:
 *   const erros = validate(campos)
 *   if (Object.keys(erros).length > 0) { setErrosCampo(erros); return }
 *
 * @param valores  Valores atuais do formulário.
 * @returns        Objeto com `errors`, `isValid` e função pura `validate`.
 */
export function useContatoFormValidation(
  valores: CamposContatoForm
): UseContatoFormValidationResult {
  // Recalcula apenas quando algum valor muda — evita trabalho redundante.
  const errors = useMemo(() => validarCampos(valores), [valores])

  const isValid = useMemo(
    () => Object.keys(errors).length === 0,
    [errors]
  )

  return { errors, isValid, validate: validarCampos }
}

/**
 * Converte os campos planos do formulário (strings) para o tipo de domínio
 * `ContatoForm`, transformando strings vazias em `undefined` para campos
 * opcionais. Conservadoramente mantém o mesmo comportamento da função
 * homônima antes existente em `ContatoForm.tsx`.
 */
export function camposParaContatoForm(
  campos: CamposContatoForm
): ContatoFormType {
  return {
    nome: campos.nome,
    email: campos.email,
    telefone: campos.telefone || undefined,
    empresa: campos.empresa || undefined,
    observacoes: campos.observacoes || undefined,
  }
}

/**
 * Converte um `ContatoForm` (potencialmente com `undefined`) para os campos
 * planos do formulário, garantindo strings em todos os inputs.
 */
export function contatoFormParaCampos(
  valorInicial?: ContatoFormType
): CamposContatoForm {
  if (!valorInicial) {
    return { nome: '', email: '', telefone: '', empresa: '', observacoes: '' }
  }
  return {
    nome: valorInicial.nome ?? '',
    email: valorInicial.email ?? '',
    telefone: valorInicial.telefone ?? '',
    empresa: valorInicial.empresa ?? '',
    observacoes: valorInicial.observacoes ?? '',
  }
}

/**
 * Compara dois conjuntos de campos para detectar alterações.
 * Usado para alimentar o flag `isDirty` consumido por `useBeforeUnload`.
 */
export function camposDiferem(
  a: CamposContatoForm,
  b: CamposContatoForm
): boolean {
  return (
    a.nome !== b.nome ||
    a.email !== b.email ||
    a.telefone !== b.telefone ||
    a.empresa !== b.empresa ||
    a.observacoes !== b.observacoes
  )
}
