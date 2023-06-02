from django.db import models
from django.db.models import Q
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
    floor = models.PositiveIntegerField(verbose_name="Индекс в списке")

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"

    class MPTTMeta:
        order_insertion_by = ['floor']

    def __str__(self):
        return '{}'.format(self.id)

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        """При создании новой Страницы создает для неё Дорогу"""
        if created:
            from road.models import Road
            Road.objects.create(author=instance.author, page=instance, is_public=instance.is_public)

    @classmethod
    def update_floors_post_create(cls, sender, instance, created, *args, **kwargs):
        if created:
            brothers_older = Page.objects.filter(author=instance.author, parent=instance.parent)
            brothers_older = brothers_older.filter(Q(floor__gte=instance.level) & ~Q(id=instance.id))
            for bro in brothers_older:
                bro.floor += 1
                bro.save()


post_save.connect(Page.post_create, sender=Page)
post_save.connect(Page.update_floors_post_create, sender=Page)
