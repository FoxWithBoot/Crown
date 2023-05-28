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


class PageSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()

    class Meta:
        model = Page
        fields = '__all__'
