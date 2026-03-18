import { setActivePinia, createPinia } from 'pinia'
import { usePlatformClientsStore } from '../../stores/platform-clients'

jest.mock('../../composables/usePlatformApi', () => {
  const mockGet = jest.fn()
  const mockPost = jest.fn()
  const mockPatch = jest.fn()
  const mockDelete = jest.fn()
  return {
    usePlatformApi: () => ({
      get: mockGet,
      post: mockPost,
      patch: mockPatch,
      delete: mockDelete,
    }),
    readPlatformSession: jest.fn(() => ({
      accessToken: '', refreshToken: '', user: null,
      verificationToken: '', pendingEmail: '',
    })),
    writePlatformSession: jest.fn(),
    clearPlatformSession: jest.fn(),
    __mockGet: mockGet,
    __mockPost: mockPost,
    __mockPatch: mockPatch,
    __mockDelete: mockDelete,
  }
})

const {
  __mockGet: mockGet,
  __mockPost: mockPost,
  __mockPatch: mockPatch,
  __mockDelete: mockDelete,
} = require('../../composables/usePlatformApi')

const SAMPLE_CLIENT = {
  user_id: 1,
  email: 'client@test.com',
  first_name: 'Ana',
  last_name: 'García',
  company_name: 'ACME',
  is_active: true,
  is_onboarded: true,
}

describe('usePlatformClientsStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformClientsStore()
    jest.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty clients array', () => {
      expect(store.clients).toEqual([])
      expect(store.currentClient).toBeNull()
      expect(store.isLoading).toBe(false)
      expect(store.error).toBe('')
    })
  })

  describe('getters', () => {
    beforeEach(() => {
      store.clients = [
        { ...SAMPLE_CLIENT, user_id: 1, is_active: true, is_onboarded: true },
        { ...SAMPLE_CLIENT, user_id: 2, is_active: true, is_onboarded: false },
        { ...SAMPLE_CLIENT, user_id: 3, is_active: false, is_onboarded: true },
      ]
    })

    it('activeClientsCount counts active clients', () => {
      expect(store.activeClientsCount).toBe(2)
    })

    it('pendingClientsCount counts active but not onboarded', () => {
      expect(store.pendingClientsCount).toBe(1)
    })

    it('inactiveClientsCount counts inactive clients', () => {
      expect(store.inactiveClientsCount).toBe(1)
    })

    it('recentClients returns first 5 clients', () => {
      expect(store.recentClients).toHaveLength(3)
    })
  })

  describe('fetchClients', () => {
    it('populates clients on success', async () => {
      mockGet.mockResolvedValueOnce({ data: [SAMPLE_CLIENT] })

      const result = await store.fetchClients()

      expect(result.success).toBe(true)
      expect(store.clients).toEqual([SAMPLE_CLIENT])
      expect(store.isLoading).toBe(false)
    })

    it('appends filter query param when not all', async () => {
      mockGet.mockResolvedValueOnce({ data: [] })

      await store.fetchClients('pending')

      expect(mockGet).toHaveBeenCalledWith('clients/?filter=pending')
      expect(store.activeFilter).toBe('pending')
    })

    it('uses plain URL for all filter', async () => {
      mockGet.mockResolvedValueOnce({ data: [] })

      await store.fetchClients('all')

      expect(mockGet).toHaveBeenCalledWith('clients/')
    })

    it('sets error on failure', async () => {
      mockGet.mockRejectedValueOnce({
        response: { data: { detail: 'No autorizado.' } },
      })

      const result = await store.fetchClients()

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
    })
  })

  describe('fetchClient', () => {
    it('sets currentClient on success', async () => {
      mockGet.mockResolvedValueOnce({ data: SAMPLE_CLIENT })

      const result = await store.fetchClient(1)

      expect(result.success).toBe(true)
      expect(store.currentClient).toEqual(SAMPLE_CLIENT)
    })

    it('sets currentClient to null on failure', async () => {
      mockGet.mockRejectedValueOnce({
        response: { data: { detail: 'No encontrado.' } },
      })

      const result = await store.fetchClient(999)

      expect(result.success).toBe(false)
      expect(store.currentClient).toBeNull()
    })
  })

  describe('createClient', () => {
    it('returns error when required fields are missing', async () => {
      const result = await store.createClient({ email: '', first_name: '', last_name: '' })

      expect(result.success).toBe(false)
      expect(store.error).toBeTruthy()
      expect(mockPost).not.toHaveBeenCalled()
    })

    it('adds new client to list on success', async () => {
      store.activeFilter = 'all'
      mockPost.mockResolvedValueOnce({ data: SAMPLE_CLIENT })

      const result = await store.createClient({
        email: 'new@test.com',
        first_name: 'New',
        last_name: 'Client',
      })

      expect(result.success).toBe(true)
      expect(store.clients).toContainEqual(SAMPLE_CLIENT)
    })

    it('sets error on API failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Email duplicado.' } },
      })

      const result = await store.createClient({
        email: 'dup@test.com',
        first_name: 'A',
        last_name: 'B',
      })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Email duplicado.')
    })
  })

  describe('updateClient', () => {
    it('replaces client in list on success', async () => {
      store.clients = [SAMPLE_CLIENT]
      const updated = { ...SAMPLE_CLIENT, first_name: 'Updated' }
      mockPatch.mockResolvedValueOnce({ data: updated })

      const result = await store.updateClient(1, { first_name: 'Updated' })

      expect(result.success).toBe(true)
      expect(store.clients[0].first_name).toBe('Updated')
    })

    it('updates currentClient if matching', async () => {
      store.clients = [SAMPLE_CLIENT]
      store.currentClient = SAMPLE_CLIENT
      const updated = { ...SAMPLE_CLIENT, first_name: 'Updated' }
      mockPatch.mockResolvedValueOnce({ data: updated })

      await store.updateClient(1, { first_name: 'Updated' })

      expect(store.currentClient.first_name).toBe('Updated')
    })
  })

  describe('updateClient', () => {
    it('sets error on API failure', async () => {
      mockPatch.mockRejectedValueOnce({
        response: { data: { detail: 'Error al actualizar.' } },
      })

      const result = await store.updateClient(1, { first_name: 'X' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error al actualizar.')
      expect(store.isUpdating).toBe(false)
    })
  })

  describe('deactivateClient', () => {
    it('marks client as inactive on success', async () => {
      store.clients = [SAMPLE_CLIENT]
      mockDelete.mockResolvedValueOnce({})

      const result = await store.deactivateClient(1)

      expect(result.success).toBe(true)
      expect(store.clients[0].is_active).toBe(false)
    })

    it('updates currentClient if matching', async () => {
      store.clients = [SAMPLE_CLIENT]
      store.currentClient = SAMPLE_CLIENT
      mockDelete.mockResolvedValueOnce({})

      await store.deactivateClient(1)

      expect(store.currentClient.is_active).toBe(false)
    })

    it('sets error on API failure', async () => {
      mockDelete.mockRejectedValueOnce({
        response: { data: { detail: 'No autorizado.' } },
      })

      const result = await store.deactivateClient(1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('No autorizado.')
      expect(store.isUpdating).toBe(false)
    })
  })

  describe('resendInvite', () => {
    it('marks client as not onboarded on success', async () => {
      store.clients = [SAMPLE_CLIENT]
      mockPost.mockResolvedValueOnce({ data: { detail: 'Invitación reenviada.' } })

      const result = await store.resendInvite(1)

      expect(result.success).toBe(true)
      expect(store.clients[0].is_onboarded).toBe(false)
    })

    it('sets error on failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Error al reenviar.' } },
      })

      const result = await store.resendInvite(1)

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error al reenviar.')
    })
  })
})
