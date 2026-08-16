import { reactive, ref } from 'vue'
import { useClientProjectCascade } from '../../composables/useClientProjectCascade'

function setup(initial = {}) {
  const form = reactive({ client: null, project: null, ...initial })
  const clientDisplayName = ref('')
  const onOperatorChoice = jest.fn()
  const cascade = useClientProjectCascade(form, clientDisplayName, { onOperatorChoice })
  return { form, clientDisplayName, onOperatorChoice, ...cascade }
}

describe('useClientProjectCascade', () => {
  it('picking a client stores its id and its label', () => {
    const { form, clientDisplayName, onClientSelect } = setup()

    onClientSelect({ id: 7, name: 'Kore SAS' })

    expect(form.client).toBe(7)
    expect(clientDisplayName.value).toBe('Kore SAS')
  })

  it('clearing the client also drops the project', () => {
    const { form, onClientSelect } = setup({ client: 7, project: 3 })

    onClientSelect(null)

    expect(form.client).toBeNull()
    // Sin cliente el proyecto no se sostiene: el backend lo derivaría de
    // vuelta y la limpieza no habría limpiado nada.
    expect(form.project).toBeNull()
  })

  it('picking a project fills an empty client — the inverse cascade', () => {
    const { form, clientDisplayName, onProjectSelect } = setup()

    onProjectSelect({ id: 3, client_profile_id: 7, client_display_name: 'Kore SAS' })

    expect(form.client).toBe(7)
    expect(clientDisplayName.value).toBe('Kore SAS')
  })

  it('picking a project never overwrites a client already chosen', () => {
    const { form, onProjectSelect } = setup({ client: 9 })

    onProjectSelect({ id: 3, client_profile_id: 7, client_display_name: 'Kore SAS' })

    expect(form.client).toBe(9)
  })

  it('ignores a cleared project selection', () => {
    const { form, onProjectSelect } = setup()

    onProjectSelect(null)

    expect(form.client).toBeNull()
  })

  it('reports every explicit choice so the caller can retract a suggestion', () => {
    const { onClientSelect, onProjectSelect, onOperatorChoice } = setup()

    onClientSelect({ id: 7, name: 'Kore SAS' })
    expect(onOperatorChoice).toHaveBeenCalledTimes(1)

    onClientSelect(null)
    expect(onOperatorChoice).toHaveBeenCalledTimes(2)
  })

  it('does not report a choice when the inverse cascade did nothing', () => {
    const { onProjectSelect, onOperatorChoice } = setup({ client: 9 })

    onProjectSelect({ id: 3, client_profile_id: 7 })

    expect(onOperatorChoice).not.toHaveBeenCalled()
  })

  it('works without the optional callback', () => {
    const form = reactive({ client: null, project: null })
    const label = ref('')
    const { onClientSelect } = useClientProjectCascade(form, label)

    expect(() => onClientSelect({ id: 1, name: 'Ana' })).not.toThrow()
    expect(form.client).toBe(1)
  })
})
