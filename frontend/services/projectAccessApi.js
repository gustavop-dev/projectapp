/** Build the project-access contract over either the panel or platform client. */
export function createProjectAccessApi(transport, accessPath) {
  const data = async (request) => (await request).data
  const path = accessPath.endsWith('/') ? accessPath : `${accessPath}/`

  return {
    load: () => data(transport.get(path)),
    updateField: (payload) => data(transport.patch(path, payload)),
    revealPassword: (environment) => data(
      transport.post(`${path}environments/${environment}/password/reveal/`, {}),
    ),
    deletePassword: (environment) => data(
      transport.remove(`${path}environments/${environment}/password/`),
    ),
    createNote: (payload) => data(transport.post(`${path}notes/`, payload)),
    updateNote: (noteId, payload) => data(
      transport.patch(`${path}notes/${noteId}/`, payload),
    ),
    deleteNote: (noteId) => data(transport.remove(`${path}notes/${noteId}/`)),
    revealNote: (noteId) => data(transport.post(`${path}notes/${noteId}/reveal/`, {})),
    classifyLegacy: (environment) => data(
      transport.post(`${path}legacy/classify/`, { environment }),
    ),
  }
}
