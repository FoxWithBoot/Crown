from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserRegistrationSerializer


class UserAPIView(APIView):
    @swagger_auto_schema(request_body=UserRegistrationSerializer, responses={status.HTTP_201_CREATED: ''})
    def post(self, request):
        """Регистрация пользователя"""
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
