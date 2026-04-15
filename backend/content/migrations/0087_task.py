# Generated manually for Task model (Kanban panel).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0086_document_folders_and_tags'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('todo', 'TO DO'),
                            ('in_progress', 'In Progress'),
                            ('blocked', 'Blocked'),
                            ('done', 'Done'),
                        ],
                        db_index=True,
                        default='todo',
                        max_length=20,
                    ),
                ),
                (
                    'priority',
                    models.CharField(
                        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                        default='medium',
                        max_length=10,
                    ),
                ),
                ('due_date', models.DateField(blank=True, null=True)),
                ('position', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'assignee',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='assigned_tasks',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'ordering': ['status', 'position', '-created_at'],
            },
        ),
    ]
