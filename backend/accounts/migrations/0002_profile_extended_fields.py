from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cedula',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(
                blank=True,
                choices=[
                    ('male', 'Masculino'),
                    ('female', 'Femenino'),
                    ('other', 'Otro'),
                    ('prefer_not_to_say', 'Prefiero no decir'),
                ],
                default='',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='education_level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('primaria', 'Primaria'),
                    ('secundaria', 'Secundaria'),
                    ('tecnico', 'Técnico'),
                    ('universitario', 'Universitario'),
                    ('posgrado', 'Posgrado'),
                    ('otro', 'Otro'),
                ],
                default='',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(
                blank=True,
                help_text='Optimized automatically on upload.',
                null=True,
                upload_to='avatars/',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_completed',
            field=models.BooleanField(
                default=False,
                help_text='True after the client fills in their profile details.',
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='avatar_url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='Deprecated — use avatar ImageField instead.',
                max_length=500,
            ),
        ),
    ]
