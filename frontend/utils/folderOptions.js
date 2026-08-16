/**
 * Lista plana e indentada de carpetas para los `<select>` de carpeta padre.
 *
 * `excludeId` saca del listado a la carpeta y a toda su descendencia: una
 * carpeta no puede colgar de sí misma ni de una hija suya (el serializer del
 * backend rechaza exactamente eso), y ofrecerlo sólo sirve para provocar el
 * error.
 */
export function buildFolderOptions(folderStore, excludeId = null) {
  const exclude = new Set();
  if (excludeId != null) {
    exclude.add(excludeId);
    folderStore.descendantIdsOf(excludeId).forEach((id) => exclude.add(id));
  }
  const options = [];
  const walk = (parentId, depth) => {
    folderStore.childrenOf(parentId)
      .filter((folder) => !exclude.has(folder.id))
      .forEach((folder) => {
        options.push({ id: folder.id, label: `${'   '.repeat(depth)}${folder.name}` });
        walk(folder.id, depth + 1);
      });
  };
  walk(null, 0);
  return options;
}
