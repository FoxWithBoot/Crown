from rest_framework import serializers

from road.serializers import RoadsTreeSerializer
from page.serializers import PagesTreeSerializer


class FakeRecursiveSerializer(serializers.Serializer):
    """Рекурсивно проходится по дереву"""

    def to_representation(self, instance):
        serializer = self.parent.parent.__class__(instance, context=self.context)
        if serializer.data.get('author') == self.context.get('user').id or serializer.data.get('is_public'):
            return serializer.data


class FakeRoadTreeSerializer(RoadsTreeSerializer):
    """Выводит дерево страниц. Нужен для swagger отображения, но соответствует схеме выдач ответа"""
    subroads = FakeRecursiveSerializer(many=True)


class FakePagesTreeSerializer(PagesTreeSerializer):
    """Выводит дерево страниц. Нужен для swagger отображения, но соответствует схеме выдач ответа"""
    subpages = FakeRecursiveSerializer(many=True)