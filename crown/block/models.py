from django.db import models

from road.models import Road


class Block(models.Model):
    """Блок контента на дороге"""
    road = models.ForeignKey(Road,
                             on_delete=models.CASCADE,
                             verbose_name="Дорога")
    next_blocks = models.ManyToManyField('self',
                                         symmetrical=False,
                                         verbose_name="Следующий(-е) блок(-и)",
                                         blank=True)
    is_start = models.BooleanField(default=False,
                                   verbose_name="Начальный блок дороги")
    content = models.TextField(verbose_name="Текст блока", blank=True, null=True)

    class Meta:
        verbose_name = "Блок"
        verbose_name_plural = "Блоки"

    def __str__(self):
        return "{}".format(self.id)
