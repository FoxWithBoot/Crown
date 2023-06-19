from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import serializers

from .models import Page
from user.serializers import UserShortSerializer
from crown.validators import check_public_or_author


class WhereInsertPage(serializers.Serializer):
    before_after = serializers.ChoiceField(choices=(('before', 1), ('after', 2)),
                                           help_text="Вставлять до или после указанной страницы")
    page = serializers.ModelField(model_field=Page()._meta.get_field('id'), required=True)

    class Meta:
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


class UpdatePageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Page
        fields = ['title', 'is_public']

    def validate_is_public(self, value):
        author = self.context['user']
        page = self.instance
        ancestry = page.get_ancestors()
        if value and ancestry.filter(Q(is_public=False) & ~Q(author=author)).exists():
            raise serializers.ValidationError("Автор одной из родительских страниц отменил публикацию.")
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


class MovePageSerializer(serializers.Serializer):
    before_after = serializers.ChoiceField(choices=(('before', 1), ('after', 2)),
                                           help_text="Вставлять до или после указанной страницы", required=False)
    page = serializers.ModelField(model_field=Page()._meta.get_field('id'), required=True, allow_null=True)

    def validate_page(self, value):
        # print(self.instance)
        """Валидация поля page - id страницы до или после которой нужно вставить новую страницу"""
        try:
            if value is None:
                return None
            page = Page.objects.get(id=value)
            if not check_public_or_author(self.context['user'], page):
                raise serializers.ValidationError("Попытка доступа к чужой приватной странице")
            if page in list(self.instance.get_descendants(include_self=True)):
                raise serializers.ValidationError("Нельзя ссылаться на себя или своего потомка")
            return page
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Такой страницы не существует")

    def update(self, instance, validated_data):
        instance.insert_cut_page(insert=False, created=False)
        if 'before_after' in validated_data:
            if validated_data['before_after'] == 'after':
                instance.floor = validated_data['page'].floor + 1
            else:
                instance.floor = validated_data['page'].floor
            instance.parent = validated_data['page'].parent
            instance.save()
            return instance.insert_cut_page(insert=True, created=False)
        else:
            instance.floor = 0
            instance.parent = validated_data['page']
            instance.save()
            return instance.insert_cut_page(insert=True, created=False)


class DefaultPageSerializer(serializers.ModelSerializer):
    author = UserShortSerializer()
    ancestry = serializers.SerializerMethodField(help_text="Путь к странице от корня")

    class Meta:
        model = Page
        exclude = ['lft', 'rght', 'tree_id', 'level', 'floor', 'is_removed']

    def get_ancestry(self, instance):
        ancestry = instance.get_ancestors(include_self=True)
        return ShortPageSerializer(ancestry, many=True).data


class ShortPageSerializerInList(serializers.ModelSerializer):
    author = UserShortSerializer()
    ancestry = serializers.SerializerMethodField(help_text="Путь к странице от корня")

    class Meta:
        model = Page
        fields = ['id', 'title', 'author', 'ancestral_line']

    def get_ancestry(self, instance):
        ancestry = instance.get_ancestors(include_self=True)
        return ShortPageSerializer(ancestry, many=True).data


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
        other_author_list = self.context['other_author_list']
        subpages = instance.subpages.all()
        if len(subpages) == 0:
            return []

        if user.is_anonymous:
            """Если пользователь - аноним, то он получит только опубликованные подстраницы автора вселенной
            и опубликованные подстраницы указанного (дополнительного) автора."""
            subpages = subpages.filter(Q(is_public=True) & (Q(author=origin_author) | Q(author__in=other_author_list)))
        elif user == origin_author:
            """Если пользователь - это автор вселенной, то он получит свои подстраницы 
            и опубликованные подстраницы указанного (дополнительного) автора."""
            subpages = subpages.filter(Q(author=user) | (Q(is_public=True) & Q(author__in=other_author_list)))
        else:
            """Если пользователь авторизован, но это не его вселенная, то он получит
            опубликованные подстраницы автора вселенной, 
            свои подстраницы в данной вселенной
            и опубликованные страницы указанного (дополнительного) автора."""
            subpages = subpages.filter((Q(is_public=True) & (Q(author=origin_author) | Q(author__in=other_author_list)))
                                       | Q(author=user))
        subpages = subpages.order_by('floor')
        return PagesTreeSerializer(subpages, many=True, context=self.context).data


