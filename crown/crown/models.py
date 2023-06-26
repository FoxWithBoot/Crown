from django.db import models

from user.models import User


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_removed=False)

    def removed(self):
        return super().get_queryset().filter(is_removed=True)

    def all_obj(self):
        return super().get_queryset()


class AbstractAuthorsObj(models.Model):
    """Абстрактный класс, описывающий творческие объекты созданные пользователем"""
    author = models.ForeignKey(User, models.CASCADE, verbose_name="Автор")
    is_public = models.BooleanField(default=False, verbose_name="Опубликовано?")
    is_removed = models.BooleanField(default=False, verbose_name="Удалено?")

    class Meta:
        abstract = True
