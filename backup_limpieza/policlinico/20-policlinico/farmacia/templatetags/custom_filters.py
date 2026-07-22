# farmacia/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def absolute(value):
    """Devuelve el valor absoluto de un número"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        try:
            return int(value) * int(arg)
        except (ValueError, TypeError):
            return 0

@register.filter(name='format_currency')
def format_currency(value):
    """Formatea un número como moneda"""
    try:
        return f"S/ {float(value):,.2f}"
    except (ValueError, TypeError):
        return "S/ 0.00"
