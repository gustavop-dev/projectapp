"""Audita (y opcionalmente repara) el invariante del archivado de documentos.

Invariante: toda fila activa tiene su cadena de contenedores activa. Se rompe
por escrituras que no pasan por el servicio (el admin de Django editando
`parent`, carreras archive×unarchive) y su síntoma es un documento invisible —
el caso 'requirements_mapping' que reparó la migración 0186. Aquella corre una
sola vez; este comando es la versión re-ejecutable para auditar producción
cuando se sospeche un huérfano nuevo.

Chequeos:
1. Documentos activos con algún ancestro archivado (invisibles en el panel).
2. Carpetas activas con algún ancestro archivado.
3. Ciclos en `parent` (se reportan; jamás se re-parenta — misma asimetría
   deliberada que 0186: silencioso es peor que un ciclo raro).
4. Procedencia anómala: filas ACTIVAS con `archived_via_folder` (toda ruta de
   restauración lo limpia, su presencia delata edición manual) y filas
   archivadas cuya carpeta causante ya está activa (informativo).

Por defecto sólo reporta. Con `--repair` aplica EXACTAMENTE la política de
0186: un único UPDATE que reabre los ancestros archivados de (1)+(2) —
`is_archived=False, archived_at=None, archived_via_folder=None` — y nada más:
ni ciclos, ni procedencia, ni el resto del contenido de esas carpetas.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import Document, DocumentFolder


def _build_tree():
    """Árbol completo en memoria: {id: (parent_id, is_archived)} — como 0186."""
    return {
        pk: (parent_id, is_archived)
        for pk, parent_id, is_archived in DocumentFolder.objects
        .values_list('id', 'parent_id', 'is_archived')
    }


def _archived_ancestors(tree, folder_id):
    """IDs archivados desde `folder_id` hasta la raíz, saltando los activos."""
    found = []
    visited = set()
    while folder_id is not None and folder_id not in visited:
        visited.add(folder_id)
        node = tree.get(folder_id)
        if node is None:
            break
        parent_id, is_archived = node
        if is_archived:
            found.append(folder_id)
        folder_id = parent_id
    return found


def _find_cycles(tree):
    """Listas de ids que forman ciclos de `parent`. No muta nada."""
    color = {}
    cycles = []
    for start in tree:
        if start in color:
            continue
        path = []
        node = start
        while node is not None and node not in color and node in tree:
            color[node] = 'gray'
            path.append(node)
            node = tree[node][0]
        if node is not None and color.get(node) == 'gray':
            cycles.append(path[path.index(node):])
        for visited in path:
            color[visited] = 'black'
    return cycles


def _audit():
    tree = _build_tree()

    lost_documents = []   # (id, title, folder_id) activos bajo ancestro archivado
    buried_folders = []   # (id, name) activas bajo ancestro archivado
    to_restore = set()    # ancestros archivados a reabrir (política 0186)

    for doc_id, title, folder_id in (
        Document.objects
        .filter(is_archived=False, folder__isnull=False)
        .values_list('id', 'title', 'folder_id')
    ):
        chain = _archived_ancestors(tree, folder_id)
        if chain:
            lost_documents.append((doc_id, title, folder_id))
            to_restore.update(chain)

    for folder_id, name, parent_id in (
        DocumentFolder.objects
        .filter(is_archived=False, parent__isnull=False)
        .values_list('id', 'name', 'parent_id')
    ):
        chain = _archived_ancestors(tree, parent_id)
        if chain:
            buried_folders.append((folder_id, name))
            to_restore.update(chain)

    cycles = _find_cycles(tree)
    fully_archived_cycles = [
        cycle for cycle in cycles if all(tree[node][1] for node in cycle)
    ]

    active_docs_with_provenance = list(
        Document.objects
        .filter(is_archived=False, archived_via_folder__isnull=False)
        .values_list('id', 'title'),
    )
    active_folders_with_provenance = list(
        DocumentFolder.objects
        .filter(is_archived=False, archived_via_folder__isnull=False)
        .values_list('id', 'name'),
    )
    archived_with_active_cause = (
        Document.objects
        .filter(is_archived=True, archived_via_folder__is_archived=False)
        .count()
        + DocumentFolder.objects
        .filter(is_archived=True, archived_via_folder__is_archived=False)
        .count()
    )

    return {
        'lost_documents': lost_documents,
        'buried_folders': buried_folders,
        'ancestors_to_restore': to_restore,
        'cycles': cycles,
        'fully_archived_cycles': fully_archived_cycles,
        'active_docs_with_provenance': active_docs_with_provenance,
        'active_folders_with_provenance': active_folders_with_provenance,
        'archived_with_active_cause': archived_with_active_cause,
    }


class Command(BaseCommand):
    help = (
        'Audita el invariante del archivado de documentos: filas activas bajo '
        'carpetas archivadas (documentos perdidos), ciclos de parent y '
        'procedencia anómala. Por defecto sólo reporta; con --repair reabre la '
        'cadena de ancestros archivados con la política exacta de la migración '
        '0186. En producción: DJANGO_SETTINGS_MODULE=projectapp.settings_prod '
        'python manage.py audit_archive_integrity'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--repair',
            action='store_true',
            help='Reabre los ancestros archivados de cada fila activa '
                 'inalcanzable. Nunca re-parenta ni toca ciclos o procedencia.',
        )

    def handle(self, *args, **options):
        findings = self._report(_audit())
        if not options['repair']:
            return

        to_restore = findings['ancestors_to_restore']
        if not to_restore:
            self.stdout.write('Nada que reparar.')
            return

        with transaction.atomic():
            DocumentFolder.objects.filter(pk__in=to_restore).update(
                is_archived=False, archived_at=None, archived_via_folder=None,
            )
        self.stdout.write(self.style.SUCCESS(
            f'Reparado: {len(to_restore)} carpeta(s) de cadena reabiertas.',
        ))
        # Re-auditar deja constancia del residuo (ciclos, procedencia) que la
        # política deliberadamente no toca.
        self.stdout.write('--- Re-auditoría posterior a la reparación ---')
        self._report(_audit())

    def _report(self, findings):
        violations = False

        if findings['lost_documents']:
            violations = True
            self.stdout.write(self.style.WARNING(
                f"DOCUMENTOS PERDIDOS (activos bajo carpeta archivada): "
                f"{len(findings['lost_documents'])}",
            ))
            for doc_id, title, folder_id in findings['lost_documents']:
                self.stdout.write(f'  - #{doc_id} "{title}" (carpeta {folder_id})')

        if findings['buried_folders']:
            violations = True
            self.stdout.write(self.style.WARNING(
                f"CARPETAS SEPULTADAS (activas bajo ancestro archivado): "
                f"{len(findings['buried_folders'])}",
            ))
            for folder_id, name in findings['buried_folders']:
                self.stdout.write(f'  - #{folder_id} "{name}"')

        if findings['cycles']:
            violations = True
            for cycle in findings['cycles']:
                archived = cycle in findings['fully_archived_cycles']
                suffix = ' (totalmente archivado: punto muerto)' if archived else ''
                self.stdout.write(self.style.WARNING(
                    f"CICLO en parent: {' -> '.join(str(pk) for pk in cycle)}{suffix}",
                ))

        provenance = (
            findings['active_docs_with_provenance']
            + findings['active_folders_with_provenance']
        )
        if provenance:
            violations = True
            self.stdout.write(self.style.WARNING(
                f'PROCEDENCIA ANÓMALA (filas activas con archived_via_folder): '
                f'{len(provenance)}',
            ))
            for row_id, label in provenance:
                self.stdout.write(f'  - #{row_id} "{label}"')

        if findings['archived_with_active_cause']:
            # Informativo, no viola el invariante: la causa se restauró sin
            # arrastrar esta fila (comportamiento normal de la cadena).
            self.stdout.write(
                f"Nota: {findings['archived_with_active_cause']} fila(s) "
                'archivadas apuntan a una carpeta causante ya activa.',
            )

        if not violations:
            self.stdout.write(self.style.SUCCESS(
                'Invariante OK: ninguna fila activa quedó bajo una carpeta archivada.',
            ))
        return findings
