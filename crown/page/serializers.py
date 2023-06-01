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
    ancestral_line = serializers.SerializerMethodField(help_text="Путь к странице от корня")

    class Meta:
        model = Page
        exclude = ['lft', 'rght', 'tree_id', 'level']

    def get_ancestral_line(self, instance):
        ancestral_line = instance.get_ancestors(include_self=True)
        return ShortPageSerializer(ancestral_line, many=True).data


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
        origin_author = self.context['origin_author']
        user = self.context['user']
        other_author = self.context['other_author']
        subpages = instance.subpages.all()
        if len(subpages) == 0:
            return []

        if user.is_anonymous:
            """Если пользователь - аноним, то он получит только опубликованные подстраницы автора вселенной
            и опубликованные подстраницы указанного (дополнительного) автора."""
            subpages = subpages.filter(Q(is_public=True) & (Q(author=origin_author) | Q(author=other_author)))
        elif user == origin_author:
            """Если пользователь - это автор вселенной, то он получит свои подстраницы 
            и опубликованные подстраницы указанного (дополнительного) автора."""
            subpages = subpages.filter(Q(author=user) | (Q(is_public=True) & Q(author=other_author)))
        else:
            """Если пользователь авторизован, но это не его вселенная, то он получит
            опубликованные подстраницы автора вселенной, 
            свои подстраницы в данной вселенной
            и опубликованные страницы указанного (дополнительного) автора."""
            subpages = subpages.filter((Q(is_public=True) & (Q(author=origin_author) | Q(author=other_author)))
                                       | Q(author=user))
        return PagesTreeSerializer(subpages, many=True, context=self.context).data
