from rest_framework import serializers

from .models import Page
from user.serializers import UserShortSerializer


class CreatePageSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новой страницы"""
    class Meta:
        model = Page
        fields = ['title', 'parent']

    def create(self, validated_data):
        return Page.objects.create(**validated_data)

    def validate_parent(self, value):
        """Проверка на то, что родительская страница либо опубликована, либо принадлежит пользователю"""
        if value:
            if not value.is_public and value.author != self.context['user']:
                raise serializers.ValidationError("Попытка доступа к чужой приватной странице")
        return value


class PageSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()

    class Meta:
        model = Page
        fields = '__all__'
