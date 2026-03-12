from django.urls import path
from . import views

urlpatterns = [
    path('mis-consultas/', views.lista_consultas, name='doctor_consultas'),
    path('atender-consulta/<int:consulta_id>/', views.atender_consulta, name='atender_consulta'),
    path('buscar-historial/', views.buscar_historial, name='buscar_historial'),
    path('historial-paciente/<int:paciente_id>/', views.historial_paciente, name='historial_paciente'),
    path('editar-receta/<int:receta_id>/', views.editar_receta, name='editar_receta'),  # ← NUEVA
    path('eliminar-receta/<int:receta_id>/', views.eliminar_receta, name='eliminar_receta'),
    path('editar-orden-examen/<int:orden_id>/', views.editar_orden_examen, name='editar_orden_examen'),
    path('eliminar-orden-examen/<int:orden_id>/', views.eliminar_orden_examen, name='eliminar_orden_examen'),
    path('buscar-medicamentos/', views.buscar_medicamentos_ajax, name='buscar_medicamentos'),
    path('eliminar-temporal/', views.eliminar_item_temporal, name='eliminar_temporal'),
    path('limpiar-temporales/', views.limpiar_temporales, name='limpiar_temporales'),
    path('agregar-receta-temp-ajax/', views.agregar_receta_temp_ajax, name='agregar_receta_temp_ajax'),
    path('agregar-lab-temp-ajax/', views.agregar_lab_temp_ajax, name='agregar_lab_temp_ajax'),
    path('agregar-eco-temp-ajax/', views.agregar_eco_temp_ajax, name='agregar_eco_temp_ajax'),
    path('imprimir-recetas/<int:consulta_id>/', views.imprimir_recetas, name='imprimir_recetas'),
    path('imprimir-laboratorio/<int:consulta_id>/', views.imprimir_laboratorio, name='imprimir_laboratorio'),
    path('imprimir-ecografias/<int:consulta_id>/', views.imprimir_ecografias, name='imprimir_ecografias'),
    path('exportar-historial-pdf/<int:paciente_id>/', views.exportar_historial_pdf, name='exportar_historial_pdf'),
    path('buscar-examenes-laboratorio/', views.buscar_examenes_laboratorio_ajax, name='buscar_examenes_laboratorio'),
    path('buscar-ecografias/', views.buscar_ecografias_ajax, name='buscar_ecografias'),
    path('consulta/<int:consulta_id>/guardar-diagnostico-ajax/',views.guardar_diagnostico_tratamiento_ajax,name='guardar_diagnostico_ajax'),
    path('ver-resultado-examen/<int:examen_id>/', views.ver_resultado_examen, name='ver_resultado_examen'),
    ]
