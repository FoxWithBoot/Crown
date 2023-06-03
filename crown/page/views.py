from django.db.models import Q, F
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, generics, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .controller import get_list_public_authors_in_space
from .models import Page
from .permissions import OnlyAuthorIfPrivate
from .serializers import CreatePageSerializer, DefaultPageSerializer, PagesTreeSerializer, FakePagesTreeSerializer, \
    ShortPageSerializerInList
from user.models import User
from user.serializers import UserShortSerializer


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
        return Response(DefaultPageSerializer(page).data,
                        status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={200: DefaultPageSerializer()})
    def retrieve(self, request, pk):
        """Получение общей информации о странице.
        - доступно всем, если страница публична;
        - доступно только автору, если страница приватна;"""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        return Response(DefaultPageSerializer(page).data,
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: FakePagesTreeSerializer()})
    @action(methods=['get'], detail=True)
    def subpages_tree(self, request, pk):
        """Возвращает дерево корневой страницы по одному из ее предков.
        Дополнительный параметр ?other_author=int добавляет в дерево подстраницы интересующего автора.
        - Если пользователь - аноним, то он получит только опубликованные подстраницы автора вселенной
                    и опубликованные подстраницы указанного (дополнительного) автора.
        - Если пользователь - это автор вселенной, то он получит свои подстраницы
                    и опубликованные подстраницы указанного (дополнительного) автора.
        - Если пользователь авторизован, но это не его вселенная, то он получит
                    опубликованные подстраницы автора вселенной, 
                    свои подстраницы в данной вселенной
                    и опубликованные страницы указанного (дополнительного) автора."""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        parent_page = page.get_root()
        other_author = request.query_params.get('other_author', None)
        try:
            other_author = other_author if User.objects.filter(pk=other_author).exists() else parent_page.author
        except:
            raise ValidationError(detail={"parent": ["Некорректный id автора"]})
        pages_tree = PagesTreeSerializer(parent_page, context={'origin_author': parent_page.author,
                                                               'user': request.user,
                                                               'other_author': other_author})
        return Response(pages_tree.data,
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={200: UserShortSerializer(many=True)})
    @action(methods=['get'], detail=True)
    def other_authors_list(self, request, pk):
        """Возвращает список пользователей, которые создавали и публиковали страницы в пределах вселенной страницы pk.
        Нужен для фильтрации дерева страниц по пользователям (см. subpages_tree)"""
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        authors_in_space = get_list_public_authors_in_space(page, request.user)
        authors_list = UserShortSerializer(authors_in_space, many=True)
        return Response(authors_list.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


# class PageWriterList(mixins.ListModelMixin, viewsets.GenericViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = ShortPageSerializer
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_fields = ['is_public', 'parent']
#     search_fields = ['^title']
#     ordering_fields = ['title']
#
#     def get_queryset(self):
#         user = self.request.user
#         if 'in_other_space' in self.request.query_params:
#             return Page.objects.filter(Q(author=user) & ~Q(parent__author=user) & ~Q(parent=None))
#         return Page.objects.filter(author=user)
#
#
# class PageReaderListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
#     permission_classes = [AllowAny]
#     serializer_class = ShortPageSerializerInList
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_fields = ['author']
#     search_fields = ['^title']
#     ordering_fields = ['title']
#
#     def get_queryset(self):
#         return Page.objects.filter(is_public=True)
