from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import RoadViewSet, RoadWriterList

router = DefaultRouter()
router.register('roads', RoadViewSet, basename='roads')
router.register('roads-writer-list', RoadWriterList, basename='roads-writer-list')
urlpatterns = [path('road/<int:pkr>/', include('block.urls'))]
urlpatterns += router.urls


