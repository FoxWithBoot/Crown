from django.db.models import Q
from django.http import Http404
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.openapi import Parameter, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from .controller import get_list_public_authors_in_space, get_list_public_authors_in_page_roads
from .filters import PageFilter
from .models import Page

from .serializers import CreatePageSerializer, DefaultPageSerializer, PagesTreeSerializer, \
    UpdatePageSerializer, MovePageSerializer, ShortPageSerializer

from user.models import User
from user.serializers import UserShortSerializer
from crown.permissions import OnlyAuthorIfPrivate
from road.serializers import RoadsTreeSerializer
from road.models import Road
from crown.serializers import FakePagesTreeSerializer, FakeRoadTreeSerializer


class PageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, OnlyAuthorIfPrivate]

    @swagger_auto_schema(request_body=CreatePageSerializer, responses={201: DefaultPageSerializer()})
    def create(self, request):
        """Создание новой страницы. В теле запроса передается название страницы и родительская страница.
        Дополнительно указывается блок where: до или после какой страницы вставить новую.
        - доступно только авторизованным;
        - родительская страница должна быть публичной или принадлежать пользователю;"""
        serializer = CreatePageSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        page = serializer.save(author=request.user)
        return Response(DefaultPageSerializer(page).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={200: DefaultPageSerializer()})
    def retrieve(self, request, pk):
        """Получение общей информации о странице.
        - доступно всем, если страница публична;
        - доступно только автору, если страница приватна;"""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        return Response(DefaultPageSerializer(page).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: FakePagesTreeSerializer()},
                         manual_parameters=[Parameter('other_author', IN_QUERY,
                                                      'Добавляет в дерево подстраницы интересующего автора',
                                                      type='int'), ])
    @action(methods=['get'], detail=True)
    def subpages_tree(self, request, pk):
        """
        Возвращает дерево корневой страницы по одному из ее предков.
        - Если пользователь - аноним, то он получит только опубликованные подстраницы автора вселенной
                    и опубликованные подстраницы указанного (дополнительного) автора.
        - Если пользователь - это автор вселенной, то он получит свои подстраницы
                    и опубликованные подстраницы указанного (дополнительного) автора.
        - Если пользователь авторизован, но это не его вселенная, то он получит
                    опубликованные подстраницы автора вселенной,
                    свои подстраницы в данной вселенной
                    и опубликованные страницы указанного (дополнительного) автора.
        * Если дополнительный автор(-ы) не указаны, то будет использован список всех авторов,
        которые писали во вселенной. (ВОЗМОЖНО ПЕРЕДЕЛАТЬ НА ФИЛЬТР ВООБЩЕ ПО ВСЕМ АВТОРАМ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ)
        - Если пользователь - автор страницы, но не автор вселенной и вселенная приватна, то 403.
        """
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        parent_page = page.get_root()
        self.check_object_permissions(request, parent_page)
        other_author = request.query_params.getlist('other_author', '')
        if len(other_author)>0:
            try:
                other_author_list = []
                for i in other_author:
                    if User.objects.filter(pk=i).exists():
                        other_author_list.append(i)
            except:
                raise ValidationError(detail={"parent": ["Некорректный id автора"]})
        else:
            authors_space = get_list_public_authors_in_space(page=page, user=request.user, parent_page=parent_page)
            other_author_list = list(authors_space.values_list('id', flat=True))
        pages_tree = PagesTreeSerializer(parent_page, context={'origin_author': parent_page.author,
                                                               'user': request.user,
                                                               'other_author_list': other_author_list})
        return Response(pages_tree.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: FakeRoadTreeSerializer()},
                         manual_parameters=[Parameter('other_author', IN_QUERY,
                                                      'Добавляет в дерево дорог интересующего автора',
                                                      type='int'), ])
    @action(methods=['get'], detail=True)
    def roads_tree(self, request, pk):
        """Возвращает дерево дорог(веток) страницы (аналогично subpages_tree)"""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        parent_road = Road.objects.get(page=page, parent=None)
        other_author = request.query_params.getlist('other_author', '')
        if len(other_author) > 0:
            try:
                other_author_list = []
                for i in other_author:
                    if User.objects.filter(pk=i).exists():
                        other_author_list.append(i)
            except:
                raise ValidationError(detail={"parent": ["Некорректный id автора"]})
        else:
            authors_page = get_list_public_authors_in_page_roads(page=page, user=request.user)
            other_author_list = list(authors_page.values_list('id', flat=True))
        roads_tree = RoadsTreeSerializer(parent_road, context={'origin_author': page.author,
                                                               'user': request.user,
                                                               'other_author_list': other_author_list})
        return Response(roads_tree.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: UserShortSerializer(many=True)})
    @action(methods=['get'], detail=True)
    def other_authors_list(self, request, pk):
        """
        Возвращает список пользователей, которые создавали и публиковали страницы в пределах вселенной страницы pk.
        Нужен для фильтрации дерева страниц по пользователям (см. subpages_tree)
        """
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        authors_in_space = get_list_public_authors_in_space(page, request.user)
        authors_list = UserShortSerializer(authors_in_space, many=True)
        return Response(authors_list.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: UserShortSerializer(many=True)})
    @action(methods=['get'], detail=True)
    def other_authors_in_page(self, request, pk):
        """
        Возвращает список пользователей, которые создавали и публиковали ветки(дороги) в пределах страницы pk.
        Нужен для фильтрации дерева дорог по пользователям (см. roads_tree)
        """
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        authors_in_page = get_list_public_authors_in_page_roads(page=page, user=request.user)
        authors_list = UserShortSerializer(authors_in_page, many=True)
        return Response(authors_list.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=UpdatePageSerializer, responses={200: DefaultPageSerializer()})
    def partial_update(self, request, pk=None):
        """Обновление заголовка страницы и статуса публикации.
        При снятии с публикации страницы также снимаются с публикации все её дороги и все дочерние страницы с их дорогами в независимости от их авторства.
        При публикации страницы публикуются её корневая дорога, а также все её предки с их корневыми дорогами.
        Публикация не доступна если, одна из страниц-предков не опубликована и принадлежит другому пользователю."""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        serializer = UpdatePageSerializer(data=request.data, context={'user': request.user}, instance=page)
        serializer.is_valid(raise_exception=True)
        page = serializer.save()
        return Response(DefaultPageSerializer(page).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=MovePageSerializer, responses={200: DefaultPageSerializer()})
    @action(methods=['patch'], detail=True)
    def move_page(self, request, pk):
        """Перемещение страницы по дереву. Указывается страница и до или после неё нужно вставить целевую страницу.
        Если не указано до или после, то страница считается новой родительской страницей для целевой.
        Если публичная страница перемещается в неопубликованную, то перемещаемая страница снимается с публикации."""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        serializer = MovePageSerializer(data=request.data, context={'user': request.user}, instance=page)
        serializer.is_valid(raise_exception=True)
        page = serializer.save()
        return Response(DefaultPageSerializer(page).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: DefaultPageSerializer()})
    def update(self, request, pk):
        """Восстановление удаленной в корзину страницы."""
        try:
            page = Page.objects.removed().get(pk=pk)
            self.check_object_permissions(request, page)
            ancestry = page.get_ancestors()
            if ancestry.filter(Q(is_removed=True) & ~Q(author=request.user)).exists():
                return Response(data={'detail': 'Одна из родительских страниц удалена автором.'},
                                status=status.HTTP_400_BAD_REQUEST)
            page.recovery()
            return Response(DefaultPageSerializer(page).data, status=status.HTTP_200_OK)
        except Page.DoesNotExist:
            raise Http404

    @swagger_auto_schema(responses={200: '', 204: ''})
    def destroy(self, request, pk):
        """
        Удаление страницы. При первом вызове для страницы происходит мягкое удаление, то есть помещение в корзину.
        При повторном вызове метода для уже 'удаленной' страницы, страница действительно удаляется (каскадно).
        Помещение в корзину аналогично отмене публикации, то есть в корзину помещаются все подстраницы и дороги страницы,
        не зависимо от авторства. При удалении страницы с публикации снимаются.
        """
        try:
            page = Page.objects.get(pk=pk)
            self.check_object_permissions(request, page)
            page.soft_delete()
            return Response(status=status.HTTP_200_OK)
        except Page.DoesNotExist:
            try:
                page = Page.objects.removed().get(pk=pk)
                self.check_object_permissions(request, page)
                page.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Page.DoesNotExist:
                raise Http404


class PagesWriterList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Выдает списки страниц, принадлежащих авторизованному пользователю. С рядом фильтров, сортировкой и поиском.
    - without_parent=True - вселенные пользователя;
    - in_other_space=True - страницы пользователя с чужими родительскими страницами;
    - is_removed=True - корзина страниц пользователя."""
    permission_classes = [IsAuthenticated]
    serializer_class = ShortPageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PageFilter
    search_fields = ['^title']
    ordering_fields = ['title']

    def get_queryset(self):
        user = self.request.user
        if 'is_removed' not in self.request.query_params:
            return Page.objects.filter(author=user)
        return Page.objects.all_obj().filter(author=user)


