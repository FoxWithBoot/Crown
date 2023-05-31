from django.db import models
from django.db.models.signals import post_save
from mptt.models import MPTTModel, TreeForeignKey

from crown.models import AbstractAuthorsObj


class Page(MPTTModel, AbstractAuthorsObj):
    """Страница"""
    title = models.CharField(max_length=150,
                             verbose_name="Название",
                             default="Страница")
    parent = TreeForeignKey('self',
                            on_delete=models.CASCADE,
                            blank=True, null=True,
                            verbose_name="Родительская страница",
                            default=None,
                            related_name="subpages")

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"

    def __str__(self):
        return '{}'.format(self.id)

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        """При создании новой Страницы создает для неё Дорогу"""
        if created:
            from road.models import Road
            Road.objects.create(author=instance.author, page=instance, is_public=instance.is_public)


post_save.connect(Page.post_create, sender=Page)
