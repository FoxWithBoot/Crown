from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import Road

from crown.validators import check_public_or_author
from page.serializers import DefaultPageSerializer, ShortPageSerializer
from user.serializers import UserShortSerializer


class CreateRoadSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новой дороги(ветки)"""
    parent = serializers.ModelField(model_field=Road()._meta.get_field('parent'), required=True)

    class Meta:
        model = Road
        fields = ['title', 'parent']

    def create(self, validated_data):
        return Road.objects.create(**validated_data, page=validated_data['parent'].page)

    def validate_parent(self, value):
        try:
            road = Road.objects.get(pk=value)
            if not check_public_or_author(self.context['user'], road):
                raise serializers.ValidationError("Попытка доступа к чужой приватной ветке")
            return road
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Такой ветки не существует")


class DefaultRoadSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()
    page = ShortPageSerializer()
    ancestry = serializers.SerializerMethodField(help_text="Путь к ветке от корня")

    class Meta:
        model = Road
        exclude = ['lft', 'rght', 'tree_id', 'level', 'is_removed']

    def get_ancestry(self, instance):
        ancestry = instance.get_ancestors(include_self=True)
        return ShortRoadSerializer(ancestry, many=True).data


class ShortRoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Road
        fields = ['id', 'title']