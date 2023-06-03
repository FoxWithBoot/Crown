import factory

from ..models import Page


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    title = factory.Sequence(lambda n: f'Page_{n}')
