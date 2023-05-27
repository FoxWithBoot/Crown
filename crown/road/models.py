from django.db import models

from page.models import Page


class Road(models.Model):
    """Дорога на странице"""
    page = models.ForeignKey(Page,
                             on_delete=models.CASCADE,
                             verbose_name="Страница")
    title = models.CharField(max_length=150,
                             verbose_name="Название",
                             default="Дорога")
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name="subroad",
                               verbose_name="Дорога, от которой пошла развилка")

    class Meta:
        verbose_name = "Дорога"
        verbose_name_plural = "Дороги"

    def __str__(self):
        return "{}".format(self.id)
