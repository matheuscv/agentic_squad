'use client'

import { useState, useEffect, FormEvent, ChangeEvent } from 'react'
import { ContatoForm as ContatoFormType } from '../types'

interface ContatoFormProps {
  valorInicial?: ContatoFormType
  onSubmit: (dados: ContatoFormType) => Promise<void>
  loading: boolean
  erro?: string
}

// Estado interno do formulário espelha ContatoFormType com strings (nunca undefined no input)
interface CamposForm {
  nome: string
  email: string
  telefone: string
  empresa: string
  observacoes: string
}

const camposVazios: CamposForm = {
  nome: '',
  email: '',
  telefone: '',
  empresa: '',
  observacoes: '',
}

function formParaContatoForm(campos: CamposForm): ContatoFormType {
  return {
    nome: campos.nome,
    email: campos.email,
    telefone: campos.telefone || undefined,
    empresa: campos.empresa || undefined,
    observacoes: campos.observacoes || undefined,
  }
}

export default function ContatoForm({
  valorInicial,
  onSubmit,
  loading,
  erro,
}: ContatoFormProps) {
  const [campos, setCampos] = useState<CamposForm>(() =>
    valorInicial
      ? {
          nome: valorInicial.nome ?? '',
          email: valorInicial.email ?? '',
          telefone: valorInicial.telefone ?? '',
          empresa: valorInicial.empresa ?? '',
          observacoes: valorInicial.observacoes ?? '',
        }
      : camposVazios
  )

  // Atualiza campos quando valorInicial mudar (ex: edição carregando dados async)
  useEffect(() => {
    if (valorInicial) {
      setCampos({
        nome: valorInicial.nome ?? '',
        email: valorInicial.email ?? '',
        telefone: valorInicial.telefone ?? '',
        empresa: valorInicial.empresa ?? '',
        observacoes: valorInicial.observacoes ?? '',
      })
    }
  }, [valorInicial])

  // Erros de validação client-side por campo
  const [errosCampo, setErrosCampo] = useState<Partial<CamposForm>>({})

  function validar(): boolean {
    const novosErros: Partial<CamposForm> = {}
    if (!campos.nome.trim()) {
      novosErros.nome = 'Nome Completo é obrigatório.'
    }
    if (!campos.email.trim()) {
      novosErros.email = 'E-mail é obrigatório.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(campos.email)) {
      novosErros.email = 'Informe um e-mail válido.'
    }
    setErrosCampo(novosErros)
    return Object.keys(novosErros).length === 0
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validar()) return
    await onSubmit(formParaContatoForm(campos))
  }

  function handleChange(
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    const { name, value } = e.target
    setCampos((prev: CamposForm) => ({ ...prev, [name]: value }))
    // Limpa erro do campo ao digitar
    if (errosCampo[name as keyof CamposForm]) {
      setErrosCampo((prev: Partial<CamposForm>) => ({ ...prev, [name]: undefined }))
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="bg-white rounded-lg shadow p-6 space-y-5 max-w-lg"
    >
      {/* Alerta de erro externo (API) */}
      {erro && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {erro}
        </div>
      )}

      {/* Nome Completo */}
      <div>
        <label
          htmlFor="nome"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Nome Completo <span className="text-red-500">*</span>
        </label>
        <input
          id="nome"
          name="nome"
          type="text"
          value={campos.nome}
          onChange={handleChange}
          disabled={loading}
          placeholder="Ex.: João da Silva"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        {errosCampo.nome && (
          <p className="mt-1 text-xs text-red-600">{errosCampo.nome}</p>
        )}
      </div>

      {/* E-mail */}
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          E-mail <span className="text-red-500">*</span>
        </label>
        <input
          id="email"
          name="email"
          type="email"
          value={campos.email}
          onChange={handleChange}
          disabled={loading}
          placeholder="Ex.: joao@empresa.com"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
        {errosCampo.email && (
          <p className="mt-1 text-xs text-red-600">{errosCampo.email}</p>
        )}
      </div>

      {/* Telefone */}
      <div>
        <label
          htmlFor="telefone"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Telefone
        </label>
        <input
          id="telefone"
          name="telefone"
          type="tel"
          value={campos.telefone}
          onChange={handleChange}
          disabled={loading}
          placeholder="Ex.: (11) 99999-9999"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
      </div>

      {/* Empresa */}
      <div>
        <label
          htmlFor="empresa"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Empresa
        </label>
        <input
          id="empresa"
          name="empresa"
          type="text"
          value={campos.empresa}
          onChange={handleChange}
          disabled={loading}
          placeholder="Ex.: Acme Ltda."
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
      </div>

      {/* Observações */}
      <div>
        <label
          htmlFor="observacoes"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Observações
        </label>
        <textarea
          id="observacoes"
          name="observacoes"
          rows={3}
          value={campos.observacoes}
          onChange={handleChange}
          disabled={loading}
          placeholder="Informações adicionais..."
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed resize-none"
        />
      </div>

      {/* Botões */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {loading && (
            <span
              className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"
              aria-hidden="true"
            />
          )}
          Salvar
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={() => window.history.back()}
          className="px-5 py-2 rounded-md border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}
