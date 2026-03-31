from django.db import models


class IssuerProfile(models.Model):
    """Legal entity that issues commercial documents (e.g. ProjectApp)."""

    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True, default='')
    identification_type = models.CharField(max_length=32, blank=True, default='')
    identification_number = models.CharField(max_length=64, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=64, blank=True, default='')
    address = models.CharField(max_length=512, blank=True, default='')
    city = models.CharField(max_length=128, blank=True, default='')
    country = models.CharField(max_length=2, blank=True, default='CO')
    logo = models.ImageField(upload_to='issuer_logos/', null=True, blank=True)
    public_number_prefix = models.CharField(
        max_length=16,
        default='PA',
        help_text='Prefix for public document numbers, e.g. PA-2026-004.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name
