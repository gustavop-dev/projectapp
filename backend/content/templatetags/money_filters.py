from django import template

from content.utils import format_cop_email

register = template.Library()


@register.filter
def cop(value):
    """1490000 → 1'490.000 (sin '$'; el template lo antepone)."""
    return format_cop_email(value)
