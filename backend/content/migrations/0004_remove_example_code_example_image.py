# Generated by Django 5.0.6 on 2024-06-13 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_example_title_en_example_title_es'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='example',
            name='code',
        ),
        migrations.AddField(
            model_name='example',
            name='image',
            field=models.ImageField(default=1, upload_to='components/examples/'),
            preserve_default=False,
        ),
    ]