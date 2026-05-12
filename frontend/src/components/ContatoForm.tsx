'use client'

import { useState, useEffect, useCallback, FormEvent, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import InputMask from 'react-input-mask'
import { Save, X } from 'lucide-react'
import { ContatoForm as ContatoFormType } from '../types'
import { useBeforeUnload } from '../hooks/useBeforeUnload'
import UnsavedChangesModal from './UnsavedChangesModal'

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

/** Converte valorInicial (pode ter undefined) em CamposForm normalizado */
function inicialParaCampos(valorInicial?: ContatoFormType): CamposForm {
  if (!valorInicial) return camposVazios
  return {
    nome: valorInicial.nome ?? '',
    email: valorInicial.email ?? '',
    telefone: valorInicial.telefone ?? '',
    empresa: valorInicial.empresa ?? '',
    observacoes: valorInicial.observacoes ?? '',
  }
}

/** Compara dois CamposForm campo a campo para detectar alterações */
function camposDiferem(a: CamposForm, b: CamposForm): boolean {
  return (
    a.nome !== b.nome ||
    a.email !== b.email ||
    a.telefone !== b.telefone ||
    a.empresa !== b.empresa ||
    a.observacoes !== b.observacoes
  )
}

export default function ContatoForm({
  valorInicial,
  onSubmit,
  loading,
  erro,
}: ContatoFormProps) {
  const router = useRouter()

  // Snapshot dos valores originais — atualizado apenas quando valorInicial muda
  const [camposOriginais, setCamposOriginais] = useState<CamposForm>(() =>
    inicialParaCampos(valorInicial)
  )

  const [campos, setCampos] = useState<CamposForm>(() =>
    inicialParaCampos(valorInicial)
  )

  // Atualiza campos e snapshot quando valorInicial mudar (ex: edição carregando dados async)
  useEffect(() => {
    const iniciais = inicialParaCampos(valorInicial)
    setCampos(iniciais)
    setCamposOriginais(iniciais)
  }, [valorInicial])

  // isDirty: true quando campos atuais diferem dos originais
  const isDirty = camposDiferem(campos, camposOriginais)

  // Intercepta fechamento/reload de aba quando há alterações
  useBeforeUnload(isDirty)

  // Controle do modal de confirmação para navegação interna
  const [modalAberto, setModalAberto] = useState(false)
  // Rota de destino pendente enquanto o modal aguarda confirmação
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(null)

  // Erros de validação client-side por campo
  const [errosCampo, setErrosCampo] = useState<Partial<CamposForm>>({})

  // Erro de validação específico do campo telefone (opcional, mas com formato exigido se preenchido)
  const [telefoneErro, setTelefoneErro] = useState<string>('')

  // Valida formato de telefone: aceita celular (11 dígitos) ou fixo (10 dígitos).
  // Retorna mensagem de erro ou string vazia se válido/vazio.
  function validarFormatoTelefone(valor: string): string {
    // Remove os caracteres da máscara para verificar se o campo foi preenchido
    const soDigitos = valor.replace(/\D/g, '')
    if (soDigitos.length === 0) return ''
    const celular = /^\(\d{2}\) \d{5}-\d{4}$/
    const fixo = /^\(\d{2}\) \d{4}-\d{4}$/
    if (!celular.test(valor) && !fixo.test(valor)) {
      return 'Formato inválido. Use (99) 99999-9999 ou (99) 9999-9999.'
    }
    return ''
  }

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
    // Valida telefone também na submissão, para garantir consistência
    const erroTel = validarFormatoTelefone(campos.telefone)
    setTelefoneErro(erroTel)
    setErrosCampo(novosErros)
    return Object.keys(novosErros).length === 0 && erroTel === ''
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validar()) return
    await onSubmit(formParaContatoForm(campos))
    // Zera o estado dirty após submit bem-sucedido para evitar alerta ao navegar
    setCamposOriginais({ ...campos })
    setTelefoneErro('')
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

  /**
   * Trata clique em "Cancelar".
   * - Sem alterações: navega diretamente (sem modal).
   * - Com alterações: salva rota destino e abre modal de confirmação.
   *
   * Conservadoramente usamos window.history.back() como destino quando
   * não há rota explícita configurada via props (mantém comportamento original).
   */
  const handleCancelar = useCallback(() => {
    if (!isDirty) {
      // Sem alterações — navega diretamente
      window.history.back()
      return
    }
    // Com alterações — guarda rota e abre modal.
    // Usando string especial 'BACK' para representar history.back()
    // (não há rota de destino explícita neste componente).
    setPendingNavigation('BACK')
    setModalAberto(true)
  }, [isDirty])

  /** Usuário escolheu "Continuar editando": fecha modal, mantém dados */
  function handleContinueEditing() {
    setModalAberto(false)
    setPendingNavigation(null)
  }

  /** Usuário escolheu "Sair sem salvar": navega para o destino pendente */
  function handleLeaveWithoutSaving() {
    setModalAberto(false)
    // Limpa dirty antes de navegar para evitar duplo disparo do beforeunload
    setCamposOriginais({ ...campos })

    if (pendingNavigation && pendingNavigation !== 'BACK') {
      router.push(pendingNavigation)
    } else {
      window.history.back()
    }
    setPendingNavigation(null)
  }

  return (
    <>
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

        {/* Telefone — máscara de celular (99) 99999-9999; campo opcional */}
        <div>
          <label
            htmlFor="telefone"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Telefone
          </label>
          {/*
            react-input-mask usa mask="(99) 99999-9999" para cobrir celular.
            Para fixo (8 dígitos) o usuário pode apagar o último algarismo —
            a validação no onBlur aceita ambos os formatos.
          */}
          <InputMask
            mask="(99) 99999-9999"
            maskChar={null}
            value={campos.telefone}
            onChange={handleChange}
            onBlur={() => setTelefoneErro(validarFormatoTelefone(campos.telefone))}
            disabled={loading}
          >
            {/* react-input-mask passa props para o input filho via render prop interno */}
            {(inputProps: React.InputHTMLAttributes<HTMLInputElement>) => (
              <input
                {...inputProps}
                id="telefone"
                name="telefone"
                type="tel"
                placeholder="Ex.: (11) 99999-9999"
                disabled={loading}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed"
              />
            )}
          </InputMask>
          {telefoneErro && (
            <p className="mt-1 text-xs text-red-600">{telefoneErro}</p>
          )}
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
            {loading ? (
              <span
                className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"
                aria-hidden="true"
              />
            ) : (
              <Save size={16} aria-hidden="true" />
            )}
            <span>Salvar</span>
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleCancelar}
            className="flex items-center gap-1 px-5 py-2 rounded-md border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            <X size={16} aria-hidden="true" /><span>Cancelar</span>
          </button>
        </div>
      </form>

      {/* Modal de confirmação — renderizado fora do <form> para evitar submit acidental */}
      <UnsavedChangesModal
        isOpen={modalAberto}
        onContinue={handleContinueEditing}
        onLeave={handleLeaveWithoutSaving}
      />
    </>
  )
}
