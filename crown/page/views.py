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

from .models import Page
from .permissions import OnlyAuthorOrReadOnly
from .serializers import CreatePageSerializer, PageSerializer, ShortPageSerializer


class PageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=CreatePageSerializer, responses={201: PageSerializer()})
    def create(self, request):
        """Создание новой страницы. В теле запроса передается название страницы и родительская страница."""
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


class PageWriterList(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ShortPageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_public', 'parent']
    search_fields = ['^title']
    ordering_fields = []

    def get_queryset(self):
        user = self.request.user
        if 'in_other_space' in self.request.query_params:
            return Page.objects.filter(Q(author=user) & ~Q(parent__author=user) & ~Q(parent__author=None))
        return Page.objects.filter(author=user)


class PageReaderList(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = ShortPageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_public', 'parent']
    search_fields = ['^title']
    ordering_fields = ['title']

    def get_queryset(self):
        return Page.objects.filter(is_public=True)
