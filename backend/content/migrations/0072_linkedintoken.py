from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0071_add_linkedin_fields_to_blogpost'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkedInToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token_encrypted', models.TextField(blank=True, default='', help_text='Fernet-encrypted LinkedIn access token.')),
                ('refresh_token_encrypted', models.TextField(blank=True, default='', help_text='Fernet-encrypted LinkedIn refresh token.')),
                ('expires_at', models.DateTimeField(blank=True, help_text='When the access token expires.', null=True)),
                ('refresh_token_expires_at', models.DateTimeField(blank=True, help_text='When the refresh token expires (typically 60 days).', null=True)),
                ('member_sub', models.CharField(blank=True, default='', help_text='LinkedIn member "sub" claim (used to build urn:li:person:XXX).', max_length=100)),
                ('profile_name', models.CharField(blank=True, default='', max_length=255)),
                ('profile_picture', models.URLField(blank=True, default='', max_length=500)),
                ('profile_email', models.EmailField(blank=True, default='', max_length=254)),
                ('obtained_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'LinkedIn Token',
                'verbose_name_plural': 'LinkedIn Tokens',
            },
        ),
    ]
