from rest_framework.generics import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from crown.permissions import OnlyAuthorIfPrivate
from road.models import Road

from .controller import read_road
from .serializers import CreateBlockSerializer, BlockSerializer


class BlockViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, OnlyAuthorIfPrivate]

    def list(self, request, pkr):
        """
        Возвращает блоки контента дороги.
        """
        road = get_object_or_404(Road, pk=pkr)
        self.check_object_permissions(request, road)
        blocks = read_road(road)
        return Response(BlockSerializer(blocks, many=True).data, status=status.HTTP_200_OK)

    def create(self, request, pkr):
        road = get_object_or_404(Road, pk=pkr)
        self.check_object_permissions(request, road)
        request.data['road'] = road
        serializer = CreateBlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        block = serializer.save()

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
