from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from .models import OrdenPago
from .forms import RegistrarPagoForm
from consultas.models import Consulta
from triaje.models import Triaje


def detalle_orden_pago(request, orden_id):
    orden = get_object_or_404(OrdenPago, id=orden_id)

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
            consulta.estado = Consulta.EstadoConsulta.TRIAJE_PENDIENTE
            consulta.save()

            # ✅ Crear triaje inicial SOLO si no existe (vacío)
            Triaje.objects.get_or_create(consulta=consulta)

            return redirect('lista_triaje_pendiente')
    else:
        form = RegistrarPagoForm(instance=orden)

    return render(request, 'pagos/detalle_orden_pago.html', {
        'orden': orden,
        'form': form
    })

