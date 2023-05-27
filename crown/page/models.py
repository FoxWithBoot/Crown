from django.db import models

from user.models import User


class Page(models.Model):
    """Страница"""
    title = models.CharField(max_length=150,
                             verbose_name="Название",
                             default="Страница")
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               blank=True, null=True,
                               verbose_name="Родительская страница",
                               default=None,
                               related_name="subpages")
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name="Автор")

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"

    def __str__(self):
        return '{}'.format(self.id)
