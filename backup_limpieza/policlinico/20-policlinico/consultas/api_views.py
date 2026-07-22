from django.http import JsonResponse
from doctores.models import Doctor
from tarifas.models import TarifaConsulta

def doctores_por_especialidad(request):
    """
    API que devuelve doctores filtrados por especialidad
    Uso: /api/doctores/?especialidad=GENERAL
    """
    especialidad = request.GET.get('especialidad', '')
    
    doctores = Doctor.objects.filter(activo=True)
    
    if especialidad:
        doctores = doctores.filter(especialidad__nombre=especialidad)
    
    # Ordenar por apellidos
    doctores = doctores.order_by('apellidos', 'nombres')
    
    # Preparar datos para JSON
    data = [
        {
            'id': d.id,
            'nombre_completo': f"{d.nombres} {d.apellidos}",
            'especialidad': d.especialidad.get_nombre_display(),
            'especialidad_codigo': d.especialidad.nombre,
        }
        for d in doctores
    ]
    
    return JsonResponse(data, safe=False)


def tarifa_detalle(request, tarifa_id):
    """
    API que devuelve detalles de una tarifa
    Uso: /api/tarifa/1/
    """
    try:
        tarifa = TarifaConsulta.objects.get(id=tarifa_id, activo=True)

        data = {
            'id': tarifa.id,
            'tipo_consulta': tarifa.tipo_consulta,
            'especialidad': tarifa.especialidad or '',
            'precio': str(tarifa.precio),
            'tipo_consulta_display': tarifa.get_tipo_consulta_display(),
            'especialidad_display': tarifa.get_especialidad_display() if tarifa.especialidad else '',
        }

        return JsonResponse(data)
    except TarifaConsulta.DoesNotExist:
        return JsonResponse({'error': 'Tarifa no encontrada'}, status=404)
