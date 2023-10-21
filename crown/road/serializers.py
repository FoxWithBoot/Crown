from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import serializers

from .models import Road

from crown.validators import check_public_or_author
from page.serializers import DefaultPageSerializer, ShortPageSerializer
from user.serializers import UserShortSerializer
from block.controller import read_road
from block.models import BlocksOnRoad


class CreateRoadSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новой дороги(ветки)"""
    parent = serializers.ModelField(model_field=Road()._meta.get_field('parent'), required=True)

    class Meta:
        model = Road
        fields = ['title', 'parent']

    def create(self, validated_data):
        road = Road.objects.create(**validated_data, page=validated_data['parent'].page)
        line = read_road(validated_data['parent'])
        for block in line:
            BlocksOnRoad.objects.create(block=block, road=road, index=line.index(block))
        return road

    def validate_parent(self, value):
        try:
            road = Road.objects.get(pk=value)
            if not check_public_or_author(self.context['user'], road):
                raise serializers.ValidationError("Попытка доступа к чужой приватной ветке")
            return road
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Такой ветки не существует")


class UpdateRoadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Road
        fields = ['title', 'is_public']

    def validate_is_public(self, value):
        author = self.context['user']
        road = self.instance
        ancestry = road.get_ancestors()
        if value and ancestry.filter(Q(is_public=False) & ~Q(author=author)).exists():
            raise serializers.ValidationError("Автор одной из родительских веток отменил публикацию.")
        return value

    def update(self, instance, validated_data):
        title = validated_data.get('title', None)
        is_public = validated_data.get('is_public', None)
        if title is not None and title != instance.title:
            instance.title = title
            instance.save()
        if is_public is not None and is_public != instance.is_public:
            instance = instance.change_public_state(is_public)
        return instance


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


class RoadsTreeSerializer(serializers.ModelSerializer):
    subroads = serializers.SerializerMethodField()
    author = UserShortSerializer()

    class Meta:
        model = Road
        fields = ("id", "author", "page", "title", "is_public", "subroads")

    def get_subroads(self, instance):
        origin_author = self.context['origin_author']
        user = self.context['user']
        other_author_list = self.context['other_author_list']
        subroads = instance.subroad.all()
        if len(subroads) == 0:
            return []

        if user.is_anonymous:
            subroads = subroads.filter(Q(is_public=True) & (Q(author=origin_author) | Q(author__in=other_author_list)))
        elif user == origin_author:
            subroads = subroads.filter(Q(author=user) | (Q(is_public=True) & Q(author__in=other_author_list)))
        else:
            subroads = subroads.filter((Q(is_public=True) & (Q(author=origin_author) | Q(author__in=other_author_list)))
                                       | Q(author=user))
        return RoadsTreeSerializer(subroads, many=True, context=self.context).data


