from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from crown.permissions import OnlyAuthorIfPrivate
from road.models import Road

from .controller import read_road
from .models import Block
from .serializers import CreateBlockSerializer, BlockSerializer, UpdateBlockSerializer


class BlockViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, OnlyAuthorIfPrivate]

    @swagger_auto_schema(responses={201: BlockSerializer(many=True)})
    def list(self, request, pkr):
        """
        Возвращает блоки контента дороги.
        """
        road = get_object_or_404(Road, pk=pkr)
        self.check_object_permissions(request, road)
        blocks = read_road(road)
        return Response(BlockSerializer(blocks, many=True).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CreateBlockSerializer(), responses={201: BlockSerializer()})
    def create(self, request, pkr):
        """
        Создание блока на конкретной дороге.
        """
        road = get_object_or_404(Road, pk=pkr)
        self.check_object_permissions(request, road)
        serializer = CreateBlockSerializer(data=request.data, context={'road': road})
        serializer.is_valid(raise_exception=True)
        block = serializer.save()
        return Response(BlockSerializer(block).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        pass

    @swagger_auto_schema(request_body=UpdateBlockSerializer(), responses={200: BlockSerializer()})
    def partial_update(self, request, pkr, pk):
        """
        Обновление текста (контента) блока.
        """
        road = get_object_or_404(Road, pk=pkr)
        block = get_object_or_404(Block, pk=pk)
        self.check_object_permissions(request, road)
        serializer = UpdateBlockSerializer(data=request.data, context={'road': road}, instance=block)
        serializer.is_valid(raise_exception=True)
        block = serializer.save()
        return Response(BlockSerializer(block).data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        pass
