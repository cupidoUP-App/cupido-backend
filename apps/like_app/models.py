"""Modelo de interacciones LIKE/DISLIKE entre usuarios.

Cada registro representa una interacción única de un emisor a un receptor.
Cuando ambos se dan LIKE, esMutuo=True y se crea un Match.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DetallesLike(models.Model):
    """Registro de una interacción LIKE/DISLIKE entre dos usuarios.

    La combinación (usuarioEmisor, usuarioReceptor) es única para evitar
    interacciones duplicadas. esMutuo se activa cuando hay reciprocidad.
    """

    ESTADO_CHOICES = [
        ('LIKE', 'Me Gusta'),
        ('DISLIKE', 'No Me Gusta'),
    ]

    usuarioEmisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_hechos')
    usuarioReceptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_recibidos')
    fechaInteraccion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=7, choices=ESTADO_CHOICES)
    esMutuo = models.BooleanField(default=False)

    class Meta:
        db_table = 'detalles_like'
        unique_together = ('usuarioEmisor', 'usuarioReceptor')

    def __str__(self):
        return f'{self.usuarioEmisor.email} -> {self.usuarioReceptor.email} ({self.estado})'