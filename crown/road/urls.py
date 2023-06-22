from rest_framework.routers import DefaultRouter

from .views import RoadViewSet, RoadWriterList

router = DefaultRouter()
router.register('road', RoadViewSet, basename='road')
router.register('roads-writer-list', RoadWriterList, basename='roads-writer-list')
urlpatterns = router.urls
