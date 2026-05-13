"""Modelo de Match entre dos usuarios.

Se crea cuando dos usuarios se dan LIKE mutuamente.
Los IDs se almacenan ordenados (menor→mayor) para unicidad del par.
"""

from django.db import models
from django.conf import settings


class Match(models.Model):
    """Representa un match mutuo entre dos usuarios.

    usuarioA y usuarioB se almacenan con IDs ordenados (min→max)
    para garantizar la unicidad del par (unique_together).

    La creación de un Match dispara automaticamente la creación
    de un Chat via señal post_save.
    """

    usuarioA = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_como_a')
    usuarioB = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_como_b')
    fechaMatch = models.DateTimeField(auto_now_add=True)
    afinidad = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    estadoMatch = models.CharField(max_length=10, default='ACTIVO')

    class Meta:
        db_table = 'match_app_match'
        unique_together = ('usuarioA', 'usuarioB')

    def __str__(self):
        return f'Match entre {self.usuarioA} y {self.usuarioB}'