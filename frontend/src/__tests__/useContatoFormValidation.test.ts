/**
 * Testes unitários para o hook useContatoFormValidation — TASK-20 (FASE C / RF-07)
 *
 * Hook: frontend/src/hooks/useContatoFormValidation.ts
 * Cobre:
 *   - Função pura validarTelefone (vazio, celular, fixo, formatos inválidos)
 *   - Função pura validarCampos (obrigatórios + formato de e-mail + telefone)
 *   - Hook useContatoFormValidation (reatividade via useMemo)
 *   - Conversores camposParaContatoForm e contatoFormParaCampos
 *   - Função camposDiferem (dirty flag)
 */

import { renderHook } from '@testing-library/react'
import {
  validarTelefone,
  validarCampos,
  useContatoFormValidation,
  camposParaContatoForm,
  contatoFormParaCampos,
  camposDiferem,
  CamposContatoForm,
} from '../hooks/useContatoFormValidation'

const CAMPOS_VAZIOS: CamposContatoForm = {
  nome: '',
  email: '',
  telefone: '',
  empresa: '',
  observacoes: '',
}

const CAMPOS_VALIDOS: CamposContatoForm = {
  nome: 'João Silva',
  email: 'joao@empresa.com',
  telefone: '(11) 99999-9999',
  empresa: 'Acme',
  observacoes: 'obs',
}


// ---------------------------------------------------------------------------
// validarTelefone
// ---------------------------------------------------------------------------

describe('validarTelefone', () => {
  test('retorna string vazia para entrada vazia (campo opcional)', () => {
    expect(validarTelefone('')).toBe('')
  })

  test('retorna string vazia para celular válido', () => {
    expect(validarTelefone('(11) 99999-9999')).toBe('')
  })

  test('retorna string vazia para fixo válido', () => {
    expect(validarTelefone('(11) 3333-4444')).toBe('')
  })

  test('retorna mensagem de erro para formato inválido (só dígitos)', () => {
    expect(validarTelefone('11999999999')).toMatch(/formato inválido/i)
  })

  test('retorna mensagem de erro para formato parcial', () => {
    expect(validarTelefone('(11) 999')).toMatch(/formato inválido/i)
  })

  test('retorna erro para 9 dígitos (nem fixo nem celular)', () => {
    expect(validarTelefone('(11) 999-9999')).toMatch(/formato inválido/i)
  })
})


// ---------------------------------------------------------------------------
// validarCampos
// ---------------------------------------------------------------------------

describe('validarCampos', () => {
  test('sem erros quando todos os campos válidos', () => {
    expect(validarCampos(CAMPOS_VALIDOS)).toEqual({})
  })

  test('exige nome obrigatório', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, nome: '' })
    expect(erros.nome).toMatch(/nome.*obrigat/i)
  })

  test('considera apenas espaços como nome vazio', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, nome: '   ' })
    expect(erros.nome).toBeDefined()
  })

  test('exige e-mail obrigatório', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, email: '' })
    expect(erros.email).toMatch(/obrigat/i)
  })

  test('valida formato de e-mail — rejeita "abc"', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, email: 'abc' })
    expect(erros.email).toMatch(/e-mail.*válido/i)
  })

  test('valida formato de e-mail — rejeita "abc@"', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, email: 'abc@' })
    expect(erros.email).toBeDefined()
  })

  test('valida formato de e-mail — rejeita "abc@dominio"', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, email: 'abc@dominio' })
    expect(erros.email).toBeDefined()
  })

  test('aceita e-mail bem formado', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, email: 'a@b.c' })
    expect(erros.email).toBeUndefined()
  })

  test('valida telefone quando preenchido', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, telefone: '123' })
    expect(erros.telefone).toBeDefined()
  })

  test('telefone vazio não gera erro (opcional)', () => {
    const erros = validarCampos({ ...CAMPOS_VALIDOS, telefone: '' })
    expect(erros.telefone).toBeUndefined()
  })

  test('acumula múltiplos erros simultaneamente', () => {
    const erros = validarCampos(CAMPOS_VAZIOS)
    expect(erros.nome).toBeDefined()
    expect(erros.email).toBeDefined()
  })
})


// ---------------------------------------------------------------------------
// useContatoFormValidation
// ---------------------------------------------------------------------------

describe('useContatoFormValidation hook', () => {
  test('retorna isValid=true para campos válidos', () => {
    const { result } = renderHook(() => useContatoFormValidation(CAMPOS_VALIDOS))
    expect(result.current.isValid).toBe(true)
    expect(result.current.errors).toEqual({})
  })

  test('retorna isValid=false quando há erro', () => {
    const { result } = renderHook(() => useContatoFormValidation(CAMPOS_VAZIOS))
    expect(result.current.isValid).toBe(false)
  })

  test('expõe função validate pura', () => {
    const { result } = renderHook(() => useContatoFormValidation(CAMPOS_VAZIOS))
    expect(typeof result.current.validate).toBe('function')
    // Validate aplica em qualquer entrada — não depende do estado do hook
    expect(result.current.validate(CAMPOS_VALIDOS)).toEqual({})
  })

  test('recalcula errors quando valores mudam (reatividade)', () => {
    const { result, rerender } = renderHook(
      ({ valores }: { valores: CamposContatoForm }) => useContatoFormValidation(valores),
      { initialProps: { valores: CAMPOS_VAZIOS } }
    )
    expect(result.current.isValid).toBe(false)

    rerender({ valores: CAMPOS_VALIDOS })
    expect(result.current.isValid).toBe(true)
  })
})


// ---------------------------------------------------------------------------
// Conversores
// ---------------------------------------------------------------------------

describe('camposParaContatoForm', () => {
  test('converte campos vazios opcionais para undefined', () => {
    const resultado = camposParaContatoForm(CAMPOS_VAZIOS)
    expect(resultado.telefone).toBeUndefined()
    expect(resultado.empresa).toBeUndefined()
    expect(resultado.observacoes).toBeUndefined()
  })

  test('preserva valores não-vazios', () => {
    const resultado = camposParaContatoForm(CAMPOS_VALIDOS)
    expect(resultado).toEqual({
      nome: 'João Silva',
      email: 'joao@empresa.com',
      telefone: '(11) 99999-9999',
      empresa: 'Acme',
      observacoes: 'obs',
    })
  })

  test('mantém nome e email como string mesmo se vazios', () => {
    const resultado = camposParaContatoForm(CAMPOS_VAZIOS)
    expect(resultado.nome).toBe('')
    expect(resultado.email).toBe('')
  })
})


describe('contatoFormParaCampos', () => {
  test('retorna estrutura vazia quando valorInicial é undefined', () => {
    expect(contatoFormParaCampos(undefined)).toEqual(CAMPOS_VAZIOS)
  })

  test('converte undefineds para string vazia', () => {
    const resultado = contatoFormParaCampos({
      nome: 'A',
      email: 'a@a.com',
      telefone: undefined,
      empresa: undefined,
      observacoes: undefined,
    })
    expect(resultado.telefone).toBe('')
    expect(resultado.empresa).toBe('')
    expect(resultado.observacoes).toBe('')
  })

  test('preserva valores definidos', () => {
    const resultado = contatoFormParaCampos({
      nome: 'A',
      email: 'a@a.com',
      telefone: '(11) 99999-9999',
      empresa: 'X',
      observacoes: 'obs',
    })
    expect(resultado).toEqual({
      nome: 'A',
      email: 'a@a.com',
      telefone: '(11) 99999-9999',
      empresa: 'X',
      observacoes: 'obs',
    })
  })
})


// ---------------------------------------------------------------------------
// camposDiferem
// ---------------------------------------------------------------------------

describe('camposDiferem', () => {
  test('retorna false quando objetos iguais', () => {
    expect(camposDiferem(CAMPOS_VALIDOS, { ...CAMPOS_VALIDOS })).toBe(false)
  })

  test('retorna true quando nome difere', () => {
    expect(camposDiferem(CAMPOS_VALIDOS, { ...CAMPOS_VALIDOS, nome: 'Outro' })).toBe(true)
  })

  test('retorna true quando email difere', () => {
    expect(camposDiferem(CAMPOS_VALIDOS, { ...CAMPOS_VALIDOS, email: 'x@x.com' })).toBe(true)
  })

  test('retorna true quando telefone difere', () => {
    expect(camposDiferem(CAMPOS_VALIDOS, { ...CAMPOS_VALIDOS, telefone: '' })).toBe(true)
  })

  test('retorna true quando empresa difere', () => {
    expect(camposDiferem(CAMPOS_VALIDOS, { ...CAMPOS_VALIDOS, empresa: 'novo' })).toBe(true)
  })

  test('retorna true quando observacoes difere', () => {
    expect(camposDiferem(CAMPOS_VALIDOS, { ...CAMPOS_VALIDOS, observacoes: 'novo' })).toBe(true)
  })
})
