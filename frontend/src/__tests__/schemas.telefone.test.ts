/**
 * Testes do schema Zod do telefone — TASK-08 (Fase D / D.3 / RF-04).
 *
 * Arquivo testado: frontend/src/lib/schemas.ts
 *
 * Garante que o regex frontend (Zod) e o regex backend (Pydantic) estao
 * alinhados pelo MESMO contrato: ^\(\d{2}\) \d{5}-\d{4}$ (celular brasileiro
 * com mascara).
 *
 * Casos cobertos:
 *  - undefined  -> valido (opcional)
 *  - ''         -> valido (campo vazio aceito; consumidor normaliza para undefined)
 *  - '(11) 91234-5678'  -> valido
 *  - '123'      -> invalido
 *  - '(11) 1234-5678' (fixo 10 digitos) -> invalido
 *  - '11999999999' (digits-only) -> invalido
 */

import {
  telefoneSchema,
  TELEFONE_MENSAGEM_ERRO,
  TELEFONE_REGEX,
  contatoFormSchema,
} from '../lib/schemas'

describe('telefoneSchema (Zod) — TASK-08 / D.3', () => {
  test('aceita undefined (campo opcional)', () => {
    const r = telefoneSchema.safeParse(undefined)
    expect(r.success).toBe(true)
  })

  test("aceita string vazia ''", () => {
    const r = telefoneSchema.safeParse('')
    expect(r.success).toBe(true)
  })

  test('aceita telefone celular mascarado valido', () => {
    const r = telefoneSchema.safeParse('(11) 91234-5678')
    expect(r.success).toBe(true)
  })

  test('rejeita string curta como "123"', () => {
    const r = telefoneSchema.safeParse('123')
    expect(r.success).toBe(false)
    if (!r.success) {
      // A mensagem PT-BR documentada deve estar presente
      expect(r.error.issues[0].message).toBe(TELEFONE_MENSAGEM_ERRO)
    }
  })

  test('rejeita telefone fixo (XX) XXXX-XXXX (10 digitos)', () => {
    // Decisao TASK-04/TASK-08: contrato unico aceita apenas celular (11 digitos).
    const r = telefoneSchema.safeParse('(11) 1234-5678')
    expect(r.success).toBe(false)
  })

  test('rejeita digits-only sem mascara', () => {
    const r = telefoneSchema.safeParse('11999999999')
    expect(r.success).toBe(false)
  })

  test('rejeita string com letras', () => {
    const r = telefoneSchema.safeParse('(11) A1234-5678')
    expect(r.success).toBe(false)
  })

  test('TELEFONE_REGEX bate exatamente com o formato celular', () => {
    expect(TELEFONE_REGEX.test('(11) 91234-5678')).toBe(true)
    expect(TELEFONE_REGEX.test('11999999999')).toBe(false)
    expect(TELEFONE_REGEX.test('(11) 1234-5678')).toBe(false)
  })
})


describe('contatoFormSchema — TASK-08 / D.3', () => {
  test('aceita objeto valido sem telefone', () => {
    const r = contatoFormSchema.safeParse({
      nome: 'Joao',
      email: 'joao@x.com',
    })
    expect(r.success).toBe(true)
  })

  test('aceita objeto valido com telefone celular mascarado', () => {
    const r = contatoFormSchema.safeParse({
      nome: 'Joao',
      email: 'joao@x.com',
      telefone: '(11) 91234-5678',
    })
    expect(r.success).toBe(true)
  })

  test('rejeita objeto com telefone invalido', () => {
    const r = contatoFormSchema.safeParse({
      nome: 'Joao',
      email: 'joao@x.com',
      telefone: '123',
    })
    expect(r.success).toBe(false)
  })

  test('rejeita objeto sem nome (campo obrigatorio)', () => {
    const r = contatoFormSchema.safeParse({
      nome: '',
      email: 'joao@x.com',
    })
    expect(r.success).toBe(false)
  })

  test('rejeita objeto com email invalido', () => {
    const r = contatoFormSchema.safeParse({
      nome: 'Joao',
      email: 'nao-eh-email',
    })
    expect(r.success).toBe(false)
  })
})
