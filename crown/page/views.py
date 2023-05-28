from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import OnlyAuthorOrReadOnly
from .serializers import CreatePageSerializer, PageSerializer


class PageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def list(self, request):
        pass

    @swagger_auto_schema(request_body=CreatePageSerializer, responses={201: PageSerializer()})
    def create(self, request):
        """Создание новой страницы"""
        serializer = CreatePageSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        page = serializer.save(author=request.user)
        return Response(PageSerializer(page).data,
                        status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
