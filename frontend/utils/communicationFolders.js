/** Build folder locations from one flat response without per-row requests. */
export function folderPath(folder, folders) {
  const byId = new Map(folders.map((item) => [Number(item.id), item]));
  const segments = [];
  const seen = new Set();
  let node = folder;
  while (node && !seen.has(node.id)) {
    seen.add(node.id);
    segments.unshift(node);
    node = byId.get(Number(node.parent));
  }
  return segments;
}

export function folderOptions(folders, { client, project, exclude } = {}) {
  return folders.filter((folder) => (
    (!client || Number(folder.client) === Number(client))
    && (!folder.project || Number(folder.project) === Number(project))
    && !folderPath(folder, folders).some((node) => Number(node.id) === Number(exclude))
  )).map((folder) => ({
    value: String(folder.id),
    label: folderPath(folder, folders).map((node) => node.name).join(' / '),
  }));
}
