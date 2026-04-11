from django import template

from content.utils import format_bogota_date, format_bogota_datetime

register = template.Library()


@register.filter
def bogota_date(value):
    """Format a datetime as '8 de abril, 2026' in Bogotá timezone."""
    return format_bogota_date(value)


@register.filter
def bogota_datetime(value):
    """Format a datetime as '8 de abril, 2026 — 14:30' in Bogotá timezone."""
    return format_bogota_datetime(value)
