from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from mptt.models import MPTTModel, TreeForeignKey

from crown.models import AbstractAuthorsObj
from mptt.signals import node_moved


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

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"

    # class MPTTMeta:
    #     #level_attr = 'mptt_level'
    #     order_insertion_by = ['lft']

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
            insert_cut_page(instance, insert=True, created=True)


post_save.connect(Page.post_create, sender=Page)
post_save.connect(Page.update_floors_post_create, sender=Page)


def insert_cut_page(instance, insert, created=True):
    if instance.parent:
        brothers_older = Page.objects.filter(parent=instance.parent)
    else:
        brothers_older = Page.objects.filter(author=instance.author)
    brothers_older = brothers_older.filter(Q(floor__gte=instance.floor) & ~Q(id=instance.id))
    for bro in brothers_older:
        if insert:
            bro.floor += 1
        else:
            bro.floor -= 1
        bro.save()
    if not created and insert:
        if instance.parent and not instance.parent.is_public:
            change_public_state(False, instance)
    instance.refresh_from_db()
    return instance


def change_public_state(is_public, instance):
    from road.models import Road
    if is_public:
        pages = instance.get_ancestors(include_self=True)
        roads = Road.objects.filter(page__in=list(pages), parent=None)
    else:
        pages = instance.get_descendants(include_self=True)
        roads = Road.objects.filter(page__in=list(pages))
    pages.update(is_public=is_public)
    roads.update(is_public=is_public)
    instance.refresh_from_db()
    return instance
