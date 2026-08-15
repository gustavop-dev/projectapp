/**
 * Conteos de un subárbol de carpetas: lo que guarda una carpeta a cualquier
 * profundidad, no sólo lo que cuelga directo de ella.
 *
 * Se resuelve acá y no en el backend porque el número NO es una propiedad de la
 * carpeta: es una propiedad de la carpeta dentro de la partición que dibuja el
 * panel. Esa partición la define `isRootInScope`, que es una regla de la vista y
 * depende del modo en que se esté parado. La lista completa de carpetas ya está
 * en memoria (`document-folders/?scope=all` no pagina y trae los dos estados),
 * así que el rollup no cuesta ni una consulta más.
 *
 * INVARIANTE DEL QUE DEPENDE TODO: `folders` tiene que ser el árbol COMPLETO,
 * de ambos estados. Si algún día se pagina `document-folders/`, o alguien pide
 * la lista con `{ scope: 'active' }` para ahorrar payload, o `searchFolders`
 * pasa a poblar `folders`, todos estos números sub-reportan EN SILENCIO — que es
 * exactamente el bug que este módulo existe para corregir. El backend tiene un
 * test que fija que la lista no pagina y devuelve los dos estados.
 *
 * Los dos ejes, que es lo único sutil acá:
 *
 *   - `countingScope`  qué documentos se suman en cada nodo.
 *   - `membershipScope` por qué carpetas se puede bajar. Es el mismo scope con
 *     que el panel decide qué fila queda en la cima, y por eso los subárboles
 *     de las raíces son disjuntos: cada carpeta del scope tiene exactamente una
 *     raíz encima suyo, así que ningún documento se cuenta dos veces y la suma
 *     de las filas más «Sin carpeta» da el total de «Todos».
 *
 * El caso que obliga a separarlos: A(activa) → B(archivada) → C(activa). En modo
 * normal el panel PROMUEVE a C a raíz, porque su contenedor no está en el scope.
 * Si el rollup de A bajara por B hasta C, los documentos de C aparecerían en la
 * insignia de A y en la de C. Bajando sólo por carpetas del `membershipScope`,
 * la cuenta de A se corta en B y C responde por lo suyo.
 *
 * Residuo conocido en modo normal: un documento ACTIVO que viva dentro de una
 * carpeta archivada no queda en ninguna fila — su carpeta no se lista y no es
 * «Sin carpeta». Es un estado que el módulo considera anómalo (lo detecta el
 * comando `audit_archive_integrity` y lo reparó la migración 0186), hoy con cero
 * filas en producción. No se le inventa un bucket: mentiría sobre dónde está.
 */

import { matchesScope } from '~/utils/archiveScope';
import { scopedCounts } from '~/utils/documentStatus';

/**
 * Mapa `id → { docs, subs, ownDocs, ownSubs }` para todas las carpetas del
 * `membershipScope`. `docs`/`subs` incluyen el subárbol; `ownDocs`/`ownSubs` son
 * lo que cuelga directo, que es lo que permite decir «12 en total, 1 acá».
 */
export function buildFolderRollup(folders, { countingScope = 'active', membershipScope = 'all' } = {}) {
  const rollup = new Map();
  const list = Array.isArray(folders) ? folders : [];

  const own = new Map();
  const childrenByParent = new Map();
  for (const folder of list) {
    if (!folder || folder.id == null || !matchesScope(folder, membershipScope)) continue;
    own.set(folder.id, scopedCounts(folder, countingScope));
    // Una carpeta que se declara su propio padre no cuelga de nadie: se trata
    // como raíz en vez de dejarla fuera del mapa.
    if (folder.parent == null || folder.parent === folder.id) continue;
    const siblings = childrenByParent.get(folder.parent);
    if (siblings) siblings.push(folder.id);
    else childrenByParent.set(folder.parent, [folder.id]);
  }

  // Recorrido con pila explícita, no recursión: la profundidad del árbol no
  // tiene tope y una insignia jamás debe reventar la pila ni colgar el panel.
  // `onStack` corta las back-edges — los ciclos son imposibles por la API
  // (`validate_parent` los rechaza), pero los helpers vecinos del store ya se
  // defienden igual y un dato torcido no puede ser peor que un número flojo.
  const onStack = new Set();
  for (const startId of own.keys()) {
    if (rollup.has(startId)) continue;
    const stack = [{ id: startId, exiting: false }];
    while (stack.length) {
      const frame = stack.pop();
      const { id } = frame;
      if (frame.exiting) {
        const mine = own.get(id);
        let docs = mine.docs;
        let subs = mine.subs;
        for (const childId of childrenByParent.get(id) || []) {
          const child = rollup.get(childId);
          if (child) {
            docs += child.docs;
            subs += child.subs;
          }
        }
        rollup.set(id, { docs, subs, ownDocs: mine.docs, ownSubs: mine.subs });
        onStack.delete(id);
        continue;
      }
      if (rollup.has(id) || onStack.has(id)) continue;
      onStack.add(id);
      stack.push({ id, exiting: true });
      for (const childId of childrenByParent.get(id) || []) {
        if (!rollup.has(childId) && !onStack.has(childId)) {
          stack.push({ id: childId, exiting: false });
        }
      }
    }
  }

  return rollup;
}

/** Registro de una carpeta que no está en el mapa: sus conteos directos. */
export function directRollupRecord(folder, countingScope = 'active') {
  const { docs, subs } = scopedCounts(folder, countingScope);
  return { docs, subs, ownDocs: docs, ownSubs: subs };
}
