import factory

from ..models import Road


class RoadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Road

    title = factory.Sequence(lambda n: f'Road_{n}')