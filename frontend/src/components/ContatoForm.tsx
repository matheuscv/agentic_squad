'use client'

import { useState, useEffect, useCallback, FormEvent, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Save, X } from 'lucide-react'
import { ContatoForm as ContatoFormType } from '../types'
import { useBeforeUnload } from '../hooks/useBeforeUnload'
import {
  CamposContatoForm, ErrosContatoForm, useContatoFormValidation,
  validarTelefone, camposParaContatoForm, contatoFormParaCampos, camposDiferem,
} from '../hooks/useContatoFormValidation'
import InputField from './form/InputField'
import TextAreaField from './form/TextAreaField'
import UnsavedChangesModal from './UnsavedChangesModal'

interface ContatoFormProps {
  valorInicial?: ContatoFormType
  onSubmit: (dados: ContatoFormType) => Promise<void>
  loading: boolean
  erro?: string
}

// Classes Tailwind extraídas para enxugar o JSX e preservar o visual original.
const BOTAO_SALVAR = 'flex items-center gap-2 px-5 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500'
const BOTAO_CANCELAR = 'flex items-center gap-1 px-5 py-2 rounded-md border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400'

/**
 * Formulário de criação/edição de contato.
 *
 * Pós-refatoração (TASK-14):
 *  - Validação extraída para `useContatoFormValidation` (e-mail/telefone/obrigatórios).
 *  - Inputs e textarea substituídos pelos componentes em `components/form/`.
 *  - Estado dos campos permanece local para alimentar `isDirty` (useBeforeUnload).
 */
export default function ContatoForm({ valorInicial, onSubmit, loading, erro }: ContatoFormProps) {
  const router = useRouter()

  // Snapshot original e valores atuais — a diferença alimenta `isDirty`.
  const [camposOriginais, setCamposOriginais] = useState<CamposContatoForm>(
    () => contatoFormParaCampos(valorInicial)
  )
  const [campos, setCampos] = useState<CamposContatoForm>(
    () => contatoFormParaCampos(valorInicial)
  )

  // Sincroniza quando `valorInicial` chega via async (edição).
  useEffect(() => {
    const iniciais = contatoFormParaCampos(valorInicial)
    setCampos(iniciais)
    setCamposOriginais(iniciais)
  }, [valorInicial])

  const isDirty = camposDiferem(campos, camposOriginais)
  useBeforeUnload(isDirty)

  const { validate } = useContatoFormValidation(campos)

  // Erros e modal — controlados localmente para preservar UX original.
  const [errosCampo, setErrosCampo] = useState<ErrosContatoForm>({})
  const [modalAberto, setModalAberto] = useState(false)
  const [pendingNavigation, setPendingNavigation] = useState<string | null>(null)

  function handleChange(e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const { name, value } = e.target
    setCampos((prev) => ({ ...prev, [name]: value }))
    if (errosCampo[name as keyof CamposContatoForm]) {
      setErrosCampo((prev) => ({ ...prev, [name]: undefined }))
    }
  }

  // Valida telefone apenas no `onBlur` — não bloqueia digitação.
  function handleTelefoneBlur() {
    const erro = validarTelefone(campos.telefone)
    setErrosCampo((prev) => ({ ...prev, telefone: erro || undefined }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const erros = validate(campos)
    setErrosCampo(erros)
    if (Object.keys(erros).length > 0) return
    await onSubmit(camposParaContatoForm(campos))
    setCamposOriginais({ ...campos }) // zera dirty após submit bem-sucedido
  }

  // Sem alterações navega direto; com alterações abre o modal.
  const handleCancelar = useCallback(() => {
    if (!isDirty) { window.history.back(); return }
    setPendingNavigation('BACK')
    setModalAberto(true)
  }, [isDirty])

  function handleContinueEditing() {
    setModalAberto(false)
    setPendingNavigation(null)
  }

  function handleLeaveWithoutSaving() {
    setModalAberto(false)
    setCamposOriginais({ ...campos }) // evita duplo disparo do beforeunload
    if (pendingNavigation && pendingNavigation !== 'BACK') router.push(pendingNavigation)
    else window.history.back()
    setPendingNavigation(null)
  }

  return (
    <>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="bg-white rounded-lg shadow p-6 space-y-5 max-w-lg"
      >
        {erro && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {erro}
          </div>
        )}

        <InputField label="Nome Completo" name="nome" value={campos.nome}
          onChange={handleChange} required placeholder="Ex.: João da Silva"
          disabled={loading} error={errosCampo.nome} />

        <InputField label="E-mail" name="email" type="email" value={campos.email}
          onChange={handleChange} required placeholder="Ex.: joao@empresa.com"
          disabled={loading} error={errosCampo.email} />

        <InputField label="Telefone" name="telefone" type="tel"
          mask="(99) 99999-9999" value={campos.telefone}
          onChange={handleChange} onBlur={handleTelefoneBlur}
          placeholder="Ex.: (11) 99999-9999"
          disabled={loading} error={errosCampo.telefone} />

        <InputField label="Empresa" name="empresa" value={campos.empresa}
          onChange={handleChange} placeholder="Ex.: Acme Ltda." disabled={loading} />

        <TextAreaField label="Observações" name="observacoes" value={campos.observacoes}
          onChange={handleChange} rows={3} placeholder="Informações adicionais..."
          disabled={loading} />

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={loading} className={BOTAO_SALVAR}>
            {loading ? (
              <span className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" aria-hidden="true" />
            ) : (
              <Save size={16} aria-hidden="true" />
            )}
            <span>Salvar</span>
          </button>
          <button type="button" disabled={loading} onClick={handleCancelar} className={BOTAO_CANCELAR}>
            <X size={16} aria-hidden="true" />
            <span>Cancelar</span>
          </button>
        </div>
      </form>

      <UnsavedChangesModal
        isOpen={modalAberto}
        onContinue={handleContinueEditing}
        onLeave={handleLeaveWithoutSaving}
      />
    </>
  )
}
