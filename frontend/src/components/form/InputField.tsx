'use client'

import { ChangeEvent, FocusEvent, ReactNode } from 'react'
import InputMask from 'react-input-mask'

/**
 * Tipos suportados pelo `InputField`. Cobre os tipos utilizados nos
 * formulários do projeto (contato, login, cadastro).
 */
export type InputFieldType = 'text' | 'email' | 'tel' | 'password'

export interface InputFieldProps {
  /** Texto do `<label>`. */
  label: string
  /** Atributos `id`/`name` do input — devem coincidir com a chave no estado. */
  name: string
  /** Valor controlado. */
  value: string
  /** Handler de `change`. */
  onChange: (e: ChangeEvent<HTMLInputElement>) => void
  /** Handler opcional de `blur` (ex.: validar formato no foco perdido). */
  onBlur?: (e: FocusEvent<HTMLInputElement>) => void
  /** Marca como obrigatório (asterisco vermelho no label). */
  required?: boolean
  /** Tipo HTML do input. */
  type?: InputFieldType
  /** Placeholder de exemplo. */
  placeholder?: string
  /** Mensagem de erro — se preenchida, exibe abaixo do campo em vermelho. */
  error?: string
  /** Desabilita o input (loading/submit em andamento). */
  disabled?: boolean
  /**
   * Máscara opcional (formato `react-input-mask`). Quando presente, o input
   * é renderizado dentro de `<InputMask>`. Útil para telefone.
   */
  mask?: string
}

// Classes Tailwind extraídas do padrão atual do ContatoForm — mantém visual
// idêntico ao código pré-refatoração.
const INPUT_BASE_CLASSES =
  'w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none ' +
  'focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed'

/**
 * Componente de input genérico para formulários.
 *
 * Renderiza `<label>` + `<input>` (ou `<InputMask>` se `mask` for fornecida)
 * + mensagem de erro condicional. Mantém os mesmos estilos visuais do
 * formulário de contato original.
 *
 * @example
 *   <InputField
 *     label="E-mail"
 *     name="email"
 *     type="email"
 *     value={campos.email}
 *     onChange={handleChange}
 *     required
 *     error={errosCampo.email}
 *   />
 *
 * @example  // Com máscara (telefone)
 *   <InputField
 *     label="Telefone"
 *     name="telefone"
 *     type="tel"
 *     mask="(99) 99999-9999"
 *     value={campos.telefone}
 *     onChange={handleChange}
 *     onBlur={validarTel}
 *     error={telefoneErro}
 *   />
 */
export default function InputField({
  label,
  name,
  value,
  onChange,
  onBlur,
  required = false,
  type = 'text',
  placeholder,
  error,
  disabled = false,
  mask,
}: InputFieldProps) {
  // Renderiza o <input> base. Quando há máscara, `extraProps` traz os
  // handlers internos do `react-input-mask` (não devemos sobrescrevê-los);
  // por isso `value`/`onChange`/`onBlur` ficam no wrapper `<InputMask>`,
  // e o input filho herda os handlers via `inputProps`.
  const renderInput = (
    extraProps: Partial<React.InputHTMLAttributes<HTMLInputElement>> = {}
  ): ReactNode => (
    <input
      id={name}
      name={name}
      type={type}
      disabled={disabled}
      placeholder={placeholder}
      className={INPUT_BASE_CLASSES}
      // No caso sem máscara, aplicamos value/onChange/onBlur direto no input.
      // No caso com máscara, esses são sobrescritos pelos `extraProps`.
      value={value}
      onChange={onChange}
      onBlur={onBlur}
      {...extraProps}
    />
  )

  return (
    <div>
      <label
        htmlFor={name}
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>

      {mask ? (
        <InputMask
          mask={mask}
          maskChar={null}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
        >
          {(inputProps: React.InputHTMLAttributes<HTMLInputElement>) =>
            renderInput(inputProps)
          }
        </InputMask>
      ) : (
        renderInput()
      )}

      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
