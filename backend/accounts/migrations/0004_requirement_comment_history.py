import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0003_project'),
    ]

    operations = [
        migrations.CreateModel(
            name='Requirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('description', models.TextField(blank=True, default='')),
                ('status', models.CharField(
                    choices=[
                        ('backlog', 'Backlog'),
                        ('todo', 'To do'),
                        ('in_progress', 'In progress'),
                        ('in_review', 'In review'),
                        ('approval', 'Aprobación'),
                        ('done', 'Done'),
                    ],
                    default='backlog',
                    max_length=20,
                )),
                ('priority', models.CharField(
                    choices=[
                        ('critical', 'Crítica'),
                        ('high', 'Alta'),
                        ('medium', 'Media'),
                        ('low', 'Baja'),
                    ],
                    default='medium',
                    max_length=20,
                )),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True)),
                ('module', models.CharField(blank=True, default='', max_length=100)),
                ('order', models.PositiveIntegerField(default=0, help_text='Sort order within the column.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='requirements',
                    to='accounts.project',
                )),
            ],
            options={
                'ordering': ['order', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RequirementComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('is_internal', models.BooleanField(default=False, help_text='Internal comments are visible only to admins.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('requirement', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='accounts.requirement',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='requirement_comments',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='RequirementHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_status', models.CharField(
                    choices=[
                        ('backlog', 'Backlog'),
                        ('todo', 'To do'),
                        ('in_progress', 'In progress'),
                        ('in_review', 'In review'),
                        ('approval', 'Aprobación'),
                        ('done', 'Done'),
                    ],
                    max_length=20,
                )),
                ('to_status', models.CharField(
                    choices=[
                        ('backlog', 'Backlog'),
                        ('todo', 'To do'),
                        ('in_progress', 'In progress'),
                        ('in_review', 'In review'),
                        ('approval', 'Aprobación'),
                        ('done', 'Done'),
                    ],
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
                ('requirement', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='history',
                    to='accounts.requirement',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
