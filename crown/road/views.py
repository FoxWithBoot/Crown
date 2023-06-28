from django.db.models import Q
from rest_framework.generics import get_object_or_404
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema

from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

from crown.permissions import OnlyAuthorIfPrivate

from .models import Road
from .serializers import CreateRoadSerializer, DefaultRoadSerializer, UpdateRoadSerializer


class RoadViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, OnlyAuthorIfPrivate]

    @swagger_auto_schema(request_body=CreateRoadSerializer, responses={201: DefaultRoadSerializer()})
    def create(self, request):
        """Создание новой дороги(ветки).
        В теле запроса передается название дороги (необязательно) и родительская дорога."""
        serializer = CreateRoadSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        road = serializer.save(author=request.user)
        return Response(DefaultRoadSerializer(road).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={200: DefaultRoadSerializer()})
    def retrieve(self, request, pk):
        """Получение общей информации о ветке.
                - доступно всем, если дорога публична;
                - доступно только автору, если дорога приватна;"""
        road = get_object_or_404(Road, pk=pk)
        self.check_object_permissions(request, road)
        return Response(DefaultRoadSerializer(road).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=UpdateRoadSerializer(), responses={200: DefaultRoadSerializer()})
    def partial_update(self, request, pk):
        """
        Обновление заголовка ветки и статуса ее публикации.
        При снятии с публикации корневой ветки снимается с публикации и ее страница.
        При снятии с публикации ветки (дороги) снимаются с публикации ее ветки-потомки.
        При публикации ветки публикуются ее предки и страница.
        Публикация не доступна если, одна из дорог-предков не опубликована и принадлежит другому пользователю.
        """
        road = get_object_or_404(Road, pk=pk)
        self.check_object_permissions(request, road)
        serializer = UpdateRoadSerializer(data=request.data, context={'user': request.user}, instance=road)
        serializer.is_valid(raise_exception=True)
        road = serializer.save()
        return Response(DefaultRoadSerializer(road).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={204: ''})
    def destroy(self, request, pk):
        """
        Полное удаление ветки.
        Если удаляется корневая ветка, то безвозвратно удаляется и вся страница.
        """
        road = get_object_or_404(Road, pk=pk)
        self.check_object_permissions(request, road)
        if road.parent is None:
            road.page.delete()
        else:
            road.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoadWriterList(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Выдает список дорог(веток) пользователя на чужих страницах.
    Фильтрация по странице, автору страницы, публичности, автору родительской ветки, удаленности.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DefaultRoadSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['page', 'page__author', 'is_public', 'parent__author', 'is_removed']
    search_fields = ['^title']
    ordering_fields = ['title']

    def get_queryset(self):
        user = self.request.user
        return Road.objects.all_obj().filter(Q(author=user) & ~Q(parent__author=user) & ~Q(parent=None))
