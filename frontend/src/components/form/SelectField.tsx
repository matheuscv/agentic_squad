'use client'

import { ChangeEvent } from 'react'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectFieldProps {
  /** Texto do `<label>`. */
  label: string
  /** Atributos `id`/`name` — devem coincidir com a chave do estado. */
  name: string
  /** Valor selecionado (controlado). */
  value: string
  /** Handler de `change` do `<select>`. */
  onChange: (e: ChangeEvent<HTMLSelectElement>) => void
  /** Lista de opções para renderizar. */
  options: SelectOption[]
  /** Marca como obrigatório (asterisco no label). */
  required?: boolean
  /** Placeholder opcional — renderizado como `<option value="">`. */
  placeholder?: string
  /** Mensagem de erro — exibida abaixo do campo se presente. */
  error?: string
  /** Desabilita o select. */
  disabled?: boolean
}

const SELECT_BASE_CLASSES =
  'w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none ' +
  'focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed'

/**
 * Componente de select genérico para formulários.
 *
 * Mantém o mesmo padrão visual (`<label>` + control + erro) do `InputField`,
 * permitindo composição uniforme em qualquer formulário do projeto.
 *
 * @example
 *   <SelectField
 *     label="Categoria"
 *     name="categoria"
 *     value={form.categoria}
 *     onChange={handleChange}
 *     options={[
 *       { value: 'cliente', label: 'Cliente' },
 *       { value: 'fornecedor', label: 'Fornecedor' },
 *     ]}
 *     placeholder="Selecione..."
 *     required
 *   />
 */
export default function SelectField({
  label,
  name,
  value,
  onChange,
  options,
  required = false,
  placeholder,
  error,
  disabled = false,
}: SelectFieldProps) {
  return (
    <div>
      <label
        htmlFor={name}
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>

      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={SELECT_BASE_CLASSES}
      >
        {placeholder && (
          // Opção placeholder com valor vazio — útil para forçar seleção
          // explícita em campos obrigatórios.
          <option value="">{placeholder}</option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
