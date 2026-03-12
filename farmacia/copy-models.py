# farmacia/models.py - VERSIÓN COMPLETA Y CORREGIDA
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime
from django.core.validators import MinValueValidator, MaxValueValidator

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
        db_table = 'farmacia_categoria'

    def __str__(self):
        return self.nombre

    def medicamentos_count(self):
        return self.medicamentos.filter(activo=True).count()

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
        db_table = 'farmacia_presentacion'

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
        db_table = 'farmacia_proveedor'

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

    # Campos calculados (definidos como propiedades primero)
    @property
    def valor_inventario(self):
        """Valor en inventario (stock * precio compra)"""
        return self.stock_actual * self.precio_compra if self.precio_compra else 0

    @property
    def dias_vencimiento(self):
        """Días hasta vencimiento"""
        if self.fecha_vencimiento:
            hoy = date.today()
            dias = (self.fecha_vencimiento - hoy).days
            return max(dias, 0) if dias >= 0 else 0
        return None

    @property
    def vencido(self):
        """¿Está vencido?"""
        if self.fecha_vencimiento:
            return self.fecha_vencimiento < date.today()
        return False

    @property
    def proximo_vencer(self):
        """¿Próximo a vencer (menos de 30 días)?"""
        if self.fecha_vencimiento and self.dias_vencimiento is not None:
            return 0 <= self.dias_vencimiento <= 30
        return False

    @property
    def bajo_stock(self):
        """¿Stock por debajo del mínimo?"""
        return self.stock_actual < self.stock_minimo

    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering = ['nombre_comercial']
        db_table = 'farmacia_medicamento'
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
        """Sobreescribir save para validaciones"""
        # Asegurar que stock no sea negativo
        if self.stock_actual < 0:
            self.stock_actual = 0
            
        super().save(*args, **kwargs)

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
    def nombre_display(self):
        """Nombre para mostrar"""
        display = f"{self.nombre_comercial}"
        if self.concentracion:
            display += f" {self.concentracion}"
        if self.presentacion:
            display += f" - {self.presentacion}"
        return display


# ==============================================
# VENTAS DIRECTAS (Sistema de ventas actual)
# ==============================================

# Definir METODOS_PAGO aquí
METODOS_PAGO = [
    ('EFECTIVO', 'Efectivo'),
    ('YAPE', 'Yape'),
    ('PLIN', 'Plin'),
    ('TARJETA', 'Tarjeta'),
]

class Venta(models.Model):
    """Modelo de ventas para el sistema actual"""
    fecha_hora = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        db_table = 'farmacia_venta'

    def __str__(self):
        return f"Venta #{self.id} - S/ {self.total} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    @property
    def subtotal_sin_descuento(self):
        return self.total + self.descuento

#############
# En farmacia/models.py - MODIFICAR DetalleVenta
# En farmacia/models.py - MODIFICAR DetalleVenta

class DetalleVenta(models.Model):
    """Detalles de venta para el sistema actual"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    medicamento = models.ForeignKey(
        Medicamento, 
        on_delete=models.PROTECT,
        null=True,  # 👈 AGREGAR
        blank=True  # 👈 AGREGAR
    )
    descripcion = models.CharField(  # 👈 NUEVO CAMPO
        max_length=255,
        blank=True,
        default='',  # Valor por defecto
        verbose_name='Descripción',
        help_text='Descripción del servicio/producto'
    )
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
        db_table = 'farmacia_detalleventa'

    def __str__(self):
        if self.medicamento:
            return f"{self.medicamento.nombre_comercial} x {self.cantidad}"
        return f"{self.descripcion} x {self.cantidad}"

    def save(self, *args, **kwargs):
        # Si hay medicamento, usar su nombre como descripción por defecto
        if self.medicamento and not self.descripcion:
            self.descripcion = self.medicamento.nombre_comercial
        
        # Calcular subtotal automáticamente
        if not self.subtotal and self.precio_unitario and self.cantidad:
            self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

# ==============================================
# MOVIMIENTOS DE INVENTARIO (Compatible con ambos sistemas)
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

    # Relación con venta si aplica
    venta = models.ForeignKey(
        Venta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Venta Relacionada',
        help_text='Venta que generó este movimiento'
    )

    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha']
        db_table = 'farmacia_movimientoinventario'
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['tipo']),
            models.Index(fields=['medicamento', 'fecha']),
            models.Index(fields=['usuario', 'fecha']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.medicamento.nombre_comercial} ({self.cantidad}) - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        """Sobreescribir save para actualizar stock"""
        # Si es nuevo movimiento
        if not self.pk:
            # Actualizar stock del medicamento
            if self.tipo in ['ENTRADA', 'AJUSTE', 'DEVOLUCION']:
                self.medicamento.stock_actual += self.cantidad
            elif self.tipo in ['SALIDA', 'VENTA', 'DONACION', 'PERDIDA', 'TRASLADO']:
                self.medicamento.stock_actual -= self.cantidad

            # Asegurar que stock no sea negativo
            if self.medicamento.stock_actual < 0:
                self.medicamento.stock_actual = 0

            # Guardar cambios en el medicamento
            self.medicamento.save()

        super().save(*args, **kwargs)

    @property
    def valor_total(self):
        """Valor total del movimiento"""
        if self.precio_unitario:
            return self.cantidad * self.precio_unitario
        return 0


# ==============================================
# FUNCIÓN DE AYUDA PARA DATOS INICIALES
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


############# combos topico
class ComboTopico(models.Model):
    """
    Combos predeterminados de tópico
    Ej: Combo 1 = Aspirina + Vendas + Paracetamol
    """
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del combo',
        help_text='Ej: Combo 1 - Curaciones básicas'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción opcional del combo'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está desactivado, no aparecerá en las listas'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )

    class Meta:
        verbose_name = 'Combo de tópico'
        verbose_name_plural = 'Combos de tópico'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def calcular_precio_total(self):
        """
        Calcula el precio total del combo sumando todos los medicamentos
        """
        total = 0
        for item in self.medicamentos.all():
            total += item.medicamento.precio_venta * item.cantidad
        return total

    def obtener_detalle(self):
        """
        Retorna lista de medicamentos del combo con sus detalles
        """
        detalle = []
        for item in self.medicamentos.all():
            detalle.append({
                'medicamento_id': item.medicamento.id,
                'medicamento_nombre': item.medicamento.nombre_comercial,
                'cantidad': item.cantidad,
                'precio_unitario': item.medicamento.precio_venta,
                'subtotal': item.medicamento.precio_venta * item.cantidad
            })
        return detalle


class ComboMedicamento(models.Model):
    """
    Medicamentos que incluye cada combo (tabla intermedia)
    """
    combo = models.ForeignKey(
        ComboTopico,
        on_delete=models.CASCADE,
        related_name='medicamentos',
        verbose_name='Combo'
    )
    medicamento = models.ForeignKey(
        'Medicamento',
        on_delete=models.CASCADE,
        verbose_name='Medicamento',
        limit_choices_to={'activo': True}  # Solo medicamentos activos
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name='Cantidad'
    )

    class Meta:
        verbose_name = 'Medicamento del combo'
        verbose_name_plural = 'Medicamentos del combo'
        unique_together = ['combo', 'medicamento']  # Evita duplicados

    def __str__(self):
        return f"{self.combo.nombre} - {self.medicamento.nombre_comercial} x{self.cantidad}"

    def subtotal(self):
        """Calcula el subtotal de este medicamento en el combo"""
        return self.medicamento.precio_venta * self.cantidad

