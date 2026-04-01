# Generated manually for collection accounts platform

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_document_types_and_backfill(apps, schema_editor):
    DocumentType = apps.get_model('content', 'DocumentType')
    Document = apps.get_model('content', 'Document')
    IssuerProfile = apps.get_model('content', 'IssuerProfile')

    md, _ = DocumentType.objects.get_or_create(
        code='markdown',
        defaults={
            'name': 'Markdown document',
            'description': 'Editorial markdown content for PDF generation.',
            'is_active': True,
        },
    )
    DocumentType.objects.get_or_create(
        code='collection_account',
        defaults={
            'name': 'Collection account',
            'description': 'Commercial collection account with line items.',
            'is_active': True,
        },
    )
    IssuerProfile.objects.get_or_create(
        name='ProjectApp',
        defaults={
            'legal_name': 'ProjectApp',
            'public_number_prefix': 'PA',
        },
    )
    Document.objects.filter(document_type__isnull=True).update(document_type_id=md.id)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0014_theme_customization_fields'),
        ('content', '0051_add_cover_flags_to_document'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(db_index=True, max_length=64, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='IssuerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('legal_name', models.CharField(blank=True, default='', max_length=255)),
                ('identification_type', models.CharField(blank=True, default='', max_length=32)),
                ('identification_number', models.CharField(blank=True, default='', max_length=64)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('phone', models.CharField(blank=True, default='', max_length=64)),
                ('address', models.CharField(blank=True, default='', max_length=512)),
                ('city', models.CharField(blank=True, default='', max_length=128)),
                ('country', models.CharField(blank=True, default='CO', max_length=2)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='issuer_logos/')),
                ('public_number_prefix', models.CharField(default='PA', help_text='Prefix for public document numbers, e.g. PA-2026-004.', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='DocumentNumberSequence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveIntegerField()),
                ('last_value', models.PositiveIntegerField(default=0)),
                ('issuer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='number_sequences', to='content.issuerprofile')),
            ],
        ),
        migrations.AddConstraint(
            model_name='documentnumbersequence',
            constraint=models.UniqueConstraint(fields=('issuer', 'year'), name='uniq_document_number_sequence_issuer_year'),
        ),
        migrations.AddField(
            model_name='document',
            name='city',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='document',
            name='client_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='commercial_status',
            field=models.CharField(blank=True, choices=[('draft', 'Draft'), ('issued', 'Issued'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='currency',
            field=models.CharField(default='COP', max_length=3),
        ),
        migrations.AddField(
            model_name='document',
            name='discount_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='document',
            name='document_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='documents', to='content.documenttype'),
        ),
        migrations.AddField(
            model_name='document',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='issue_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='issuer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='content.issuerprofile'),
        ),
        migrations.AddField(
            model_name='document',
            name='metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='document',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='document',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='accounts.project'),
        ),
        migrations.AddField(
            model_name='document',
            name='public_number',
            field=models.CharField(blank=True, db_index=True, default='', help_text='Human-visible consecutive number, e.g. PA-2026-004.', max_length=64),
        ),
        migrations.AddField(
            model_name='document',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='document',
            name='tax_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='document',
            name='template_version',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='document',
            name='terms_and_conditions',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='document',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='document',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='DocumentCollectionAccount',
            fields=[
                ('billing_concept', models.CharField(blank=True, default='', max_length=512)),
                ('payment_term_type', models.CharField(choices=[('against_delivery', 'Against delivery'), ('fixed_date', 'Fixed date'), ('days_after_issue', 'Days after issue')], default='days_after_issue', max_length=32)),
                ('payment_term_days', models.PositiveIntegerField(blank=True, null=True)),
                ('payer_name', models.CharField(blank=True, default='', max_length=255)),
                ('payer_identification', models.CharField(blank=True, default='', max_length=64)),
                ('payer_identification_type', models.CharField(blank=True, default='', max_length=32)),
                ('payer_address', models.CharField(blank=True, default='', max_length=512)),
                ('payer_phone', models.CharField(blank=True, default='', max_length=64)),
                ('payer_email', models.EmailField(blank=True, default='', max_length=254)),
                ('customer_name', models.CharField(blank=True, default='', max_length=255)),
                ('customer_identification', models.CharField(blank=True, default='', max_length=64)),
                ('customer_identification_type', models.CharField(blank=True, default='', max_length=32)),
                ('customer_contact_name', models.CharField(blank=True, default='', max_length=255)),
                ('customer_email', models.EmailField(blank=True, default='', max_length=254)),
                ('customer_address', models.CharField(blank=True, default='', max_length=512)),
                ('observations', models.TextField(blank=True, default='')),
                ('support_reference', models.CharField(blank=True, default='', max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='collection_account', serialize=False, to='content.document')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0)),
                ('item_type', models.CharField(choices=[('service', 'Service'), ('hosting', 'Hosting'), ('support', 'Support'), ('advance', 'Advance'), ('balance', 'Balance'), ('adjustment', 'Adjustment'), ('other', 'Other')], default='service', max_length=32)),
                ('description', models.CharField(max_length=1024)),
                ('quantity', models.DecimalField(decimal_places=4, default=1, max_digits=14)),
                ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('line_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('period_start', models.DateField(blank=True, null=True)),
                ('period_end', models.DateField(blank=True, null=True)),
                ('reference_type', models.CharField(blank=True, default='', max_length=64)),
                ('reference_id', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='content.document')),
            ],
            options={
                'ordering': ['document_id', 'position', 'id'],
            },
        ),
        migrations.CreateModel(
            name='DocumentPaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_method_type', models.CharField(choices=[('bank_transfer', 'Bank transfer'), ('nequi', 'Nequi'), ('daviplata', 'Daviplata'), ('wompi', 'Wompi'), ('cash', 'Cash'), ('other', 'Other')], default='bank_transfer', max_length=32)),
                ('bank_name', models.CharField(blank=True, default='', max_length=128)),
                ('account_type', models.CharField(blank=True, default='', max_length=32)),
                ('account_number', models.CharField(blank=True, default='', max_length=64)),
                ('account_holder_name', models.CharField(blank=True, default='', max_length=255)),
                ('account_holder_identification', models.CharField(blank=True, default='', max_length=64)),
                ('payment_instructions', models.TextField(blank=True, default='')),
                ('is_primary', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to='content.document')),
            ],
            options={
                'ordering': ['-is_primary', 'id'],
            },
        ),
        migrations.RunPython(seed_document_types_and_backfill, migrations.RunPython.noop),
    ]
