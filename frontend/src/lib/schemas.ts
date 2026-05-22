/**
 * Schemas Zod do projeto.
 *
 * Centraliza as regras de validação compartilhadas entre os formulários
 * (front) e o contrato definido no backend. Para a TASK-08 (FASE D.3), o
 * foco é o campo `telefone` do contato:
 *
 *  - Opcional. Aceita ausência (`undefined`) ou string vazia.
 *  - Quando preenchido, deve casar exatamente com `^\(\d{2}\) \d{5}-\d{4}$`,
 *    o mesmo regex aplicado no schema Pydantic do backend (TASK-04).
 *  - Antes do POST, o consumidor deve normalizar string vazia para
 *    `undefined`/`null` para manter coerência com o backend, que rejeita
 *    qualquer string não-vazia que não case com o regex.
 *
 * Notas de paralelismo / decisões conservadoras (TASK-08):
 *  - O projeto ainda não migrou para `react-hook-form` + Zod (ver dívida
 *    técnica em `MEMORY.md`). Este arquivo é o primeiro schema Zod e
 *    serve como ponto único de verdade para o regex do telefone. A
 *    validação imperativa em `useContatoFormValidation.ts` permanece
 *    intacta para não conflitar com a TASK-07/09/10 em paralelo, mas
 *    futuras tasks devem consumir `contatoFormSchema` daqui.
 *  - Mensagens de erro em PT-BR, como exige o PRD (RNF-10).
 */

import { z } from 'zod'

/**
 * Regex oficial do telefone — celular brasileiro com DDD entre parênteses,
 * espaço, 5 dígitos, hífen e 4 dígitos. Idêntico ao contrato do backend
 * definido na TASK-04 (Pydantic). Não aceita telefone fixo (10 dígitos):
 * a normalização para celular é intencional para evitar ambiguidade entre
 * front e back, conforme alinhamento da TASK-04.
 */
export const TELEFONE_REGEX = /^\(\d{2}\) \d{5}-\d{4}$/

/**
 * Mensagem PT-BR exibida quando o telefone preenchido não casa com o regex.
 * Mantida em constante exportável para reuso em testes e componentes.
 */
export const TELEFONE_MENSAGEM_ERRO =
  'Telefone deve estar no formato (XX) XXXXX-XXXX.'

/**
 * Schema do campo `telefone` isolado — útil para validar apenas o telefone
 * (ex.: `onBlur` do input) sem montar o schema inteiro do formulário.
 *
 * Regras:
 *  - `undefined` -> válido (campo opcional).
 *  - `''` (string vazia) -> válido; o consumidor deve normalizar para
 *    `undefined` antes de enviar ao backend.
 *  - Qualquer outra string -> deve casar com `TELEFONE_REGEX`.
 */
export const telefoneSchema = z
  .string()
  .optional()
  .refine(
    (valor) => valor === undefined || valor === '' || TELEFONE_REGEX.test(valor),
    { message: TELEFONE_MENSAGEM_ERRO }
  )

/**
 * Schema completo do formulário de contato (mesmo contrato de
 * `ContatoForm` em `src/types/index.ts`).
 *
 *  - `nome` e `email` são obrigatórios.
 *  - `telefone`, `empresa` e `observacoes` são opcionais.
 *  - O e-mail é validado pelo helper nativo do Zod (RFC 5322 simplificado).
 */
export const contatoFormSchema = z.object({
  nome: z
    .string()
    .min(1, { message: 'Nome Completo é obrigatório.' })
    .trim(),
  email: z
    .string()
    .min(1, { message: 'E-mail é obrigatório.' })
    .email({ message: 'Informe um e-mail válido.' }),
  telefone: telefoneSchema,
  empresa: z.string().optional(),
  observacoes: z.string().optional(),
})

/**
 * Tipo inferido a partir do schema — pode ser usado pelos consumidores
 * (ex.: `react-hook-form` na migração futura) para garantir paridade
 * entre validação e tipagem.
 */
export type ContatoFormSchema = z.infer<typeof contatoFormSchema>
