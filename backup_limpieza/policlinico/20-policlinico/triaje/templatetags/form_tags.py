from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """Añade clase CSS a un campo de formulario"""
    return field.as_widget(attrs={"class": css})
