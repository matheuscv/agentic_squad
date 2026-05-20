'use client'

import { ChangeEvent } from 'react'

export interface TextAreaFieldProps {
  /** Texto do `<label>`. */
  label: string
  /** Atributos `id`/`name` do textarea. */
  name: string
  /** Valor controlado. */
  value: string
  /** Handler de `change`. */
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void
  /** Marca como obrigatório (asterisco no label). */
  required?: boolean
  /** Placeholder. */
  placeholder?: string
  /** Mensagem de erro — exibida abaixo do campo. */
  error?: string
  /** Desabilita o textarea. */
  disabled?: boolean
  /** Número de linhas visíveis. Default: 4 (conforme plano). */
  rows?: number
}

const TEXTAREA_BASE_CLASSES =
  'w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none ' +
  'focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed ' +
  'resize-none'

/**
 * Componente de textarea genérico para formulários.
 *
 * Mantém o padrão visual `<label>` + control + erro dos demais componentes
 * `*Field`. `resize-none` evita que o usuário arraste o textarea para fora
 * do layout, preservando consistência com o design original.
 *
 * @example
 *   <TextAreaField
 *     label="Observações"
 *     name="observacoes"
 *     value={campos.observacoes}
 *     onChange={handleChange}
 *     rows={3}
 *     placeholder="Informações adicionais..."
 *   />
 */
export default function TextAreaField({
  label,
  name,
  value,
  onChange,
  required = false,
  placeholder,
  error,
  disabled = false,
  rows = 4,
}: TextAreaFieldProps) {
  return (
    <div>
      <label
        htmlFor={name}
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>

      <textarea
        id={name}
        name={name}
        rows={rows}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={placeholder}
        className={TEXTAREA_BASE_CLASSES}
      />

      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
