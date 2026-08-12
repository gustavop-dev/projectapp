"""Une las dos ramas 0186 del grafo de migraciones.

Dos olas de trabajo numeraron su migración 0186 en paralelo: la reparación de
elementos activos sepultados bajo carpetas archivadas (gestor de documentos) y
la relación cliente/proyecto de contabilidad. Ambas cuelgan de 0185, así que el
grafo quedó con dos hojas y `migrate` se niega a avanzar.

Es una migración vacía a propósito: no toca el esquema ni los datos, sólo
reunifica el grafo. La alternativa —re-apuntar la reparación del archivo para
que dependa de la de contabilidad— rompería producción, donde la primera ya
está aplicada y la segunda no: `check_consistent_history` levantaría
`InconsistentMigrationHistory` por una migración aplicada antes que su
dependencia.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0186_accounting_project_relation'),
        ('content', '0186_repair_active_rows_under_archived_folders'),
    ]

    operations = [
    ]
