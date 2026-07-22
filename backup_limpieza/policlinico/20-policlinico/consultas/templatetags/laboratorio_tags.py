from django import template

register = template.Library()

@register.simple_tag
def obtener_nombre_paciente(orden):
    """Obtiene el nombre del paciente según el tipo de orden"""
    if orden.consulta:
        return f"{orden.consulta.paciente.nombres} {orden.consulta.paciente.apellidos}"
    elif hasattr(orden, 'venta_ambulatoria') and orden.venta_ambulatoria:
        return orden.venta_ambulatoria.paciente_nombre
    return "Paciente no disponible"

@register.simple_tag
def obtener_dni_paciente(orden):
    """Obtiene el DNI del paciente según el tipo de orden"""
    if orden.consulta:
        return orden.consulta.paciente.dni
    elif hasattr(orden, 'venta_ambulatoria') and orden.venta_ambulatoria:
        return orden.venta_ambulatoria.paciente_dni
    return "No disponible"

@register.simple_tag
def es_ambulatorio(orden):
    """Determina si es una orden ambulatoria"""
    return orden.consulta is None and hasattr(orden, 'venta_ambulatoria') and orden.venta_ambulatoria
