from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from .models import OrdenPago
from .forms import RegistrarPagoForm
from consultas.models import Consulta
from triaje.models import Triaje
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.contrib import messages  # 👈 ESTA LÍNEA ES LA QUE FALTA
from .models import OrdenPago
from consultas.models import Consulta
from triaje.models import Triaje
from .forms import RegistrarPagoForm

##############################
def detalle_orden_pago(request, orden_id):
    orden = get_object_or_404(OrdenPago, id=orden_id)
    consulta = orden.consulta

    # 🚫 Si ya está pagada, solo mostrar
    if orden.estado == OrdenPago.EstadoPago.PAGADO:
        return render(request, 'pagos/detalle_orden_pago.html', {
            'orden': orden,
            'pagada': True
        })

    if request.method == 'POST':
        form = RegistrarPagoForm(request.POST, instance=orden)
        if form.is_valid():
            orden = form.save(commit=False)
            orden.estado = OrdenPago.EstadoPago.PAGADO
            orden.fecha_pago = now()
            orden.save()

            # ✅ Actualizar estado de la consulta
            consulta = orden.consulta

            # ========================================
            # 🎯 COMPORTAMIENTO SEGÚN TIPO DE CONSULTA
            # ========================================

            if consulta.tipo_consulta == 'TOPICO':
                # ✅ TÓPICO: No necesita triaje, va directo a completado
                consulta.estado = Consulta.EstadoConsulta.ATENDIDA
                consulta.save()
                messages.success(request, '✅ Pago registrado. Tópico completado.')

                # 👈 REDIRIGIR DE VUELTA A LA ORDEN PAGADA
                return redirect('detalle_orden_pago', orden.id)

            else:
                # ✅ OTROS: Van a triaje
                consulta.estado = Consulta.EstadoConsulta.TRIAJE_PENDIENTE
                consulta.save()

                # ✅ Crear triaje inicial SOLO si no existe (vacío)
                Triaje.objects.get_or_create(consulta=consulta)

                messages.success(request, '✅ Pago registrado. Derive a triaje.')

                # 👈 REDIRIGIR DE VUELTA A LA ORDEN PAGADA
                return redirect('detalle_orden_pago', orden.id)
    else:
        form = RegistrarPagoForm(instance=orden)

    return render(request, 'pagos/detalle_orden_pago.html', {
        'orden': orden,
        'form': form
    })
##############################
# /home/luis/policlinico/pagos/views.py
# Agregar esta función al final

def ticket_pago(request, orden_id):
    from django.shortcuts import get_object_or_404, render
    from django.utils import timezone
    from .models import OrdenPago
    
    orden = get_object_or_404(OrdenPago, id=orden_id)
    consulta = orden.consulta
    
    context = {
        'orden': orden,
        'consulta': consulta,
        'paciente': consulta.paciente,
        'fecha': timezone.now(),
        'usuario': request.user,
    }
    
    return render(request, 'pagos/ticket_pago.html', context)

############

# /home/luis/policlinico/pagos/views.py

def ticket_termico(request, orden_id):
    from django.shortcuts import get_object_or_404, render
    from django.utils import timezone
    from .models import OrdenPago

    orden = get_object_or_404(OrdenPago, id=orden_id)
    consulta = orden.consulta

    # ✅ DEBUG: Verificar que los datos existen
    print("="*50)
    print(f"🎫 TICKET TÉRMICO - Orden #{orden.id}")
    print(f"   Paciente: {consulta.paciente.nombres} {consulta.paciente.apellidos}")
    print(f"   Tipo: {consulta.tipo_consulta}")
    print(f"   Monto: {orden.monto}")
    print(f"   Método pago: {orden.metodo_pago}")
    print("="*50)

    context = {
        'orden': orden,
        'consulta': consulta,
        'paciente': consulta.paciente,
        'fecha': timezone.now(),
        'usuario': request.user,
    }

    return render(request, 'pagos/ticket_termico.html', context)
