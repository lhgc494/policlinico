from django.db import models
from django.contrib.auth.models import User

class Notificacion(models.Model):
    TIPO_USUARIO = [
        ('DOCTOR', 'Doctor'),
        ('FARMACIA', 'Farmacia'),
        ('LABORATORIO', 'Laboratorio'),
    ]
    
    TIPO_EVENTO = [
        ('NUEVA_CONSULTA', 'Nueva consulta'),
        ('NUEVA_RECETA', 'Nueva receta'),
        ('NUEVO_EXAMEN', 'Nuevo examen'),
    ]
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO)
    tipo = models.CharField(max_length=20, choices=TIPO_EVENTO)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    elemento_id = models.IntegerField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
