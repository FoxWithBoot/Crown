import factory

from ..models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'User{n}')
    password = factory.PostGenerationMethodCall('set_password', '123')