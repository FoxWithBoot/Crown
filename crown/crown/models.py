from django.db import models

from user.models import User


class AbstractAuthorsObj(models.Model):
    """Абстрактный класс, описывающий творческие объекты созданные пользователем"""
    author = models.ForeignKey(User, models.CASCADE, verbose_name="Автор")
    is_public = models.BooleanField(default=False, verbose_name="Опубликовано?")

    class Meta:
        abstract = True
