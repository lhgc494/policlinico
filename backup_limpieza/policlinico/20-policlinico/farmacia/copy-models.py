from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime
from django.core.validators import MinValueValidator, MaxValueValidator
#from .models import Medicamento, Proveedor, Categoria, Presentacion, VentaDirecta

# ==============================================
# MODELOS BÁSICOS
# ==============================================

class Categoria(models.Model):
    """Categorías de medicamentos"""
    nombre = models.CharField(
        max_length=100, 
        verbose_name='Nombre',
        unique=True,
        help_text='Nombre de la categoría (Analgésicos, Antibióticos, etc.)'
    )
    descripcion = models.TextField(
        verbose_name='Descripción', 
        blank=True, 
        null=True,
        help_text='Descripción de la categoría'
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name='Color',
        help_text='Color para identificar la categoría (hexadecimal)'
    )
    icono = models.CharField(
        max_length=50,
        default='fas fa-pills',
        verbose_name='Ícono',
        help_text='Clase de FontAwesome para el ícono'
    )
    activa = models.BooleanField(
        default=True, 
        verbose_name='¿Activa?',
        help_text='Indica si la categoría está disponible'
    )
    orden = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización'
    )
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']
        db_table = 'farmacia_categoria'  # Nombre singular
    
    def __str__(self):
        return self.nombre
    
    def medicamentos_count(self):
        return self.medicamento_set.filter(activo=True).count()
    
    medicamentos_count.short_description = 'Medicamentos Activos'
    
    @property
    def descripcion_corta(self):
        if self.descripcion and len(self.descripcion) > 60:
            return self.descripcion[:60] + '...'
        return self.descripcion or 'Sin descripción'


class Presentacion(models.Model):
    """Presentaciones de medicamentos"""
    nombre = models.CharField(
        max_length=100, 
        verbose_name='Nombre',
        unique=True,
        help_text='Nombre de la presentación'
    )
    abreviatura = models.CharField(
        max_length=10, 
        verbose_name='Abreviatura',
        blank=True, 
        null=True,
        help_text='Abreviatura (TAB, CAP, JAR, etc.)'
    )
    descripcion = models.TextField(
        verbose_name='Descripción', 
        blank=True, 
        null=True,
        help_text='Descripción de la presentación'
    )
    unidad_medida = models.CharField(
        max_length=20,
        default='unidades',
        verbose_name='Unidad de Medida',
        help_text='Ej: tabletas, ml, gramos, etc.'
    )
    activa = models.BooleanField(
        default=True, 
        verbose_name='¿Activa?',
        help_text='Indica si la presentación está disponible'
    )
    
    class Meta:
        verbose_name = 'Presentación'
        verbose_name_plural = 'Presentaciones'
        ordering = ['nombre']
        db_table = 'farmacia_presentacion'  # Nombre singular
    
    def __str__(self):
        if self.abreviatura:
            return f"{self.nombre} ({self.abreviatura})"
        return self.nombre
    
    @property
    def nombre_completo(self):
        if self.abreviatura:
            return f"{self.nombre} ({self.abreviatura})"
        return self.nombre


class Proveedor(models.Model):
    """Proveedores de medicamentos"""
    
    TIPO_PROVEEDOR_CHOICES = [
        ('NACIONAL', 'Nacional'),
        ('INTERNACIONAL', 'Internacional'),
        ('LABORATORIO', 'Laboratorio'),
        ('DISTRIBUIDOR', 'Distribuidor'),
    ]
    
    nombre = models.CharField(
        max_length=200, 
        verbose_name='Nombre/Razón Social',
        help_text='Nombre completo del proveedor'
    )
    ruc = models.CharField(
        max_length=11, 
        verbose_name='RUC', 
        unique=True,
        help_text='Registro Único de Contribuyente'
    )
    tipo_proveedor = models.CharField(
        max_length=20,
        choices=TIPO_PROVEEDOR_CHOICES,
        default='DISTRIBUIDOR',
        verbose_name='Tipo de Proveedor'
    )
    telefono = models.CharField(
        max_length=15, 
        verbose_name='Teléfono', 
        blank=True, 
        null=True,
        help_text='Teléfono principal'
    )
    telefono_alternativo = models.CharField(
        max_length=15, 
        verbose_name='Teléfono Alternativo', 
        blank=True, 
        null=True,
        help_text='Teléfono secundario'
    )
    email = models.EmailField(
        verbose_name='Email', 
        blank=True, 
        null=True,
        help_text='Correo electrónico'
    )
    direccion = models.TextField(
        verbose_name='Dirección', 
        blank=True, 
        null=True,
        help_text='Dirección completa'
    )
    contacto = models.CharField(
        max_length=100, 
        verbose_name='Persona de Contacto', 
        blank=True, 
        null=True,
        help_text='Nombre del contacto principal'
    )
    sitio_web = models.URLField(
        verbose_name='Sitio Web', 
        blank=True, 
        null=True,
        help_text='Página web del proveedor'
    )
    notas = models.TextField(
        verbose_name='Notas', 
        blank=True, 
        null=True,
        help_text='Notas adicionales'
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name='¿Activo?',
        help_text='Indica si el proveedor está activo'
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Registro'
    )
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
        db_table = 'farmacia_proveedor'  # Nombre singular
    
    def __str__(self):
        return f"{self.nombre} - RUC: {self.ruc}"
    
    @property
    def medicamentos_suministrados(self):
        return self.medicamentos.filter(activo=True).count() 
    @property
    def contacto_completo(self):
        if self.contacto and self.telefono:
            return f"{self.contacto} - {self.telefono}"
        elif self.contacto:
            return self.contacto
        elif self.telefono:
            return self.telefono
        return "Sin contacto"


# ==============================================
# MODELO PRINCIPAL: MEDICAMENTO
# ==============================================

class Medicamento(models.Model):
    """Medicamentos del inventario"""
    
    # Información básica
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='Código',
        help_text='Código único del medicamento'
    )
    codigo_barras = models.CharField(
        max_length=50,
        verbose_name='Código de Barras',
        blank=True,
        null=True,
        unique=True,
        help_text='Código de barras (opcional)'
    )
    nombre_comercial = models.CharField(
        max_length=200, 
        verbose_name='Nombre Comercial',
        help_text='Nombre comercial del medicamento'
    )
    nombre_generico = models.CharField(
        max_length=200,
        verbose_name='Nombre Genérico',
        blank=True,
        null=True,
        help_text='Nombre genérico del principio activo'
    )
    principio_activo = models.CharField(
        max_length=200, 
        verbose_name='Principio Activo',
        help_text='Principio activo del medicamento'
    )
    concentracion = models.CharField(
        max_length=100, 
        verbose_name='Concentración',
        help_text='Concentración del principio activo'
    )
    forma_farmaceutica = models.CharField(
        max_length=100,
        verbose_name='Forma Farmacéutica',
        blank=True,
        null=True,
        help_text='Ej: Tableta, Cápsula, Jarabe, etc.'
    )
    
    # Clasificación
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Categoría',
        related_name='medicamentos',
        help_text='Categoría del medicamento'
    )
    
    presentacion = models.ForeignKey(
        Presentacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Presentación',
        related_name='medicamentos',
        help_text='Presentación del medicamento'
    )
    
    # Stock y precios
    stock_actual = models.IntegerField(
        default=0, 
        verbose_name='Stock Actual',
        validators=[MinValueValidator(0)],
        help_text='Cantidad actual en inventario'
    )
    stock_minimo = models.IntegerField(
        default=10, 
        verbose_name='Stock Mínimo',
        validators=[MinValueValidator(0)],
        help_text='Cantidad mínima para alerta de stock bajo'
    )
    stock_maximo = models.IntegerField(
        default=100,
        verbose_name='Stock Máximo',
        validators=[MinValueValidator(1)],
        help_text='Cantidad máxima recomendada en inventario'
    )
    precio_compra = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Precio Compra',
        validators=[MinValueValidator(0)],
        help_text='Precio unitario de compra'
    )
    precio_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Precio Venta',
        validators=[MinValueValidator(0)],
        help_text='Precio unitario de venta al público'
    )
    precio_venta_mayorista = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio Venta Mayorista',
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Precio para ventas al por mayor'
    )
    
    # Información de lote
    lote = models.CharField(
        max_length=50, 
        verbose_name='Número de Lote', 
        blank=True, 
        null=True,
        help_text='Número de lote del fabricante'
    )
    registro_sanitario = models.CharField(
        max_length=50,
        verbose_name='Registro Sanitario',
        blank=True,
        null=True,
        help_text='Número de registro sanitario'
    )
    fecha_vencimiento = models.DateField(
        verbose_name='Fecha de Vencimiento', 
        blank=True, 
        null=True,
        help_text='Fecha de vencimiento del lote actual'
    )
    fabricante = models.CharField(
        max_length=200,
        verbose_name='Fabricante/Laboratorio',
        blank=True,
        null=True,
        help_text='Nombre del fabricante o laboratorio'
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Proveedor',
        related_name='medicamentos',
        help_text='Proveedor del medicamento'
    )
    
    # Información adicional
    descripcion = models.TextField(
        verbose_name='Descripción', 
        blank=True, 
        null=True,
        help_text='Descripción detallada del medicamento'
    )
    indicaciones = models.TextField(
        verbose_name='Indicaciones',
        blank=True,
        null=True,
        help_text='Indicaciones médicas'
    )
    contraindicaciones = models.TextField(
        verbose_name='Contraindicaciones',
        blank=True,
        null=True,
        help_text='Contraindicaciones y precauciones'
    )
    condiciones_almacenamiento = models.CharField(
        max_length=100,
        verbose_name='Condiciones de Almacenamiento',
        default='Ambiente fresco y seco',
        help_text='Temperatura y condiciones recomendadas'
    )
    
    # Control de estado
    requiere_receta = models.BooleanField(
        default=False,
        verbose_name='¿Requiere Receta Médica?',
        help_text='Requiere receta médica para su venta'
    )
    controlado = models.BooleanField(
        default=False,
        verbose_name='¿Medicamento Controlado?',
        help_text='Es un medicamento controlado'
    )
    refrigerado = models.BooleanField(
        default=False,
        verbose_name='¿Requiere Refrigeración?',
        help_text='Requiere refrigeración para su almacenamiento'
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name='¿Activo?',
        help_text='Desactivar para ocultar del sistema'
    )
    
    # Campos automáticos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Fecha de Creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True, 
        verbose_name='Fecha de Actualización'
    )
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medicamentos_creados',
        verbose_name='Creado por'
    )
    
    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering = ['nombre_comercial']
        db_table = 'farmacia_medicamento'  # ¡IMPORTANTE! Nombre singular
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nombre_comercial']),
            models.Index(fields=['principio_activo']),
            models.Index(fields=['activo']),
            models.Index(fields=['fecha_vencimiento']),
            models.Index(fields=['categoria', 'activo']),
            models.Index(fields=['stock_actual']),
        ]
    
    def __str__(self):
        return f"{self.nombre_comercial} ({self.codigo})"
    
    def save(self, *args, **kwargs):
        """Sobreescribir save para calcular valores automáticos"""
        # Calcular valor de inventario antes de guardar
        self.valor_inventario = self.stock_actual * self.precio_compra
        
        # Calcular días hasta vencimiento
        if self.fecha_vencimiento:
            hoy = date.today()
            dias = (self.fecha_vencimiento - hoy).days
            self.dias_vencimiento = max(dias, 0) if dias >= 0 else 0
            self.vencido = self.fecha_vencimiento < hoy
            self.proximo_vencer = 0 <= dias <= 30
        else:
            self.dias_vencimiento = None
            self.vencido = False
            self.proximo_vencer = False
        
        # Calcular si está bajo stock
        self.bajo_stock = self.stock_actual < self.stock_minimo
        
        super().save(*args, **kwargs)
    
    # Propiedades calculadas (también como campos para filtros)
    valor_inventario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Valor en Inventario',
        editable=False
    )
    
    dias_vencimiento = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Días hasta Vencimiento',
        editable=False
    )
    
    vencido = models.BooleanField(
        default=False,
        verbose_name='¿Vencido?',
        editable=False
    )
    
    proximo_vencer = models.BooleanField(
        default=False,
        verbose_name='¿Próximo a Vencer?',
        editable=False
    )
    
    bajo_stock = models.BooleanField(
        default=False,
        verbose_name='¿Stock Bajo?',
        editable=False
    )
    
    # Propiedades adicionales
    @property
    def valor_venta_inventario(self):
        """Valor de venta total (stock * precio venta)"""
        return self.stock_actual * self.precio_venta
    
    @property
    def margen_ganancia(self):
        """Margen de ganancia porcentual"""
        if self.precio_compra > 0:
            return round(((self.precio_venta - self.precio_compra) / self.precio_compra) * 100, 2)
        return 0
    
    @property
    def margen_ganancia_mayorista(self):
        """Margen de ganancia para ventas mayoristas"""
        if self.precio_compra > 0 and self.precio_venta_mayorista > 0:
            return round(((self.precio_venta_mayorista - self.precio_compra) / self.precio_compra) * 100, 2)
        return 0
    
    @property
    def estado_stock(self):
        """Estado del stock en texto"""
        if self.vencido:
            return "Vencido"
        elif self.bajo_stock:
            return "Stock Bajo"
        elif self.proximo_vencer:
            return "Próximo a Vencer"
        else:
            return "Normal"
    
    @property
    def porcentaje_stock(self):
        """Porcentaje de stock respecto al máximo"""
        if self.stock_maximo > 0:
            porcentaje = (self.stock_actual / self.stock_maximo) * 100
            return round(porcentaje, 1)
        return 0
    
    @property
    def necesita_reabastecimiento(self):
        """Indica si necesita reabastecimiento urgente"""
        return self.bajo_stock or self.stock_actual == 0
    
    @property
    def nombre_display(self):
        """Nombre para mostrar con información relevante"""
        display = f"{self.nombre_comercial}"
        if self.concentracion:
            display += f" {self.concentracion}"
        if self.presentacion:
            display += f" - {self.presentacion}"
        return display
    
    @property
    def es_vencido(self):
        """Alias para vencido (compatibilidad)"""
        return self.vencido
    
    @property
    def es_proximo_vencer(self):
        """Alias para proximo_vencer (compatibilidad)"""
        return self.proximo_vencer


# ==============================================
# MOVIMIENTOS DE INVENTARIO
# ==============================================

class MovimientoInventario(models.Model):
    """Registro de movimientos de inventario"""
    
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
        ('VENTA', 'Venta'),
        ('DONACION', 'Donación'),
        ('PERDIDA', 'Pérdida'),
        ('DEVOLUCION', 'Devolución'),
        ('TRASLADO', 'Traslado'),
    ]
    
    medicamento = models.ForeignKey(
        Medicamento,
        on_delete=models.CASCADE,
        related_name='movimientos',
        verbose_name='Medicamento'
    )
    
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Movimiento'
    )
    
    cantidad = models.IntegerField(
        verbose_name='Cantidad',
        validators=[MinValueValidator(1)],
        help_text='Cantidad del movimiento'
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio Unitario',
        null=True,
        blank=True,
        help_text='Precio por unidad al momento del movimiento'
    )
    
    referencia = models.CharField(
        max_length=255,
        verbose_name='Referencia/Motivo',
        blank=True,
        null=True,
        help_text='Número de factura, receta, motivo del movimiento, etc.'
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario',
        related_name='movimientos_inventario',
        help_text='Usuario que realizó el movimiento'
    )
    
    fecha = models.DateTimeField(
        default=datetime.now,
        verbose_name='Fecha y Hora'
    )
    
    observaciones = models.TextField(
        verbose_name='Observaciones',
        blank=True,
        null=True,
        help_text='Observaciones adicionales'
    )
    
    # Campos para ventas
    paciente = models.ForeignKey(
        'pacientes.Paciente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Paciente',
        related_name='compras_farmacia',
        help_text='Paciente que compró el medicamento'
    )
    
    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha']
        db_table = 'farmacia_movimientoinventario'  # Nombre singular
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['tipo']),
            models.Index(fields=['medicamento', 'fecha']),
            models.Index(fields=['usuario', 'fecha']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.medicamento.nombre_comercial} ({self.cantidad}) - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Sobreescribir save para actualizar stock del medicamento"""
        # Si es nuevo movimiento
        if not self.pk:
            # Actualizar stock del medicamento
            if self.tipo in ['ENTRADA', 'AJUSTE', 'DEVOLUCION']:
                self.medicamento.stock_actual += self.cantidad
            elif self.tipo in ['SALIDA', 'VENTA', 'DONACION', 'PERDIDA', 'TRASLADO']:
                self.medicamento.stock_actual -= self.cantidad
            
            # Guardar cambios en el medicamento
            self.medicamento.save()
        
        super().save(*args, **kwargs)
    
    @property
    def valor_total(self):
        """Valor total del movimiento"""
        if self.precio_unitario:
            return self.cantidad * self.precio_unitario
        return 0
    
    @property
    def es_entrada(self):
        """Indica si es un movimiento de entrada"""
        return self.tipo in ['ENTRADA', 'AJUSTE', 'DEVOLUCION']
    
    @property
    def es_salida(self):
        """Indica si es un movimiento de salida"""
        return self.tipo in ['SALIDA', 'VENTA', 'DONACION', 'PERDIDA', 'TRASLADO']
    
    @property
    def fecha_formateada(self):
        """Fecha formateada para display"""
        return self.fecha.strftime('%d/%m/%Y %H:%M')


# ==============================================
# DATOS INICIALES (FUNCIÓN DE AYUDA)
# ==============================================
def crear_categorias_basicas():
    """Crea solo las categorías básicas"""
    from farmacia.models import Categoria

    categorias = [
        ('Analgésicos', 'Medicamentos para el dolor'),
        ('Antibióticos', 'Antibacterianos'),
        ('Antiinflamatorios', 'Reducen inflamación'),
        ('Antigripales', 'Para gripe y resfriado'),
        ('Antialérgicos', 'Antihistamínicos'),
        ('Gastrointestinales', 'Problemas digestivos'),
        ('Cardiovasculares', 'Corazón y presión'),
        ('Antidiabéticos', 'Diabetes'),
        ('Vitaminas', 'Suplementos vitamínicos'),
        ('Dermatológicos', 'Para la piel'),
    ]

    for i, (nombre, descripcion) in enumerate(categorias):
        Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={
                'descripcion': descripcion,
                'orden': i * 10,
                'activa': True,
                'color': '#007bff',
                'icono': 'fas fa-pills'
            }
        )

    print(f"✅ {len(categorias)} categorías básicas creadas")
    return True

########### ventas directas ###########
# Añade estos modelos al final del archivo models.py

class VentaDirecta(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('YAPE/PLIN', 'Yape/Plin'),
    ]
    
    fecha = models.DateTimeField(auto_now_add=True)
    paciente = models.ForeignKey('pacientes.Paciente', on_delete=models.PROTECT, 
                                null=True, blank=True, verbose_name="Paciente (opcional)")
    cliente_externo = models.CharField(max_length=200, blank=True, verbose_name="Cliente externo")
    dni = models.CharField(max_length=8, blank=True, verbose_name="DNI (opcional)")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='EFECTIVO')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='COMPLETADA')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Venta Directa"
        verbose_name_plural = "Ventas Directas"
        ordering = ['-fecha']
    
    def __str__(self):
        if self.paciente:
            return f"Venta #{self.id} - {self.paciente.nombres}"
        else:
            return f"Venta #{self.id} - {self.cliente_externo}"


class DetalleVentaDirecta(models.Model):
    venta = models.ForeignKey(VentaDirecta, on_delete=models.CASCADE, related_name='detalles')
    medicamento = models.ForeignKey(Medicamento, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"
    
    def __str__(self):
        return f"{self.cantidad} x {self.medicamento.nombre_comercial}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)




