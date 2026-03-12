from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notificacion

@login_required
def notificaciones_recientes(request):
    """
    API endpoint para obtener notificaciones no leídas del usuario actual
    """
    # Obtener las últimas 10 notificaciones no leídas
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-fecha_creacion')[:10]
    
    # Preparar datos para JSON
    data = []
    for n in notificaciones:
        data.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'tipo_usuario': n.tipo_usuario,
            'elemento_id': n.elemento_id,
            'fecha': n.fecha_creacion.strftime('%H:%M'),
            'fecha_completa': n.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        })
    
    return JsonResponse({
        'cantidad': len(data),
        'notificaciones': data
    })

@login_required
def marcar_como_leida(request, notificacion_id):
    """
    Marca una notificación como leída
    """
    notificacion = get_object_or_404(
        Notificacion, 
        id=notificacion_id, 
        usuario=request.user
    )
    
    notificacion.leida = True
    notificacion.save(update_fields=['leida'])
    
    return JsonResponse({
        'status': 'ok',
        'mensaje': 'Notificación marcada como leída'
    })

@login_required
def marcar_todas_leidas(request):
    """
    Marca todas las notificaciones del usuario como leídas
    """
    Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).update(leida=True)
    
    return JsonResponse({
        'status': 'ok',
        'mensaje': 'Todas las notificaciones marcadas como leídas'
    })

@login_required
def historial_notificaciones(request):
    """
    API endpoint para obtener historial de notificaciones (leídas y no leídas)
    """
    pagina = int(request.GET.get('pagina', 1))
    por_pagina = 20
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    
    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[inicio:fin]
    
    total = Notificacion.objects.filter(usuario=request.user).count()
    
    data = [{
        'id': n.id,
        'titulo': n.titulo,
        'mensaje': n.mensaje,
        'tipo': n.tipo,
        'leida': n.leida,
        'fecha': n.fecha_creacion.strftime('%d/%m/%Y %H:%M')
    } for n in notificaciones]
    
    return JsonResponse({
        'pagina': pagina,
        'total_paginas': (total + por_pagina - 1) // por_pagina,
        'total': total,
        'notificaciones': data
    })
