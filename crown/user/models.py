from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Кастомный пользователь системы"""
    groups = None
