from django.db import models
from django.db.models.signals import post_save
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from page.models import Page
from crown.models import AbstractAuthorsObj


class Road(MPTTModel, AbstractAuthorsObj):
    """Дорога (ветка) на странице"""
    page = models.ForeignKey(Page,
                             on_delete=models.CASCADE,
                             verbose_name="Страница")
    title = models.CharField(max_length=150,
                             verbose_name="Название",
                             default="Дорога")
    parent = TreeForeignKey('self',
                            on_delete=models.CASCADE,
                            null=True, blank=True,
                            related_name="subroad",
                            verbose_name="Дорога, от которой пошла развилка")

    class Meta:
        verbose_name = "Дорога"
        verbose_name_plural = "Дороги"

    def __str__(self):
        return "{}".format(self.id)

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        """При создании новой корневой дороги (ветки) создается блок на этой дороге."""
        if created and not instance.parent:
            from block.models import Block
            Block.objects.create(road=instance, is_start=True, content="<p>Давай начнем писать;)</p>")

    def change_public_state(self, is_public):
        if is_public:
            roads = self.get_ancestors(include_self=True)
        else:
            roads = self.get_descendants(include_self=True)
        roads.update(is_public=is_public)
        if is_public:
            """Если ветку публикуем, то публикуем и ее страницу."""
            if not self.page.is_public:
                self.page.change_public_state(is_public)
        if not is_public and not self.parent:
            """Если ветку приватим и это корневая ветка, то приватим и страницу."""
            self.page.change_public_state(is_public)
        self.refresh_from_db()
        return self


post_save.connect(Road.post_create, sender=Road)
