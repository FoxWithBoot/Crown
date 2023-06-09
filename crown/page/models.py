from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from mptt.models import MPTTModel, TreeForeignKey

from crown.models import AbstractAuthorsObj, SoftDeleteManager


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
    floor = models.PositiveIntegerField(blank=True, null=True, default=0, verbose_name="Индекс в списке подстраниц")

    objects = SoftDeleteManager()

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

    @classmethod
    def update_floors_post_create(cls, sender, instance, created, *args, **kwargs):
        """Обновляет значения floor старших братьев для новой страницы"""
        if created:
            instance.insert_cut_page(insert=True, created=True)

    def change_public_state(self, is_public):
        from road.models import Road
        if is_public:
            pages = self.get_ancestors(include_self=True)
            roads = Road.objects.filter(page__in=list(pages), parent=None)
        else:
            pages = self.get_descendants(include_self=True)
            roads = Road.objects.filter(page__in=list(pages))
        pages.update(is_public=is_public)
        roads.update(is_public=is_public)
        self.refresh_from_db()
        return self

    def insert_cut_page(self, insert, created=True):
        if self.parent:
            brothers_older = Page.objects.filter(parent=self.parent)
        else:
            brothers_older = Page.objects.filter(author=self.author, parent=None)
        brothers_older = brothers_older.filter(Q(floor__gte=self.floor) & ~Q(id=self.id))
        for bro in brothers_older:
            if insert:
                bro.floor += 1
            else:
                bro.floor -= 1
            print('aaa', bro, bro.floor)
            bro.save()
        if not created and insert:
            if self.parent and not self.parent.is_public:
                self.change_public_state(False)
        self.refresh_from_db()
        return self

    def insert_page(self):
        return self.insert_cut_page(insert=True, created=False)

    def cut_page(self):
        return self.insert_cut_page(insert=False, created=False)

    def _change_remove_state(self, is_removed=True):
        from road.models import Road
        if not is_removed:
            pages = self.get_ancestors(include_self=True)
            roads = Road.objects.filter(page__in=list(pages), parent=None)
        else:
            pages = self.get_descendants(include_self=True)
            roads = Road.objects.filter(page__in=list(pages))
        if not is_removed:
            pages.update(is_removed=is_removed, is_public=False)
            roads.update(is_removed=is_removed, is_public=False)
        else:
            pages.update(is_removed=is_removed)
            roads.update(is_removed=is_removed)
        self.refresh_from_db()
        return self

    def soft_delete(self):
        self._change_remove_state(True)

    def recovery(self):
        self._change_remove_state(False)


post_save.connect(Page.post_create, sender=Page)
post_save.connect(Page.update_floors_post_create, sender=Page)



