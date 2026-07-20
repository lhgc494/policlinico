from django.db import models
from django.utils import timezone
from tarifas.models import TarifaConsulta
from doctores.models import Doctor
from django.contrib.auth.models import User

###############
class TopicoCatalogo(models.Model):
    """SOLO ESTO ES NUEVO"""
    nombre = models.CharField(max_length=100)  # "Sutura", "Curación"
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=20.00)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - S/{self.precio}"

#######################################
class Consulta(models.Model):

    class EstadoConsulta(models.TextChoices):
        REGISTRADA = 'REGISTRADA', 'Registrada'
        PAGADA = 'PAGADA', 'Pagada'
        TRIAJE_PENDIENTE = 'TRIAJE_PENDIENTE', 'Triaje pendiente'
        EN_TRIAGE = 'EN_TRIAGE', 'En triaje'
        TRIAJE_COMPLETO = 'TRIAJE_COMPLETO', 'Triaje completo'
        ATENDIDA = 'ATENDIDA', 'Atendida'

    #################
    paciente = models.ForeignKey(
        'pacientes.Paciente',
        on_delete=models.PROTECT,
        related_name='consultas'
    )

    tarifa = models.ForeignKey(
        TarifaConsulta,
        on_delete=models.PROTECT
    )

    tipo_consulta = models.CharField(
        max_length=20
    )

    especialidad = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Médico asignado',
        help_text='Seleccione el médico que atenderá la consulta'
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoConsulta.choices,
        default=EstadoConsulta.REGISTRADA
    )

    fecha = models.DateTimeField(auto_now_add=True)

    # 📝 1. MOTIVO DE CONSULTA (NUEVO)
    motivo_consulta = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo de consulta',
        help_text='Síntomas y razón por la que el paciente consulta'
    )

    # 🏥 2. EXAMEN FÍSICO (RENOMBRADO: antes era 'observaciones')
    examen_fisico = models.TextField(
        blank=True,
        null=True,
        verbose_name='Examen físico',
        help_text='Hallazgos del examen físico realizado'
    )

    # 🔬 3. DIAGNÓSTICO (SE MANTIENE)
    diagnostico = models.TextField(
        blank=True,
        null=True,
        verbose_name='Diagnóstico',
        help_text='Diagnóstico principal de la consulta'
    )

    # 💊 4. TRATAMIENTO (SE MANTIENE)
    tratamiento = models.TextField(
        blank=True,
        null=True,
        verbose_name='Tratamiento',
        help_text='Plan de tratamiento indicado'
    )

    fecha_atencion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de atención',
        help_text='Fecha y hora en que se atendió la consulta'
    )

    # NUEVO CAMPO: Para identificar si es lectura de resultados
    es_lectura_resultados = models.BooleanField(
        default=False,
        verbose_name='Es lectura de resultados',
        help_text='Consulta solo para lectura de resultados de exámenes'
    )

    # Método para calcular edad al momento de la consulta
    @property
    def paciente_edad_en_consulta(self):
        """Retorna la edad del paciente en el momento de la consulta"""
        from pacientes.models import Paciente
        return self.paciente.edad

    def save(self, *args, **kwargs):
        # Copiar datos desde la tarifa SOLO al crear
        if not self.pk:
            self.tipo_consulta = self.tarifa.tipo_consulta
            self.precio = self.tarifa.precio

            # 🟢 CORREGIDO: Asignar especialidad según tipo de consulta
            if self.tarifa.tipo_consulta == 'GENERAL':
                self.especialidad = 'GENERAL'  # ← Especialidad fija para General
                self.es_lectura_resultados = False

            elif self.tarifa.tipo_consulta == 'ECOGRAFIA':
                self.especialidad = 'ECOGRAFIA'  # ← Especialidad fija para Ecografía
                self.es_lectura_resultados = False

            elif self.tarifa.tipo_consulta == 'LECTURA_RESULTADOS':
                self.especialidad = 'LECTURA_RESULTADOS'  # ← Nueva especialidad
                self.es_lectura_resultados = True

            elif self.tarifa.tipo_consulta == 'ESPECIALIDAD' and self.tarifa.especialidad:
                self.especialidad = self.tarifa.especialidad  # ← Copiar de la tarifa
                self.es_lectura_resultados = False

            else:
                self.especialidad = None  # ← Por defecto
                self.es_lectura_resultados = False

        # Si se está marcando como ATENDIDA, establecer fecha_atencion
        if self.estado == self.EstadoConsulta.ATENDIDA and not self.fecha_atencion:
            self.fecha_atencion = timezone.now()

        super().save(*args, **kwargs)

    # NUEVA PROPERTY: Para mostrar especialidad de forma amigable
    @property
    def especialidad_display(self):
        """Retorna la especialidad para mostrar"""
        if self.especialidad == 'LECTURA_RESULTADOS':
            return 'Lectura de Resultados'
        elif self.especialidad == 'GENERAL':
            return 'Medicina General'
        elif self.especialidad == 'ECOGRAFIA':
            return 'Ecografía'
        elif self.especialidad:
            # Usar choices del modelo Especialidad si existe
            try:
                from doctores.models import Especialidad
                especialidad_obj = Especialidad.objects.filter(nombre=self.especialidad).first()
                if especialidad_obj:
                    return especialidad_obj.get_nombre_display()
            except:
                pass
            # Fallback: mostrar el valor crudo
            return self.especialidad.replace('_', ' ').title()
        return 'Sin especialidad'

    # NUEVA PROPERTY: Para saber si muestra TODOS los doctores
    @property
    def muestra_todos_doctores(self):
        """Indica si para esta consulta se deben mostrar TODOS los doctores"""
        return self.especialidad == 'LECTURA_RESULTADOS'

    def __str__(self):
        tipo = "Consulta"
        if self.es_lectura_resultados:
            tipo = "Lectura de Resultados"

        return f"{tipo} #{self.id} - {self.paciente.nombres} {self.paciente.apellidos}"

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha']



###################### receta #######
class Receta(models.Model):
    """
    Receta médica - Medicamentos recetados en una consulta
    """

    class EstadoReceta(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        CANCELADA = 'CANCELADA', 'Cancelada'
        PARCIAL = 'PARCIAL', 'Parcialmente atendida'

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='recetas',
        verbose_name='Consulta'
    )

    medicamento = models.CharField(
        max_length=200,
        verbose_name='Medicamento',
        help_text='Ej: Paracetamol 500mg, Amoxicilina 250mg'
    )

    dosis = models.CharField(
        max_length=100,
        verbose_name='Dosis',
        help_text='Ej: 500mg, 1 tableta, 5ml'
    )

    frecuencia = models.CharField(
        max_length=100,
        verbose_name='Frecuencia',
        help_text='Ej: Cada 8 horas, Cada 12 horas, Una vez al día'
    )

    duracion = models.CharField(
        max_length=100,
        verbose_name='Duración',
        help_text='Ej: 7 días, 10 días, Hasta terminar'
    )

    indicaciones = models.TextField(
        blank=True,
        verbose_name='Indicaciones especiales',
        help_text='Ej: Tomar con alimentos, No manejar maquinaria'
    )

    # NUEVOS CAMPOS PARA CONTROL DE FARMACIA
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad recetada',
        help_text='Número total de unidades recetadas'
    )

    cantidad_atendida = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad atendida',
        help_text='Unidades que ya se han entregado al paciente'
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoReceta.choices,
        default=EstadoReceta.PENDIENTE,
        verbose_name='Estado'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    fecha_atencion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de atención',
        help_text='Fecha y hora en que se entregó el medicamento'
    )

    usuario_atencion = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario que atendió'
    )

    observaciones_farmacia = models.TextField(
        blank=True,
        verbose_name='Observaciones de farmacia',
        help_text='Notas sobre la dispensación del medicamento'
    )

    class Meta:
        verbose_name = 'Receta'
        verbose_name_plural = 'Recetas'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.medicamento} - {self.consulta.paciente}"

    def pendiente_por_atender(self):
        """Retorna cuántas unidades faltan por atender"""
        return self.cantidad - self.cantidad_atendida

    def puede_atender(self):
        """Verifica si se puede atender más unidades"""
        return self.estado in [self.EstadoReceta.PENDIENTE, self.EstadoReceta.PARCIAL]

    def porcentaje_atendido(self):
        """Retorna el porcentaje de atención"""
        if self.cantidad == 0:
            return 0
        return (self.cantidad_atendida / self.cantidad) * 100


#####################
class OrdenExamen(models.Model):
    """
    Orden de exámenes de laboratorio
    """
    # SOLO LABORATORIO
    TIPO_LABORATORIO = 'LABORATORIO'
    TIPOS_EXAMEN = [
        (TIPO_LABORATORIO, 'Laboratorio'),
    ]

    ESTADOS = [
        ('SOLICITADO', 'Solicitado'),
        ('EN_PROCESO', 'En proceso'),
        ('COMPLETADO', 'Completado'),
        ('ENTREGADO', 'Entregado'),
    ]

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='ordenes_examen',
        verbose_name='Consulta',
        null=True,
        blank=True
    )

    venta_ambulatoria = models.ForeignKey(
        'VentaAmbulatoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_examen',
        verbose_name='Venta Ambulatoria'
    )

    tecnico_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_examen_asignadas',
        verbose_name='Técnico asignado',
        help_text='Personal de laboratorio asignado para procesar esta orden'
    )

    tipo_examen = models.CharField(
        max_length=50,
        choices=TIPOS_EXAMEN,
        default=TIPO_LABORATORIO,
        verbose_name='Tipo de Examen'
    )

    examen_especifico = models.CharField(
        max_length=200,
        verbose_name='Examen Específico',
        help_text='Ej: Hemograma completo, Glucosa, Perfil lipídico'
    )

    indicaciones = models.TextField(
        blank=True,
        verbose_name='Indicaciones',
        help_text='Preparación especial o indicaciones para el examen'
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_asignacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de asignación',
        help_text='Fecha y hora en que se asignó a un técnico'
    )
    fecha_realizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de realización'
    )
    fecha_entrega = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de entrega'
    )

    # 📝 CAMPO EXISTENTE - Lo mantenemos para compatibilidad
    resultado = models.TextField(
        blank=True,
        verbose_name='Resultado (texto plano)'
    )

    # 🆕 NUEVO CAMPO - JSON para resultados estructurados
    resultado_json = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Resultados estructurados',
        help_text='Almacena los resultados en formato JSON para exámenes con múltiples campos'
    )

    archivo_resultado = models.FileField(
        upload_to='resultados_laboratorio/',
        null=True,
        blank=True,
        verbose_name='Archivo PDF de resultados',
        help_text='PDF con los resultados del examen'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='SOLICITADO'
    )

    # CAMPOS DE PAGO - EN UN SOLO LUGAR
    pagado = models.BooleanField(default=False, verbose_name='¿Pagado?')
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('EFECTIVO', 'Efectivo'),
            ('TARJETA', 'Tarjeta'),
            ('YAPE', 'Yape'),
            ('PLIN', 'Plin'),
        ],
        null=True,
        blank=True,
        verbose_name='Método de pago'
    )
    monto_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name='Monto Pagado'
    )
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Pago'
    )

    # Métodos esenciales para el funcionamiento del módulo

    def get_paciente_nombre(self):
        """Obtiene nombre completo del paciente"""
        if self.consulta:
            return f"{self.consulta.paciente.nombres} {self.consulta.paciente.apellidos}"
        elif self.venta_ambulatoria:
            return self.venta_ambulatoria.paciente_nombre
        return "Paciente no identificado"

    def get_paciente_dni(self):
        """Obtiene DNI del paciente"""
        if self.consulta:
            return self.consulta.paciente.dni
        elif self.venta_ambulatoria:
            return self.venta_ambulatoria.paciente_dni
        return ""

    def get_examenes_lista(self):
        """Retorna lista de exámenes para mostrar en tabla"""
        return [self.examen_especifico]

    def cambiar_estado(self, nuevo_estado, usuario=None):
        """Cambia el estado y actualiza fechas automáticamente"""
        from django.utils import timezone

        self.estado = nuevo_estado
        ahora = timezone.now()

        if nuevo_estado == 'EN_PROCESO' and not self.fecha_asignacion:
            self.fecha_asignacion = ahora
            if usuario:
                self.tecnico_asignado = usuario

        elif nuevo_estado == 'COMPLETADO' and not self.fecha_realizacion:
            self.fecha_realizacion = ahora

        elif nuevo_estado == 'ENTREGADO' and not self.fecha_entrega:
            self.fecha_entrega = ahora

        self.save()
        return True

    def get_tiempo_transcurrido(self):
        """Calcula tiempo transcurrido según estado"""
        from django.utils import timezone

        if self.estado == 'SOLICITADO':
            inicio = self.fecha_solicitud
        elif self.estado == 'EN_PROCESO':
            inicio = self.fecha_asignacion or self.fecha_solicitud
        elif self.estado == 'COMPLETADO':
            inicio = self.fecha_realizacion or self.fecha_solicitud
        else:  # ENTREGADO
            return "Entregado"

        if not inicio:
            return "Sin tiempo"

        diff = timezone.now() - inicio
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)

        if horas > 0:
            return f"{horas}h {minutos}m"
        return f"{minutos}m"

    # 🔄 NUEVO MÉTODO: Obtener resultados formateados según tipo de examen
    def get_resultados_formateados(self):
        """
        Retorna los resultados en el formato apropiado para el template
        """
        if self.resultado_json:
            return self.resultado_json
        elif self.resultado:
            # Si solo hay texto plano, lo convertimos a JSON simple
            return {'resultado': self.resultado}
        return {}

    # 🔄 NUEVO MÉTODO: Guardar resultados estructurados
    def guardar_resultados(self, datos_json, texto_plano=None):
        """
        Guarda resultados tanto en JSON como en texto plano (para compatibilidad)
        """
        self.resultado_json = datos_json
        if texto_plano:
            self.resultado = texto_plano
        elif isinstance(datos_json, dict):
            # Crear una versión texto legible
            self.resultado = "\n".join([f"{k}: {v}" for k, v in datos_json.items()])
        self.save()

    # Métodos para compatibilidad con código existente
    def asignar_a_tecnico(self, usuario_tecnico):
        """Compatibilidad con código que usa este método"""
        return self.cambiar_estado('EN_PROCESO', usuario_tecnico)

    def marcar_como_completado(self):
        """Compatibilidad con código que usa este método"""
        return self.cambiar_estado('COMPLETADO')

    def marcar_como_entregado(self):
        """Compatibilidad con código que usa este método"""
        return self.cambiar_estado('ENTREGADO')

    # Property para compatibilidad si alguna vista usa 'orden.tecnico'
    @property
    def tecnico(self):
        """Alias para compatibilidad con vistas existentes"""
        return self.tecnico_asignado

    @tecnico.setter
    def tecnico(self, value):
        """Setter para compatibilidad"""
        self.tecnico_asignado = value

    def __str__(self):
        return f"Orden #{self.id} - {self.get_paciente_nombre()} - {self.examen_especifico}"

    class Meta:
        verbose_name = 'Orden de Examen'
        verbose_name_plural = 'Órdenes de Examen'
        ordering = ['-fecha_solicitud']



##############

class CatalogoExamen(models.Model):
    """
    Catálogo de exámenes con precios configurados por administrador
    Para exámenes de laboratorio, ecografías, rayos X, etc.
    """
    TIPOS_EXAMEN = [
        ('LABORATORIO', 'Laboratorio'),
        ('ECOGRAFIA', 'Ecografía'),
        ('RAYOS_X', 'Rayos X'),
        ('TOMOGRAFIA', 'Tomografía'),
        ('RESONANCIA', 'Resonancia Magnética'),
        ('ELECTROCARDIOGRAMA', 'Electrocardiograma'),
        ('OTRO', 'Otro'),
    ]

    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Examen',
        help_text='Ej: Hemograma completo, Ecografía abdominal, Radiografía de tórax'
    )

    tipo = models.CharField(
        max_length=50,
        choices=TIPOS_EXAMEN,
        default='LABORATORIO',
        verbose_name='Tipo de Examen'
    )

    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Precio (S/)',
        help_text='Precio en soles'
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del examen'
    )

    tiempo_entrega = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tiempo de Entrega',
        help_text='Ej: 24 horas, 48 horas, Inmediato'
    )

    preparacion = models.TextField(
        blank=True,
        verbose_name='Preparación Requerida',
        help_text='Instrucciones de preparación para el paciente'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='¿Este examen está disponible para la venta?'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Examen del Catálogo'
        verbose_name_plural = 'Catálogo de Exámenes'
        ordering = ['tipo', 'nombre']
        indexes = [
            models.Index(fields=['tipo', 'activo']),
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return f"{self.nombre} - S/ {self.precio}"

    @property
    def precio_formateado(self):
        """Retorna el precio formateado como string"""
        return f"S/ {self.precio:,.2f}"

    @property
    def es_laboratorio(self):
        """Verifica si es un examen de laboratorio"""
        return self.tipo == 'LABORATORIO'

####################
class VentaAmbulatoria(models.Model):
    """
    Venta de exámenes ambulatorios (pacientes externos)
    """
    paciente_dni = models.CharField(max_length=15, verbose_name='DNI del Paciente')
    paciente_nombre = models.CharField(max_length=200, verbose_name='Nombre del Paciente')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total (S/)')

    # ✅ NUEVO CAMPO
    descuento_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Descuento Aplicado (S/)'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Usuario que registró')

    class Meta:
        verbose_name = 'Venta Ambulatoria'
        verbose_name_plural = 'Ventas Ambulatorias'
        ordering = ['-fecha_creacion']

    def __str__(self):
        descuento_text = f" (-S/{self.descuento_aplicado})" if self.descuento_aplicado > 0 else ""
        return f"Venta #{self.id} - {self.paciente_nombre} - S/ {self.total}{descuento_text}"

    @property
    def subtotal(self):
        """Retorna el total sin descuento (total + descuento)"""
        from decimal import Decimal
        try:
            # Asegurarse de que los valores sean Decimal
            total_decimal = Decimal(str(self.total))
            descuento_decimal = Decimal(str(self.descuento_aplicado))
            return total_decimal + descuento_decimal
        except:
            # Si hay error, retornar solo el total
            return Decimal(str(self.total))


########################
class CatalogoEcografia(models.Model):
    """
    Catálogo específico para ecografías
    - Nombre: ingresado manualmente
    - Tipo: siempre "ECOGRAFIA" (fijo)
    - Precio: ingresado manualmente
    - Activo: checkbox
    - Fechas: automáticas
    """
    
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Ecografía',
        help_text='Ej: Ecografía Abdominal, Ecografía Obstétrica, Ecografía Pélvica'
    )
    
    # Campo tipo será fijo - no se mostrará en el formulario
    # pero lo guardamos por si necesitamos diferenciar después
    TIPO_ECOGRAFIA = 'ECOGRAFIA'
    
    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Precio (S/)',
        help_text='Precio en soles'
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='¿Esta ecografía está disponible?'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ecografía del Catálogo'
        verbose_name_plural = 'Catálogo de Ecografías'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - S/ {self.precio}"
    
    @property
    def precio_formateado(self):
        """Retorna el precio formateado como string"""
        return f"S/ {self.precio:,.2f}"
    
    @property
    def tipo(self):
        """Siempre retorna 'ECOGRAFIA'"""
        return 'ECOGRAFIA'
