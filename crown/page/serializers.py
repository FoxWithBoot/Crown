from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import serializers

from .models import Page
from user.serializers import UserShortSerializer

from .validators import check_public_or_author


class WhereInsertPage(serializers.Serializer):
    before_after = serializers.ChoiceField(choices=(('before', 1), ('after', 2)),
                                           help_text="Вставлять до или после указанной страницы")
    page = serializers.ModelField(model_field=Page()._meta.get_field('id'), required=True)

    class Meta:
        model = Page
        fields = ['page', 'before_after']

    def validate_page(self, value):
        """Валидация поля page - id страницы до или после которой нужно вставить новую страницу"""
        try:
            page = Page.objects.get(id=value)
            if not check_public_or_author(self.context['user'], page):
                raise serializers.ValidationError("Попытка доступа к чужой приватной странице")
            return page
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Такой страницы не существует")


class CreatePageSerializer(serializers.ModelSerializer):
    """Сериализатор для создания новой страницы"""
    where = WhereInsertPage(required=False, allow_null=False)

    class Meta:
        model = Page
        fields = ['title', 'parent', 'where']

    def create(self, validated_data):
        where = validated_data.get('where', None)
        if where:
            validated_data.pop('where')
            if where['before_after'] == 'after':
                return Page.objects.create(**validated_data, floor=where['page'].floor+1)
            else:
                return Page.objects.create(**validated_data, floor=where['page'].floor)
        return Page.objects.create(**validated_data, floor=0)

    def validate_parent(self, value):
        if not check_public_or_author(self.context['user'], value):
            raise serializers.ValidationError("Попытка доступа к чужой приватной странице")
        return value

    def validate(self, data):
        parent = data.get('parent', None)
        where = data.get('where', None)
        if where and parent:
            if where['page'].parent != parent:
                raise serializers.ValidationError({'where': {'page': ["Указанная страница не является дочерней к parent"]}})
        return data


class DefaultPageSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()
    ancestral_line = serializers.SerializerMethodField(help_text="Путь к странице от корня")

    class Meta:
        model = Page
        exclude = ['lft', 'rght', 'tree_id', 'level', 'floor']

    def get_ancestral_line(self, instance):
        ancestral_line = instance.get_ancestors(include_self=True)
        return ShortPageSerializer(ancestral_line, many=True).data


class ShortPageSerializerInList(serializers.ModelSerializer):
    author = UserShortSerializer()
    ancestral_line = serializers.SerializerMethodField(help_text="Путь к странице от корня")

    class Meta:
        model = Page
        fields = ['id', 'title', 'author', 'ancestral_line']

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
        subpages = subpages.order_by('floor')
        print(subpages.values('id', 'title', 'floor'))
        return PagesTreeSerializer(subpages, many=True, context=self.context).data


#  =====================================================================================================================
class FakeRecursiveSerializer(serializers.Serializer):
    """Рекурсивно проходится по дереву"""

    def to_representation(self, instance):
        serializer = self.parent.parent.__class__(instance, context=self.context)
        if serializer.data.get('author') == self.context.get('user').id or serializer.data.get('is_public'):
            return serializer.data


class FakePagesTreeSerializer(PagesTreeSerializer):
    """Выводит дерево страниц. Нужен для swagger отображения, но соответствует схеме выдач ответа"""
    subpages = FakeRecursiveSerializer(many=True)

