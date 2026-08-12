"""Devuelve a la vista los elementos activos sepultados bajo una carpeta archivada.

Los produjo restaurar un documento suelto cuya carpeta seguía archivada:
`unarchive_document` no comprobaba el contenedor, así que el documento quedaba
activo dentro de una carpeta archivada y no salía en ninguna de las dos vistas
del panel — ni en Archivados (no está archivado) ni en el árbol (su carpeta no
se lista). Un documento perdido.

Se reabre la cadena de carpetas contenedoras, no el resto de su contenido: lo
que estaba archivado a propósito sigue archivado, y la carpeta queda con
contenido mixto, que es el estado que la UI ahora señaliza.

Con un ciclo en `parent` la migración desarchiva lo que encuentra y NUNCA
desengancha. Es una asimetría deliberada con el servicio: aquel corre
interactivo y reporta `moved_to_root` en la respuesta, mientras que esto corre
desatendido contra producción, donde re-parentar filas en silencio es peor que
dejar intacto un ciclo raro.

La lógica va inline con `apps.get_model` a propósito: una migración no debe
importar el servicio, tiene que sobrevivir a los refactors futuros del runtime.
"""
from django.db import migrations


def repair_unreachable_rows(apps, schema_editor):
    DocumentFolder = apps.get_model('content', 'DocumentFolder')
    Document = apps.get_model('content', 'Document')
    db_alias = schema_editor.connection.alias

    # El árbol entero en memoria: son decenas de filas y así se evita una
    # query por ancestro.
    tree = {
        pk: (parent_id, is_archived)
        for pk, parent_id, is_archived in DocumentFolder.objects.using(db_alias)
        .values_list('id', 'parent_id', 'is_archived')
    }

    def archived_ancestors(folder_id):
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

    to_restore = set()
    for folder_id in (
        Document.objects.using(db_alias)
        .filter(is_archived=False, folder__isnull=False)
        .values_list('folder_id', flat=True)
    ):
        to_restore.update(archived_ancestors(folder_id))

    for parent_id in (
        DocumentFolder.objects.using(db_alias)
        .filter(is_archived=False, parent__isnull=False)
        .values_list('parent_id', flat=True)
    ):
        to_restore.update(archived_ancestors(parent_id))

    if to_restore:
        DocumentFolder.objects.using(db_alias).filter(pk__in=to_restore).update(
            is_archived=False, archived_at=None, archived_via_folder=None,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0185_payment_calendar_reminders'),
    ]

    operations = [
        migrations.RunPython(repair_unreachable_rows, migrations.RunPython.noop),
    ]
