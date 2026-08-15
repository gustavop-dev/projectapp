from django.db import models


class EmailBody(models.Model):
    """
    The message as it went out, stored once per send.

    An accounting notice reaches every configured recipient, and each one
    gets its own ``EmailLog`` row; they all point at the same body instead of
    each carrying a copy of the same HTML.
    """

    html = models.TextField(blank=True, default='')
    text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Email Body'
        verbose_name_plural = 'Email Bodies'

    def __str__(self):
        return f'EmailBody #{self.pk} ({len(self.html)} chars)'
