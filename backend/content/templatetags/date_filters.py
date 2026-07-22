from django import template

from content.utils import format_bogota_date, format_bogota_datetime

register = template.Library()


@register.filter
def bogota_date(value):
    """Format a datetime as 'Jue, 16 jul 2026' in Bogotá timezone."""
    return format_bogota_date(value)


@register.filter
def bogota_datetime(value):
    """Format a datetime as 'Lun, 3 ago 2026, 15:20' in Bogotá timezone."""
    return format_bogota_datetime(value)
