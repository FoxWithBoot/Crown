from django.shortcuts import get_object_or_404
from drf_yasg.openapi import Parameter, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from crown.serializers import FakeRoadTreeSerializer
from crown.permissions import OnlyAuthorIfPrivate
from user.models import User

from .models import Road
from .serializers import CreateRoadSerializer, DefaultRoadSerializer, RoadsTreeSerializer


class RoadViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, OnlyAuthorIfPrivate]

    def list(self, request):
        pass

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

    @swagger_auto_schema(responses={200: FakeRoadTreeSerializer()},
                         manual_parameters=[Parameter('other_author', IN_QUERY,
                                                      'Добавляет в дерево дорог интересующего автора',
                                                      type='int'), ])
    @action(methods=['get'], detail=True)
    def roads_tree(self, request, pk):
        """Возвращает дерево дорог по одной дороге. (аналогично subpages_tree)"""
        road = get_object_or_404(Road, pk=pk)
        self.check_object_permissions(request, road)
        parent_road = road.get_root()
        self.check_object_permissions(request, parent_road)
        other_author = request.query_params.getlist('other_author', '')
        try:
            other_author_list = []
            for i in other_author:
                if User.objects.filter(pk=i).exists():
                    other_author_list.append(i)
        except:
            raise ValidationError(detail={"parent": ["Некорректный id автора"]})
        roads_tree = RoadsTreeSerializer(parent_road, context={'origin_author': parent_road.author,
                                                               'user': request.user,
                                                               'other_author_list': other_author_list})
        return Response(roads_tree.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
