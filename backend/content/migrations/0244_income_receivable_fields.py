from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0243_merge_mcp_financing'),
    ]

    operations = [
        migrations.AddField(
            model_name='incomerecord',
            name='collection_confidence',
            field=models.CharField(
                blank=True,
                choices=[
                    ('high', 'Cobro muy probable'),
                    ('medium', 'Cobro incierto (50/50)'),
                    ('low', 'Alto riesgo de pérdida'),
                ],
                default='',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='incomerecord',
            name='is_receivable_candidate',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='incomerecord',
            index=models.Index(
                fields=[
                    'ledger', 'kind', 'is_receivable_candidate',
                    'collection_confidence',
                ],
                name='income_receivable_lookup_idx',
            ),
        ),
        migrations.AddConstraint(
            model_name='incomerecord',
            constraint=models.CheckConstraint(
                condition=(
                    Q(is_receivable_candidate=False)
                    | Q(kind='expected', ledger='company')
                ),
                name='income_candidate_expected_company',
            ),
        ),
    ]
