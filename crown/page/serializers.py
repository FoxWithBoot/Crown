from django.db.models import Q
from rest_framework import serializers

from .models import Page
from user.serializers import UserShortSerializer

from .validators import check_public_or_author


class CreatePageSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новой страницы"""
    class Meta:
        model = Page
        fields = ['title', 'parent']

    def create(self, validated_data):
        return Page.objects.create(**validated_data)

    def validate_parent(self, value):
        if not check_public_or_author(self.context['user'], value):
            raise serializers.ValidationError("Попытка доступа к чужой приватной странице")
        return value


class DefaultPageSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()

    class Meta:
        model = Page
        fields = '__all__'


class ShortPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'title']


class PagesTreeSerializer(serializers.ModelSerializer):
    """Обрабатывает дерево страниц"""
    subpages = serializers.SerializerMethodField()
    author = UserShortSerializer()

    class Meta:
        model = Page
        fields = ("id", "author", "title", "is_public", "subpages")

    def get_subpages(self, instance):
        if self.context.get('user').is_anonymous:
            subpages = instance.subpages.all().filter(Q(is_public=True))
        else:
            subpages = instance.subpages.all().filter(Q(author=self.context.get('user')) | Q(is_public=True))
        print(subpages)
        print(PagesTreeSerializer(subpages, many=True, context=self.context).data)
        if len(subpages) == 0:
            return []
        return PagesTreeSerializer(subpages, many=True, context=self.context).data
