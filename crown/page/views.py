from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, generics, mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .controller import get_parent_page
from .models import Page
from .permissions import OnlyAuthorIfPrivate
from .serializers import CreatePageSerializer, DefaultPageSerializer, PagesTreeSerializer


class PageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, OnlyAuthorIfPrivate]

    @swagger_auto_schema(request_body=CreatePageSerializer, responses={201: DefaultPageSerializer()})
    def create(self, request):
        """Создание новой страницы. В теле запроса передается название страницы и родительская страница.
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

    @action(methods=['get'], detail=True)
    def subpages_tree(self, request, pk):
        page = get_object_or_404(Page, pk=pk)
        self.check_object_permissions(request, page)
        parent_page = get_parent_page(page)
        return Response(PagesTreeSerializer(parent_page, context={'user': request.user}).data,
                        status=status.HTTP_200_OK)

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
# class PageReaderList(mixins.ListModelMixin, viewsets.GenericViewSet):
#     permission_classes = [AllowAny]
#     serializer_class = ShortPageSerializer
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_fields = ['parent', 'author']
#     search_fields = ['^title']
#     ordering_fields = ['title']
#
#     def get_queryset(self):
#         if 'in_other_space' in self.request.query_params and 'author' in self.request.query_params:
#             user = self.kwargs['author']
#             return Page.objects.filter(Q(author=user) & ~Q(parent__author=user) & ~Q(parent=None))
#
#         return Page.objects.filter(is_public=True)